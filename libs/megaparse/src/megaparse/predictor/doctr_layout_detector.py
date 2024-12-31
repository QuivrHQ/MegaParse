from typing import Any, List

import numpy as np
from megaparse.predictor.models.base import (
    BlockLayout,
    PageLayout,
    BBOX,
    Point2D,
    BlockType,
)
from onnxtr.models.detection.predictor import DetectionPredictor
from onnxtr.models.engine import EngineConfig
from onnxtr.models.predictor.base import _OCRPredictor
from onnxtr.utils.geometry import detach_scores
from onnxtr.utils.repr import NestedObject


class LayoutPredictor(NestedObject, _OCRPredictor):
    """Implements an object able to localize and identify text elements in a set of documents

    Args:
        det_predictor: detection module
        reco_predictor: recognition module
        assume_straight_pages: if True, speeds up the inference by assuming you only pass straight pages
            without rotated textual elements.
        straighten_pages: if True, estimates the page general orientation based on the median line orientation.
            Then, rotates page before passing it to the deep learning modules. The final predictions will be remapped
            accordingly. Doing so will improve performances for documents with page-uniform rotations.
        detect_orientation: if True, the estimated general page orientation will be added to the predictions for each
            page. Doing so will slightly deteriorate the overall latency.
        detect_language: if True, the language prediction will be added to the predictions for each
            page. Doing so will slightly deteriorate the overall latency.
        clf_engine_cfg: configuration of the orientation classification engine
        **kwargs: keyword args of `DocumentBuilder`
    """

    def __init__(
        self,
        det_predictor: DetectionPredictor,
        assume_straight_pages: bool = True,
        straighten_pages: bool = False,
        preserve_aspect_ratio: bool = True,
        symmetric_pad: bool = True,
        detect_orientation: bool = False,
        clf_engine_cfg: EngineConfig | None = None,
        **kwargs: Any,
    ):
        self.det_predictor = det_predictor
        _OCRPredictor.__init__(
            self,
            assume_straight_pages,
            straighten_pages,
            preserve_aspect_ratio,
            symmetric_pad,
            detect_orientation,
            clf_engine_cfg=clf_engine_cfg,
            **kwargs,
        )
        self.detect_orientation = detect_orientation

    def __call__(
        self,
        pages: list[np.ndarray],
        **kwargs: Any,
    ) -> List[PageLayout]:  # FIXME : Create new LayoutDocument class
        """Localize and identify text elements in a set of documents

        Args:
            pages: list of pages to be processed

        Returns:
            Document: the document object containing the text elements
        """
        # Dimension check
        if any(page.ndim != 3 for page in pages):
            raise ValueError(
                "incorrect input shape: all pages are expected to be multi-channel 2D images."
            )

        # Localize text elements
        loc_preds, out_maps = self.det_predictor(pages, return_maps=True, **kwargs)

        # Detect document rotation and rotate pages
        seg_maps = [
            np.where(
                out_map > self.det_predictor.model.postprocessor.bin_thresh,
                255,
                0,
            ).astype(np.uint8)
            for out_map in out_maps
        ]
        if self.detect_orientation:
            general_pages_orientations, origin_pages_orientations = (
                self._get_orientations(pages, seg_maps)
            )
        else:
            general_pages_orientations = None
            origin_pages_orientations = None
        if self.straighten_pages:
            pages = self._straighten_pages(
                pages, seg_maps, general_pages_orientations, origin_pages_orientations
            )

            # forward again to get predictions on straight pages
            loc_preds = self.det_predictor(pages, **kwargs)  # type: ignore[assignment]

        # Detach objectness scores from loc_preds
        loc_preds, objectness_scores = detach_scores(loc_preds)  # type: ignore[arg-type]

        # Apply hooks to loc_preds if any
        for hook in self.hooks:
            loc_preds = hook(loc_preds)

        all_pages_layouts = []
        for page_index, (page, loc_pred, objectness_score) in enumerate(
            zip(pages, loc_preds, objectness_scores, strict=True)
        ):
            block_layouts = []
            for bbox, score in zip(loc_pred, objectness_score, strict=True):
                block_layouts.append(
                    BlockLayout(
                        bbox=BBOX(bbox[:2].tolist(), bbox[2:].tolist()),
                        objectness_score=score,
                        block_type=BlockType.TEXT,
                    )
                )
            all_pages_layouts.append(
                PageLayout(
                    bboxes=block_layouts,
                    page_index=page_index,
                    dimensions=page.shape[:2],
                    orientation=general_pages_orientations[page_index]
                    if general_pages_orientations is not None
                    else 0,
                )
            )

        return all_pages_layouts
