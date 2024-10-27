import asyncio
import os
from pathlib import Path
from langchain_openai import ChatOpenAI

from megaparse.parser.unstructured_parser import UnstructuredParser

from megaparse.parser import MegaParser
from megaparse.checker.format_checker import FormatChecker

# Dead Code, now relying on unstructured for all the other formats
# class Converter:
#     def __init__(self) -> None:
#         pass

#     async def convert(self, file_path: str | Path) -> LangChainDocument:
#         raise NotImplementedError("Subclasses should implement this method")

#     def save_md(self, md_content: str, file_path: Path | str) -> None:
#         with open(file_path, "w") as f:
#             f.write(md_content)


# class XLSXConverter(Converter):
#     def __init__(self) -> None:
#         pass

#     async def convert(self, file_path: str | Path) -> LangChainDocument:
#         if isinstance(file_path, str):
#             file_path = Path(file_path)
#         xls = pd.ExcelFile(file_path)  # type: ignore
#         sheets = pd.read_excel(xls)

#         target_text = self.table_to_text(sheets)

#         return LangChainDocument(
#             page_content=target_text,
#             metadata={"filename": file_path.name, "type": "xlsx"},
#         )

#     def convert_tab(self, file_path: str | Path, tab_name: str) -> str:
#         if isinstance(file_path, str):
#             file_path = Path(file_path)
#         xls = pd.ExcelFile(str(file_path))
#         sheets = pd.read_excel(xls, tab_name)
#         target_text = self.table_to_text(sheets)
#         return target_text

#     def table_to_text(self, df):
#         text_rows = []
#         for _, row in df.iterrows():
#             row_text = " | ".join(str(value) for value in row.values if pd.notna(value))
#             if row_text:
#                 text_rows.append("|" + row_text + "|")
#         return "\n".join(text_rows)


# class DOCXConverter(Converter):
#     def __init__(self) -> None:
#         self.header_handled = False

#     async def convert(self, file_path: str | Path) -> LangChainDocument:
#         if isinstance(file_path, str):
#             file_path = Path(file_path)
#         doc = Document(str(file_path))
#         md_content = []
#         # Handle header
#         if doc.sections and doc.sections[0].header:
#             header_content = self._handle_header(doc.sections[0].header)
#             if header_content:
#                 md_content.append(header_content)

#         for element in doc.element.body:
#             if isinstance(element, CT_P):
#                 md_content.append(self._handle_paragraph(Paragraph(element, doc)))
#             elif isinstance(element, CT_Tbl):
#                 md_content += self._handle_table(Table(element, doc))
#             # Add more handlers here (image, header, footer, etc)

#         return LangChainDocument(
#             page_content="\n".join(md_content),
#             metadata={"filename": file_path.name, "type": "docx"},
#         )

#     def _handle_header(self, header) -> str:
#         if not self.header_handled:
#             parts = []
#             for paragraph in header.paragraphs:
#                 parts.append(f"# {paragraph.text}")
#             for table in header.tables:
#                 parts += self._handle_header_table(table)
#             self.header_handled = True
#             return "\n".join(parts)
#         return ""

#     def _handle_header_table(self, table: Table) -> List[str]:
#         cell_texts = [cell.text for row in table.rows for cell in row.cells]
#         cell_texts.remove("")
#         # Find the most repeated cell text
#         text_counts = Counter(cell_texts)
#         title = text_counts.most_common(1)[0][0] if cell_texts else ""
#         other_texts = [text for text in cell_texts if text != title and text != ""]

#         md_table_content = []
#         if title:
#             md_table_content.append(f"# {title}")
#         for text in other_texts:
#             md_table_content.append(f"*{text}*;")
#         return md_table_content

#     def _handle_paragraph(self, paragraph: Paragraph) -> str:
#         if paragraph.style.name.startswith("Heading"):  # type: ignore
#             level = int(paragraph.style.name.split()[-1])  # type: ignore
#             return f"{'#' * level} {paragraph.text}"
#         else:
#             parts = []
#             for run in paragraph.runs:
#                 if run.text != "":
#                     parts.append(self._handle_run(run))
#             return "".join(parts)

#     def _handle_run(self, run: Run) -> str:
#         text: str = run.text
#         if run.bold:
#             if len(text) < 200:
#                 # FIXME : handle table needs to be improved -> have the paragraph they are in
#                 text = f"## {text}"
#             else:
#                 text = f"**{text}**"
#         if run.italic:
#             text = f"*{text}*"
#         return text

#     def _handle_table(self, table: Table) -> List[str]:
#         row_content = []
#         for i, row in enumerate(table.rows):
#             row_content.append(
#                 "| " + " | ".join(cell.text.strip() for cell in row.cells) + " |"
#             )
#             if i == 0:
#                 row_content.append("|" + "---|" * len(row.cells))

#         return row_content

#     def save_md(self, md_content: str, file_path: Path | str) -> None:
#         with open(file_path, "w") as f:
#             f.write(md_content)


# class PPTXConverter:
#     def __init__(self, add_images=False) -> None:
#         self.header_handled = False
#         self.add_images = add_images

#     async def convert(self, file_path: str | Path) -> LangChainDocument:
#         if isinstance(file_path, str):
#             file_path = Path(file_path)
#         prs = Presentation(str(file_path))
#         md_content = []
#         unique_slides: Set[str] = set()

#         # Handle header
#         if prs.slides and prs.slides[0].placeholders:
#             header_content = self._handle_header(prs.slides[0].placeholders)
#             if header_content:
#                 md_content.append(header_content)

#         for i, slide in enumerate(prs.slides):
#             slide_md_content: List[str] = []
#             for shape in slide.shapes:
#                 if shape.shape_type == MSO_SHAPE_TYPE.TABLE:  # type: ignore
#                     slide_md_content += self._handle_table(shape.table)
#                 elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE and self.add_images:  # type: ignore
#                     slide_md_content.append(self._handle_image(shape))
#                 elif hasattr(shape, "text"):
#                     slide_md_content.append(self._handle_paragraph(shape.text))

#             slide_md_str = "\n".join(slide_md_content)
#             if slide_md_str not in unique_slides:
#                 unique_slides.add(slide_md_str)
#                 slide_md_str = f"## Slide {i+1}\n{slide_md_str}"
#                 md_content.append(slide_md_str)

#         return LangChainDocument(
#             page_content="\n".join(md_content),
#             metadata={"filename": file_path.name, "type": "pptx"},
#         )

#     def _handle_header(self, placeholders) -> str:
#         if not self.header_handled:
#             parts = []
#             for placeholder in placeholders:
#                 if placeholder.placeholder_format.idx == 0:  # Title placeholder
#                     parts.append(f"# {placeholder.text}")
#                 elif placeholder.placeholder_format.idx == 1:  # Subtitle placeholder
#                     parts.append(f"## {placeholder.text}")
#             self.header_handled = True
#             return "\n".join(parts)
#         return ""

#     def _handle_paragraph(self, text: str) -> str:
#         # Assuming text is a simple paragraph without complex formatting
#         # if text contains letters return text
#         if any(c.isalpha() for c in text):
#             return text + "\n"
#         return ""

#     def _handle_image(self, shape) -> str:
#         image = shape.image
#         image_bytes = image.blob
#         image_format = image.ext
#         image_filename = f"images/image_{shape.shape_id}.{image_format}"
#         with open(image_filename, "wb") as f:
#             f.write(image_bytes)
#         return f"![Image {shape.shape_id}](../{image_filename})"

#     def _handle_table(self, table) -> List[str]:
#         row_content = []
#         for i, row in enumerate(table.rows):
#             row_content.append(
#                 "| " + " | ".join(cell.text.strip() for cell in row.cells) + " |"
#             )
#             if i == 0:
#                 row_content.append("|" + "---|" * len(row.cells))
#         return row_content

#     def save_md(self, md_content: str, file_path: Path | str) -> None:
#         with open(file_path, "w") as f:
#             f.write(md_content)


class MegaParse:
    def __init__(
        self, parser: MegaParser, format_checker: FormatChecker | None = None
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
