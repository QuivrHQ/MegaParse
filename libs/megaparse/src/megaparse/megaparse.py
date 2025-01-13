import logging
import warnings
from pathlib import Path
from typing import IO, BinaryIO, List

import pypdfium2 as pdfium
from megaparse_sdk.schema.extensions import FileExtension
from megaparse_sdk.schema.parser_config import StrategyEnum

from megaparse.configs.auto import DeviceEnum, MegaParseConfig
from megaparse.exceptions.base import ParsingException
from megaparse.formatter.base import BaseFormatter
from megaparse.models.page import GatewayDocument, Page, PageDimension
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse.utils.strategy import (
    determine_global_strategy,
    get_page_strategy,
)

logger = logging.getLogger("megaparse")


class MegaParse:
    def __init__(
        self, formatters: List[BaseFormatter] | None = None, config=MegaParseConfig()
    ) -> None:
        self.config = config
        self.formatters = formatters
        self.doctr_parser = DoctrParser(
            text_det_config=self.config.doctr_config.text_det_config,
            text_reco_config=self.config.doctr_config.text_reco_config,
            device=self.config.device,
            straighten_pages=self.config.doctr_config.straighten_pages,
            detect_orientation=self.config.doctr_config.detect_orientation,
            detect_language=self.config.doctr_config.detect_language,
        )
        self.unstructured_parser = UnstructuredParser()

    def validate_input(
        self,
        file_path: Path | str | None = None,
        file: IO[bytes] | None = None,
        file_extension: str | FileExtension | None = None,
    ) -> FileExtension:
        if not (file_path or file):
            raise ValueError("Either file_path or file should be provided")

        if file_path and file:
            raise ValueError("Only one of file_path or file should be provided")

        if file_path and file is None:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            file_extension = file_path.suffix
        elif file and file_path is None:
            if not file_extension:
                raise ValueError(
                    "file_extension should be provided when given file argument"
                )
            file.seek(0)
        else:
            raise ValueError("Either provider a file_path or file")

        if isinstance(file_extension, str):
            try:
                file_extension = FileExtension(file_extension)
            except ValueError:
                raise ValueError(f"Unsupported file extension: {file_extension}")
        return file_extension

    def extract_page_strategies(
        self, file: BinaryIO, rast_scale: int = 2
    ) -> List[Page]:
        pdfium_document = pdfium.PdfDocument(file)

        pages = []
        for i, pdfium_page in enumerate(pdfium_document):
            rasterized_page = pdfium_page.render(scale=rast_scale)
            assert (
                abs(pdfium_page.get_width() * rast_scale - rasterized_page.width) <= 1
            ), (
                f"Widths do not match within a margin of 1: "
                f"{pdfium_page.get_width() * rast_scale} != {rasterized_page.width}"
            )
            pages.append(
                Page(
                    strategy=StrategyEnum.AUTO,
                    text_detections=None,
                    rasterized=rasterized_page.to_pil(),
                    page_size=PageDimension(
                        width=pdfium_page.get_width() * rast_scale,
                        height=pdfium_page.get_height() * rast_scale,
                    ),
                    page_index=i,
                    pdfium_elements=pdfium_page,
                )
            )

        # ----
        # Get text detection for each page -> PAGE

        pages = self.doctr_parser.get_text_detections(pages)

        # ---

        # Get strategy per page -> PAGE
        for page in pages:
            page.strategy = get_page_strategy(
                page.pdfium_elements,
                page.text_detections,
                threshold=self.config.auto_config.page_threshold,
            )
        return pages

    def load(
        self,
        file_path: Path | str | None = None,
        file: BinaryIO | None = None,
        file_extension: str | FileExtension = "",
        strategy: StrategyEnum = StrategyEnum.AUTO,
    ) -> str:
        file_extension = self.validate_input(
            file=file, file_path=file_path, file_extension=file_extension
        )
        if file_extension != FileExtension.PDF or strategy == StrategyEnum.FAST:
            self.unstructured_parser.strategy = strategy
            return str(
                self.unstructured_parser.convert(
                    file_path=file_path, file=file, file_extension=file_extension
                )
            )
        else:
            opened_file = None
            try:
                if file_path:
                    opened_file = open(file_path, "rb")
                    file = opened_file

                assert file is not None, "No File provided"
                pages = self.extract_page_strategies(file)
                strategy = determine_global_strategy(
                    pages, self.config.auto_config.document_threshold
                )

                if strategy == StrategyEnum.HI_RES:
                    print("Using Doctr for text recognition")
                    parsed_document = self.doctr_parser.get_text_recognition(pages)

                else:
                    print("Switching to Unstructured Parser")
                    self.unstructured_parser.strategy = StrategyEnum.FAST
                    parsed_document = self.unstructured_parser.convert(
                        file=file, file_extension=file_extension
                    )

                parsed_document.file_name = str(file_path) if file_path else None

                if self.formatters:
                    for formatter in self.formatters:
                        if isinstance(parsed_document, str):
                            warnings.warn(
                                f"The last step returned a string, the {formatter.__class__} and following will not be applied",
                                stacklevel=2,
                            )
                            break
                        parsed_document = formatter.format(parsed_document)

                if not isinstance(parsed_document, str):
                    return str(parsed_document)
                return parsed_document
            except Exception as e:
                raise ParsingException(
                    f"Error while parsing file {file_path or file}, file_extension: {file_extension}: {e}"
                )
            finally:
                if opened_file:
                    opened_file.close()

    async def aload(
        self,
        file_path: Path | str | None = None,
        file: BinaryIO | None = None,
        file_extension: str | FileExtension = "",
        strategy: StrategyEnum = StrategyEnum.AUTO,
    ) -> str:
        file_extension = self.validate_input(
            file=file, file_path=file_path, file_extension=file_extension
        )
        if file_extension != FileExtension.PDF or strategy == StrategyEnum.FAST:
            self.unstructured_parser.strategy = strategy
            parsed_document = await self.unstructured_parser.aconvert(
                file_path=file_path, file=file, file_extension=file_extension
            )
            return str(parsed_document)
        else:
            opened_file = None
            try:
                if file_path:
                    opened_file = open(file_path, "rb")
                    file = opened_file

                assert file is not None, "No File provided"
                pages = self.extract_page_strategies(file)
                strategy = determine_global_strategy(
                    pages, self.config.auto_config.document_threshold
                )

                if strategy == StrategyEnum.HI_RES:
                    print("Using Doctr for text recognition")
                    parsed_document = self.doctr_parser.get_text_recognition(pages)

                else:
                    print("Switching to Unstructured Parser")
                    self.unstructured_parser.strategy = StrategyEnum.FAST
                    parsed_document = await self.unstructured_parser.aconvert(
                        file=file, file_extension=file_extension
                    )

                parsed_document.file_name = str(file_path) if file_path else None

                if self.formatters:
                    for formatter in self.formatters:
                        if isinstance(parsed_document, str):
                            warnings.warn(
                                f"The last step returned a string, the {formatter.__class__} and following will not be applied",
                                stacklevel=2,
                            )
                            break
                        parsed_document = await formatter.aformat(parsed_document)

                if not isinstance(parsed_document, str):
                    return str(parsed_document)
                return parsed_document
            except Exception as e:
                raise ParsingException(
                    f"Error while parsing file {file_path or file}, file_extension: {file_extension}: {e}"
                )
            finally:
                if opened_file:
                    opened_file.close()
