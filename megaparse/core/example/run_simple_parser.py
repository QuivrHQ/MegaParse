from langchain_openai import ChatOpenAI
from megaparse.core.formatter.table_formatter.vision_md_formatter import (
    VisionMDTableFormatter,
)
from megaparse.core.formatter.unstructured_formatter.markdown_formatter import (
    MarkDownFormatter,
)
from megaparse.core.megaparse import MegaParse
from megaparse.core.parser.unstructured_parser import UnstructuredParser
import os


def main():
    # This is a simple example of how to use the MegaParse class
    # You can use this class to parse any file format supported by the parser
    # and apply any formatter to the parsed document
    # The parsed document can then be saved to a file

    # Create an instance of UnstructuredParser
    parser = UnstructuredParser()

    # Add a table formatter to the parser
    formatter_list = []
    model = ChatOpenAI(model="gpt-4o", api_key=str(os.getenv("OPENAI_API_KEY")))  # type:ignore
    formatter_list.append(VisionMDTableFormatter(model=model))

    # Add a MD formatter to the parser
    formatter_list.append(MarkDownFormatter())

    # Create an instance of MegaParse
    mega_parse = MegaParse(parser=parser, formatters=formatter_list)

    # Load a file
    parsed_document = mega_parse.load("tests/data/MegaFake_report.pdf")

    print(parsed_document)


if __name__ == "__main__":
    main()
