import logging
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pypdfium2 as pdfium
from megaparse_sdk.schema.parser_config import StrategyEnum
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfImage

logger = logging.getLogger("megaparse")


def get_strategy_page(
    page: PdfPage,
    threshold=0.5,
) -> StrategyEnum:
    total_page_area = page.get_width() * page.get_height()
    total_image_area = 0
    images_coords = []
    # Get all the images in the page
    for obj in page.get_objects():
        if isinstance(obj, PdfImage):
            images_coords.append(obj.get_pos())

    canva = np.zeros((int(page.get_height()), int(page.get_width())))
    for coords in images_coords:
        p_width, p_height = int(page.get_width()), int(page.get_height())
        x1 = max(0, min(p_width, int(coords[0])))
        y1 = max(0, min(p_height, int(coords[1])))
        x2 = max(0, min(p_width, int(coords[2])))
        y2 = max(0, min(p_height, int(coords[3])))
        canva[y1:y2, x1:x2] = 1
    # Get the total area of the images
    total_image_area = np.sum(canva)

    if total_image_area / total_page_area > threshold:
        return StrategyEnum.HI_RES
    return StrategyEnum.FAST


def determine_strategy(file: str | Path | bytes | BinaryIO) -> StrategyEnum:
    logger.info("Determining strategy...")
    need_ocr = 0
    document = pdfium.PdfDocument(file)
    for page in document:
        strategy = get_strategy_page(page)
        need_ocr += strategy == StrategyEnum.HI_RES
    doc_need_ocr = (need_ocr / len(document)) > 0.2
    document.close()

    if doc_need_ocr:
        logger.info("Using HI_RES strategy")
        return StrategyEnum.HI_RES
    logger.info("Using FAST strategy")
    return StrategyEnum.FAST
