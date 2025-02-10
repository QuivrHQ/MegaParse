import os

import pypdfium2
import pytest
from megaparse.megaparse import MegaParse
from megaparse.utils.strategy import determine_global_strategy
from megaparse_sdk.schema.parser_config import StrategyEnum

ocr_pdfs = os.listdir("./tests/pdf/ocr")
native_pdfs = os.listdir("./tests/pdf/native")

megaparse = MegaParse()


@pytest.mark.parametrize("hi_res_pdf", ocr_pdfs)
def test_hi_res_strategy(hi_res_pdf):
    if hi_res_pdf == "0168004.pdf":
        pytest.skip("Skip 0168004.pdf as it is flaky currently")

    pdf_doc = pypdfium2.PdfDocument(f"./tests/pdf/ocr/{hi_res_pdf}")
    pages = megaparse.extract_page_strategies(pdf_doc)
    assert (
        determine_global_strategy(
            pages, megaparse.config.auto_config.document_threshold
        )
        == StrategyEnum.HI_RES
    )


@pytest.mark.parametrize("native_pdf", native_pdfs)
def test_fast_strategy(native_pdf):
    if native_pdf == "0168029.pdf":
        pytest.skip("Skip 0168029.pdf as it is too long to process")

    pdf_doc = pypdfium2.PdfDocument(f"./tests/pdf/native/{native_pdf}")
    pages = megaparse.extract_page_strategies(pdf_doc)

    assert (
        determine_global_strategy(
            pages, megaparse.config.auto_config.document_threshold
        )
        == StrategyEnum.FAST
    )
