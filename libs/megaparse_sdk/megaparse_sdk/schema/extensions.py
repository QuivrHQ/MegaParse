from enum import Enum


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
