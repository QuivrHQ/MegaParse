from enum import Enum


class ParserType(str, Enum):
    """Parser type enumeration."""

    UNSTRUCTURED = "unstructured"
    LLAMA_PARSER = "llama_parser"
    MEGAPARSE_VISION = "megaparse_vision"


class StrategyEnum(str, Enum):
    """Method to use for the conversion"""

    FAST = "fast"
    AUTO = "auto"
    HI_RES = "hi_res"
