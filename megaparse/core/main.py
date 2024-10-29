import asyncio
import os
from pathlib import Path
from langchain_openai import ChatOpenAI

from megaparse.parser.unstructured_parser import UnstructuredParser

from megaparse.parser import MegaParser
from megaparse.checker.format_checker import FormatChecker


class MegaParse:
    def __init__(
        self,
        parser: MegaParser = UnstructuredParser(),
        format_checker: FormatChecker | None = None,
    ) -> None:
        self.parser = parser
        self.format_checker = format_checker
        self.last_parsed_document: str = ""

    async def aload(self, file_path: Path | str) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_extension: str = file_path.suffix

        if file_extension != ".pdf":
            if self.format_checker:
                raise ValueError(
                    f"Format Checker : Unsupported file extension: {file_extension}"
                )
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f"Parser {self.parser}: Unsupported file extension: {file_extension}"
                )

        try:
            parsed_document: str = await self.parser.convert(file_path)
            # @chloe FIXME: format_checker needs unstructured Elements as input which is to change
            # if self.format_checker:
            #     parsed_document: str = await self.format_checker.check(parsed_document)

        except Exception as e:
            raise ValueError(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def load(self, file_path: Path | str) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_extension: str = file_path.suffix

        if file_extension != ".pdf":
            if self.format_checker:
                raise ValueError(
                    f"Format Checker : Unsupported file extension: {file_extension}"
                )
            if not isinstance(self.parser, UnstructuredParser):
                raise ValueError(
                    f"Parser {self.parser}: Unsupported file extension: {file_extension}"
                )

        try:
            loop = asyncio.get_event_loop()
            parsed_document: str = loop.run_until_complete(
                self.parser.convert(file_path)
            )
            # @chloe FIXME: format_checker needs unstructured Elements as input which is to change
            # if self.format_checker:
            #     parsed_document: str = loop.run_until_complete(
            #         self.format_checker.check(parsed_document)
            #     )

        except Exception as e:
            raise ValueError(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def save(self, file_path: Path | str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w+") as f:
            f.write(self.last_parsed_document)


if __name__ == "__main__":
    model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
    parser = UnstructuredParser(model=model)
    megaparse = MegaParse(parser)
    response = megaparse.load("./tests/data/input_tests/MegaFake_report.pdf")
    print(response)
    # megaparse.save("megaparse/tests/output_tests/cdp.md")