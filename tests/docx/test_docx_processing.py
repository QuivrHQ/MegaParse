from pathlib import Path
from uuid import uuid4

import pytest

from langchain_openai import ChatOpenAI
from megaparse.parser.llama import LlamaParser
from megaparse.parser.megaparse_vision import MegaParseVision
from megaparse.main import MegaParse


@pytest.mark.asyncio
async def test_megaparse_docx_processor():
    p = Path("./tests/docx/sample.docx")
    processor = MegaParse()
    result = await processor.aload(file_path=p)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_megaparse_docx_processor_fail():
    p = Path("./tests/docx/sample.docx")
    parser = LlamaParser(api_key=str(uuid4()))
    processor = MegaParse(parser=parser)
    with pytest.raises(ValueError):
        await processor.aload(file_path=p)

    parser = MegaParseVision(model=ChatOpenAI(model="gpt-4o", api_key=str(uuid4())))  # type: ignore
    processor = MegaParse(parser=parser)
    with pytest.raises(ValueError):
        await processor.aload(file_path=p)
