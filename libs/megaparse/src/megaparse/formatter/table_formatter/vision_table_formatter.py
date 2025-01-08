import base64
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from megaparse.formatter.table_formatter import TableFormatter
from megaparse.models.document import Document, TableBlock
from pdf2image import convert_from_path
from PIL import Image
from unstructured.documents.elements import Element

TABLE_OCR_PROMPT = """
You are tasked with transcribing the content of a table into markdown format. Your goal is to create a well-structured, readable markdown table that accurately represents the original content while adding appropriate formatting.
Answer uniquely with the parsed table. Do not include the fenced code blocks backticks.
"""


class VisionMDTableFormatter(TableFormatter):
    """
    A formatter that converts table elements into Markdown format using an AI language model.
    """

    TABLE_MARKER_START = "[TABLE]"
    TABLE_MARKER_END = "[/TABLE]"
    CODE_BLOCK_PATTERN = r"^```.*$\n?"

    def __init__(self, model: Optional[BaseChatModel] = None):
        super().__init__(model)

    def _crop_table_image(self, table_element: TableBlock, file_path: str) -> str:
        """
        Helper method to crop the table portion of the PDF page and convert it to a base64 string.
        """
        assert table_element.bbox, "Table element must have coordinates."
        bbox = table_element.bbox
        page_number = table_element.page_range[0]
        assert page_number, "Table element must have a page number."
        assert bbox, "Table element must have coordinates."

        pages = convert_from_path(file_path)

        # Calculate the box for cropping
        box = (
            bbox.top_left.x,
            bbox.top_left.y,
            bbox.bottom_right.x,
            bbox.bottom_right.y,
        )
        table_image = pages[page_number - 1].crop(box)
        # Convert the cropped image to base64
        table_image64 = self.process_file([table_image])[0]
        return table_image64

    async def aformat(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        """
        Asynchronously formats table elements within a list of elements.
        """
        if not self.model:
            raise ValueError("A Model is needed to use the VisionMDTableFormatter.")
        print("Formatting tables using VisionMDTableFormatter (async)...")
        assert (
            file_path
        ), "A file path is needed to format tables using VisionMDTableFormatter."
        if not isinstance(file_path, str):
            file_path = str(file_path)
        formatted_elements = []
        for block in document.content:
            if isinstance(block, TableBlock):
                formatted_table = await self.aformat_table(block, file_path)
                formatted_elements.append(formatted_table)
            else:
                formatted_elements.append(block)

        document.content = formatted_elements
        return document

    def format(
        self, document: Document, file_path: Path | str | None = None
    ) -> Document:
        """
        Asynchronously formats table elements within a list of elements.
        """
        if not self.model:
            raise ValueError("A Model is needed to use the VisionMDTableFormatter.")
        print("Formatting tables using VisionMDTableFormatter (async)...")
        assert (
            file_path
        ), "A file path is needed to format tables using VisionMDTableFormatter."
        if not isinstance(file_path, str):
            file_path = str(file_path)
        formatted_elements = []
        for block in document.content:
            if isinstance(block, TableBlock):
                formatted_table = self.format_table(block, file_path)
                formatted_elements.append(formatted_table)
            else:
                formatted_elements.append(block)

        document.content = formatted_elements
        return document

    async def aformat_table(
        self, table_element: TableBlock, file_path: str
    ) -> TableBlock:
        """
        Asynchronously formats a table element into Markdown format using a Vision Model.
        """
        table_image64 = self._crop_table_image(table_element, file_path)
        formatted_table = await self.avision_extract(table_image64)

        markdown_table = (
            f"{self.TABLE_MARKER_START}\n"
            f"{formatted_table}\n"
            f"{self.TABLE_MARKER_END}\n\n"
        )
        # Replace the element's text with the formatted table text
        table_element.text = markdown_table
        return table_element

    def format_table(self, table_element: TableBlock, file_path: str) -> TableBlock:
        """
        Asynchronously formats a table element into Markdown format using a Vision Model.
        """
        table_image64 = self._crop_table_image(table_element, file_path)
        formatted_table = self.vision_extract(table_image64)

        markdown_table = (
            f"{self.TABLE_MARKER_START}\n"
            f"{formatted_table}\n"
            f"{self.TABLE_MARKER_END}\n\n"
        )
        # Replace the element's text with the formatted table text
        table_element.text = markdown_table
        return table_element

    def process_file(self, images: List[Image.Image], image_format="PNG") -> List[str]:
        """
        Convert a list of PIL images to base64 encoded images.
        """
        try:
            images_base64 = []
            for image in images:
                buffered = BytesIO()
                image.save(buffered, format=image_format)
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                images_base64.append(image_base64)
            return images_base64
        except Exception as e:
            raise ValueError(f"Error processing PDF file: {str(e)}")

    async def avision_extract(self, table_image: str) -> str:
        """
        Asynchronously send image data to the language model for processing.
        """
        assert (
            self.model
        ), "A model is needed to use the VisionMDTableFormatter (async)."
        image_prompt = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{table_image}"},
        }

        message = HumanMessage(
            content=[
                {"type": "text", "text": TABLE_OCR_PROMPT},
                image_prompt,
            ],
        )
        response = await self.model.ainvoke([message])
        return str(response.content)

    def vision_extract(self, table_image: str) -> str:
        """
        Synchronously send image data to the language model for processing.
        """
        assert self.model, "A model is needed to use the VisionMDTableFormatter (sync)."
        image_prompt = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{table_image}"},
        }

        message = HumanMessage(
            content=[
                {"type": "text", "text": TABLE_OCR_PROMPT},
                image_prompt,
            ],
        )
        response = self.model.invoke([message])
        return str(response.content)
