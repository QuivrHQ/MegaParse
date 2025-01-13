import warnings
from pathlib import Path
from typing import IO, Any, List, Tuple

import numpy as np
import onnxruntime as rt
import pypdfium2 as pdfium
from megaparse.configs.auto import (
    AutoStrategyConfig,
    DeviceEnum,
    TextDetConfig,
    TextRecoConfig,
)
from megaparse.models.page import Page, PageDimension
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse.predictor.models.base import BBOX, BlockLayout, BlockType, PageLayout
from megaparse.utils.strategy_utils import need_hi_res
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum
from numpy.typing import NDArray
from onnxtr.io import DocumentFile
from onnxtr.models import detection_predictor, recognition_predictor
from onnxtr.models.detection.predictor import DetectionPredictor
from onnxtr.models.engine import EngineConfig
from onnxtr.utils.geometry import (
    detach_scores,
    extract_crops,
    extract_rcrops,
)
from pypdfium2._helpers.page import PdfPage
from onnxtr.models.builder import DocumentBuilder


def get_strategy_page(
    pdfium_page: PdfPage, onnxtr_page: PageLayout, page_threshold: float = 0.6
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
    if iou < page_threshold:
        return StrategyEnum.HI_RES
    return StrategyEnum.FAST


def _get_providers(device=DeviceEnum.CPU) -> List[str]:
    prov = rt.get_available_providers()
    print("Available providers:", prov)
    if device == DeviceEnum.CUDA:
        # TODO: support openvino, directml etc
        if "CUDAExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CUDAExecutionProvider in list of available providers"
            )
        return ["TensorrtExecutionProvider", "CUDAExecutionProvider"]
    elif device == DeviceEnum.COREML:
        if "CoreMLExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CoreMLExecutionProvider in list of available providers"
            )
        return ["CoreMLExecutionProvider"]
    elif device == DeviceEnum.CPU:
        return ["CPUExecutionProvider"]
    else:
        warnings.warn(
            "Device not supported, using CPU",
            UserWarning,
            stacklevel=2,
        )
        return ["CPUExecutionProvider"]


def validate_input(
    file_path: Path | str | None = None,
    file: IO[bytes] | None = None,
    file_extension: str | FileExtension | None = None,
) -> FileExtension:
    if not (file_path or file):
        raise ValueError("Either file_path or file should be provided")

    if file_path and file:
        raise ValueError("Only one of file_path or file should be provided")

    if file_path and file is None:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_extension = file_path.suffix
    elif file and file_path is None:
        if not file_extension:
            raise ValueError(
                "file_extension should be provided when given file argument"
            )
        file.seek(0)
    else:
        raise ValueError("Either provider a file_path or file")

    if isinstance(file_extension, str):
        try:
            file_extension = FileExtension(file_extension)
        except ValueError:
            raise ValueError(f"Unsupported file extension: {file_extension}")
    return file_extension


def _generate_crops(
    pages: list[np.ndarray],
    loc_preds: list[np.ndarray],
    channels_last: bool,
    assume_straight_pages: bool = False,
    assume_horizontal: bool = False,
) -> list[list[np.ndarray]]:
    if assume_straight_pages:
        crops = [
            extract_crops(page, _boxes[:, :4], channels_last=channels_last)
            for page, _boxes in zip(pages, loc_preds)
        ]
    else:
        crops = [
            extract_rcrops(
                page,
                _boxes[:, :4],
                channels_last=channels_last,
                assume_horizontal=assume_horizontal,
            )
            for page, _boxes in zip(pages, loc_preds)
        ]
    return crops


def _prepare_crops(
    pages: list[np.ndarray],
    loc_preds: list[np.ndarray],
    channels_last: bool,
    assume_straight_pages: bool = False,
    assume_horizontal: bool = False,
) -> tuple[list[list[np.ndarray]], list[np.ndarray]]:
    crops = _generate_crops(
        pages, loc_preds, channels_last, assume_straight_pages, assume_horizontal
    )

    # Avoid sending zero-sized crops
    is_kept = [
        [all(s > 0 for s in crop.shape) for crop in page_crops] for page_crops in crops
    ]
    crops = [
        [crop for crop, _kept in zip(page_crops, page_kept) if _kept]
        for page_crops, page_kept in zip(crops, is_kept)
    ]
    loc_preds = [_boxes[_kept] for _boxes, _kept in zip(loc_preds, is_kept)]

    return crops, loc_preds


def _process_predictions(
    loc_preds: list[np.ndarray],
    word_preds: list[tuple[str, float]],
    crop_orientations: list[dict[str, Any]],
) -> tuple[list[np.ndarray], list[list[tuple[str, float]]], list[list[dict[str, Any]]]]:
    text_preds = []
    crop_orientation_preds = []
    if len(loc_preds) > 0:
        # Text & crop orientation predictions at page level
        _idx = 0
        for page_boxes in loc_preds:
            text_preds.append(word_preds[_idx : _idx + page_boxes.shape[0]])
            crop_orientation_preds.append(
                crop_orientations[_idx : _idx + page_boxes.shape[0]]
            )
            _idx += page_boxes.shape[0]

    return loc_preds, text_preds, crop_orientation_preds


def main():
    file_path = Path("./tests/pdf/sample_pdf.pdf")
    strategy = StrategyEnum.AUTO
    device = DeviceEnum.COREML
    ocr_parser = DoctrParser()
    default_parser = UnstructuredParser(strategy=StrategyEnum.FAST)
    file_extension = validate_input(file_path=file_path)
    with open(file_path, "rb") as file:
        pdfium_document = pdfium.PdfDocument(file)
        rasterized_pages: list[np.ndarray] = [
            np.array(page.render().to_pil(scale=2)) for page in pdfium_document
        ]
        ##-----------------------------------
        ## GET PAGES
        ##-----------------------------------
        mp_pages = []
        if strategy == StrategyEnum.FAST:
            parsed_document = default_parser.convert(
                file=file,
                file_extension=file_extension,
            )
        else:
            text_det_config = TextDetConfig()
            general_options = rt.SessionOptions()
            providers = _get_providers(device=device)
            engine_config = EngineConfig(
                session_options=general_options,
                providers=providers,
            )
            det_predictor = detection_predictor(
                arch=text_det_config.det_arch,
                assume_straight_pages=text_det_config.assume_straight_pages,
                preserve_aspect_ratio=text_det_config.preserve_aspect_ratio,
                symmetric_pad=text_det_config.symmetric_pad,
                batch_size=text_det_config.batch_size,
                load_in_8_bit=text_det_config.load_in_8_bit,
                engine_cfg=engine_config,
            )
            if any(page.ndim != 3 for page in rasterized_pages):
                raise ValueError(
                    "incorrect input shape: all pages are expected to be multi-channel 2D images."
                )

            orientations = None
            general_pages_orientations = None
            # Localize text elements
            loc_preds, out_maps = det_predictor(rasterized_pages, return_maps=True)
            # FIXME: For simplicity we do not care about page orientation rn
            # FIXME: similaly we don't care about straighten page

            # Detach objectness scores from loc_preds
            loc_preds, objectness_scores = detach_scores(loc_preds)  # type: ignore[arg-type]

            # FIXME: Do not care about hooks here
            # # Apply hooks to loc_preds if any
            # for hook in hooks:
            #     loc_preds = hook(loc_preds)
            all_pages_layouts = []
            for page_index, (page, loc_pred, objectness_score) in enumerate(
                zip(rasterized_pages, loc_preds, objectness_scores, strict=True)
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
                all_pages_layouts.append(
                    PageLayout(
                        bboxes=block_layouts,
                        page_index=page_index,
                        dimensions=page.shape[:2],
                        orientation=general_pages_orientations[page_index]
                        if general_pages_orientations is not None
                        else 0,
                    )
                )
            for pdfium_page, onnxtr_page, rasterized_page in zip(
                pdfium_document, all_pages_layouts, rasterized_pages, strict=True
            ):
                strategy = get_strategy_page(pdfium_page, onnxtr_page)
                mp_pages.append(
                    Page(
                        strategy=strategy,
                        text_detections=onnxtr_page,
                        rasterized=rasterized_page,
                        page_size=PageDimension(
                            width=pdfium_page.get_width(),
                            height=pdfium_page.get_height(),
                        ),
                        page_index=onnxtr_page.page_index,
                        pdfium_elements=pdfium_page,
                    )
                )

            ##-----------------------------------
            ## GET PARSER BASE ON CHOSE STRATEGY
            ##-----------------------------------
            if file_extension != FileExtension.PDF or strategy == StrategyEnum.FAST:
                parser = default_parser
            elif strategy == StrategyEnum.HI_RES:
                parser = ocr_parser
            else:
                if need_hi_res(mp_pages, AutoStrategyConfig()):
                    parser = ocr_parser
                else:
                    parser = default_parser

            ##-----------------------------------
            ## PARSE FILE
            ##-----------------------------------
            if isinstance(parser, UnstructuredParser):
                parsed_document = parser.convert(
                    file=file,
                    pages=mp_pages,
                    file_extension=file_extension,
                )
            else:
                origin_page_shapes: List[Tuple[int, int]] = [
                    (page.shape[0], page.shape[1]) for page in rasterized_pages
                ]

                reco_config = TextRecoConfig()
                reco_predictor = recognition_predictor(
                    arch=reco_config.reco_arch,
                    batch_size=reco_config.batch_size,
                    load_in_8_bit=text_det_config.load_in_8_bit,
                    engine_cfg=engine_config,
                )

                # Crop images
                crops, loc_preds = _prepare_crops(
                    rasterized_pages,
                    loc_preds,  # type: ignore[arg-type]
                    channels_last=True,
                    assume_straight_pages=True,  # FIXME: To change
                    assume_horizontal=True,  # FIXME: To change
                )
                # Rectify crop orientation and get crop orientation predictions
                crop_orientations: Any = []

                # Identify character sequences
                word_preds = reco_predictor(
                    [crop for page_crops in crops for crop in page_crops]
                )
                if not crop_orientations:
                    crop_orientations = [
                        {"value": 0, "confidence": None} for _ in word_preds
                    ]

                boxes, text_preds, crop_orientations = _process_predictions(
                    loc_preds, word_preds, crop_orientations
                )
                doc_builder = DocumentBuilder()
                parsed_document = doc_builder(
                    rasterized_pages,
                    boxes,
                    objectness_scores,
                    text_preds,
                    origin_page_shapes,
                    crop_orientations,
                    orientations,
                    None,
                )

        print(parsed_document)


if __name__ == "__main__":
    main()
