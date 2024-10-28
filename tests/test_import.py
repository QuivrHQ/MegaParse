import pytest

from megaparse.main import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser


@pytest.mark.skip("slow test")
def test_load():
    parser = UnstructuredParser(model=None)
    megaparse = MegaParse(parser)
    response = megaparse.load("./tests/data/files/dummy.pdf")
    print(response)
    assert response.strip("\n") == "# Dummy PDF download"
