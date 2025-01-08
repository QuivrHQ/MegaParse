import re
import warnings
from pathlib import Path
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from megaparse.formatter.table_formatter import TableFormatter
from megaparse.models.document import Document, TableBlock


class SimpleMDTableFormatter(TableFormatter):
    """
    A formatter that converts table elements into Markdown format using llms.
    """

    TABLE_MARKER_START = "[TABLE]"
    TABLE_MARKER_END = "[/TABLE]"
    CODE_BLOCK_PATTERN = r"^```.*$\n?"

    def __init__(self, model: Optional[BaseChatModel] = None):
        super().__init__(model)

    async def aformat(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        warnings.warn(
            "The SimpleMDTableFormatter is a sync formatter, please use the sync format method",
            UserWarning,
            stacklevel=2,
        )
        return self.format(document=document, file_path=file_path)

    def format(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        """
        Formats table elements within a list of elements.
        Args:
            elements: A list of Element objects.
        Returns:
            A list of Element objects with formatted tables.
        """
        if not self.model:
            raise ValueError("A Model is needed to use the SimpleMDTableFormatter.")
        print("Formatting tables using SimpleMDTableFormatter...")
        table_stack = []
        formatted_elements = []

        for block in document.content:
            if isinstance(block, TableBlock):
                previous_table = table_stack[-1] if table_stack else ""
                formatted_table = self.format_table(block, previous_table)
                table_stack.append(formatted_table.text)
                formatted_elements.append(formatted_table)
            else:
                formatted_elements.append(block)

        document.content = formatted_elements
        return document

    def format_table(
        self, table_element: TableBlock, previous_table: str
    ) -> TableBlock:
        """
        Formats a single table element into Markdown using an AI language model.
        Args:
            table_element: The table element to format.
            previous_table: The previously formatted table text.
        Returns:
            The formatted table element.
        """
        assert self.model is not None, "Model is not set."

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    (
                        "You are an expert in markdown tables. Transform the following parsed table into a "
                        "markdown table. Provide just the table in pure markdown, nothing else.\n"
                        "<TEXT>\n{text}\n</TEXT>\n"
                        "<PREVIOUS_TABLE>\n{previous_table}\n</PREVIOUS_TABLE>"
                    ),
                ),
            ]
        )

        chain = prompt | self.model
        result = chain.invoke(
            {
                "text": table_element.text,
                "previous_table": previous_table,
            }
        )

        content_str = str(result.content)
        cleaned_content = re.sub(
            self.CODE_BLOCK_PATTERN, "", content_str, flags=re.MULTILINE
        )
        markdown_table = (
            f"{self.TABLE_MARKER_START}\n"
            f"{cleaned_content}\n"
            f"{self.TABLE_MARKER_END}\n\n"
        )

        table_element.text = markdown_table

        return table_element
