from pathlib import Path

from megaparse.megaparse import MegaParse
from pydantic import BaseModel, Field


class MyCustomFormat(BaseModel):
    title: str = Field(description="The title of the document.")
    problem: str = Field(description="The problem statement.")
    solution: str = Field(description="The solution statement.")


def main():
    # model = ChatOpenAI(name="gpt-4o")
    # formatter_1 = CustomStructuredFormatter(model=model, output_model=MyCustomFormat)

    megaparse = MegaParse()

    file_path = Path("./tests/pdf/ocr/0168127.pdf")
    result = megaparse.load(file_path=file_path)
    print(result)


if __name__ == "__main__":
    main()
