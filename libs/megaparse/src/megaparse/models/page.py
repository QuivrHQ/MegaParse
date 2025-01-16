from typing import List
from megaparse.predictor.models.base import PageLayout
from megaparse_sdk.schema.parser_config import StrategyEnum
from PIL.Image import Image as PILImage
from pydantic import BaseModel, ConfigDict
from pypdfium2._helpers.page import PdfPage


class PageDimension(BaseModel):
    """
    A class to represent a page dimension
    """

    width: float
    height: float


class Page(BaseModel):
    """
    A class to represent a page
    """

    strategy: StrategyEnum
    text_detections: PageLayout | None = None
    rasterized: PILImage | None = None
    page_size: PageDimension
    page_index: int
    pdfium_elements: PdfPage

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GatewayDocument(BaseModel):
    """
    A class to represent a Gateway MegaParse Document, which is a container of pages.
    """

    file_name: str
    pages: List[Page]
