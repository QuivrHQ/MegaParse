import pytest


@pytest.mark.asyncio
async def test_parse_file_endpoint(test_client):
    # Simulate a request to the parse endpoint
    with open("./tests/pdf/sample_pdf.pdf", "rb") as file:
        response = await test_client.post(
            "/v1/file",
            files={"file": ("test.pdf", file)},
            data={
                "method": "unstructured",
                "strategy": "auto",
                "language": "en",
                "check_table": False,
            },
        )
    assert response.status_code == 200
    assert response.json()["message"] == "File parsed successfully"


@pytest.mark.asyncio
async def test_parse_url_endpoint(test_client):
    response = await test_client.post("/v1/url?url=https://www.quivr.com")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Website content parsed successfully",
        "result": "Fake website content",
    }
