import pytest_asyncio
from httpx import AsyncClient
from megaparse.api.app import app, parser_builder_dep
from megaparse.core.parser.builder import (
    FakeParserBuilder,
)
from httpx import ASGITransport


@pytest_asyncio.fixture(scope="function")
async def test_client():
    print("Setting up test_client fixture")

    def fake_parser_builder():
        return FakeParserBuilder()

    app.dependency_overrides[parser_builder_dep] = fake_parser_builder
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides = {}
