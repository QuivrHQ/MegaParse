import asyncio
from enum import Enum
from unstructured.partition.auto import partition
from dotenv import load_dotenv
from megaparse.parser import MegaParser


class StrategyEnum(str, Enum):
    """Method to use for the conversion"""

    FAST = "fast"
    AUTO = "auto"
    HI_RES = "hi_res"


class UnstructuredParser(MegaParser):
    load_dotenv()

    def __init__(self, strategy=StrategyEnum.AUTO):
        self.strategy = strategy

    # Function to convert element category to markdown format
    def convert_to_markdown(self, elements):
        markdown_content = ""

        for el in elements:
            markdown_content += self.get_markdown_line(el)

        return markdown_content

    def get_markdown_line(self, el):
        element_type = el["type"]
        text = el["text"]
        metadata = el["metadata"]
        parent_id = metadata.get("parent_id", None)
        category_depth = metadata.get("category_depth", 0)
        if "emphasized_text_contents" in metadata:
            print(metadata["emphasized_text_contents"])

        markdown_line = ""

        if element_type == "Title":
            if parent_id:
                markdown_line = (
                    f"## {text}\n\n"  # Adjusted to add sub headers if parent_id exists
                )
            else:
                markdown_line = f"# {text}\n\n"
        elif element_type == "Subtitle":
            markdown_line = f"## {text}\n\n"
        elif element_type == "Header":
            markdown_line = f"{'#' * (category_depth + 1)} {text}\n\n"
        elif element_type == "Footer":
            markdown_line = f"#### {text}\n\n"
        elif element_type == "NarrativeText":
            markdown_line = f"{text}\n\n"
        elif element_type == "ListItem":
            markdown_line = f"- {text}\n"
        elif element_type == "Table":
            markdown_line = el["metadata"]["text_as_html"]
        elif element_type == "PageBreak":
            markdown_line = "---\n\n"
        elif element_type == "Image":
            markdown_line = f"![Image]({el['metadata'].get('image_path', '')})\n\n"
        elif element_type == "Formula":
            markdown_line = f"$$ {text} $$\n\n"
        elif element_type == "FigureCaption":
            markdown_line = f"**Figure:** {text}\n\n"
        elif element_type == "Address":
            markdown_line = f"**Address:** {text}\n\n"
        elif element_type == "EmailAddress":
            markdown_line = f"**Email:** {text}\n\n"
        elif element_type == "CodeSnippet":
            markdown_line = f"```{el['metadata'].get('language', '')}\n{text}\n```\n\n"
        elif element_type == "PageNumber":
            markdown_line = f"**Page {text}**\n\n"
        else:
            markdown_line = f"{text}\n\n"

        return markdown_line

    async def convert(self, file_path, **kwargs) -> str:
        # Partition the PDF
        elements = partition(
            filename=str(file_path), infer_table_structure=True, strategy=self.strategy
        )
        elements_dict = [el.to_dict() for el in elements]
        markdown_content = self.convert_to_markdown(elements_dict)
        return markdown_content


if __name__ == "__main__":
    parser = UnstructuredParser()
    response = asyncio.run(
        parser.convert(
            "/Users/chloed./Documents/quivr/MegaParse/tests/data/input_tests/MegaFake_report.pdf"
        )
    )
    print(response)
    # with open("megaparse/tests/output_tests/cdp.md", "w") as f:
    #     f.write(response)
    # print("ok")
