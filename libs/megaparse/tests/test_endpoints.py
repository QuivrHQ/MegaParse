from unittest.mock import patch

import pytest


@pytest.mark.asyncio
@pytest.mark.timeout(30)
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
@pytest.mark.timeout(30)
async def test_parse_file_missing(test_client):
    """Test handling of missing file."""
    response = await test_client.post(
        "/v1/file",
        files={},
        data={
            "method": "unstructured",
            "strategy": "auto",
            "language": "en",
            "check_table": False,
        },
    )
    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_file_unsupported_model(test_client):
    """Test handling of unsupported model."""
    with open("./tests/pdf/sample_pdf.pdf", "rb") as file:
        response = await test_client.post(
            "/v1/file",
            files={"file": ("test.pdf", file)},
            data={
                "method": "unstructured",
                "strategy": "auto",
                "language": "en",
                "check_table": True,
                "model_name": "unsupported-model",
            },
        )
    assert response.status_code == 501
    assert "not supported" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_file_memory_error(test_client):
    """Test handling of memory limit exceeded."""
    with patch("megaparse.api.app._check_free_memory", return_value=False):
        with open("./tests/pdf/sample_pdf.pdf", "rb") as file:
            response = await test_client.post(
                "/v1/file",
                files={"file": ("test.pdf", file)},
                data={
                    "method": "unstructured",
                    "strategy": "auto",
                    "language": "en",
                },
            )
        assert response.status_code == 503
        assert "memory" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_url_endpoint(test_client):
    response = await test_client.post("/v1/url?url=https://www.quivr.com")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Website content parsed successfully",
        "result": "Fake website content",
    }


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_url_invalid(test_client):
    """Test handling of invalid URL."""
    response = await test_client.post("/v1/url?url=invalid-url")
    assert response.status_code == 400
    assert "Failed to load website content" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_url_timeout(test_client):
    """Test handling of URL timeout."""
    with patch("httpx.AsyncClient.get", side_effect=TimeoutError):
        response = await test_client.post("/v1/url?url=https://example.com/test.pdf")
        assert response.status_code == 504
        assert "timed out" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_url_memory_error(test_client):
    """Test handling of memory limit exceeded for URL parsing."""
    with patch("megaparse.api.app._check_free_memory", return_value=False):
        response = await test_client.post("/v1/url?url=https://example.com")
        assert response.status_code == 503
        assert "memory" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_parse_url_too_many_retries(test_client):
    """Test handling of too many retry attempts."""
    with patch("httpx.AsyncClient.get", side_effect=ConnectionError):
        response = await test_client.post("/v1/url?url=https://example.com/test.pdf")
        assert response.status_code == 429
        assert "Failed after" in response.json()["detail"]
