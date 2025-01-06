import re
import warnings
from pathlib import Path
from typing import IO, List

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum
from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

from megaparse.parser import BaseParser


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
    ) -> List[Element]:
        # Partition the PDF
        elements = partition(
            filename=str(file_path) if file_path else None,
            file=file,
            strategy=self.strategy,
            content_type=file_extension.mimetype if file_extension else None,
        )
        return elements

    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: FileExtension | None = None,
        **kwargs,
    ) -> List[Element]:
        self.check_supported_extension(file_extension, file_path)
        warnings.warn(
            "The UnstructuredParser is a sync parser, please use the sync convert method",
            UserWarning,
            stacklevel=2,
        )
        return self.convert(file_path, file, file_extension, **kwargs)
