from uuid import UUID

from megaparse.predictor.models.base import BBOX
from pydantic import BaseModel


class LayoutDetectionOutput(BaseModel):
    bbox_id: UUID
    bbox: BBOX
    prob: float
    label: int
