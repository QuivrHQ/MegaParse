import pytest_asyncio
from httpx import AsyncClient
from megaparse.api.app import app, parser_builder_dep, get_playwright_loader
from megaparse.core.parser.builder import (
    FakeParserBuilder,
)
from httpx import ASGITransport
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_core.documents import Document


@pytest_asyncio.fixture(scope="function")
async def test_client():
    print("Setting up test_client fixture")

    def fake_parser_builder():
        return FakeParserBuilder()

    def fake_playwright_loader():
        class FakePlaywrightLoader(PlaywrightURLLoader):
            async def aload(self):
                return [Document(page_content="Fake website content")]

        return FakePlaywrightLoader(urls=[], remove_selectors=["header", "footer"])

    app.dependency_overrides[parser_builder_dep] = fake_parser_builder
    app.dependency_overrides[get_playwright_loader] = fake_playwright_loader
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides = {}
