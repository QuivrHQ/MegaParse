from abc import ABC
from pathlib import Path
from typing import List, Union

from langchain_core.language_models.chat_models import BaseChatModel
from megaparse.models.document import Document


class BaseFormatter(ABC):
    """
    A class used to improve the layout of elements, particularly focusing on converting HTML tables to markdown tables.
    Attributes
    ----------
    model : BaseChatModel
        An instance of a chat model used to process and improve the layout of elements.
    Methods
    -------
    improve_layout(elements: List[Element]) -> List[Element]
        Processes a list of elements, converting HTML tables to markdown tables and improving the overall layout.
    """

    def __init__(self, model: BaseChatModel | None = None):
        self.model = model

    def format(
        self, document: Document, file_path: Path | str | None = None
    ) -> Union[Document, str]:
        raise NotImplementedError("Subclasses should implement this method")

    async def aformat(
        self, document: Document, file_path: Path | str | None = None
    ) -> Union[Document, str]:
        raise NotImplementedError("Subclasses should implement this method")
