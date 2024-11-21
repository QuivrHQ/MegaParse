from pathlib import Path
from typing import IO, List

from llama_index.core.schema import Document as LlamaDocument
from llama_parse import LlamaParse as _LlamaParse
from llama_parse.utils import Language, ResultType

from megaparse.parser import BaseParser


class LlamaParser(BaseParser):
    def __init__(
        self,
        api_key: str,
        verbose=True,
        language: Language = Language.FRENCH,
        parsing_instruction: str | None = None,
        **kwargs,
    ) -> None:
        self.api_key = api_key
        self.verbose = verbose
        self.language = language
        if parsing_instruction:
            self.parsing_instruction = parsing_instruction
        else:
            self.parsing_instruction = """Do not take into account the page breaks (no --- between pages),
            do not repeat the header and the footer so the tables are merged if needed. Keep the same format for similar tables."""

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        **kwargs,
    ) -> str:
        if not file_path:
            raise ValueError("File_path should be provided to run LlamaParser")

        llama_parser = _LlamaParse(
            api_key=self.api_key,
            result_type=ResultType.MD,
            gpt4o_mode=True,
            verbose=self.verbose,
            language=self.language,
            parsing_instruction=self.parsing_instruction,
        )

        documents: List[LlamaDocument] = await llama_parser.aload_data(str(file_path))
        parsed_md = ""
        for document in documents:
            text_content = document.text
            parsed_md = parsed_md + text_content

        return parsed_md
