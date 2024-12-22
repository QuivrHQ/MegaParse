import asyncio
from pathlib import Path
from typing import IO, List

from llama_index.core.schema import Document as LlamaDocument
from llama_parse import LlamaParse as _LlamaParse
from llama_parse.utils import Language, ResultType
from megaparse_sdk.schema.extensions import FileExtension

from megaparse.parser import BaseParser


class LlamaParser(BaseParser):
    """LlamaParse-based document parser with advanced PDF parsing capabilities.

    This parser leverages the LlamaParse API for high-quality PDF parsing with
    support for multiple languages and custom parsing instructions. It's particularly
    effective for documents with complex layouts and tables that span multiple pages.

    Attributes:
        supported_extensions (List[FileExtension]): Currently supports PDF files only.

    Args:
        api_key (str): LlamaParse API key for authentication
        verbose (bool): Enable detailed logging output (default: True)
        language (Language): Target language for parsing (default: Language.FRENCH)
        parsing_instruction (str, optional): Custom instructions for the parser
            If not provided, uses default instructions for handling headers, footers,
            and table merging across pages.
        **kwargs: Additional arguments passed to LlamaParse

    Note:
        - Requires valid LlamaParse API key for operation
        - Both sync and async interfaces make API calls
        - Default parsing instruction optimizes for table continuity across pages
        - Memory usage scales with document size and complexity
    """
    supported_extensions = [FileExtension.PDF]

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

    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> str:
        if not file_path:
            raise ValueError("File_path should be provided to run LlamaParser")
        self.check_supported_extension(file_extension, file_path)

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

    def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> str:
        if not file_path:
            raise ValueError("File_path should be provided to run LlamaParser")
        self.check_supported_extension(file_extension, file_path)

        llama_parser = _LlamaParse(
            api_key=self.api_key,
            result_type=ResultType.MD,
            gpt4o_mode=True,
            verbose=self.verbose,
            language=self.language,
            parsing_instruction=self.parsing_instruction,
        )

        documents: List[LlamaDocument] = llama_parser.load_data(str(file_path))
        parsed_md = ""
        for document in documents:
            text_content = document.text
            parsed_md = parsed_md + text_content

        return parsed_md
