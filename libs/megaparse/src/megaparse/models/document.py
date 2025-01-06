from typing import Dict, List

from pydantic import BaseModel
from unstructured.documents.elements import Element


class Document(BaseModel):
    """
    A class to represent a document.
    Really Simplified.
    """

    name: str
    metadata: Dict
    content: List[Element]
