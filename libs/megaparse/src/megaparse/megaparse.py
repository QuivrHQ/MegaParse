import asyncio
import os
from pathlib import Path
from typing import IO

from megaparse_sdk.schema.extensions import FileExtension

from megaparse.checker.format_checker import FormatChecker
from megaparse.exceptions.base import ParsingException
from megaparse.parser.base import BaseParser
from megaparse.parser.unstructured_parser import UnstructuredParser


class MegaParse:
    def __init__(
        self,
        parser: BaseParser = UnstructuredParser(),
        format_checker: FormatChecker | None = None,
    ) -> None:
        self.parser = parser
        self.format_checker = format_checker
        self.last_parsed_document: str = ""

    async def aload(
        self,
        file_path: Path | str | None = None,
        file: IO[bytes] | None = None,
        file_extension: str | None = "",
    ) -> str:
        if not (file_path or file):
            raise ValueError("Either file_path or file should be provided")
        if file_path and file:
            raise ValueError("Only one of file_path or file should be provided")

        if file_path:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            file_extension = file_path.suffix
        elif file:
            if not file_extension:
                raise ValueError(
                    "file_extension should be provided when given file argument"
                )
            file.seek(0)

        try:
            FileExtension(file_extension)
        except ValueError:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        if file_extension != ".pdf":
            if self.format_checker:
                raise ValueError(
                    f"Format Checker : Unsupported file extension: {file_extension}"
                )
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f" Unsupported file extension : Parser {self.parser} do not support {file_extension}"
                )

        try:
            parsed_document: str = await self.parser.convert(
                file_path=file_path, file=file
            )
            # @chloe FIXME: format_checker needs unstructured Elements as input which is to change
            # if self.format_checker:
            #     parsed_document: str = await self.format_checker.check(parsed_document)

        except Exception as e:
            raise ParsingException(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def load(self, file_path: Path | str) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_extension: str = file_path.suffix

        if file_extension != ".pdf":
            if self.format_checker:
                raise ValueError(
                    f"Format Checker : Unsupported file extension: {file_extension}"
                )
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f"Parser {self.parser}: Unsupported file extension: {file_extension}"
                )

        try:
            loop = asyncio.get_event_loop()
            parsed_document: str = loop.run_until_complete(
                self.parser.convert(file_path)
            )
            # @chloe FIXME: format_checker needs unstructured Elements as input which is to change
            # if self.format_checker:
            #     parsed_document: str = loop.run_until_complete(
            #         self.format_checker.check(parsed_document)
            #     )

        except Exception as e:
            raise ValueError(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def save(self, file_path: Path | str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w+") as f:
            f.write(self.last_parsed_document)
