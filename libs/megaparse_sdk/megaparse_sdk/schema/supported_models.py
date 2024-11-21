from enum import Enum


class SupportedModel(str, Enum):
    """Supported models enumeration."""

    # OpenAI Models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"

    # Anthropic Models
    CLAUDE_3_5_SONNET_LATEST = "claude-3-5-sonnet-latest"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_5_HAIKU_LATEST = "claude-3-5-haiku-latest"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_OPUS_LATEST = "claude-3-opus-latest"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    def __str__(self):
        return self.value

    @classmethod
    def is_supported(cls, model_name: str) -> bool:
        """Check if the model is supported."""
        return model_name in cls.__members__.values()

    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Get the list of supported models."""
        return list(cls.__members__.values())
