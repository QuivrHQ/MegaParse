from enum import Enum, auto
from typing import Dict

from pydantic import BaseModel, Field

from megaparse_sdk.schema.document import Document


class MPErrorType(Enum):
    MEMORY_LIMIT = auto()
    INTERNAL_SERVER_ERROR = auto()
    MODEL_NOT_SUPPORTED = auto()
    DOWNLOAD_ERROR = auto()
    PARSING_ERROR = auto()


class ParseError(BaseModel):
    mp_err_code: MPErrorType
    message: str


class MPOutputType(str, Enum):
    PARSE_OK = "parse_file_ok"
    PARSE_ERR = "parse_file_err"


class MPOutput(BaseModel):
    output_type: MPOutputType
    result: str | Document | None
    err: ParseError | None = None
    metadata: Dict[str, str] = Field(default_factory=dict)
