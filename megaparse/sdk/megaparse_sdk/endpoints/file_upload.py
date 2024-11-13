from typing import Optional

from httpx import Response
from megaparse_sdk.client import MegaParseClient
from megaparse_sdk.utils.type import Language, ParserType, StrategyEnum
import json


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
        mc_data = {
            "method": method,
            "strategy": strategy,
            "check_table": check_table,
            "language": language.value,
            "parsing_instruction": parsing_instruction,
            "model_name": model_name,
        }
        with open(file_path, "rb") as file:
            multipart_data = {
                "parser_config": (None, json.dumps(mc_data), "application/json"),
                "file": (file_path, file),
            }
            return await self.client.request(
                "POST",
                "/v1/file",
                files=multipart_data,
            )
