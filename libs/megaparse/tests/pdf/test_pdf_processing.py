from pathlib import Path

import pypdfium2
import pytest
from megaparse.configs.auto import (
    DeviceEnum,
    MegaParseConfig,
)
from megaparse.megaparse import MegaParse
from megaparse.utils.strategy import determine_global_strategy
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum


@pytest.fixture
def native_pdf() -> Path:
    p = Path("./tests/pdf/sample_native.pdf")
    return p


@pytest.fixture
def scanned_pdf() -> Path:
    p = Path("./tests/pdf/sample_pdf.pdf")
    return p


# def test_get_default_processors_megaparse():
#     megaparse = MegaParse()
#     assert type(megaparse.parser) is UnstructuredParser


@pytest.mark.asyncio
@pytest.mark.parametrize("pdf_name", ["scanned_pdf", "native_pdf"])
async def test_async_megaparse_pdf_processor_file_path(pdf_name, request):
    pdf = request.getfixturevalue(pdf_name)
    processor = MegaParse(config=MegaParseConfig(device=DeviceEnum.COREML))
    result = await processor.aload(file_path=pdf)
    assert len(str(result)) > 0


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
        assert len(str(result)) > 0


def test_strategy_native(native_pdf):
    processor = MegaParse()
    pdf_doc = pypdfium2.PdfDocument(native_pdf)

    pages = processor.extract_page_strategies(pdf_doc)

    assert (
        determine_global_strategy(
            pages, processor.config.auto_config.document_threshold
        )
        == StrategyEnum.FAST
    )
    pdf_doc.close()


def test_strategy_scanned(scanned_pdf):
    processor = MegaParse()
    pdf_doc = pypdfium2.PdfDocument(scanned_pdf)
    pages = processor.extract_page_strategies(pdf_doc)
    assert (
        determine_global_strategy(
            pages, processor.config.auto_config.document_threshold
        )
        == StrategyEnum.HI_RES
    )
    pdf_doc.close()
