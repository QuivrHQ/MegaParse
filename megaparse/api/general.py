import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from megaparse.api.utils.type import HTTPModelNotSupported, parser_dict
from megaparse.main import MegaParse
from megaparse.parser.type import ParserType
from megaparse.parser.unstructured_parser import StrategyEnum, UnstructuredParser
from megaparse.parser.llama import LlamaParser
from megaparse.parser.megaparse_vision import MegaParseVision
import psutil
import os
from langchain_community.document_loaders import PlaywrightURLLoader

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from llama_parse.utils import Language
import httpx

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"message": "Hello World"}


def _check_free_memory() -> bool:
    """Reject traffic when free memory is below minimum (default 2GB)."""
    mem = psutil.virtual_memory()
    memory_free_minimum = int(os.environ.get("MEMORY_FREE_MINIMUM_MB", 2048))

    if mem.available <= memory_free_minimum * 1024 * 1024:
        return False
    return True


@app.post("v1/file")
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
        if "gpt" in model_name:
            model = ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
        elif "claude" in model_name:
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

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.file.read())
        megaparse = MegaParse(parser=parser)
        result = await megaparse.aload(file_path=temp_file.name)
        return {"message": "File uploaded successfully", "result": result}


@app.post("/url")
async def upload_url(url: str) -> dict[str, str]:
    loader = PlaywrightURLLoader(urls=[url], remove_selectors=["header", "footer"])

    if url.endswith(".pdf"):
        ## Download the file

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the file")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(response.content)
            megaparse = MegaParse(parser=UnstructuredParser(strategy=StrategyEnum.AUTO))
            result = megaparse.load(temp_file.name)
            return {"message": "File uploaded successfully", "result": result}
    else:
        data = await loader.aload()
        # Now turn the data into a string
        extracted_content = ""
        for page in data:
            extracted_content += page.page_content
        return {"message": "File uploaded successfully", "result": extracted_content}
