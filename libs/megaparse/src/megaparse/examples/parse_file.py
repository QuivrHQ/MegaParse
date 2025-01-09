import asyncio
from pathlib import Path
from typing import List

from langchain_openai import ChatOpenAI
from llama_index.core.schema import Document as LlamaDocument
from llama_parse import LlamaParse
from llama_parse.utils import Language, ResultType
from megaparse.formatter.structured_formatter.custom_structured_formatter import (
    CustomStructuredFormatter,
)
from megaparse.megaparse import MegaParse
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.extensions import FileExtension
from pydantic import BaseModel, Field


class MyCustomFormat(BaseModel):
    title: str = Field(description="The title of the document.")
    problem: str = Field(description="The problem statement.")
    solution: str = Field(description="The solution statement.")


async def main():
    # Parse a file
    parser = DoctrParser()
    model = ChatOpenAI(name="gpt-4o")
    # formatter_1 = CustomStructuredFormatter(model=model, output_model=MyCustomFormat)

    megaparse = MegaParse(ocr_parser=parser)

    file_path = Path("./tests/pdf/sample_pdf.pdf")
    result = await megaparse.aload(file_path=file_path)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
