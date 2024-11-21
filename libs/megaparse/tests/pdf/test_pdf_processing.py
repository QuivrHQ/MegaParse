from pathlib import Path

import pytest
from megaparse.megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser


def test_get_default_processors_megaparse():
    megaparse = MegaParse()
    assert type(megaparse.parser) is UnstructuredParser


@pytest.mark.asyncio
async def test_megaparse_pdf_processor():
    p = Path("./tests/pdf/sample_pdf.pdf")
    processor = MegaParse()
    result = await processor.aload(file_path=p)
    assert len(result) > 0
