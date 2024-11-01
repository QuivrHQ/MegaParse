from enum import Enum
from fastapi import HTTPException, status


class HTTPModelNotSupported(HTTPException):
    def __init__(
        self,
        detail: str = "The requested model is not supported yet.",
        headers: dict | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail, headers=headers
        )


class MarkDownType(str, Enum):
    """Markdown type enumeration."""

    TITLE = "Title"
    SUBTITLE = "Subtitle"
    HEADER = "Header"
    FOOTER = "Footer"
    NARRATIVE_TEXT = "NarrativeText"
    LIST_ITEM = "ListItem"
    TABLE = "Table"
    PAGE_BREAK = "PageBreak"
    IMAGE = "Image"
    FORMULA = "Formula"
    FIGURE_CAPTION = "FigureCaption"
    ADDRESS = "Address"
    EMAIL_ADDRESS = "EmailAddress"
    CODE_SNIPPET = "CodeSnippet"
    PAGE_NUMBER = "PageNumber"
    DEFAULT = "Default"
    UNDEFINED = "Undefined"


class FileExtension(str, Enum):
    """Supported file extension enumeration."""

    PDF = ".pdf"
    DOCX = ".docx"
    DOC = ".doc"
    TXT = ".txt"
    OTF = ".odt"
    EPUB = ".epub"
    HTML = ".html"
    XML = ".xml"
    CSV = ".csv"
    XLSX = ".xlsx"
    XLS = ".xls"
    PPTX = ".pptx"
    PPT = ".ppt"
    JSON = ".json"
    MD = ".md"
    MARKDOWN = ".markdown"
