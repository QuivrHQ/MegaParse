from enum import Enum
from typing import List, Optional


class TagEnum(str, Enum):
    """Possible tags for the elements in the file"""

    TABLE = "TABLE"
    TOC = "TOC"
    HEADER = "HEADER"
    IMAGE = "IMAGE"


class SupportedModel(Enum):
    GPT_4O = ("gpt-4o", None)
    GPT_4O_TURBO = ("gpt-4o-turbo", None)
    CLAUDE_3_5_SONNET = ("claude-3-5-sonnet", ["latest", "20241022"])
    CLAUDE_3_OPUS = ("claude-3-opus", ["latest", "20240229"])

    def __init__(self, model_name: str, supported_releases: Optional[List[str]]):
        self.model_name = model_name
        self.supported_releases = supported_releases

    @classmethod
    def is_supported(cls, model_name: str) -> bool:
        # Attempt to match model_name by checking if it starts with a known model name
        for model in cls:
            if model_name.startswith(model.model_name):
                # Extract the release version if available
                release = model_name[len(model.model_name) :].lstrip("-") or None
                # Check if the model supports this release
                if model.supported_releases is None:
                    return True
                return release in model.supported_releases if release else False
        return False
