import re
from pathlib import Path
from typing import IO

import numpy as np
import pypdfium2 as pdfium
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from megaparse_sdk.schema.parser_config import StrategyEnum
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfImage
from unstructured.partition.auto import partition

from megaparse.parser import BaseParser


class UnstructuredParser(BaseParser):
    load_dotenv()

    def __init__(
        self, strategy=StrategyEnum.AUTO, model: BaseChatModel | None = None, **kwargs
    ):
        self.strategy = strategy
        self.model = model

    # Function to convert element category to markdown format
    def convert_to_markdown(self, elements):
        markdown_content = ""

        for el in elements:
            markdown_content += self.get_markdown_line(el)

        return markdown_content

    def get_markdown_line(self, el: dict):
        element_type = el["type"]
        text = el["text"]
        metadata = el["metadata"]
        parent_id = metadata.get("parent_id", None)
        category_depth = metadata.get("category_depth", 0)
        table_stack = []  # type: ignore

        # Markdown line defaults to empty
        markdown_line = ""

        # Element type-specific markdown content
        markdown_types = {
            "Title": f"## {text}\n\n" if parent_id else f"# {text}\n\n",
            "Subtitle": f"## {text}\n\n",
            "Header": f"{'#' * (category_depth + 1)} {text}\n\n",
            "Footer": f"#### {text}\n\n",
            "NarrativeText": f"{text}\n\n",
            "ListItem": f"- {text}\n",
            "Table": f"{text}\n\n",
            "PageBreak": "---\n\n",
            "Image": f"![Image]({el['metadata'].get('image_path', '')})\n\n",
            "Formula": f"$$ {text} $$\n\n",
            "FigureCaption": f"**Figure:** {text}\n\n",
            "Address": f"**Address:** {text}\n\n",
            "EmailAddress": f"**Email:** {text}\n\n",
            "CodeSnippet": f"```{el['metadata'].get('language', '')}\n{text}\n```\n\n",
            "PageNumber": "",  # Page number is not included in markdown
        }

        markdown_line = markdown_types.get(element_type, f"{text}\n\n")

        if element_type == "Table" and self.model:
            # FIXME: @Chloé - Add a modular table enhancement here - LVM
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "human",
                        """You are an expert in markdown tables, match this text and this html table to fill a md table. You answer with just the table in pure markdown, nothing else.
                        <TEXT>
                        {text}
                        </TEXT>
                        <HTML>
                        {html}
                        </HTML>
                        <PREVIOUS_TABLE>
                        {previous_table}
                        </PREVIOUS_TABLE>""",
                    ),
                ]
            )
            chain = prompt | self.model
            result = chain.invoke(
                {
                    "text": el["text"],
                    "html": metadata["text_as_html"],
                    "previous_table": table_stack[-1] if table_stack else "",
                }
            )
            content_str = (
                str(result.content)
                if not isinstance(result.content, str)
                else result.content
            )
            cleaned_content = re.sub(r"^```.*$\n?", "", content_str, flags=re.MULTILINE)
            markdown_line = f"[TABLE]\n{cleaned_content}\n[/TABLE]\n\n"

        return markdown_line

    def get_strategy(
        self,
        page: PdfPage,
        threshold=0.5,
    ) -> StrategyEnum:
        if self.strategy != StrategyEnum.AUTO:
            raise ValueError("Strategy must be AUTO to use get_strategy")

        # Get the dim of the page
        total_page_area = page.get_width() * page.get_height()
        total_image_area = 0
        images_coords = []
        # Get all the images in the page
        for obj in page.get_objects():
            if isinstance(obj, PdfImage):
                images_coords.append(obj.get_pos())

        canva = np.zeros((int(page.get_height()), int(page.get_width())))
        for coords in images_coords:
            p_width, p_height = int(page.get_width()), int(page.get_height())
            x1 = max(0, min(p_width, int(coords[0])))
            y1 = max(0, min(p_height, int(coords[1])))
            x2 = max(0, min(p_width, int(coords[2])))
            y2 = max(0, min(p_height, int(coords[3])))
            canva[y1:y2, x1:x2] = 1
        # Get the total area of the images
        total_image_area = np.sum(canva)

        if total_image_area / total_page_area > threshold:
            return StrategyEnum.HI_RES
        return StrategyEnum.FAST

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extensions: str = "",
        **kwargs,
    ) -> str:
        strategies = {}
        if file_extensions == ".pdf" and self.strategy == StrategyEnum.AUTO:
            print("Determining strategy...")
            document = (
                pdfium.PdfDocument(file_path) if file_path else pdfium.PdfDocument(file)
            )
            for i, page in enumerate(document):
                strategies[i] = self.get_strategy(page)

            # count number of pages needing HI_RES
            num_hi_res = len(
                [
                    strategies[i]
                    for i in strategies
                    if strategies[i] == StrategyEnum.HI_RES
                ]
            )
            if num_hi_res / len(strategies) > 0.2:
                print("Using HI_RES strategy")
                self.strategy = StrategyEnum.HI_RES
            else:
                print("Using FAST strategy")
                self.strategy = StrategyEnum.FAST

        # Partition the PDF
        elements = partition(
            filename=str(file_path) if file_path else None,
            file=file,
            strategy=self.strategy,
        )
        elements_dict = [el.to_dict() for el in elements]
        markdown_content = self.convert_to_markdown(elements_dict)
        return markdown_content
