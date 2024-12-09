import re
from pathlib import Path
from typing import IO, List

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from megaparse_sdk.schema.parser_config import StrategyEnum
from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

from megaparse.parser import BaseParser


class UnstructuredParser(BaseParser):
    load_dotenv()

    def __init__(
        self, strategy=StrategyEnum.AUTO, model: BaseChatModel | None = None, **kwargs
    ):
        self.strategy = strategy
        self.model = model

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        **kwargs,
    ) -> List[Element]:
        # Partition the PDF
        elements = partition(
            filename=str(file_path) if file_path else None,
            file=file,
            strategy=self.strategy,
            skip_infer_table_types=[],
        )
        return elements
