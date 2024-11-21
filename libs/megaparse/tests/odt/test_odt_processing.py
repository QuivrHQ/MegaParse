from pathlib import Path
from uuid import uuid4

import pytest
from langchain_core.language_models import FakeListChatModel
from megaparse.megaparse import MegaParse
from megaparse.parser.llama import LlamaParser
from megaparse.parser.megaparse_vision import MegaParseVision


@pytest.mark.asyncio
async def test_megaparse_odt_processor():
    p = Path("./tests/odt/file-sample_500kB.odt")
    processor = MegaParse()
    result = await processor.aload(file_path=p)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_megaparse_odt_processor_fail():
    p = Path("./tests/odt/file-sample_500kB.odt")
    parser = LlamaParser(api_key=str(uuid4()))
    processor = MegaParse(parser=parser)
    with pytest.raises(ValueError):
        await processor.aload(file_path=p)

    parser = MegaParseVision(model=FakeListChatModel(responses=["good"]))  # type: ignore
    processor = MegaParse(parser=parser)
    with pytest.raises(ValueError):
        await processor.aload(file_path=p)
