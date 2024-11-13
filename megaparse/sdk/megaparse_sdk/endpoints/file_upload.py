from enum import Enum
from typing import Optional

from httpx import Response
from megaparse_sdk.client import MegaParseClient
from megaparse_sdk.utils.type import Language, ParserType, StrategyEnum


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
                "method": method.value if isinstance(method, Enum) else method,
                "strategy": strategy.value if isinstance(strategy, Enum) else strategy,
                "check_table": check_table,
                "language": language.value if isinstance(language, Enum) else language,
                "parsing_instruction": parsing_instruction,
                "model_name": model_name,
            }
            return await self.client.request("POST", "/v1/file", files=files, data=data)
