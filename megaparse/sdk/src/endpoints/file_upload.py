from typing import Optional
from httpx import Response
from megaparse.sdk.src.client import MegaParseClient
from megaparse.core.parser.type import ParserType, StrategyEnum
from llama_parse.utils import Language


class FileUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def upload(
        self,
        file_path: str,
        method: ParserType = ParserType.UNSTRUCTURED,
        strategy: str = StrategyEnum.AUTO,
        check_table: bool = False,
        language: Language = Language.ENGLISH,
        parsing_instruction: Optional[str] = None,
        model_name: str = "gpt-4o",
    ) -> Response:
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file)}
            data = {
                "method": method,
                "strategy": strategy,
                "check_table": check_table,
                "language": language.value,
                "parsing_instruction": parsing_instruction,
                "model_name": model_name,
            }
            return await self.client.request("POST", "/file", files=files, data=data)
