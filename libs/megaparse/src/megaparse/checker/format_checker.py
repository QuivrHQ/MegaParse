from typing import List

from langchain_core.language_models.chat_models import BaseChatModel
from unstructured.documents.elements import Element


# TODO: Implement the FormatChecker class @Chloe
class FormatChecker:
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

    def __init__(self, model: BaseChatModel):
        self.model = model

    def check(self, elements: List[Element]):
        raise NotImplementedError("Method not implemented yet")
