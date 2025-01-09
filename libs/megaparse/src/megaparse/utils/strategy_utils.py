from typing import List

from megaparse.configs.auto import AutoStrategyConfig
from megaparse.models.page import Page
from megaparse_sdk.schema.parser_config import StrategyEnum


def need_hi_res(
    pages: List[Page], auto_config: AutoStrategyConfig = AutoStrategyConfig()
) -> bool:
    need_ocr = 0
    for page in pages:
        if page.strategy == StrategyEnum.HI_RES:
            need_ocr += 1

    return (need_ocr / len(pages)) > auto_config.auto_document_threshold
