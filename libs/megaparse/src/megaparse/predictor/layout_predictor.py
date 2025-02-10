from PIL import Image
from unstructured_inference.inference.layout import PageLayout
from unstructured_inference.models.base import get_model
from unstructured_inference.visualize import draw_bbox


def extract_layout(
    page_number: int, page_image: Image.Image, model_name: str = "yolox"
) -> PageLayout:
    layout_model = get_model(model_name)
    parsed_page = PageLayout.from_image(
        image=page_image,
        number=page_number,
        detection_model=layout_model,
        element_extraction_model=None,
        fixed_layout=None,
    )

    colors = ["red" for _ in parsed_page.elements]
    for el, color in zip(parsed_page.elements, colors, strict=True):
        page_image = draw_bbox(page_image, el, color=color, details=False)

    page_image.show()

    return parsed_page


if __name__ == "__main__":
    import pypdfium2 as pdfium

    file = "/Users/amine/Downloads/0168126.pdf"
    pdfium_document = pdfium.PdfDocument(file)

    page_number = 3
    page = pdfium_document[page_number]

    # Render the selected page to an image
    pil_image = page.render(scale=2).to_pil()  # Increase scale for higher resolution

    layout_result = extract_layout(page_number=page_number, page_image=pil_image)

    # Output the layout result
    print(layout_result)
