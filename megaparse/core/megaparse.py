import asyncio
import os
from pathlib import Path

from megaparse.api.utils.type import FileExtension
from megaparse.core.parser.unstructured_parser import UnstructuredParser

from megaparse.core.parser import MegaParser
from megaparse.core.formatter.formatter import Formatter
from typing import List


class MegaParse:
    def __init__(
        self,
        parser: MegaParser = UnstructuredParser(),
        formatters: List[Formatter] | None = None,
    ) -> None:
        self.parser = parser
        self.formatters = formatters
        self.last_parsed_document: str = ""

    async def aload(self, file_path: Path | str) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_extension: str = file_path.suffix
        try:
            FileExtension(file_extension)
        except ValueError:
            raise ValueError("Unsupported file extension: {file_extension}")

        if file_extension != ".pdf":
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f" Unsupported file extension : Parser {self.parser} do not support {file_extension}"
                )

        try:
            parsed_document = await self.parser.convert(file_path)
            if self.formatters:
                for formatter in self.formatters:
                    parsed_document = await formatter.format(
                        parsed_document, file_path=str(file_path)
                    )

            assert isinstance(parsed_document, str), "The end result should be a string"

        except Exception as e:
            raise ValueError(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def load(self, file_path: Path | str) -> str:
        return asyncio.run(self.aload(file_path))

    def save(self, file_path: Path | str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w+") as f:
            f.write(self.last_parsed_document)
