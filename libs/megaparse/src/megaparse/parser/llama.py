from pathlib import Path
from typing import IO, List

from llama_index.core.schema import Document as LlamaDocument
from llama_parse import LlamaParse as _LlamaParse
from llama_parse.utils import Language, ResultType
from megaparse_sdk.schema.extensions import FileExtension

from megaparse.models.document import Document as MPDocument
from megaparse.models.document import TextBlock
from megaparse.parser import BaseParser
from megaparse.predictor.models.base import BBOX, Point2D


class LlamaParser(BaseParser):
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
    ) -> MPDocument:
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

        return self.__to_elements_list__(documents)

    def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> MPDocument:
        if not file_path:
            raise ValueError("File_path should be provided to run LlamaParser")
        self.check_supported_extension(file_extension, file_path)

        llama_parser = _LlamaParse(
            api_key=self.api_key,
            result_type=ResultType.JSON,
            gpt4o_mode=True,
            verbose=self.verbose,
            language=self.language,
            parsing_instruction=self.parsing_instruction,
        )

        documents: List[LlamaDocument] = llama_parser.load_data(str(file_path))

        return self.__to_elements_list__(documents)

    def __to_elements_list__(self, llama_doc: List[LlamaDocument]) -> MPDocument:
        list_blocks = []
        for i, page in enumerate(llama_doc):
            list_blocks.append(
                TextBlock(
                    text=page.text,
                    metadata={},
                    page_range=(i, i + 1),
                    bbox=BBOX(
                        top_left=Point2D(x=0, y=0), bottom_right=Point2D(x=1, y=1)
                    ),
                )
            )
        return MPDocument(
            metadata={},
            detection_origin="llamaparse",
            content=list_blocks,
        )
