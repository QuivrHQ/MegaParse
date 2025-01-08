from pathlib import Path
from langchain_core.language_models.chat_models import BaseChatModel
from megaparse.formatter.base import BaseFormatter
from megaparse.models.document import Document
from pydantic import BaseModel


class StructuredFormatter(BaseFormatter):
    def __init__(self, model: BaseChatModel, output_model: type[BaseModel]):
        super().__init__(model)
        self.output_model = output_model

    async def aformat(
        self,
        document: Document,
        file_path: Path | str | None = None,
    ) -> str:  # FIXME: Return a structured output of type BaseModel ?
        raise NotImplementedError()

    def format(
        self,
        document: Document,
        file_path: Path | str | None = None,
    ) -> str:  # FIXME: Return a structured output of type BaseModel ?
        raise NotImplementedError()
