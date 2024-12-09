from megaparse.formatter.unstructured_formatter.md_formatter import MarkDownFormatter
from megaparse.megaparse import MegaParse
from megaparse.formatter.structured_formatter.custom_structured_formatter import (
    CustomStructuredFormatter,
)
from megaparse.parser.unstructured_parser import UnstructuredParser

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class MyCustomFormat(BaseModel):
    title: str = Field(description="The title of the document.")
    problem: str = Field(description="The problem statement.")
    solution: str = Field(description="The solution statement.")


if __name__ == "__main__":
    # Parse a file
    parser = UnstructuredParser()
    model = ChatOpenAI()
    formatter_1 = MarkDownFormatter()
    formatter_2 = CustomStructuredFormatter(model=model, output_model=MyCustomFormat)

    megaparse = MegaParse(parser=parser, formatters=[formatter_1, formatter_2])

    file_path = "libs/megaparse/tests/pdf/sample_pdf.pdf"
    result = megaparse.load(file_path=file_path)
    print(result)
