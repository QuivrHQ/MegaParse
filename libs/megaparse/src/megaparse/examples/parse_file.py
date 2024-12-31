from megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser
import pypdfium2 as pdfium


def main():
    parser = UnstructuredParser()
    megaparse = MegaParse(parser=parser)

    file_path = "./tests/pdf/ocr/0168126.pdf"

    parsed_file = megaparse.load(file_path)
    print(f"\n----- File Response : {file_path} -----\n")
    print(parsed_file)


if __name__ == "__main__":
    main()
