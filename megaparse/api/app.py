import os
import tempfile
from typing import Optional

import httpx
import psutil
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_openai import ChatOpenAI
from llama_parse.utils import Language

from megaparse.api.utils.type import HTTPModelNotSupported
from megaparse.core.megaparse import MegaParse
from megaparse.core.parser.builder import ParserBuilder
from megaparse.core.parser.type import ParserConfig, ParserConfigInput
from megaparse.core.parser.unstructured_parser import StrategyEnum, UnstructuredParser

app = FastAPI()

playwright_loader = PlaywrightURLLoader(urls=[], remove_selectors=["header", "footer"])

_megaparse_instances_cache = {}


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


@app.post("/v1/file")
@app.post(
    "/v1/file",
)
async def parse_file(
    file: UploadFile,
    parser_config: str = File(...),
    parser_builder=Depends(parser_builder_dep),
) -> dict[str, str]:
    in_parser_config = ParserConfigInput.model_validate_json(parser_config)

    if not _check_free_memory():
        raise HTTPException(
            status_code=503, detail="Service unavailable due to low memory"
        )
    model = None
    if in_parser_config.model_name:
        if in_parser_config.model_name.startswith("gpt"):
            model = ChatOpenAI(
                model=in_parser_config.model_name, api_key=os.getenv("OPENAI_API_KEY")
            )  # type: ignore
        elif in_parser_config.model_name.startswith("claude"):
            model = ChatAnthropic(
                model_name=in_parser_config.model_name,
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # type: ignore
                timeout=60,
                stop=None,
            )

        else:
            raise HTTPModelNotSupported()

    out_parser_config = ParserConfig(
        method=in_parser_config.method,
        strategy=in_parser_config.strategy,
        model=model if model and in_parser_config.check_table else None,
        language=in_parser_config.language,
        parsing_instruction=in_parser_config.parsing_instruction,
    )

    # TODO: move to function or metaclass in Megaparse
    # if hash(out_parser_config) in _megaparse_instances_cache:
    #     megaparse = _megaparse_instances_cache[hash(out_parser_config)]
    # else:
    parser = parser_builder.build(out_parser_config)
    megaparse = MegaParse(parser=parser)
    # _megaparse_instances_cache[hash(out_parser_config)] = megaparse

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{str(file.filename).split('.')[-1]}"
        ) as temp_file:
            temp_file.write(file.file.read())
            result = await megaparse.aload(file_path=temp_file.name)
            return {"message": "File parsed successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/url")
async def upload_url(
    url: str, playwright_loader=Depends(get_playwright_loader)
) -> dict[str, str]:
    playwright_loader.urls = [url]

    if url.endswith(".pdf"):
        ## Download the file

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the file")

        with tempfile.NamedTemporaryFile(delete=False, suffix="pdf") as temp_file:
            temp_file.write(response.content)
            try:
                megaparse = MegaParse(
                    parser=UnstructuredParser(strategy=StrategyEnum.AUTO)
                )
                result = megaparse.load(temp_file.name)
                return {"message": "File parsed successfully", "result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    else:
        data = await playwright_loader.aload()
        # Now turn the data into a string
        extracted_content = ""
        for page in data:
            extracted_content += page.page_content
        if not extracted_content:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from the website, have you provided the correct and entire URL?",
            )
        return {
            "message": "Website content parsed successfully",
            "result": extracted_content,
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
