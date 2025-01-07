import logging
import warnings
from pathlib import Path
from typing import IO, BinaryIO, List

from megaparse.configs.auto import DeviceEnum, TextRecoConfig, TextDetConfig
import onnxruntime as rt
from megaparse_sdk.schema.extensions import FileExtension
from onnxtr.io import DocumentFile
from onnxtr.models import ocr_predictor
from onnxtr.models.engine import EngineConfig

from megaparse.parser.base import BaseParser

logger = logging.getLogger("megaparse")


class DoctrParser(BaseParser):
    supported_extensions = [FileExtension.PDF]

    def __init__(
        self,
        text_det_config: TextDetConfig = TextDetConfig(),
        text_reco_config: TextRecoConfig = TextRecoConfig(),
        device: DeviceEnum = DeviceEnum.CPU,
        straighten_pages: bool = False,
        **kwargs,
    ):
        self.device = device
        general_options = rt.SessionOptions()
        providers = self._get_providers()
        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
        )
        # TODO: set in config or pass as kwargs
        self.predictor = ocr_predictor(
            det_arch=text_det_config.det_arch,
            reco_arch=text_reco_config.reco_arch,
            det_bs=text_det_config.batch_size,
            reco_bs=text_reco_config.batch_size,
            assume_straight_pages=text_det_config.assume_straight_pages,
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
        if self.device == DeviceEnum.CUDA:
            # TODO: support openvino, directml etc
            if "CUDAExecutionProvider" not in prov:
                raise ValueError(
                    "onnxruntime can't find CUDAExecutionProvider in list of available providers"
                )
            return ["TensorrtExecutionProvider", "CUDAExecutionProvider"]
        elif self.device == DeviceEnum.COREML:
            if "CoreMLExecutionProvider" not in prov:
                raise ValueError(
                    "onnxruntime can't find CoreMLExecutionProvider in list of available providers"
                )
            return ["CoreMLExecutionProvider"]
        elif self.device == DeviceEnum.CPU:
            return ["CPUExecutionProvider"]
        else:
            warnings.warn(
                "Device not supported, using CPU",
                UserWarning,
                stacklevel=2,
            )
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
