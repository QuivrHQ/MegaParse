from enum import Enum
from typing import List, Literal, NamedTuple, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel


class Point2D(NamedTuple):
    x: float
    y: float


class BlockType(str, Enum):
    TEXT = "text"


class BBOX(NamedTuple):
    top_left: Point2D
    bottom_right: Point2D


class BlockLayout(BaseModel):
    bbox: BBOX
    objectness_score: float
    block_type: BlockType


class PageLayout:
    __slots__ = ["bboxes", "page_index", "dimensions", "orientation"]
    bboxes: List[BlockLayout]
    page_index: int
    dimensions: Tuple[int, ...]
    orientation: Tuple[int, float] | Literal[0]

    def __init__(self, bboxes, page_index, dimensions, orientation):
        self.bboxes = bboxes
        self.page_index = page_index
        self.dimensions = dimensions
        self.orientation = orientation

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
