import asyncio
import platform
from pathlib import Path
from typing import IO

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_core.documents import Document
from megaparse.api.app import app, get_playwright_loader, parser_builder_dep
from megaparse.parser.base import BaseParser
from megaparse_sdk.schema.extensions import FileExtension


class FakeParserBuilder:
    def build(self, *args, **kwargs) -> BaseParser:
        """
        Build a fake parser based on the given configuration.

        Returns:
            BaseParser: The built fake parser.

        Raises:
            ValueError: If the configuration is invalid.
        """

        class FakeParser(BaseParser):
            def convert(
                self,
                file_path: str | Path | None = None,
                file: IO[bytes] | None = None,
                file_extension: None | FileExtension = None,
                **kwargs,
            ) -> str:
                print("Fake parser is converting the file")
                return "Fake conversion result"

            async def aconvert(
                self,
                file_path: str | Path | None = None,
                file: IO[bytes] | None = None,
                file_extension: None | FileExtension = None,
                **kwargs,
            ) -> str:
                print("Fake parser is converting the file")
                # Simulate some async work without actually blocking
                await asyncio.sleep(0)
                return "Fake conversion result"

        return FakeParser()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_client():
    """Async test client fixture with proper resource cleanup and debugging."""
    print("Setting up test_client fixture - initializing")
    original_overrides = app.dependency_overrides.copy()
    client = None

    try:

        def fake_parser_builder():
            return FakeParserBuilder()

        def fake_playwright_loader():
            class FakePlaywrightLoader(PlaywrightURLLoader):
                async def aload(self):
                    return [Document(page_content="Fake website content")]

            return FakePlaywrightLoader(urls=[], remove_selectors=["header", "footer"])

        print("Setting up test_client fixture - configuring dependencies")
        app.dependency_overrides[parser_builder_dep] = fake_parser_builder
        app.dependency_overrides[get_playwright_loader] = fake_playwright_loader

        print("Setting up test_client fixture - creating client")
        client = AsyncClient(
            transport=ASGITransport(app=app),  # type: ignore
            base_url="http://test",
        )
        await client.__aenter__()
        print("Setting up test_client fixture - client ready")
        yield client

    except Exception as e:
        print(f"Error in test_client fixture: {str(e)}")
        raise
    finally:
        print("Cleaning up test_client fixture")
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error during client cleanup: {str(e)}")
        app.dependency_overrides = original_overrides
        print("Test client cleanup complete")
