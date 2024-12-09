from megaparse.formatter.unstructured_formatter.md_formatter import MarkDownFormatter
from megaparse.megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser

if __name__ == "__main__":
    # Parse a file
    parser = UnstructuredParser()
    formatter = MarkDownFormatter()

    megaparse = MegaParse(parser=parser, formatters=[formatter])

    file_path = "libs/megaparse/tests/pdf/sample_pdf.pdf"
    result = megaparse.load(file_path=file_path)
    print(result)
