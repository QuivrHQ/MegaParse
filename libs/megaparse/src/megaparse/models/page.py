from typing import List

from megaparse.predictor.models.base import PageLayout
from megaparse_sdk.schema.parser_config import StrategyEnum
from pydantic import BaseModel, ConfigDict
from pypdfium2._helpers.page import PdfPage
from PIL.Image import Image as PILImage
import numpy as np


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
