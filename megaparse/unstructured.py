from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from unstructured.partition.pdf import partition_pdf
from dotenv import load_dotenv
import os


class UnstructuredParser:
    load_dotenv()

    # Function to convert element category to markdown format
    def convert_to_markdown(self, elements):
        markdown_content = ""
        element_hierarchy = {}

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
            markdown_line = f"---\n\n"
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

    def partition_pdf_file(self, path):
        return partition_pdf(
            filename=path, infer_table_structure=True, strategy="hi_res"
        )

    def improve_table_elements(self, elements):
        llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

        # Define the prompt
        messages = [
            (
                "system",
                "You are an expert at parsing HTML tables in markdown, improve this html table and return it as markdown. You answer with just the table in pure markdown, nothing else.",
            ),
        ]

        improved_elements = []
        for el in elements:
            if el.category == "Table":
                messages.append(("human", el.metadata.text_as_html))
                result = llm.invoke(messages)
                el.metadata.text_as_html = result.content
                # add line break to separate tables
                el.metadata.text_as_html = el.metadata.text_as_html + "\n\n"

            improved_elements.append(el)

        return improved_elements

    def convert(self, path):
        # Partition the PDF
        elements = self.partition_pdf_file(path)

        # Improve table elements
        improved_elements = self.improve_table_elements(elements)

        elements_dict = [el.to_dict() for el in improved_elements]
        markdown_content = self.convert_to_markdown(elements_dict)
        return markdown_content
