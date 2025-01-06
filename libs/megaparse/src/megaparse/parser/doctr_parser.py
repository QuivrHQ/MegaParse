import logging
import warnings
from pathlib import Path
from typing import IO, BinaryIO, List

import onnxruntime as rt
from megaparse_sdk.schema.extensions import FileExtension
from onnxtr.io import Document, DocumentFile
from onnxtr.models import ocr_predictor
from onnxtr.models.engine import EngineConfig
from unstructured.documents.coordinates import RelativeCoordinateSystem
from unstructured.documents.elements import (
    Element,
    ElementMetadata,
    Image,
    PageBreak,
    Text,
)

from megaparse.parser.base import BaseParser

logger = logging.getLogger("megaparse")


class DoctrParser(BaseParser):
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
    ) -> None:
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
    ) -> List[Element]:
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
        doctr_result = self.predictor(doc)

        return self.__to_elements_list__(doctr_result)

    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | BinaryIO | None = None,
        file_extension: None | FileExtension = None,
        **kwargs,
    ) -> List[Element]:
        warnings.warn(
            "The DocTRParser is a sync parser, please use the sync convert method",
            UserWarning,
            stacklevel=2,
        )
        return self.convert(file_path, file, file_extension, **kwargs)

    def __to_elements_list__(self, doctr_document: Document) -> List[Element]:
        result = []

        for page in doctr_document.pages:
            for block in page.blocks:
                if len(block.lines) and len(block.artefacts) > 0:
                    raise ValueError(
                        "Block should not contain both lines and artefacts"
                    )
                word_coordinates = [
                    word.geometry for line in block.lines for word in line.words
                ]
                x0 = min(word[0][0] for word in word_coordinates)
                y0 = min(word[0][1] for word in word_coordinates)
                x1 = max(word[1][0] for word in word_coordinates)
                y1 = max(word[1][1] for word in word_coordinates)

                result.append(
                    Text(
                        text=block.render(),
                        coordinates=(
                            (x0, y0),
                            (x1, y0),
                            (x1, y1),
                            (x0, y1),
                        ),
                        coordinate_system=RelativeCoordinateSystem(),
                        metadata=ElementMetadata(),
                        detection_origin="doctr",
                    )
                )

                for artefact in block.artefacts:
                    result.append(
                        Image(
                            text="",
                            coordinates=(
                                (artefact.geometry[0][0], artefact.geometry[0][1]),
                                (artefact.geometry[1][0], artefact.geometry[0][1]),
                                (artefact.geometry[1][0], artefact.geometry[1][1]),
                                (artefact.geometry[0][0], artefact.geometry[1][1]),
                            ),
                            coordinate_system=RelativeCoordinateSystem(),
                            metadata=ElementMetadata(),
                            detection_origin="doctr",
                        )
                    )

            result.append(PageBreak(text=""))

        return result
