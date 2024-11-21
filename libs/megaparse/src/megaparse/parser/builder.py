from megaparse_sdk.schema.parser_config import ParseFileConfig

from megaparse.parser.base import BaseParser
from megaparse.parser.llama import LlamaParser
from megaparse.parser.megaparse_vision import MegaParseVision
from megaparse.parser.unstructured_parser import UnstructuredParser

parser_dict: dict[str, type] = {
    "unstructured": UnstructuredParser,
    "llama_parser": LlamaParser,
    "megaparse_vision": MegaParseVision,
}


class ParserBuilder:
    def build(self, config: ParseFileConfig) -> BaseParser:
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
