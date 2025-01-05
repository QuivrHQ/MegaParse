import logging
from pathlib import Path
from typing import Any, List

import numpy as np
import onnxruntime as rt
import pypdfium2 as pdfium
from megaparse_sdk.schema.parser_config import StrategyEnum
from onnxtr.io import DocumentFile
from onnxtr.models import detection_predictor
from onnxtr.models.engine import EngineConfig
from pypdfium2._helpers.page import PdfPage

from megaparse.configs.auto import AutoStrategyConfig
from megaparse.predictor.doctr_layout_detector import LayoutPredictor
from megaparse.predictor.models.base import PageLayout

logger = logging.getLogger("megaparse")


class StrategyHandler:
    config: AutoStrategyConfig = AutoStrategyConfig()

    def __init__(
        self,
        assume_straight_pages: bool = True,
        preserve_aspect_ratio: bool = True,
        symmetric_pad: bool = True,
        load_in_8_bit: bool = False,
    ) -> None:
        self.use_gpu = self.config.use_gpu
        general_options = rt.SessionOptions()
        providers = self._get_providers()
        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
        )

        self.det_predictor = detection_predictor(
            arch=self.config.det_arch,
            assume_straight_pages=assume_straight_pages,
            preserve_aspect_ratio=preserve_aspect_ratio,
            symmetric_pad=symmetric_pad,
            batch_size=self.config.batch_size,
            load_in_8_bit=load_in_8_bit,
            engine_cfg=engine_config,
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

    def get_strategy_page(
        self, pdfium_page: PdfPage, onnxtr_page: PageLayout
    ) -> StrategyEnum:
        # assert (
        #     p_width == onnxtr_page.dimensions[1]
        #     and p_height == onnxtr_page.dimensions[0]
        # ), "Page dimensions do not match"
        text_coords = []
        # Get all the images in the page
        for obj in pdfium_page.get_objects():
            if obj.type == 1:
                text_coords.append(obj.get_pos())

        p_width, p_height = int(pdfium_page.get_width()), int(pdfium_page.get_height())

        pdfium_canva = np.zeros((int(p_height), int(p_width)))

        for coords in text_coords:
            # (left,bottom,right, top)
            # 0---l--------------R-> y
            # |
            # B   (x0,y0)
            # |
            # T                 (x1,y1)
            # ^
            # x
            x0, y0, x1, y1 = (
                p_height - coords[3],
                coords[0],
                p_height - coords[1],
                coords[2],
            )
            x0 = max(0, min(p_height, int(x0)))
            y0 = max(0, min(p_width, int(y0)))
            x1 = max(0, min(p_height, int(x1)))
            y1 = max(0, min(p_width, int(y1)))
            pdfium_canva[x0:x1, y0:y1] = 1

        onnxtr_canva = np.zeros((int(p_height), int(p_width)))
        for block in onnxtr_page.bboxes:
            x0, y0 = block.bbox[0]
            x1, y1 = block.bbox[1]
            x0 = max(0, min(int(x0 * p_width), int(p_width)))
            y0 = max(0, min(int(y0 * p_height), int(p_height)))
            x1 = max(0, min(int(x1 * p_width), int(p_width)))
            y1 = max(0, min(int(y1 * p_height), int(p_height)))
            onnxtr_canva[y0:y1, x0:x1] = 1

        intersection = np.logical_and(pdfium_canva, onnxtr_canva)
        union = np.logical_or(pdfium_canva, onnxtr_canva)
        iou = np.sum(intersection) / np.sum(union)
        if iou < self.config.auto_page_threshold:
            return StrategyEnum.HI_RES
        return StrategyEnum.FAST

    def determine_strategy(
        self,
        file: str
        | Path
        | bytes,  # FIXME : Careful here on removing BinaryIO (not handled by onnxtr)
    ) -> StrategyEnum:
        logger.info("Determining strategy...")
        need_ocr = 0

        onnxtr_document = DocumentFile.from_pdf(file)
        layout_predictor = LayoutPredictor(self.det_predictor)
        pdfium_document = pdfium.PdfDocument(file)

        onnxtr_document_layout = layout_predictor(onnxtr_document)

        for pdfium_page, onnxtr_page in zip(
            pdfium_document, onnxtr_document_layout, strict=True
        ):
            strategy = self.get_strategy_page(pdfium_page, onnxtr_page)
            need_ocr += strategy == StrategyEnum.HI_RES

        doc_need_ocr = (
            need_ocr / len(pdfium_document)
        ) > self.config.auto_document_threshold
        if isinstance(pdfium_document, pdfium.PdfDocument):
            pdfium_document.close()

        if doc_need_ocr:
            logger.info("Using HI_RES strategy")
            return StrategyEnum.HI_RES
        logger.info("Using FAST strategy")
        return StrategyEnum.FAST
