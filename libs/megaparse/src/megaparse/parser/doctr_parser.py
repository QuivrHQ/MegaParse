import logging
import warnings
from pathlib import Path
from typing import IO, BinaryIO, List

import onnxruntime as rt
from megaparse_sdk.schema.extensions import FileExtension
from onnxtr.io import DocumentFile
from onnxtr.models import EngineConfig, ocr_predictor

from megaparse.parser.base import BaseParser

logger = logging.getLogger("megaparse")


class DoctrParser(BaseParser):
    """OCR-based document parser using the doctr library for text extraction.

    This parser uses ONNX-based models for text detection and recognition, supporting
    both CPU and GPU acceleration. It's particularly effective for documents with
    complex layouts or when OCR is required for text extraction.

    Attributes:
        supported_extensions (List[FileExtension]): Currently supports PDF files only.

    Args:
        det_predictor_model (str): Detection model architecture (default: 'db_resnet50')
        reco_predictor_model (str): Recognition model architecture (default: 'crnn_vgg16_bn')
        det_bs (int): Detection batch size (default: 2)
        reco_bs (int): Recognition batch size (default: 512)
        assume_straight_pages (bool): Whether to assume pages are not rotated (default: True)
        straighten_pages (bool): Whether to attempt page rotation correction (default: False)
        use_gpu (bool): Whether to use CUDA acceleration if available (default: False)
        **kwargs: Additional arguments passed to the doctr predictor

    Note:
        - GPU support requires CUDA and appropriate ONNX runtime providers
        - The async interface (aconvert) is not truly asynchronous, it calls the sync version
        - Large documents may require significant memory, especially with GPU acceleration
    """
    supported_extensions = [FileExtension.PDF]

    def __init__(
        self,
        det_predictor_model: str = "db_resnet50",
        reco_predictor_model: str = "crnn_vgg16_bn",
        det_bs: int = 2,
        reco_bs: int = 512,
        assume_straight_pages: bool = True,
        straighten_pages: bool = False,
        use_gpu: bool = False,
        **kwargs,
    ):
        self.use_gpu = use_gpu
        general_options = rt.SessionOptions()
        providers = self._get_providers()
        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
        )
        # TODO: set in config or pass as kwargs
        self.predictor = ocr_predictor(
            det_arch=det_predictor_model,
            reco_arch=reco_predictor_model,
            det_bs=det_bs,
            reco_bs=reco_bs,
            assume_straight_pages=assume_straight_pages,
            straighten_pages=straighten_pages,
            # Preprocessing related parameters
            det_engine_cfg=engine_config,
            reco_engine_cfg=engine_config,
            clf_engine_cfg=engine_config,
            **kwargs,
        )

    def _get_providers(self) -> List[str]:
        prov = rt.get_available_providers()
        logger.info("Available providers:", prov)
        if self.use_gpu:
            # TODO: support openvino, directml etc
            if "CUDAExecutionProvider" not in prov:
                raise ValueError(
                    "onnxruntime can't find CUDAExecutionProvider in list of available providers"
                )
            return ["CUDAExecutionProvider"]
        else:
            return ["CPUExecutionProvider"]

    def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | BinaryIO | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> str:
        if file:
            file.seek(0)
            pdf = file.read()
        elif file_path:
            pdf = file_path  # type: ignore
        else:
            raise ValueError("Can't convert if file and file_path are None")

        self.check_supported_extension(file_extension, file_path)

        doc = DocumentFile.from_pdf(pdf)
        # Analyze
        result = self.predictor(doc)
        return result.render()

    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | BinaryIO | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> str:
        warnings.warn(
            "The UnstructuredParser is a sync parser, please use the sync convert method",
            UserWarning,
            stacklevel=2,
        )
        return self.convert(file_path, file, file_extension, **kwargs)
