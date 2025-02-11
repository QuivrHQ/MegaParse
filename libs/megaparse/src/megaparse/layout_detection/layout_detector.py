import logging
import os
import pathlib
import uuid
from typing import Any, List

import numpy as np
import onnxruntime as rt
from megaparse.configs.auto import DeviceEnum
from megaparse.layout_detection.output import LayoutDetectionOutput
from megaparse.utils.onnx import get_providers
from megaparse_sdk.schema.document import BBOX, Point2D
from onnxtr.models.engine import EngineConfig
from onnxtr.models.preprocessor import PreProcessor
from PIL import Image, ImageDraw
from PIL.Image import Image as PILImage

logger = logging.getLogger("megaparse")

LABEL_MAP = {
    0: "Caption",
    1: "Footnote",
    2: "Formula",
    3: "List-item",
    4: "Page-footer",
    5: "Page-header",
    6: "Picture",
    7: "Section-header",
    8: "Table",
    9: "Text",
    10: "Title",
}

default_cfg: dict[str, dict[str, Any]] = {
    "yolov10s-doclaynet": {
        "mean": (0.5, 0.5, 0.5),
        "std": (1.0, 1.0, 1.0),
        "url_8_bit": None,
        "input_shape": (1, 1024, 1024),
        "url": pathlib.Path(__file__).parent.joinpath("models/yolov10s-doclaynet.onnx"),
    }
}


class LayoutDetector:
    def __init__(
        self,
        device: DeviceEnum = DeviceEnum.CPU,
        threshold: float = 0.1,
        preserve_aspect_ratio: bool = True,
        model_name: str = "yolov10s-doclaynet",
        load_in_8_bit: bool = False,
    ):
        model_config = default_cfg[model_name]
        self.device = device
        general_options = rt.SessionOptions()
        providers = get_providers(self.device)
        self.threshold = threshold
        self.batch_size, self.required_width, self.required_height = model_config[
            "input_shape"
        ]
        self.preserve_aspect_ratio = preserve_aspect_ratio

        self.pre_processor = PreProcessor(
            output_size=(self.required_width, self.required_height),
            batch_size=self.batch_size,
            preserve_aspect_ratio=self.preserve_aspect_ratio,
        )

        engine_config = EngineConfig(
            session_options=general_options,
            providers=providers,
        )
        model_path = (
            model_config.get("url_8_bit") if load_in_8_bit else model_config.get("url")
        )
        assert model_path, f"Model path not found for {model_name}"

        self.model = rt.InferenceSession(model_path, engine_config=engine_config)

    def __call__(
        self, img_pages: list[PILImage], output_dir: str | None = None
    ) -> List[List[LayoutDetectionOutput]]:
        pages = [np.array(img) for img in img_pages]
        # Dimension check
        if any(page.ndim != 3 for page in pages):
            raise ValueError(
                "incorrect input shape: all pages are expected to be multi-channel 2D images."
            )
        processed_batches = self.pre_processor(pages)
        processed_batches = np.array(processed_batches)
        processed_batches = processed_batches.squeeze(1)  # Horrendus
        processed_batches = processed_batches.transpose(0, 3, 1, 2)

        pred_batches = np.array(
            [
                self.model.run(None, {"images": np.expand_dims(batch, axis=0)})
                for batch in processed_batches
            ]
        )
        pred_batches = np.concatenate(pred_batches, axis=0)
        pred_batches = pred_batches.squeeze(1)  # Horrendus

        processed_preds = []
        for page, pred in zip(pages, pred_batches, strict=True):
            img_h, img_w = page.shape[:2]
            bboxes = self.extract_bboxes_from_page(pred, img_h, img_w)
            processed_preds.append(bboxes)

        if output_dir:
            self._save_layout(pages=pages, preds=processed_preds, output_dir=output_dir)

        return processed_preds

    def extract_bboxes_from_page(
        self, preds: np.ndarray, img_h: int, img_w: int
    ) -> List[LayoutDetectionOutput]:
        results = []

        assert preds.shape == (300, 6)

        scale_h = img_h / self.required_height
        scale_w = img_w / self.required_width

        for det in preds:
            # Rescale the bounding box coordinates to the original dimensions
            x1, y1, x2, y2, score, cls_idx = det
            if score < self.threshold:
                continue

            x1 *= scale_w
            x2 *= scale_w
            y1 *= scale_h
            y2 *= scale_h

            if self.preserve_aspect_ratio:
                ratio = img_h / img_w
                x1 = x1 * (ratio if ratio > 1 else 1)
                x2 = x2 * (ratio if ratio > 1 else 1)
                y1 = y1 / (ratio if ratio < 1 else 1)
                y2 = y2 / (ratio if ratio < 1 else 1)

            x1 = max(0, min(x1, img_w))
            x2 = max(0, min(x2, img_w))
            y1 = max(0, min(y1, img_h))
            y2 = max(0, min(y2, img_h))

            bbox_id = uuid.uuid4()

            results.append(
                LayoutDetectionOutput(
                    bbox_id=bbox_id,
                    bbox=BBOX(
                        top_left=Point2D(x=x1 / img_w, y=y1 / img_h),
                        bottom_right=Point2D(x=x2 / img_w, y=y2 / img_h),
                    ),
                    prob=det[4],
                    label=int(det[5]),
                )
            )

        result = self.topK(results)  # or topK
        return result

    def nms(
        self,
        raw_bboxes: List[LayoutDetectionOutput],
        iou_threshold: float = 0.9,  # FIXME: thresh Configurable in constructor
    ) -> List[LayoutDetectionOutput]:
        """
        Non-Maximum Suppression (NMS) algorithm.

        Args:
            raw_bboxes (list): List of LayoutBBox objects.
            iou_threshold (float): IoU threshold for suppression.

        Returns:
            None: The input list `raw_bboxes` is modified in-place.
        """
        raw_bboxes.sort(key=lambda x: x.prob, reverse=True)

        current_index = 0
        for index in range(len(raw_bboxes)):
            drop = False
            for prev_index in range(current_index):
                iou = raw_bboxes[index].bbox.iou(raw_bboxes[prev_index].bbox)
                if iou > iou_threshold:
                    drop = True
                    break
            if not drop:
                raw_bboxes[current_index], raw_bboxes[index] = (
                    raw_bboxes[index],
                    raw_bboxes[current_index],
                )
                current_index += 1

        return raw_bboxes[:current_index]

    def topK(
        self, detectResult: List[LayoutDetectionOutput], topK: int = 50
    ) -> List[LayoutDetectionOutput]:
        if len(detectResult) <= topK:
            return detectResult
        else:
            predBoxs = []
            sort_detectboxs = sorted(detectResult, key=lambda x: x.prob, reverse=True)
            for i in range(topK):
                predBoxs.append(sort_detectboxs[i])
            return predBoxs

    def _save_layout(
        self,
        pages: list[np.ndarray],
        preds: list[list[LayoutDetectionOutput]],
        output_dir: str,
    ):
        os.makedirs(output_dir, exist_ok=True)
        for i, (page, layout) in enumerate(zip(pages, preds, strict=True)):
            image = Image.fromarray(page)
            draw = ImageDraw.Draw(image)
            img_w, img_h = image.size

            for detection in layout:
                x_min, y_min, x_max, y_max = detection.bbox.to_numpy()
                bbox = x_min * img_w, y_min * img_h, x_max * img_w, y_max * img_h
                confidence = detection.prob
                category = detection.label
                label = LABEL_MAP.get(category, "Unknown")

                draw.rectangle(bbox, outline="red", width=2)
                # assert bbox[2] <= image.width
                # assert bbox[3] <= image.height
                draw.text(
                    (bbox[0], bbox[1]),
                    f"{label} ({confidence:.2f})",
                    fill="red",
                )

            image.save(os.path.join(output_dir, f"page_{i}.png"))
