from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .languages import Language
from .supported_models import SupportedModel


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


class ParseFileConfig(BaseModel):
    llm_model_name: SupportedModel = SupportedModel.GPT_4
    method: ParserType = ParserType.UNSTRUCTURED
    strategy: StrategyEnum = StrategyEnum.AUTO
    check_table: bool = False
    language: Language = Language.ENGLISH
    parsing_instruction: Optional[str] = None
