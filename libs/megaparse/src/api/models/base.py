from enum import Enum


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
