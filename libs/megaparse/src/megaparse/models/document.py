import uuid
from typing import Any, Dict, List, Optional, Tuple

from megaparse.predictor.models.base import BBOX
from pydantic import BaseModel, Field, field_validator


class Point2D(BaseModel):
    """
    A class to represent a 2D point

    """

    x: float
    y: float


class Block(BaseModel):
    """
    A class to represent a block

    """

    block_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    metadata: Dict[str, Any]  # FIXME: TBD @Amine
    bbox: Optional[BBOX] = (
        None  # (x0,y0),(x1, y1) Coordinates are given as Relative positions to the page they are in
    )
    page_range: Optional[Tuple[int, int]] = Field(
        default=None
    )  # (start_page, end_page)

    @field_validator("page_range")
    def validate_range(cls, value):
        if value is None:
            return None
        start, end = value
        if start > end:
            raise ValueError(
                "The first value of the page range must be less than the second value"
            )
        return value


class TextBlock(Block):
    """
    A class to represent a text block

    """

    text: str

    def __str__(self):
        return self.text


class TitleBlock(TextBlock):
    """
    A class to represent a title block

    """

    def __str__(self):
        return f"# {self.text}"


class SubTitleBlock(TextBlock):
    """
    A class to represent a subtitle block
    """

    depth: int

    def __str__(self):
        heading_level = min(self.depth + 1, 6)
        return f"{'#' * heading_level} {self.text}"


class ImageBlock(Block):
    """
    A class to represent an image block
    """

    text: Optional[str] = None
    caption: Optional[str] = "unknown"

    def __str__(self) -> str:
        return f"[Image: {self.caption}]"


class TableBlock(ImageBlock):
    """
    A class to represent a table block

    """

    def __str__(self):
        return self.text if self.text else f"[Table : {self.caption}]"


class ListElement(BaseModel):
    """
    A class to represent a list element

    """

    text: str
    depth: int


class ListBlock(TextBlock):
    """
    A class to represent a list block

    """

    list_elements: List[ListElement]

    # rajouter fonction pydantic pour compute l attribut

    def __str__(self):
        return "\n".join(
            f"{' ' * (2 * element.depth)}* {element.text}"
            for element in self.list_elements
        )


class HeaderBlock(TextBlock):
    """
    A class to represent a header block

    """

    def __str__(self):
        return f"{'='*len(self.text)}\n\n{self.text}\n\n{'='*len(self.text)}"


class FooterBlock(TextBlock):
    """
    A class to represent a footer block

    """

    def __str__(self):
        return f"{'='*len(self.text)}\n\n{self.text}\n\n{'='*len(self.text)}"


class SectionBlock(Block):
    """
    A class to represent a section block

    """

    title: str
    depth: int
    content: List[Block]

    def __str__(self):
        lines = []
        lines.extend(str(block) for block in self.content)
        return "\n".join(lines)


class TOCItem(BaseModel):
    title: str
    depth: int
    page_range: Tuple[int, int] = Field(...)  # (start_page, end_page)

    @field_validator("page_range")
    def validate_range(cls, value):
        start, end = value
        if start >= end:
            raise ValueError(
                "The first value of the page range must be less than the second value"
            )
        return value

    def __str__(self):
        start_page, end_page = self.page_range
        page_info = (
            f"page {start_page}"
            if start_page == end_page
            else f"pages {start_page}-{end_page}"
        )
        return f"{' ' * (2 * self.depth)}* {self.title} ({page_info})"


class TOC(BaseModel):
    content: List[TOCItem]

    @property
    def text(self) -> str:
        return "\n".join(str(item) for item in self.content)

    def __str__(self):
        return self.text


class Document(BaseModel):
    """

    A class to represent a document

    """

    file_name: Optional[str] = None
    table_of_contents: Optional[TOC] = None
    metadata: Dict[str, Any]  # TBD @Amine
    content: List[Block]
    detection_origin: str

    def __str__(self) -> str:
        lines = []

        # If there's a table of contents, include it
        if self.table_of_contents:
            lines.append("Table of Contents:")
            # Use TOC’s own string-building property or method
            lines.append(self.table_of_contents.text)

        # Print each block’s text representation
        lines.extend(str(block) for block in self.content)

        return "\n".join(lines)
