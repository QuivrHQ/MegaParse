from typing import Optional

from httpx import Response
from pydantic import BaseModel

from megaparse_sdk.client import MegaParseClient
from megaparse_sdk.schema.languages import Language
from megaparse_sdk.schema.parser_config import ParserType, StrategyEnum


class UploadFileConfig(BaseModel):
    method: ParserType
    strategy: StrategyEnum
    check_table: bool
    language: Language
    parsing_instruction: str | None = None
    model_name: str = "gpt-4o"


class FileUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def upload(
        self,
        file_path: str,
        method: ParserType = ParserType.UNSTRUCTURED,
        strategy: StrategyEnum = StrategyEnum.AUTO,
        check_table: bool = False,
        language: Language = Language.ENGLISH,
        parsing_instruction: Optional[str] = None,
        model_name: str = "gpt-4o",
    ) -> Response:
        data = UploadFileConfig(
            method=method,
            strategy=strategy,
            check_table=check_table,
            language=language,
            parsing_instruction=parsing_instruction,
            model_name=model_name,
        )
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file)}

            response = await self.client.request(
                "POST",
                "/v1/file",
                files=files,
                data=data.model_dump(mode="json"),
            )
            return response
