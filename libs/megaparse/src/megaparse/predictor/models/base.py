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

    def to_numpy(self):
        return np.array(
            [self.top_left.x, self.top_left.y, self.bottom_right.x, self.bottom_right.y]
        )


class BlockLayout(BaseModel):
    bbox: BBOX
    objectness_score: float
    block_type: BlockType


class PageLayout:
    __slots__ = [
        "bboxes",
        "page_index",
        "dimensions",
        "orientation",
        "origin_page_shape",
    ]
    bboxes: List[BlockLayout]
    page_index: int
    dimensions: Tuple[int, ...]
    orientation: Tuple[int, float] | Literal[0]
    origin_page_shape: Tuple[int, ...]

    def __init__(self, bboxes, page_index, dimensions, orientation, origin_page_shape):
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
