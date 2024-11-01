import tempfile
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from megaparse.api.utils.type import HTTPModelNotSupported, parser_dict
from megaparse.core.megaparse import MegaParse
from megaparse.core.parser.type import ParserType
from megaparse.core.parser.unstructured_parser import StrategyEnum, UnstructuredParser
import psutil
import os
from langchain_community.document_loaders import PlaywrightURLLoader

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from llama_parse.utils import Language
import httpx

app = FastAPI()

playwright_loader = PlaywrightURLLoader(urls=[], remove_selectors=["header", "footer"])


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
async def parse_file(
    file: UploadFile = File(...),
    method: ParserType = ParserType.UNSTRUCTURED,
    strategy: StrategyEnum = StrategyEnum.AUTO,
    check_table=False,
    language: Language = Language.ENGLISH,
    parsing_instruction: str | None = None,
    model_name: str | None = None,
) -> dict[str, str]:
    if not _check_free_memory():
        raise HTTPException(
            status_code=503, detail="Service unavailable due to low memory"
        )
    model = None
    if model_name:
        if model_name.startswith("gpt"):
            model = ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
        elif model_name.startswith("claude"):
            model = ChatAnthropic(
                model_name=model_name,
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # type: ignore
                timeout=60,
                stop=None,
            )

        else:
            raise HTTPModelNotSupported()

    parser = parser_dict[method](
        strategy=strategy,
        model=model if model and check_table else None,
        language=language,
        parsing_instruction=parsing_instruction,
    )
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{str(file.filename).split('.')[-1]}"
    ) as temp_file:
        temp_file.write(file.file.read())
        megaparse = MegaParse(parser=parser)
        result = await megaparse.aload(file_path=temp_file.name)
        return {"message": "File parsed successfully", "result": result}


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
            megaparse = MegaParse(parser=UnstructuredParser(strategy=StrategyEnum.AUTO))
            result = megaparse.load(temp_file.name)
            return {"message": "File parsed successfully", "result": result}
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
