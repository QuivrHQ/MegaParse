from typing import Dict, List

from pydantic import BaseModel


class Block(BaseModel):
    """
    A class to represent a block.
    Really Simplified.
    """

    metadata: Dict  # FIXME: To be defined as a pydantic model later @Amine
    content: str


class TextBlock(Block):
    """
    A class to represent a text block.
    Really Simplified.
    """

    pass


class ImageBlock(Block):
    """
    A class to represent an image block.
    Really Simplified.
    """

    pass


class TitleBlock(Block):
    """
    A class to represent a title block.
    Really Simplified.
    """

    pass


class SubTitle(Block):
    """
    A class to represent a subtitle block.
    Really Simplified.
    """

    depth: int


class TableBlock(Block):
    """
    A class to represent a table block.
    Really Simplified.
    """

    pass


class ListBlock(Block):
    """
    A class to represent a list block.
    Really Simplified.
    """

    pass


class HeaderBlock(Block):
    """
    A class to represent a header block.
    Really Simplified.
    """

    pass


class FooterBlock(Block):
    """
    A class to represent a footer block.
    Really Simplified.
    """

    pass


class Document(BaseModel):
    """
    A class to represent a document.
    Really Simplified.
    """

    name: str
    metadata: Dict  # TBD @Amine
    content: List[Block]
