import warnings
from pathlib import Path
from typing import IO, Dict, List

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum
from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

from megaparse.models.document import (
    Block,
    FooterBlock,
    HeaderBlock,
    ImageBlock,
    SubTitleBlock,
    TableBlock,
    TextBlock,
    TitleBlock,
)
from megaparse.models.document import (
    Document as MPDocument,
)
from megaparse.parser import BaseParser
from megaparse.predictor.models.base import BBOX, Point2D


class UnstructuredParser(BaseParser):
    load_dotenv()
    supported_extensions = [
        FileExtension.PDF,
        FileExtension.DOCX,
        FileExtension.TXT,
        FileExtension.OTF,
        FileExtension.EPUB,
        FileExtension.HTML,
        FileExtension.XML,
        FileExtension.CSV,
        FileExtension.XLSX,
        FileExtension.XLS,
        FileExtension.PPTX,
        FileExtension.MD,
        FileExtension.MARKDOWN,
    ]

    def __init__(
        self, strategy=StrategyEnum.AUTO, model: BaseChatModel | None = None, **kwargs
    ):
        self.strategy = strategy
        self.model = model

    def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: FileExtension | None = None,
        **kwargs,
    ) -> MPDocument:
        self.check_supported_extension(file_extension, file_path)
        # Partition the PDF
        elements = partition(
            filename=str(file_path) if file_path else None,
            file=file,
            strategy=self.strategy,
            content_type=file_extension.mimetype if file_extension else None,
        )
        return self.__to_mp_document(elements)

    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: FileExtension | None = None,
        **kwargs,
    ) -> MPDocument:
        self.check_supported_extension(file_extension, file_path)
        warnings.warn(
            "The UnstructuredParser is a sync parser, please use the sync convert method",
            UserWarning,
            stacklevel=2,
        )
        return self.convert(file_path, file, file_extension, **kwargs)

    def __to_mp_document(self, elements: List[Element]) -> MPDocument:
        text_blocks = []
        for element in elements:
            block = self.__convert_element_to_block(element)
            if block:
                text_blocks.append(block)
        return MPDocument(
            content=text_blocks, metadata={}, detection_origin="unstructured"
        )

    def __convert_element_to_block(self, element: Element) -> Block | None:
        element_type = element.category
        text = element.text
        metadata = element.metadata
        category_depth = metadata.category_depth

        # Element type-specific markdown content
        markdown_types: Dict[str, Block] = {
            "Title": TitleBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Subtitle": SubTitleBlock(
                text=text,
                depth=category_depth if category_depth else 0,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Header": HeaderBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Footer": FooterBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "NarrativeText": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "ListItem": TextBlock(  # FIXME: @chloedia, list item need to be handled differently in ListBlock
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Table": TableBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Image": ImageBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Formula": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "FigureCaption": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "Address": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "EmailAddress": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "CodeSnippet": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
            "UncategorizedText": TextBlock(
                text=text,
                metadata={},
                page_range=(metadata.page_number, metadata.page_number)
                if metadata.page_number
                else None,
                bbox=BBOX(
                    top_left=Point2D(
                        x=metadata.coordinates.points[0][0],
                        y=metadata.coordinates.points[0][1],
                    ),
                    bottom_right=Point2D(
                        x=metadata.coordinates.points[3][0],
                        y=metadata.coordinates.points[3][1],
                    ),
                )
                if metadata.coordinates and metadata.coordinates.points
                else None,
            ),
        }
        return markdown_types.get(element_type, None)
