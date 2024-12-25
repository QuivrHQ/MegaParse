import pytest
from megaparse import MegaParse
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.unstructured_parser import UnstructuredParser

PARSER_LIST = [
    UnstructuredParser,
    DoctrParser,
]  # LlamaParser, MegaParseVision are long and costly to test


@pytest.mark.parametrize("parser", PARSER_LIST)
def test_sync_parsers(parser):
    parser = parser()
    megaparse = MegaParse(parser)
    response = megaparse.load("./tests/data/dummy.pdf")
    print(response)
    assert response
    assert len(response) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("parser", PARSER_LIST)
async def test_async_parsers(parser):
    parser = parser()
    megaparse = MegaParse(parser)
    response = await megaparse.aload("./tests/data/dummy.pdf")
    print(response)
    assert len(response) > 0
