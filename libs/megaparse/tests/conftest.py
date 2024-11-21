from pathlib import Path
from typing import IO

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_core.documents import Document
from megaparse.api.app import app, get_playwright_loader, parser_builder_dep
from megaparse.core.parser.type import ParserConfig
from megaparse.parser.base import BaseParser


class FakeParserBuilder:
    def build(self, config: ParserConfig) -> BaseParser:
        """
        Build a fake parser based on the given configuration.

        Args:
            config (ParserDict): The configuration to be used for building the parser.

        Returns:
            BaseParser: The built fake parser.

        Raises:
            ValueError: If the configuration is invalid.
        """

        class FakeParser(BaseParser):
            async def convert(
                self,
                file_path: str | Path | None = None,
                file: IO[bytes] | None = None,
                **kwargs,
            ) -> str:
                print("Fake parser is converting the file")
                return "Fake conversion result"

        return FakeParser()


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
