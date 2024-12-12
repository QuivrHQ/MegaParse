import asyncio
import logging
import os
from pathlib import Path
from typing import IO, BinaryIO

from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum

from megaparse.checker.format_checker import FormatChecker
from megaparse.exceptions.base import ParsingException
from megaparse.parser.base import BaseParser
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.strategy import determine_strategy
from megaparse.parser.unstructured_parser import UnstructuredParser

logger = logging.getLogger("megaparse")


class MegaParse:
    def __init__(
        self,
        parser: BaseParser = UnstructuredParser(strategy=StrategyEnum.FAST),
        ocr_parser: BaseParser = DoctrParser(),
        strategy: StrategyEnum = StrategyEnum.AUTO,
        format_checker: FormatChecker | None = None,
    ) -> None:
        self.strategy = strategy
        self.parser = parser
        self.ocr_parser = ocr_parser
        self.format_checker = format_checker
        self.last_parsed_document: str = ""

    def validate_input(
        self,
        file_path: Path | str | None = None,
        file: IO[bytes] | None = None,
        file_extension: str | FileExtension | None = None,
    ) -> FileExtension:
        if not (file_path or file):
            raise ValueError("Either file_path or file should be provided")

        if file_path and file:
            raise ValueError("Only one of file_path or file should be provided")

        if file_path and file is None:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            file_extension = file_path.suffix
        elif file and file_path is None:
            if not file_extension:
                raise ValueError(
                    "file_extension should be provided when given file argument"
                )
            file.seek(0)
        else:
            raise ValueError("Either provider a file_path or file")

        if isinstance(file_extension, str):
            try:
                file_extension = FileExtension(file_extension)
            except ValueError:
                raise ValueError(f"Unsupported file extension: {file_extension}")

        if file_extension != FileExtension.PDF:
            if self.format_checker:
                raise ValueError(
                    f"Format Checker : Unsupported file extension: {file_extension}"
                )
            # TODO(@chloedia): each parser should have a list of supported extensions
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f" Unsupported file extension : Parser {self.parser} do not support {file_extension}"
                )
        return file_extension

    async def aload(
        self,
        file_path: Path | str | None = None,
        file: BinaryIO | None = None,
        file_extension: str | FileExtension = "",
    ) -> str:
        file_extension = self.validate_input(
            file=file, file_path=file_path, file_extension=file_extension
        )
        try:
            parser = self._select_parser(file_path, file, file_extension)
            logger.info(f"Parsing using {parser.__class__.__name__} parser.")
            parsed_document = await parser.convert(
                file_path=file_path, file=file, file_extension=file_extension
            )
            # @chloe FIXME: format_checker needs unstructured Elements as input which is to change
            # if self.format_checker:
            #     parsed_document: str = await self.format_checker.check(parsed_document
            self.last_parsed_document = parsed_document
            return parsed_document
        except Exception as e:
            raise ParsingException(
                f"Error while parsing file {file_path or file}, file_extension: {file_extension}: {e}"
            )

    def load(
        self,
        file_path: Path | str | None = None,
        file: BinaryIO | None = None,
        file_extension: str | FileExtension = "",
    ) -> str:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.aload(file_path=file_path, file=file, file_extension=file_extension)
        )

    def _select_parser(
        self,
        file_path: Path | str | None = None,
        file: BinaryIO | None = None,
        file_extension: str | FileExtension = "",
    ) -> BaseParser:
        if self.strategy != StrategyEnum.AUTO or file_extension != FileExtension.PDF:
            return self.parser
        if file:
            local_strategy = determine_strategy(file=file)
        if file_path:
            local_strategy = determine_strategy(file=file_path)

        if local_strategy == StrategyEnum.HI_RES:
            return self.ocr_parser
        return self.parser

    def save(self, file_path: Path | str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w+") as f:
            f.write(self.last_parsed_document)
