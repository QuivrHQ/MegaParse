import os

from megaparse.utils.strategy_utils import need_hi_res
import pytest
from megaparse.parser.strategy import StrategyHandler
from megaparse_sdk.schema.parser_config import StrategyEnum

ocr_pdfs = os.listdir("./tests/pdf/ocr")
native_pdfs = os.listdir("./tests/pdf/native")

strategy_handler = StrategyHandler()


@pytest.mark.parametrize("hi_res_pdf", ocr_pdfs)
def test_hi_res_strategy(hi_res_pdf):
    if hi_res_pdf == "0168004.pdf":
        pytest.skip("Skip 0168004.pdf as it is flaky currently")

    with open(f"./tests/pdf/ocr/{hi_res_pdf}", "rb") as f:
        pages = strategy_handler.determine_strategy(
            f,
        )
        assert need_hi_res(pages)


@pytest.mark.parametrize("native_pdf", native_pdfs)
def test_fast_strategy(native_pdf):
    with open(f"./tests/pdf/native/{native_pdf}", "rb") as f:
        pages = strategy_handler.determine_strategy(
            f,
        )
        assert not need_hi_res(pages)
