from enum import Enum
from llama_parse.utils import Language
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel


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


class ParserConfig(BaseModel):
    """Parser configuration model."""

    method: ParserType = ParserType.UNSTRUCTURED
    strategy: StrategyEnum = StrategyEnum.AUTO
    model: BaseChatModel | None = None
    language: Language = Language.ENGLISH
    parsing_instruction: str | None = None
