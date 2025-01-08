import os

import pytest
from megaparse.parser.strategy import StrategyHandler
from megaparse_sdk.schema.parser_config import StrategyEnum

ocr_pdfs = os.listdir("./tests/pdf/ocr")
native_pdfs = os.listdir("./tests/pdf/native")

strategy_handler = StrategyHandler()


@pytest.mark.parametrize("hi_res_pdf", ocr_pdfs)
def test_hi_res_strategy(hi_res_pdf):
    strategy = strategy_handler.determine_strategy(
        f"./tests/pdf/ocr/{hi_res_pdf}",
    )
    assert strategy == StrategyEnum.HI_RES


@pytest.mark.parametrize("native_pdf", native_pdfs)
def test_fast_strategy(native_pdf):
    strategy = strategy_handler.determine_strategy(
        f"./tests/pdf/native/{native_pdf}",
    )
    assert strategy == StrategyEnum.FAST
