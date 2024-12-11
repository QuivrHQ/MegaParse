from pathlib import Path

import pytest
from megaparse.megaparse import MegaParse
from megaparse.parser.strategy import determine_strategy
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.parser_config import StrategyEnum


@pytest.fixture
def native_pdf() -> Path:
    p = Path("./tests/pdf/sample_native.pdf")
    return p


@pytest.fixture
def scanned_pdf() -> Path:
    p = Path("./tests/pdf/sample_pdf.pdf")
    return p


def test_get_default_processors_megaparse():
    megaparse = MegaParse()
    assert type(megaparse.parser) is UnstructuredParser


@pytest.mark.asyncio
async def test_megaparse_pdf_processor(scanned_pdf):
    processor = MegaParse()
    result = await processor.aload(file_path=scanned_pdf)
    assert len(result) > 0


def test_strategy(scanned_pdf, native_pdf):
    strategy = determine_strategy(scanned_pdf)
    assert strategy == StrategyEnum.HI_RES

    strategy = determine_strategy(native_pdf)
    assert strategy == StrategyEnum.FAST
