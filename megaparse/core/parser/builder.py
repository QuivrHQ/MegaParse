from pathlib import Path
from megaparse.core.parser.megaparser import MegaParser
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
    def build(self, config: ParserConfig) -> MegaParser:
        """
        Build a parser based on the given configuration.

        Args:
            config (ParserDict): The configuration to be used for building the parser.

        Returns:
            MegaParser: The built parser.

        Raises:
            ValueError: If the configuration is invalid.
        """
        return parser_dict[config.method](**config.model_dump())


class FakeParserBuilder:
    def build(self, config: ParserConfig) -> MegaParser:
        """
        Build a fake parser based on the given configuration.

        Args:
            config (ParserDict): The configuration to be used for building the parser.

        Returns:
            MegaParser: The built fake parser.

        Raises:
            ValueError: If the configuration is invalid.
        """

        class FakeParser(MegaParser):
            async def convert(self, file_path: str | Path, **kwargs) -> str:
                return "Fake conversion result"

        return FakeParser()
