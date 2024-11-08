from typing import List, Union
from abc import ABC
from langchain_core.language_models.chat_models import BaseChatModel
from unstructured.documents.elements import Element


# TODO: Implement the Formatter class @Chloe
class Formatter(ABC):
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

    async def format(
        self, elements: Union[List[Element], str], file_path: str | None = None
    ) -> Union[List[Element], str]:
        if isinstance(elements, list):
            return await self.format_elements(elements, file_path)
        return await self.format_string(elements, file_path)

    async def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> Union[List[Element], str]:
        raise NotImplementedError("Subclasses should implement this method")

    async def format_string(
        self, text: str, file_path: str | None = None
    ) -> Union[List[Element], str]:
        raise NotImplementedError("Subclasses should implement this method")
