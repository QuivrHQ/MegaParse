from fastapi import FastAPI, UploadFile, File, HTTPException
from megaparse.core.main import MegaParse
from megaparse.core.parser.type import ParserType
from megaparse.core.parser.unstructured_parser import StrategyEnum, UnstructuredParser
from megaparse.core.parser.llama import LlamaParser
from megaparse.core.parser.megaparse_vision import MegaParseVision
import psutil
import os
from langchain_community.document_loaders import PlaywrightURLLoader

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from llama_parse.utils import Language


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}


def _check_free_memory():
    """Reject traffic when free memory is below minimum (default 2GB)."""
    mem = psutil.virtual_memory()
    memory_free_minimum = int(os.environ.get("MEMORY_FREE_MINIMUM_MB", 2048))

    if mem.available <= memory_free_minimum * 1024 * 1024:
        raise HTTPException(
            status_code=503,
            detail="Server is under heavy load. Please try again later.",
        )


@app.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    method: ParserType = ParserType.UNSTRUCTURED,
    strategy: StrategyEnum = StrategyEnum.AUTO,
    check_table=False,
    language: Language = Language.ENGLISH,
    parsing_instruction: str | None = None,
    model_name: str = "gpt-4o",
):
    _check_free_memory()
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
        raise HTTPException(
            status_code=400, detail="Model not supported for MegaParse Vision"
        )

    parser_dict = {
        "unstructured": UnstructuredParser(
            strategy=strategy, model=model if check_table else None
        ),
        "llama_parser": LlamaParser(
            api_key=str(os.getenv("LLAMA_CLOUD_API_KEY")),
            language=language,  # type: ignore
            parsing_instruction=parsing_instruction,
        ),
        "megaparse_vision": MegaParseVision(model=model),
    }

    with open(file.filename, "wb") as f:  # type: ignore
        f.write(file.file.read())
        megaparse = MegaParse(parser=parser_dict[method])
        result = await megaparse.aload(file_path=str(file.filename))
        os.remove(file.filename)  # type: ignore
        return {"message": "File uploaded successfully", "result": result}


@app.post("/url")
async def upload_url(url: str):
    loader = PlaywrightURLLoader(urls=[url], remove_selectors=["header", "footer"])

    if url.endswith(".pdf"):
        ## Download the file
        import requests
        import tempfile

        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the file")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(response.content)
            parser = UnstructuredParser()
            result = parser.convert(temp_file.name, strategy="auto")
            return result
    else:
        data = await loader.aload()
        # Now turn the data into a string
        extracted_content = ""
        for page in data:
            extracted_content += page.page_content
        return extracted_content
