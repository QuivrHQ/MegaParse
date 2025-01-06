from typing import List

from megaparse.formatter.base import BaseFormatter
from unstructured.documents.elements import Element


class TableFormatter(BaseFormatter):
    async def aformat_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> List[Element]:
        raise NotImplementedError()

    def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> List[Element]:
        raise NotImplementedError()
