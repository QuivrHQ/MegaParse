from megaparse.core.formatter.formatter import Formatter
from typing import List
from unstructured.documents.elements import Element


class TableFormatter(Formatter):
    async def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> List[Element]:
        raise NotImplementedError()
