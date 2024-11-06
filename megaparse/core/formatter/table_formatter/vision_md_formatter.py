from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from unstructured.documents.elements import Element
from megaparse.core.formatter.table_formatter import TableFormatter
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_path
from io import BytesIO
import base64
from PIL import Image

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
            raise ValueError("A Model is needed to use the VisionMDTableFormatter.")
        print("Formatting tables using VisionMDTableFormatter...")
        assert (
            file_path
        ), "A file path is needed to format tables using VisionMDTableFormatter."

        formatted_elements = []

        for element in elements:
            if element.category == "Table":
                formatted_table = await self.format_table(element, file_path)
                formatted_elements.append(formatted_table)
            else:
                formatted_elements.append(element)

        return formatted_elements

    def process_file(self, images: List[Image.Image], image_format="PNG") -> List[str]:
        """
        Process a PDF file and convert its pages to base64 encoded images.

        :param file_path: Path to the PDF file
        :param image_format: Format to save the images (default: PNG)
        :return: List of base64 encoded images
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

    async def format_table(self, table_element: Element, file_path: str) -> Element:
        """
        Formats a table element into Markdown format usinf a Vision Model

        Args:
            table_element: An Element object representing a table.
            previous_table: A string representing the previous table.

        Returns:
            An Element object with the formatted table.
        """
        assert (
            table_element.metadata.coordinates
        ), "Table element must have coordinates."
        coordinates = table_element.metadata.coordinates.points
        page_number = table_element.metadata.page_number
        assert page_number, "Table element must have a page number."
        assert coordinates, "Table element must have coordinates."
        pages = convert_from_path(file_path)

        # Crop the file image to the table coordinates
        # Convert coordinates to a tuple of four float values
        box = (
            min(
                coordinates[0][0],
                coordinates[1][0],
                coordinates[2][0],
                coordinates[3][0],
            ),
            min(
                coordinates[0][1],
                coordinates[1][1],
                coordinates[2][1],
                coordinates[3][1],
            ),
            max(
                coordinates[0][0],
                coordinates[1][0],
                coordinates[2][0],
                coordinates[3][0],
            ),
            max(
                coordinates[0][1],
                coordinates[1][1],
                coordinates[2][1],
                coordinates[3][1],
            ),
        )
        table_image = pages[page_number - 1].crop(box)
        table_image64 = self.process_file([table_image])[0]
        formatted_table = await self.vision_extract(table_image64)

        markdown_table = (
            f"{self.TABLE_MARKER_START}\n"
            f"{formatted_table}\n"
            f"{self.TABLE_MARKER_END}\n\n"
        )
        # Convert the table image to text
        table_element.text = markdown_table
        return table_element

    async def vision_extract(self, table_image) -> str:
        """
        Send images to the language model for processing.

        :param images_data: List of base64 encoded images
        :return: Processed content as a string
        """
        assert self.model, "A model is needed to use the SimpleMDTableFormatter."
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
