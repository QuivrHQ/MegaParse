from pathlib import Path

import pypdfium2 as pdfium
import pytest
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.parser_config import StrategyEnum


@pytest.mark.asyncio
async def test_unstructured_parser():
    # scanned pdf
    p = Path("./tests/pdf/mlbook.pdf")
    processor = UnstructuredParser(strategy=StrategyEnum.FAST)
    result = await processor.convert(file_path=p)
    assert len(result) > 0


def test_pdfium():
    # scanned pdf
    p = Path("./tests/pdf/mlbook.pdf")
    document = pdfium.PdfDocument(p)

    objs = []
    for page in document:
        for obj in page.get_objects():
            objs.append(obj)

    document.close()
