import asyncio
from typing import Optional

import httpx
from httpx import Response

from megaparse.sdk.megaparse_sdk.client import MegaParseClient
from megaparse.sdk.megaparse_sdk.config import UploadFileConfig
from megaparse.sdk.megaparse_sdk.utils.type import Language, ParserType, StrategyEnum


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
        max_retries: int = 3,
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
            for attempt in range(max_retries):
                try:
                    response = await self.client.request(
                        "POST",
                        "/v1/file",
                        files=files,
                        data=data.model_dump(mode="json"),
                    )
                    return response
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff

            raise RuntimeError("Can't send file to the server.")
