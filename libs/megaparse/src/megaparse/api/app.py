import asyncio
import io
import os
import tempfile
from typing import Optional
from urllib.parse import urlparse

import httpx
import psutil
import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_openai import ChatOpenAI
from llama_parse.utils import Language
from megaparse_sdk.schema.parser_config import (
    ParseFileConfig,
    ParserType,
    StrategyEnum,
)
from megaparse_sdk.schema.supported_models import SupportedModel

from megaparse import MegaParse
from megaparse.api.exceptions.megaparse_exceptions import (
    HTTPDownloadError,
    HTTPFileNotFound,
    HTTPMemoryError,
    HTTPParsingException,
    ParsingException,
)
from megaparse.parser.builder import ParserBuilder
from megaparse.parser.unstructured_parser import UnstructuredParser

app = FastAPI()

playwright_loader = PlaywrightURLLoader(urls=[], remove_selectors=["header", "footer"])


def parser_builder_dep():
    return ParserBuilder()


def get_playwright_loader():
    return playwright_loader


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def _check_free_memory() -> bool:
    """Reject traffic when free memory is below minimum (default 2GB)."""
    mem = psutil.virtual_memory()
    memory_free_minimum = int(os.environ.get("MEMORY_FREE_MINIMUM_MB", 2048))

    if mem.available <= memory_free_minimum * 1024 * 1024:
        return False
    return True


@app.post(
    "/v1/file",
)
async def parse_file(
    file: UploadFile = File(...),
    method: ParserType = Form(ParserType.UNSTRUCTURED),
    strategy: StrategyEnum = Form(StrategyEnum.AUTO),
    check_table: bool = Form(False),
    language: Language = Form(Language.ENGLISH),
    parsing_instruction: Optional[str] = Form(None),
    model_name: Optional[str] = Form(SupportedModel.GPT_4O.value),
    parser_builder=Depends(parser_builder_dep),
) -> dict[str, str]:
    if not _check_free_memory():
        raise HTTPMemoryError()
    model = None
    if model_name and check_table:
        supported_models = [model.value for model in SupportedModel]
        if model_name not in supported_models:
            raise HTTPException(
                status_code=501,
                detail=f"Model {model_name} is not supported. Please use one of {supported_models}",
            )
        model_name_str = model_name
        if model_name_str.startswith("gpt"):
            model = ChatOpenAI(
                model=model_name_str, api_key=os.getenv("OPENAI_API_KEY")
            )  # type: ignore
        elif model_name_str.startswith("claude"):
            model = ChatAnthropic(
                model_name=model_name_str,
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # type: ignore
                timeout=60,
                stop=None,
            )

    parser_config = ParseFileConfig(
        method=method,
        strategy=strategy,
        model=model if model and check_table else None,
        language=language,
        parsing_instruction=parsing_instruction,
    )
    try:
        parser = parser_builder.build(parser_config)
        megaparse = MegaParse(parser=parser)
        if not file.filename:
            raise HTTPFileNotFound("No filename provided")
        _, extension = os.path.splitext(file.filename)
        file_bytes = await file.read()
        file_stream = io.BytesIO(file_bytes)
        result = await megaparse.aload(file=file_stream, file_extension=extension)
        return {"message": "File parsed successfully", "result": result}
    except ParsingException as e:
        print(e)
        raise HTTPParsingException(file.filename)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/url",
)
async def upload_url(
    url: str, playwright_loader=Depends(get_playwright_loader)
) -> dict[str, str]:
    if not _check_free_memory():
        raise HTTPMemoryError()

    # Validate URL format
    result = urlparse(url)
    if not all([result.scheme, result.netloc]):
        raise HTTPException(
            status_code=400, detail="Failed to load website content: Invalid URL format"
        )

    playwright_loader.urls = [url]

    if url.endswith(".pdf"):
        ## Download the file with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    break
            except (
                httpx.RequestError,
                httpx.HTTPStatusError,
                TimeoutError,
                ConnectionError,
            ) as e:
                if isinstance(e, (httpx.TimeoutException, TimeoutError)):
                    if attempt == max_retries - 1:
                        raise HTTPException(
                            status_code=504,
                            detail=f"Request timed out after {max_retries} attempts",
                        )
                elif isinstance(e, ConnectionError):
                    if attempt == max_retries - 1:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Failed after {max_retries} attempts: {str(e)}",
                        )
                elif attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to load website content: {str(e)}",
                    )
                await asyncio.sleep(2**attempt)  # Exponential backoff

        with tempfile.NamedTemporaryFile(delete=False, suffix="pdf") as temp_file:
            temp_file.write(response.content)
            try:
                megaparse = MegaParse(
                    parser=UnstructuredParser(strategy=StrategyEnum.AUTO)
                )
                result = await megaparse.aload(temp_file.name)
                return {"message": "File parsed successfully", "result": result}
            except ParsingException as e:
                raise HTTPParsingException(url, message=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error while parsing PDF: {str(e)}",
                )
    else:
        try:
            data = await playwright_loader.aload()
            # Now turn the data into a string
            extracted_content = ""
            for page in data:
                extracted_content += page.page_content
            if not extracted_content:
                raise HTTPDownloadError(
                    url,
                    message="Failed to extract content from the website. Valid URL example : https://www.quivr.com",
                )
            return {
                "message": "Website content parsed successfully",
                "result": extracted_content,
            }
        except Exception as e:
            # Handle Playwright-specific errors
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load website content: {str(e)}. Make sure the URL is valid and accessible.",
            )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
