from pathlib import Path

from megaparse.formatter.base import BaseFormatter
from megaparse_sdk.schema.document import Document


class TableFormatter(BaseFormatter):
    def format(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        raise NotImplementedError("Subclasses should implement this method")

    async def aformat(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        raise NotImplementedError("Subclasses should implement this method")
