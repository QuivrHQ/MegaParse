from uuid import UUID

from megaparse_sdk.schema.document import BBOX
from pydantic import BaseModel


class LayoutDetectionOutput(BaseModel):
    bbox_id: UUID
    bbox: BBOX
    prob: float
    label: int
