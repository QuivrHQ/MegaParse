from typing import List

from unstructured.documents.elements import Element

from megaparse.formatter.base import BaseFormatter


class UnstructuredFormatter(BaseFormatter):
    async def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> str:
        raise NotImplementedError()
