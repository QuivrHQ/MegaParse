from pathlib import Path

import pytest

from langchain_openai import ChatOpenAI
from megaparse.core.parser.llama import LlamaParser
from megaparse.core.parser.type import StrategyEnum
from megaparse.core.parser.unstructured_parser import UnstructuredParser
from megaparse.core.parser.megaparse_vision import MegaParseVision
from megaparse.core.megaparse import MegaParse


def test_get_default_processors_megaparse():
    megaparse = MegaParse()
    assert type(megaparse.parser) is UnstructuredParser


@pytest.mark.asyncio
async def test_megaparse_pdf_processor():
    p = Path("./tests/pdf/sample_pdf.pdf")
    processor = MegaParse()
    result = await processor.aload(file_path=p)
    assert len(result) > 0
