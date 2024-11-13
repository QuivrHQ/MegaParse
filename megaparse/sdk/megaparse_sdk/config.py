from pydantic_settings import BaseSettings, SettingsConfigDict


class MegaparseConfig(BaseSettings):
    """
    Configuration for the Megaparse SDK.
    """

    model_config = SettingsConfigDict(env_prefix="megaparse_")
    api_key: str | None = None
    url: str = "https://megaparse.tooling.quivr.app"
    timeout: int = 600
