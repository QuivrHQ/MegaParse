import warnings
from typing import List

from megaparse.formatter.unstructured_formatter import UnstructuredFormatter
from unstructured.documents.elements import Element


class MarkDownFormatter(UnstructuredFormatter):
    def format_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> str:
        print("Formatting elements using MarkDownFormatter...")
        markdown_content = ""

        for el in elements:
            markdown_content += self.get_markdown_line(el.to_dict())

        return markdown_content

    async def aformat_elements(
        self, elements: List[Element], file_path: str | None = None
    ) -> str:
        warnings.warn(
            "The MarkDownFormatter is a sync formatter, please use the sync format method",
            UserWarning,
            stacklevel=2,
        )
        return self.format_elements(elements, file_path)

    def get_markdown_line(self, el: dict):
        element_type = el["type"]
        text = el["text"]
        metadata = el["metadata"]
        parent_id = metadata.get("parent_id", None)
        category_depth = metadata.get("category_depth", 0)
        # table_stack = []

        if "emphasized_text_contents" in metadata:
            print(metadata["emphasized_text_contents"])

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
        return markdown_line
