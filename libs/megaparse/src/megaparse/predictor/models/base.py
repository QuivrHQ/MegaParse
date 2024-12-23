from typing import List, Literal, Tuple

import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel

Point2D = tuple[float, float]


class BlockLayout(BaseModel):
    bbox: Tuple[Point2D, Point2D]
    objectness_score: float


class PageLayout(BaseModel):
    bboxes: List[BlockLayout]
    page_index: int
    dimensions: Tuple[int, ...]
    orientation: Tuple[int, float] | Literal[0]

    def render(self, page_array: np.ndarray, output_path: str = "page_layout.png"):
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

        # Save the image
        image.save(output_path)
        print(f"Page layout rendered and saved to {output_path}")
