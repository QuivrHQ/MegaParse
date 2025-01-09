import logging
import random
import warnings
from pathlib import Path
from typing import BinaryIO, List, Tuple

import numpy as np
import onnxruntime as rt
import pypdfium2 as pdfium
from megaparse_sdk.schema.parser_config import StrategyEnum
from onnxtr.io import DocumentFile
from onnxtr.models import detection_predictor
from onnxtr.models.engine import EngineConfig
from pypdfium2._helpers.page import PdfPage

from megaparse.configs.auto import AutoStrategyConfig, DeviceEnum, TextDetConfig
from megaparse.models.page import Page, PageDimension
from megaparse.predictor.doctr_layout_detector import LayoutPredictor
from megaparse.predictor.models.base import PageLayout

logger = logging.getLogger("megaparse")


class StrategyHandler:
    def __init__(
        self,
        auto_config: AutoStrategyConfig = AutoStrategyConfig(),
        text_det_config: TextDetConfig = TextDetConfig(),
        device: DeviceEnum = DeviceEnum.CPU,
    ) -> None:
        self.config = auto_config
        self.device = device
        general_options = rt.SessionOptions()
        providers = self._get_providers()
        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
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

    def _get_providers(self) -> List[str]:
        prov = rt.get_available_providers()
        logger.info("Available providers:", prov)
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

    def get_strategy_page(
        self, pdfium_page: PdfPage, onnxtr_page: PageLayout
    ) -> StrategyEnum:
        # assert (
        #     p_width == onnxtr_page.dimensions[1]
        #     and p_height == onnxtr_page.dimensions[0]
        # ), "Page dimensions do not match"
        text_coords = []
        # Get all the images in the page
        for obj in pdfium_page.get_objects():
            if obj.type == 1:
                text_coords.append(obj.get_pos())

        p_width, p_height = int(pdfium_page.get_width()), int(pdfium_page.get_height())

        pdfium_canva = np.zeros((int(p_height), int(p_width)))

        for coords in text_coords:
            # (left,bottom,right, top)
            # 0---l--------------R-> y
            # |
            # B   (x0,y0)
            # |
            # T                 (x1,y1)
            # ^
            # x
            x0, y0, x1, y1 = (
                p_height - coords[3],
                coords[0],
                p_height - coords[1],
                coords[2],
            )
            x0 = max(0, min(p_height, int(x0)))
            y0 = max(0, min(p_width, int(y0)))
            x1 = max(0, min(p_height, int(x1)))
            y1 = max(0, min(p_width, int(y1)))
            pdfium_canva[x0:x1, y0:y1] = 1

        onnxtr_canva = np.zeros((int(p_height), int(p_width)))
        for block in onnxtr_page.bboxes:
            x0, y0 = block.bbox[0]
            x1, y1 = block.bbox[1]
            x0 = max(0, min(int(x0 * p_width), int(p_width)))
            y0 = max(0, min(int(y0 * p_height), int(p_height)))
            x1 = max(0, min(int(x1 * p_width), int(p_width)))
            y1 = max(0, min(int(y1 * p_height), int(p_height)))
            onnxtr_canva[y0:y1, x0:x1] = 1

        intersection = np.logical_and(pdfium_canva, onnxtr_canva)
        union = np.logical_or(pdfium_canva, onnxtr_canva)
        iou = np.sum(intersection) / np.sum(union)
        if iou < self.config.auto_page_threshold:
            return StrategyEnum.HI_RES
        return StrategyEnum.FAST

    def determine_strategy(
        self,
        file: BinaryIO | Path | bytes,
        max_samples: int = 5,
        strategy: StrategyEnum = StrategyEnum.AUTO,
    ) -> List[Page]:
        if isinstance(file, BinaryIO):
            file = file.read()  # onnxtr expects a file as AbstractPath or bytes
        logger.info("Determining strategy...")
        pdfium_document = pdfium.PdfDocument(file)

        if strategy == StrategyEnum.FAST:
            mp_pages = []
            for i, pdfium_page in enumerate(pdfium_document):
                mp_pages.append(
                    Page(
                        strategy=strategy,
                        text_detections=None,
                        rasterized=pdfium_page.render().to_pil(),
                        page_size=PageDimension(
                            width=pdfium_page.get_width(),
                            height=pdfium_page.get_height(),
                        ),
                        page_index=i,
                        pdfium_elements=pdfium_page,
                    )
                )
            return mp_pages

        onnxtr_document = DocumentFile.from_pdf(file)
        layout_predictor = LayoutPredictor(self.det_predictor)

        # if len(pdfium_document) > max_samples:
        #     sample_pages_index = random.sample(range(len(onnxtr_document)), max_samples)
        #     onnxtr_document = [onnxtr_document[i] for i in sample_pages_index]
        #     pdfium_document = [pdfium_document[i] for i in sample_pages_index]

        onnxtr_document_layout = layout_predictor(onnxtr_document)

        mp_pages: List[Page] = []

        for pdfium_page, onnxtr_page in zip(
            pdfium_document, onnxtr_document_layout, strict=True
        ):
            strategy = self.get_strategy_page(pdfium_page, onnxtr_page)
            mp_pages.append(
                Page(
                    strategy=strategy,
                    text_detections=onnxtr_page,
                    rasterized=pdfium_page.render().to_pil(),  # FIXME check
                    page_size=PageDimension(
                        width=pdfium_page.get_width(), height=pdfium_page.get_height()
                    ),
                    page_index=onnxtr_page.page_index,
                    pdfium_elements=pdfium_page,
                )
            )

        if isinstance(pdfium_document, pdfium.PdfDocument):
            pdfium_document.close()

        return mp_pages
