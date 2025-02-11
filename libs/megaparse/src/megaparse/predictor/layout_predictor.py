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
