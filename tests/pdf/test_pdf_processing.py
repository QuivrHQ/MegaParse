from pathlib import Path
from uuid import uuid4

import pytest

from langchain_openai import ChatOpenAI
from megaparse.parser.llama import LlamaParser
from megaparse.parser.type import StrategyEnum
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse.parser.megaparse_vision import MegaParseVision
from megaparse.main import MegaParse


def test_get_default_processors_megaparse():
    megaparse = MegaParse()
    assert type(megaparse.parser) is UnstructuredParser


@pytest.mark.asyncio
async def test_megaparse_pdf_processor():
    p = Path("./tests/pdf/sample_pdf.pdf")
    processor = MegaParse()
    result = await processor.aload(file_path=p)
    assert len(result) > 0
