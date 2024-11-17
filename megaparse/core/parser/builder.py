from pathlib import Path
from typing import IO
from megaparse.core.parser.base import BaseParser
from megaparse.core.parser.type import ParserConfig

from megaparse.core.parser.llama import LlamaParser
from megaparse.core.parser.megaparse_vision import MegaParseVision
from megaparse.core.parser.unstructured_parser import UnstructuredParser

parser_dict: dict[str, type] = {
    "unstructured": UnstructuredParser,
    "llama_parser": LlamaParser,
    "megaparse_vision": MegaParseVision,
}


class ParserBuilder:
    def build(self, config: ParserConfig) -> BaseParser:
        """
        Build a parser based on the given configuration.

        Args:
            config (ParserDict): The configuration to be used for building the parser.

        Returns:
            BaseParser: The built parser.

        Raises:
            ValueError: If the configuration is invalid.
        """
        return parser_dict[config.method](**config.model_dump())


class FakeParserBuilder:
    def build(self, config: ParserConfig) -> BaseParser:
        """
        Build a fake parser based on the given configuration.

        Args:
            config (ParserDict): The configuration to be used for building the parser.

        Returns:
            BaseParser: The built fake parser.

        Raises:
            ValueError: If the configuration is invalid.
        """

        class FakeParser(BaseParser):
            async def convert(
                self,
                file_path: str | Path | None = None,
                file: IO[bytes] | None = None,
                **kwargs,
            ) -> str:
                print("Fake parser is converting the file")
                return "Fake conversion result"

        return FakeParser()
