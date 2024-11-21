import pytest
from llama_parse.utils import Language
from megaparse.megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.megaparse_sdk import MegaParseSDK
from megaparse_sdk.megaparse_sdk.utils.type import StrategyEnum


@pytest.mark.skip("slow test")
def test_load():
    parser = UnstructuredParser(model=None)
    megaparse = MegaParse(parser)
    response = megaparse.load("./tests/data/dummy.pdf")
    print(response)
    assert response.strip("\n") == "Dummy PDF download"


# @pytest.mark.skip("slow test")
@pytest.mark.asyncio
async def test_load_SDK():
    megaparse = MegaParseSDK()
    data = {
        "strategy": StrategyEnum.FAST,
        "language": Language.FRENCH,
    }
    response = await megaparse.file.upload("./tests/data/dummy.pdf", **data)
    print(response["result"])
    assert response["result"].strip("\n") == "# Dummy PDF download"
