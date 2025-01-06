from langchain_core.language_models.chat_models import BaseChatModel
from megaparse.formatter.base import BaseFormatter
from pydantic import BaseModel


class StructuredFormatter(BaseFormatter):
    def __init__(self, model: BaseChatModel, output_model: type[BaseModel]):
        super().__init__(model)
        self.output_model = output_model

    async def aformat_string(
        self,
        text: str,
        file_path: str | None = None,
    ) -> str:  # FIXME: Return a structured output of type BaseModel ?
        raise NotImplementedError()

    def format_string(
        self,
        text: str,
        file_path: str | None = None,
    ) -> str:  # FIXME: Return a structured output of type BaseModel ?
        raise NotImplementedError()
