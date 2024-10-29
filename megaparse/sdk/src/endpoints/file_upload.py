from typing import Optional
from httpx import Response
from .client import MegaParseClient
from megaparse.parser.type import ParserType
from llama_parse.utils import Language
import asyncio


class FileUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def aupload(
        self,
        file_path: str,
        method: ParserType = ParserType.UNSTRUCTURED,
        strategy: str = "AUTO",
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

    def upload(
        self,
        file_path: str,
        method: ParserType = ParserType.UNSTRUCTURED,
        strategy: str = "AUTO",
        check_table: bool = False,
        language: Language = Language.ENGLISH,
        parsing_instruction: Optional[str] = None,
        model_name: str = "gpt-4o",
    ) -> Response:
        """Synchronous wrapper for file upload using asyncio.run."""
        return asyncio.run(
            self.aupload(
                file_path,
                method=method,
                strategy=strategy,
                check_table=check_table,
                language=language,
                parsing_instruction=parsing_instruction,
                model_name=model_name,
            )
        )
