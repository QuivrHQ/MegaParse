import re
from typing import List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from unstructured.documents.elements import Element

from megaparse.formatter.table_formatter import TableFormatter


class SimpleMDTableFormatter(TableFormatter):
    """
    A formatter that converts table elements into Markdown format using llms.
    """

    TABLE_MARKER_START = "[TABLE]"
    TABLE_MARKER_END = "[/TABLE]"
    CODE_BLOCK_PATTERN = r"^```.*$\n?"

    def __init__(self, model: Optional[BaseChatModel] = None):
        super().__init__(model)

    async def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> List[Element]:
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

        for element in elements:
            if element.category == "Table":
                previous_table = table_stack[-1] if table_stack else ""
                formatted_table = self.format_table(element, previous_table)
                table_stack.append(formatted_table.text)
                formatted_elements.append(formatted_table)
            else:
                formatted_elements.append(element)

        return formatted_elements

    def format_table(self, table_element: Element, previous_table: str) -> Element:
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
                        "You are an expert in markdown tables. Match the following text and HTML table "
                        "to create a markdown table. Provide just the table in pure markdown, nothing else.\n"
                        "<TEXT>\n{text}\n</TEXT>\n"
                        "<HTML>\n{html}\n</HTML>\n"
                        "<PREVIOUS_TABLE>\n{previous_table}\n</PREVIOUS_TABLE>"
                    ),
                ),
            ]
        )

        chain = prompt | self.model
        result = chain.invoke(
            {
                "text": table_element.text,
                "html": table_element.metadata.text_as_html,
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
