import re
from pathlib import Path
from typing import IO

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from megaparse_sdk.schema.parser_config import StrategyEnum
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

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        **kwargs,
    ) -> str:
        # Partition the PDF
        elements = partition(
            filename=str(file_path) if file_path else None,
            file=file,
            strategy=self.strategy,
            skip_infer_table_types=[],
        )
        elements_dict = [el.to_dict() for el in elements]
        markdown_content = self.convert_to_markdown(elements_dict)
        return markdown_content
