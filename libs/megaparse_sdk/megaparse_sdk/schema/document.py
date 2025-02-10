import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Self, Tuple

import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field, field_validator


class Point2D(NamedTuple):
    x: float
    y: float


class BlockType(str, Enum):
    TEXT = "text"


class BBOX(NamedTuple):
    top_left: Point2D
    bottom_right: Point2D

    def to_numpy(self):
        return np.array(
            [self.top_left.x, self.top_left.y, self.bottom_right.x, self.bottom_right.y]
        )

    def iou(self, other: Self):
        x1 = max(self.top_left.x, other.top_left.x)
        y1 = max(self.top_left.y, other.top_left.y)
        x2 = min(self.bottom_right.x, other.bottom_right.x)
        y2 = min(self.bottom_right.y, other.bottom_right.y)
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area_self = (self.bottom_right.x - self.top_left.x) * (
            self.bottom_right.y - self.top_left.y
        )
        area_other = (other.bottom_right.x - other.top_left.x) * (
            other.bottom_right.y - other.top_left.y
        )
        union = area_self + area_other - intersection
        return intersection / union


class BlockLayout(BaseModel):
    bbox: BBOX
    objectness_score: float
    block_type: BlockType


class TextDetection:
    __slots__ = [
        "bboxes",
        "page_index",
        "dimensions",
        "orientation",
        "origin_page_shape",
    ]

    def __init__(
        self,
        bboxes: List[BlockLayout],
        page_index: int,
        dimensions: Tuple[int, ...],
        orientation: Tuple[int, float] | Literal[0],
        origin_page_shape,
    ):
        self.bboxes = bboxes
        self.page_index = page_index
        self.dimensions = dimensions
        self.orientation = orientation
        self.origin_page_shape = origin_page_shape

    def __repr__(self) -> str:
        return f"PageLayout(bboxes={self.bboxes}, page_index={self.page_index}, dimensions={self.dimensions}, orientation={self.orientation})"

    def render(
        self, page_array: np.ndarray, output_path: Optional[str] = "page_layout.png"
    ):
        """
        Render the page layout with bounding boxes on the original page image.

        Args:
            page_array (np.ndarray): The original page image as a NumPy array.
            output_path (str): The path to save the rendered image.
        """
        # Convert the NumPy array to a PIL image
        image = Image.fromarray(page_array)
        draw = ImageDraw.Draw(image)
        width, height = self.dimensions

        # Draw each bounding box
        for block in self.bboxes:
            bbox = block.bbox
            top_left = (bbox[0][0] * height, bbox[0][1] * width)
            bottom_right = (bbox[1][0] * height, bbox[1][1] * width)
            draw.rectangle([top_left, bottom_right], outline="red", width=2)

        if output_path:
            # Save the image
            image.save(output_path)
            print(f"Page layout saved to {output_path}")
        return image

    def get_loc_preds(self) -> np.ndarray:
        """
        Get the location predictions of the bounding boxes.

        Returns:
            np.ndarray: The location predictions as a NumPy array.
        """
        loc_preds = np.array([block.bbox.to_numpy() for block in self.bboxes])
        return loc_preds

    def get_objectness_scores(self) -> np.ndarray:
        """
        Get the objectness scores of the bounding boxes.

        Returns:
            np.ndarray: The objectness scores as a NumPy array.
        """
        objectness_scores = np.array([block.objectness_score for block in self.bboxes])
        return objectness_scores

    def get_origin_page_shapes(self) -> np.ndarray:
        """
        Get the original page shapes.

        Returns:
            np.ndarray: The original page shapes as a NumPy array.
        """
        origin_page_shapes = np.array([self.origin_page_shape for _ in self.bboxes])
        return origin_page_shapes

    def get_orientations(self) -> np.ndarray:
        """
        Get the orientations of the bounding boxes.

        Returns:
            np.ndarray: The orientations as a NumPy array.
        """
        orientations = np.array([self.orientation for _ in self.bboxes])
        return orientations


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


class UndefinedBlock(TextBlock):
    """
    A class to represent a text block

    """

    pass


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

    depth: int = 0

    def __str__(self):
        heading_level = min(self.depth + 1, 6)
        return f"{'#' * heading_level} {self.text}"


class CaptionBlock(TextBlock):
    """
    A class to represent a caption block
    """

    pass


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


class ListElementBlock(TextBlock):
    """
    A class to represent a list element

    """

    depth: int = 0


class ListBlock(Block):
    """
    A class to represent a list block

    """

    list_elements: List[ListElementBlock]

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
    content: List[Block]
    detection_origin: str
    metadata: Dict[str, Any]

    def __str__(self) -> str:
        lines = []

        # If there's a table of contents, include it
        if self.table_of_contents:
            lines.append("Table of Contents:")
            # Use TOC’s own string-building property or method
            lines.append(self.table_of_contents.text)

        # Print each block’s text representation
        lines.extend(str(block) + "\n" for block in self.content)

        return "\n".join(lines)

    def clean(self):
        """
        Clean the Document element by :
        - Merging Caption in ImageBlock
        - Merging continuous list items elements into ListBlock
        - Add Depth to Title / SubTitle / ListElementBlock
        - Creating sections
        - Creating TOC
        """

        # Merge caption in ImageBlock simplified
        i = 0
        list_elements_stack = []
        while i < len(self.content) - 1:
            if isinstance(self.content[i], ListElementBlock):
                list_elements_stack.append(self.content[i])
                self.content.pop(i)
                continue
            else:
                if list_elements_stack:
                    self.content.insert(
                        i, ListBlock(list_elements=list_elements_stack, metadata={})
                    )
                    list_elements_stack = []

            if isinstance(self.content[i], ImageBlock) and isinstance(
                self.content[i + 1], CaptionBlock
            ):
                self.content[i].caption = str(self.content[i + 1])  # type: ignore
                self.content.pop(i + 1)
            elif isinstance(self.content[i], CaptionBlock) and isinstance(
                self.content[i + 1], ImageBlock
            ):
                self.content[i + 1].caption = str(self.content[i])  # type: ignore
                self.content.pop(i)

            i += 1
