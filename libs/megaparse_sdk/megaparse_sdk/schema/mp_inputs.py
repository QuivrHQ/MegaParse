import base64
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field, field_serializer, field_validator

from .parser_config import ParseFileConfig


class FileInput(BaseModel):
    file_name: str
    file_size: int
    data: bytes

    @field_validator("data", mode="before")
    def decode_data(cls, value):
        if isinstance(value, str):
            try:
                return base64.b64decode(value)
            except Exception:
                raise ValueError("Invalid Base64 encoding for the 'data' field.")
        return value

    # TODO: this is slow !!! Move to reading bytes directly from bucket storage
    # append bytes with CRC32
    @field_serializer("data", return_type=str)
    def serialize_data(self, data: bytes, _info):
        return base64.b64encode(data).decode("utf-8")


class MPParseType(str, Enum):
    PARSE_FILE = "parse_file"
    PARSE_URL = "parse_url"


class ParseFileInput(BaseModel):
    mp_parse_type: Literal[MPParseType.PARSE_FILE] = MPParseType.PARSE_FILE
    file_input: FileInput
    parse_config: ParseFileConfig


class ParseUrlInput(BaseModel):
    mp_parse_type: Literal[MPParseType.PARSE_URL] = MPParseType.PARSE_URL
    url: str


class MPInput(BaseModel):
    input: Union[ParseFileInput, ParseUrlInput] = Field(
        ..., discriminator="mp_parse_type"
    )
