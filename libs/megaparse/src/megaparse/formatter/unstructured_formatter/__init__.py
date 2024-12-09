from typing import List

from megaparse.formatter.base import BaseFormatter
from unstructured.documents.elements import Element


class UnstructuredFormatter(BaseFormatter):
    async def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> str:
        raise NotImplementedError()
