from typing import List

from megaparse.predictor.models.base import PageLayout
from megaparse_sdk.schema.parser_config import StrategyEnum
from numpy.typing import NDArray
from pydantic import BaseModel
from pypdfium2._helpers.page import PdfPage


class PageDimension(BaseModel):
    """
    A class to represent a page dimension
    """

    width: int
    height: int


class Page(BaseModel):
    """
    A class to represent a page
    """

    strategy: StrategyEnum
    text_detections: PageLayout
    rasterized: NDArray
    page_size: PageDimension
    page_index: int
    pdfium_elements: PdfPage
