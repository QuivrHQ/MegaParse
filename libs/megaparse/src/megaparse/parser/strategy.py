import logging
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pypdfium2 as pdfium
from megaparse_sdk.schema.parser_config import StrategyEnum
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfImage

logger = logging.getLogger("megaparse")


def get_strategy_page(page: PdfPage, threshold_image_page: float) -> StrategyEnum:
    total_page_area = page.get_width() * page.get_height()
    total_image_area = 0
    images_coords = []
    # Get all the images in the page
    for obj in page.get_objects():
        if isinstance(obj, PdfImage):
            images_coords.append(obj.get_pos())

    canva = np.zeros((int(page.get_height()), int(page.get_width())))
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
        p_width, p_height = int(page.get_width()), int(page.get_height())
        x0 = max(0, min(p_height, int(x0)))
        y0 = max(0, min(p_width, int(y0)))
        x1 = max(0, min(p_height, int(x1)))
        y1 = max(0, min(p_width, int(y1)))
        canva[x0:x1, y0:y1] = 1
        # Get the total area of the images
    total_image_area = np.sum(canva)

    if total_image_area / total_page_area > threshold_image_page:
        return StrategyEnum.HI_RES
    return StrategyEnum.FAST


def determine_strategy(
    file: str | Path | bytes | BinaryIO,
    threshold_pages_ocr: float = 0.2,
    threshold_image_page: float = 0.4,
) -> StrategyEnum:
    logger.info("Determining strategy...")
    need_ocr = 0
    document = pdfium.PdfDocument(file)
    for page in document:
        strategy = get_strategy_page(page, threshold_image_page=threshold_image_page)
        need_ocr += strategy == StrategyEnum.HI_RES

    doc_need_ocr = (need_ocr / len(document)) > threshold_pages_ocr
    document.close()

    if doc_need_ocr:
        logger.info("Using HI_RES strategy")
        return StrategyEnum.HI_RES
    logger.info("Using FAST strategy")
    return StrategyEnum.FAST
