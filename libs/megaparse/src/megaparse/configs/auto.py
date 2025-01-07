from enum import Enum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class TextDetConfig(BaseModel):
    det_arch: str = "fast_base"
    batch_size: int = 2
    assume_straight_pages: bool = True
    preserve_aspect_ratio: bool = True
    symmetric_pad: bool = True
    load_in_8_bit: bool = False


class AutoStrategyConfig(BaseModel):
    auto_page_threshold: float = 0.6
    auto_document_threshold: float = 0.2


class TextRecoConfig(BaseModel):
    reco_arch: str = "crnn_vgg16_bn"
    batch_size: int = 512


class DeviceEnum(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    COREML = "coreml"


class MegaParseConfig(BaseSettings):
    """
    Configuration for Megaparse.
    """

    model_config = SettingsConfigDict(
        env_prefix="MEGAPARSE_",
        env_file=(".env.local", ".env"),
        env_nested_delimiter="__",
        extra="ignore",
        use_enum_values=True,
    )
    text_det_config: TextDetConfig = TextDetConfig()
    text_reco_config: TextRecoConfig = TextRecoConfig()
    auto_parse_config: AutoStrategyConfig = AutoStrategyConfig()
    device: DeviceEnum = DeviceEnum.CPU
