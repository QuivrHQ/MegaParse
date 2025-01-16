from typing import List

import numpy as np
from megaparse_sdk.schema.parser_config import StrategyEnum
from pypdfium2._helpers.page import PdfPage

from megaparse.models.page import Page
from megaparse.predictor.models.base import PageLayout


def get_page_strategy(
    pdfium_page: PdfPage, onnxtr_page: PageLayout | None, threshold: float
) -> StrategyEnum:
    if onnxtr_page is None:
        return StrategyEnum.FAST
    text_coords = []
    # Get all the images in the page
    for obj in pdfium_page.get_objects():
        if obj.type == 1:  # type: ignore
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
    sum_intersection = np.sum(intersection)
    sum_union = np.sum(union)
    iou = sum_intersection / sum_union if sum_union != 0 else 0
    if iou < threshold:
        return StrategyEnum.HI_RES
    return StrategyEnum.FAST


def determine_global_strategy(pages: List[Page], threshold: float) -> StrategyEnum:
    count = sum(1 for page in pages if page.strategy == StrategyEnum.HI_RES)
    if count / len(pages) > threshold:
        return StrategyEnum.HI_RES
    return StrategyEnum.FAST
