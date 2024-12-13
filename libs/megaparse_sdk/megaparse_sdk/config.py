from pydantic import BaseModel, FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict


class MegaParseConfig(BaseSettings):
    """
    Configuration for the Megaparse SDK.
    """

    model_config = SettingsConfigDict(env_prefix="megaparse_")
    api_key: str | None = None
    url: str = "https://megaparse.tooling.quivr.app"
    timeout: int = 600
    max_retries: int = 3


class SSLConfig(BaseModel):
    ssl_key_file: FilePath
    ssl_cert_file: FilePath
    ca_cert_file: FilePath | None = None


class ClientNATSConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEGAPARSE_NATS_",
        env_file=(".env.local", ".env"),
        env_nested_delimiter="__",
        extra="ignore",
    )
    subject: str = "parsing"
    endpoint: str = "https://tests@nats.tooling.quivr.app:4222"
    timeout: float = 20
    max_retries: int = 5
    backoff: float = 3
    connect_timeout: int = 5
    reconnect_time_wait: int = 1
    max_reconnect_attempts: int = 20
    ssl_config: SSLConfig | None = None
