import logging
from pathlib import Path
from typing import IO, BinaryIO, List

import onnxruntime as rt
from megaparse_sdk.schema.extensions import FileExtension
from onnxtr.io import DocumentFile
from onnxtr.models import EngineConfig, ocr_predictor

from megaparse.parser.base import BaseParser

logger = logging.getLogger("megaparse")


class DoctrParser(BaseParser):
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

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | BinaryIO | None = None,
        file_extension: str | FileExtension = "",
        **kwargs,
    ) -> str:
        if file:
            file.seek(0)
            pdf = file.read()
        elif file_path:
            pdf = file_path  # type: ignore
        else:
            raise ValueError("Can't convert if file and file_path are None")
        doc = DocumentFile.from_pdf(pdf)
        # Analyze
        result = self.predictor(doc)
        return result.render()
