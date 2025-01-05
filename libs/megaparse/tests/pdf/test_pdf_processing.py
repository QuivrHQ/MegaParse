from pathlib import Path

import pytest
from megaparse.megaparse import MegaParse
from megaparse.parser.strategy import StrategyHandler
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum

strategy_handler = StrategyHandler()


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
@pytest.mark.parametrize("pdf_name", ["scanned_pdf", "native_pdf"])
async def test_async_megaparse_pdf_processor_file_path(pdf_name, request):
    pdf = request.getfixturevalue(pdf_name)
    processor = MegaParse()
    result = await processor.aload(file_path=pdf)
    assert len(result) > 0


@pytest.mark.parametrize("pdf_name", ["scanned_pdf", "native_pdf"])
def test_sync_megaparse_pdf_processor_file_path(pdf_name, request):
    pdf = request.getfixturevalue(pdf_name)
    processor = MegaParse()
    result = processor.load(file_path=pdf)
    assert len(result) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("pdf_name", ["scanned_pdf", "native_pdf"])
async def test_megaparse_pdf_processor_file(pdf_name, request):
    pdf = request.getfixturevalue(pdf_name)
    processor = MegaParse()
    with open(pdf, "rb") as f:
        result = await processor.aload(file=f, file_extension=FileExtension.PDF)
        assert len(result) > 0


def test_strategy(scanned_pdf, native_pdf):
    strategy = strategy_handler.determine_strategy(
        scanned_pdf,
    )
    assert strategy == StrategyEnum.HI_RES

    strategy = strategy_handler.determine_strategy(
        native_pdf,
    )
    assert strategy == StrategyEnum.FAST
