from enum import Enum


class FileExtension(str, Enum):
    """Supported file extension enumeration."""

    _mimetype: str

    def __new__(cls, value: str, mimetype: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._mimetype = mimetype
        return obj

    PDF = (".pdf", "application/pdf")
    DOC = (".doc", "application/msword")
    DOCX = (
        ".docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    TXT = (".txt", "text/plain")
    OTF = (".odt", "application/vnd.oasis.opendocument.text")
    EPUB = (".epub", "application/epub")
    HTML = (".html", "text/html")
    XML = (".xml", "application/xml")
    CSV = (".csv", "text/csv")
    XLSX = (
        ".xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    XLS = (".xls", "application/vnd.ms-excel")
    PPT = (".ppt", "application/vnd.ms-powerpoint")
    PPTX = (
        ".pptx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    JSON = (".json", "application/json")
    MD = (".md", "text/markdown")
    MARKDOWN = (".markdown", "text/markdown")

    @property
    def mimetype(self) -> str:
        return self._mimetype
