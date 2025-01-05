from pydantic_settings import BaseSettings, SettingsConfigDict


class AutoStrategyConfig(BaseSettings):
    """
    Configuration for Megaparse.
    """

    model_config = SettingsConfigDict(
        env_prefix="MEGAPARSE_",
        env_file=(".env.local", ".env"),
        env_nested_delimiter="__",
        extra="ignore",
    )
    auto_page_threshold: float = 0.6
    auto_document_threshold: float = 0.2
    det_arch: str = "fast_base"
    batch_size: int = 2
    use_gpu: bool = False
