import os

import pytest
from megaparse.parser.strategy import determine_strategy
from megaparse_sdk.schema.parser_config import StrategyEnum
from megaparse_sdk.config import MegaParseConfig

ocr_pdfs = os.listdir("./tests/pdf/ocr")
native_pdfs = os.listdir("./tests/pdf/native")
config = MegaParseConfig()


@pytest.mark.parametrize("hi_res_pdf", ocr_pdfs)
def test_hi_res_strategy(hi_res_pdf):
    strategy = determine_strategy(
        f"./tests/pdf/ocr/{hi_res_pdf}",
        threshold_per_page=config.auto_page_threshold,
        threshold_pages_ocr=config.auto_document_threshold,
    )
    assert strategy == StrategyEnum.HI_RES


@pytest.mark.parametrize("native_pdf", native_pdfs)
def test_fast_strategy(native_pdf):
    strategy = determine_strategy(
        f"./tests/pdf/native/{native_pdf}",
        threshold_per_page=config.auto_page_threshold,
        threshold_pages_ocr=config.auto_document_threshold,
    )
    assert strategy == StrategyEnum.FAST
