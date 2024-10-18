from typing import IO
from fastapi import FastAPI, UploadFile, File
from megaparse import MegaParse
from megaparse.unstructured_convertor import UnstructuredParser
import psutil
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_community.document_loaders import PlaywrightURLLoader


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
def upload_file(file: UploadFile = File(...)):
    parser = UnstructuredParser()
    _check_free_memory()

    with open(file.filename, "wb") as f:  # type: ignore
        f.write(file.file.read())
        result = parser.convert(file.filename, strategy="auto")
        os.remove(file.filename)  # type: ignore
        return {"message": "File uploaded successfully", "result": result}


@app.post("/url")
async def upload_url(url: str):
    loader = PlaywrightURLLoader(urls=[url], remove_selectors=["header", "footer"])

    data = await loader.aload()
    # Now turn the data into a string
    extracted_content = ""
    for page in data:
        extracted_content += page.page_content
    return extracted_content
