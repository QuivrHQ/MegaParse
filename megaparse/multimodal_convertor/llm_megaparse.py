from enum import Enum
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import base64
from pdf2image import convert_from_path
from PIL import Image

# image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
# image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")

class Model(str, Enum):
    """Model to use for the conversion"""
    CLAUDE = "claude-3.5"
    GPT4O = "gpt-4o"


class LLM_Megaparse:
    def __init__(self, model: Model = Model.GPT4O):
        if model == Model.GPT4O:
            self.model = ChatOpenAI(model="gpt-4o")
        else:
            raise ValueError(f"Model {model} not supported")
        
    def process_file(self, file_path, image_format='PNG'):
        # Convert the specified page to an image
        images = convert_from_path(file_path)
        print(len(images))
        if not images:
            raise ValueError("No images were created from the PDF page.")
        
        # Convert the image to the specified format
        image = images
        images_base64 = []
        for image in images:
            buffered = BytesIO()

            image.save(buffered, format=image_format)
        
            # Encode the image data to base64
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            images_base64.append(image_base64)
        
        return images_base64


    def get_images(self, file_path):
        pass

    def get_tables(self):
        pass 

    def get_headers(self): #check if needed
        pass

    def get_toc(self): #check if needed
        pass

    def send_to_mlm(self, image_data: list[str]):
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Transcribe the content of this file into markdown. Be mindful of the formatting. Add formating if you think it is not clear. Do not include page breaks."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data[1]}"},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data[2]}"},
                }
                
            ],
        )
        response = self.model.invoke([message])
        return response
    
    def parse(self, file_path):
        pdf_base64 = self.process_file(file_path)
        response = self.send_to_mlm(pdf_base64)
        return response.content


if __name__ == "__main__":
    parser = LLM_Megaparse()
    response = parser.parse("megaparse/cdp/CDP_QUAL_CHART_01_CHARTE PRODUITS_2023.12.13.pdf")
    print(response)

