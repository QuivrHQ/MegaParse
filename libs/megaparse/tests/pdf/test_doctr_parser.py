from pathlib import Path

import pytest
from megaparse.parser.doctr_parser import DoctrParser


@pytest.mark.asyncio
async def test_doctr_parser():
    # scanned pdf
    p = Path("./tests/pdf/sample_pdf.pdf")
    processor = DoctrParser()
    result = await processor.convert(file_path=p)
    assert len(result) > 0
