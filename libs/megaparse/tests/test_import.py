import pytest
from megaparse import MegaParse


@pytest.mark.skip("slow test")
def test_load():
    megaparse = MegaParse()
    response = megaparse.load("./tests/data/dummy.pdf")
    print(response)
    assert response.strip("\n") == "Dummy PDF download"
