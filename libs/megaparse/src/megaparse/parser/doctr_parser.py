import logging
import warnings
from typing import Any, List

import numpy as np
import onnxruntime as rt
from megaparse_sdk.schema.extensions import FileExtension
from onnxtr.io import Document
from onnxtr.models import detection_predictor, recognition_predictor
from onnxtr.models._utils import get_language
from onnxtr.models.engine import EngineConfig
from onnxtr.models.predictor.base import _OCRPredictor
from onnxtr.utils.geometry import detach_scores
from onnxtr.utils.repr import NestedObject

from megaparse.configs.auto import DeviceEnum, TextDetConfig, TextRecoConfig
from megaparse.models.document import Document as MPDocument
from megaparse.models.document import ImageBlock, TextBlock
from megaparse.models.page import Page
from megaparse.predictor.models.base import (
    BBOX,
    BlockLayout,
    BlockType,
    PageLayout,
    Point2D,
)

logger = logging.getLogger("megaparse")


class DoctrParser(NestedObject, _OCRPredictor):
    supported_extensions = [FileExtension.PDF]

    def __init__(
        self,
        text_det_config: TextDetConfig = TextDetConfig(),
        text_reco_config: TextRecoConfig = TextRecoConfig(),
        device: DeviceEnum = DeviceEnum.CPU,
        straighten_pages: bool = False,
        detect_orientation: bool = False,
        detect_language: bool = False,
        **kwargs,
    ):
        self.device = device
        general_options = rt.SessionOptions()
        providers = self._get_providers()
        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
        )

        _OCRPredictor.__init__(
            self,
            text_det_config.assume_straight_pages,
            straighten_pages,
            text_det_config.preserve_aspect_ratio,
            text_det_config.symmetric_pad,
            detect_orientation,
            clf_engine_cfg=engine_config,
            **kwargs,
        )

        self.det_predictor = detection_predictor(
            arch=text_det_config.det_arch,
            assume_straight_pages=text_det_config.assume_straight_pages,
            preserve_aspect_ratio=text_det_config.preserve_aspect_ratio,
            symmetric_pad=text_det_config.symmetric_pad,
            batch_size=text_det_config.batch_size,
            load_in_8_bit=text_det_config.load_in_8_bit,
            engine_cfg=engine_config,
        )

        self.reco_predictor = recognition_predictor(
            arch=text_reco_config.reco_arch,
            batch_size=text_reco_config.batch_size,
            load_in_8_bit=text_det_config.load_in_8_bit,
            engine_cfg=engine_config,
        )

        self.detect_orientation = detect_orientation
        self.detect_language = detect_language

    def _get_providers(self) -> List[str]:
        prov = rt.get_available_providers()
        if self.device == DeviceEnum.CUDA:
            # TODO: support openvino, directml etc
            if "CUDAExecutionProvider" not in prov:
                raise ValueError(
                    "onnxruntime can't find CUDAExecutionProvider in list of available providers"
                )
            return ["TensorrtExecutionProvider", "CUDAExecutionProvider"]
        elif self.device == DeviceEnum.COREML:
            if "CoreMLExecutionProvider" not in prov:
                raise ValueError(
                    "onnxruntime can't find CoreMLExecutionProvider in list of available providers"
                )
            return ["CoreMLExecutionProvider"]
        elif self.device == DeviceEnum.CPU:
            return ["CPUExecutionProvider"]
        else:
            warnings.warn(
                "Device not supported, using CPU",
                UserWarning,
                stacklevel=2,
            )
            return ["CPUExecutionProvider"]

    def get_text_detections(self, pages: list[Page], **kwargs) -> List[Page]:
        rasterized_pages = [np.array(page.rasterized) for page in pages]
        # Dimension check
        if any(page.ndim != 3 for page in rasterized_pages):
            raise ValueError(
                "incorrect input shape: all pages are expected to be multi-channel 2D images."
            )

        origin_page_shapes = [page.shape[:2] for page in rasterized_pages]

        # Localize text elements
        loc_preds, out_maps = self.det_predictor(
            rasterized_pages, return_maps=True, **kwargs
        )

        # Detect document rotation and rotate pages
        seg_maps = [
            np.where(
                out_map > self.det_predictor.model.postprocessor.bin_thresh,
                255,
                0,
            ).astype(np.uint8)
            for out_map in out_maps
        ]
        if self.detect_orientation:
            general_pages_orientations, origin_pages_orientations = (
                self._get_orientations(rasterized_pages, seg_maps)
            )
            orientations = [
                {"value": orientation_page, "confidence": None}
                for orientation_page in origin_pages_orientations
            ]
        else:
            orientations = None
            general_pages_orientations = None
            origin_pages_orientations = None
        if self.straighten_pages:
            rasterized_pages = self._straighten_pages(
                rasterized_pages,
                seg_maps,
                general_pages_orientations,
                origin_pages_orientations,
            )
            # update page shapes after straightening
            origin_page_shapes = [page.shape[:2] for page in rasterized_pages]

            # forward again to get predictions on straight pagess
            loc_preds = self.det_predictor(pages, **kwargs)  # type: ignore[assignment]

        # Detach objectness scores from loc_preds
        loc_preds, objectness_scores = detach_scores(loc_preds)  # type: ignore[arg-type]

        # Apply hooks to loc_preds if any
        for hook in self.hooks:
            loc_preds = hook(loc_preds)

        for page_index, (rast_page, loc_pred, objectness_score, page) in enumerate(
            zip(rasterized_pages, loc_preds, objectness_scores, pages, strict=True)
        ):
            block_layouts = []
            for bbox, score in zip(loc_pred, objectness_score, strict=True):
                block_layouts.append(
                    BlockLayout(
                        bbox=BBOX(bbox[:2].tolist(), bbox[2:].tolist()),
                        objectness_score=score,
                        block_type=BlockType.TEXT,
                    )
                )
            page.text_detections = PageLayout(
                bboxes=block_layouts,
                page_index=page_index,
                dimensions=rast_page.shape[:2],
                orientation=orientations[page_index] if orientations is not None else 0,
                origin_page_shape=origin_page_shapes[page_index],
            )

        return pages

    def get_text_recognition(self, pages: List[Page], **kwargs) -> MPDocument:
        assert any(
            page.text_detections is not None for page in pages
        ), "Text detections should be computed before running text recognition"

        rasterized_pages = []
        loc_preds = []
        objectness_scores = []
        orientations = []
        origin_page_shapes = []
        for page in pages:
            page_loc_pred = page.text_detections.get_loc_preds()  # type: ignore
            if page_loc_pred.shape[0] == 0:
                page_loc_pred = np.zeros((0, 4))
            rasterized_pages.append(np.array(page.rasterized))
            loc_preds.append(page_loc_pred)  # type: ignore
            objectness_scores.append(page.text_detections.get_objectness_scores())  # type: ignore
            orientations.append(page.text_detections.get_orientations())  # type: ignore
            origin_page_shapes.append(page.text_detections.get_origin_page_shapes())  # type: ignore
        # Crop images
        crops, loc_preds = self._prepare_crops(
            rasterized_pages,
            loc_preds,  # type: ignore[arg-type]
            channels_last=True,
            assume_straight_pages=self.assume_straight_pages,
            assume_horizontal=self._page_orientation_disabled,
        )
        # Rectify crop orientation and get crop orientation predictions
        crop_orientations: Any = []
        if not self.assume_straight_pages:
            crops, loc_preds, _crop_orientations = self._rectify_crops(crops, loc_preds)
            crop_orientations = [
                {"value": orientation[0], "confidence": orientation[1]}
                for orientation in _crop_orientations
            ]

        # Identify character sequences
        word_preds = self.reco_predictor(
            [crop for page_crops in crops for crop in page_crops], **kwargs
        )
        if not crop_orientations:
            crop_orientations = [{"value": 0, "confidence": None} for _ in word_preds]

        boxes, text_preds, crop_orientations = self._process_predictions(
            loc_preds, word_preds, crop_orientations
        )

        if self.detect_language:
            languages = [
                get_language(" ".join([item[0] for item in text_pred]))
                for text_pred in text_preds
            ]
            languages_dict = [
                {"value": lang[0], "confidence": lang[1]} for lang in languages
            ]
        else:
            languages_dict = None

        # FIXME : Not good return type we want :(
        out = self.doc_builder(
            rasterized_pages,
            boxes,
            objectness_scores,
            text_preds,
            origin_page_shapes,
            crop_orientations,
            orientations,
            languages_dict,
        )
        return self.__to_elements_list(out)

    def __to_elements_list(self, doctr_document: Document) -> MPDocument:
        result = []

        for page_number, page in enumerate(doctr_document.pages):
            for block in page.blocks:
                if len(block.lines) and len(block.artefacts) > 0:
                    raise ValueError(
                        "Block should not contain both lines and artefacts"
                    )
                word_coordinates = [
                    word.geometry for line in block.lines for word in line.words
                ]
                x0 = min(word[0][0] for word in word_coordinates)
                y0 = min(word[0][1] for word in word_coordinates)
                x1 = max(word[1][0] for word in word_coordinates)
                y1 = max(word[1][1] for word in word_coordinates)

                result.append(
                    TextBlock(
                        text=block.render(),
                        bbox=BBOX(
                            top_left=Point2D(x=x0, y=y0),
                            bottom_right=Point2D(x=x1, y=y1),
                        ),
                        metadata={},
                        page_range=(page_number, page_number),
                    )
                )

                for artefact in block.artefacts:
                    result.append(
                        ImageBlock(
                            bbox=BBOX(
                                top_left=Point2D(
                                    x=artefact.geometry[0][0], y=artefact.geometry[0][1]
                                ),
                                bottom_right=Point2D(
                                    x=artefact.geometry[1][0], y=artefact.geometry[1][1]
                                ),
                            ),
                            metadata={},
                            page_range=(page_number, page_number),
                        )
                    )
        return MPDocument(
            metadata={},
            content=result,
            detection_origin="doctr",
        )
