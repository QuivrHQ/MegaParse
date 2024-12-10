from megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser


def main():
    parser = UnstructuredParser()
    megaparse = MegaParse(parser=parser)

    file_path = "somewhere/only_pdfs/4 The Language of Medicine  2024.07.21.pdf"
    parsed_file = megaparse.load(file_path)
    print(f"\n----- File Response : {file_path} -----\n")
    print(parsed_file)


if __name__ == "__main__":
    main()
