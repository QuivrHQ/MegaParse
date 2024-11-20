from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class MegaparseConfig(BaseSettings):
    """
    Configuration for the Megaparse SDK.
    """

    model_config = SettingsConfigDict(env_prefix="megaparse_")
    api_key: str | None = None
    url: str = "https://megaparse.tooling.quivr.app"
    timeout: int = 600
    max_retries: int = 3


class ClientNATSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="megaparse_nats")
    subject: Literal["parsing"] = "parsing"
    nats_endpoint: str = "https://tests@nats.tooling.quivr.app:4222"
    timeout: int = 600
    max_retries: int = 5
    backoff: int = 3
