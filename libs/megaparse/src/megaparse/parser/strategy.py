import logging
from pathlib import Path
from typing import BinaryIO

from megaparse.predictor.models.base import PageLayout
import numpy as np
import pypdfium2 as pdfium
from megaparse_sdk.schema.parser_config import StrategyEnum
from onnxtr.io import DocumentFile
from onnxtr.models import detection_predictor
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfImage

from megaparse.predictor.doctr_layout_detector import LayoutPredictor

logger = logging.getLogger("megaparse")


def get_strategy_page(
    pdfium_page: PdfPage, onnxtr_page: PageLayout, threshold: float
) -> StrategyEnum:
    print(f"PDFIUM PAGE : {pdfium_page.get_width()} x {pdfium_page.get_height()}")
    print(f"ONNXTR PAGE : {onnxtr_page.dimensions[1]} x {onnxtr_page.dimensions[0]}")
    # assert (
    #     p_width == onnxtr_page.dimensions[1]
    #     and p_height == onnxtr_page.dimensions[0]
    # ), "Page dimensions do not match"
    images_coords = []
    # Get all the images in the page
    for obj in pdfium_page.get_objects():
        if isinstance(obj, PdfImage) or obj.type == 2:
            images_coords.append(obj.get_pos())

    p_width, p_height = int(pdfium_page.get_width()), int(pdfium_page.get_height())

    pdfium_canva = np.zeros((int(p_height), int(p_width)))

    for coords in images_coords:
        # (left,bottom,right, top)
        # 0---l--------------R-> y
        # |
        # B   (x0,y0)
        # |
        # T                 (x1,y1)
        # ^
        # x
        x0, y0, x1, y1 = coords[1], coords[0], coords[3], coords[2]
        x0 = max(0, min(p_height, int(x0)))
        y0 = max(0, min(p_width, int(y0)))
        x1 = max(0, min(p_height, int(x1)))
        y1 = max(0, min(p_width, int(y1)))
        pdfium_canva[x0:x1, y0:y1] = 1

    onnxtr_canva = np.zeros((int(p_height), int(p_width)))
    for block in onnxtr_page.bboxes:
        x0, y0 = block.bbox[0]
        x1, y1 = block.bbox[1]
        x0 = max(0, min(int(x0 * p_height), int(p_height)))
        y0 = max(0, min(int(y0 * p_width), int(p_width)))
        x1 = max(0, min(int(x1 * p_height), int(p_height)))
        y1 = max(0, min(int(y1 * p_width), int(p_width)))
        onnxtr_canva[x0:x1, y0:y1] = 1

    # Calculate the IOU
    intersection = np.logical_and(pdfium_canva, onnxtr_canva)
    union = np.logical_or(pdfium_canva, onnxtr_canva)
    iou = np.sum(intersection) / np.sum(union)

    # print intersection, union, iou
    print(f"IOU : {iou}")
    print(f"UNION : {np.sum(union)}")
    print(f"INTERSECTION : {np.sum(intersection)}")

    if iou > threshold:
        print("Using HI_RES strategy")
        return StrategyEnum.HI_RES
    print("Using FAST strategy")
    return StrategyEnum.FAST


def determine_strategy(
    file: str
    | Path
    | bytes,  # FIXME : Careful here on removing BinaryIO (not handled by onnxtr)
    threshold_pages_ocr: float = 0.2,
    threshold_per_page: float = 0.6,
) -> StrategyEnum:
    logger.info("Determining strategy...")
    need_ocr = 0

    onnxtr_document = DocumentFile.from_pdf(file)
    det_predictor = detection_predictor()
    layout_predictor = LayoutPredictor(det_predictor)
    onnxtr_document_layout = layout_predictor(onnxtr_document)

    pfium_document = pdfium.PdfDocument(file)
    for pdfium_page, onnxtr_page in zip(
        pfium_document, onnxtr_document_layout, strict=True
    ):
        strategy = get_strategy_page(
            pdfium_page, onnxtr_page, threshold=threshold_per_page
        )
        need_ocr += strategy == StrategyEnum.HI_RES

    doc_need_ocr = (need_ocr / len(pfium_document)) > threshold_pages_ocr
    pfium_document.close()

    if doc_need_ocr:
        logger.info("Using HI_RES strategy")
        return StrategyEnum.HI_RES
    logger.info("Using FAST strategy")
    return StrategyEnum.FAST
