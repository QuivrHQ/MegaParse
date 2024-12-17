import os

import pytest
from megaparse.parser.strategy import determine_strategy
from megaparse_sdk.schema.parser_config import StrategyEnum

list_pdf = os.listdir("./tests/pdf/ocr")


@pytest.mark.parametrize("pdf", list_pdf)
def test_strategy_all(pdf):
    strategy = determine_strategy(
        f"./tests/pdf/ocr/{pdf}", threshold_pages_ocr=0.2, threshold_image_page=0.3
    )
    assert strategy == StrategyEnum.HI_RES
