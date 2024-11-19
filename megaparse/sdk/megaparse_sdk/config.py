from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from megaparse.sdk.megaparse_sdk.utils.type import Language, ParserType, StrategyEnum


class MegaparseConfig(BaseSettings):
    """
    Configuration for the Megaparse SDK.
    """

    model_config = SettingsConfigDict(env_prefix="megaparse_")
    api_key: str | None = None
    url: str = "https://megaparse.tooling.quivr.app"
    timeout: int = 600
    max_retries: int = 3


class UploadFileConfig(BaseModel):
    method: ParserType = ParserType.UNSTRUCTURED
    strategy: StrategyEnum = StrategyEnum.AUTO
    check_table: bool = False
    language: Language = Language.ENGLISH
    parsing_instruction: Optional[str] = None
    model_name: str = "gpt-4o"
