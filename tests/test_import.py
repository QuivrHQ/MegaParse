import pytest

from megaparse.main import MegaParse
from langchain_openai import ChatOpenAI
import os
from megaparse.parser.unstructured_parser import UnstructuredParser


@pytest.mark.skip("slow test")
def test_load():
    model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
    parser = UnstructuredParser(model=model)
    megaparse = MegaParse(parser)
    response = megaparse.load("./tests/data/dummy.pdf")
    print(response)
    assert response.strip("\n") == "# Dummy PDF download"
