"""Detector YOLOX adaptado de Proyecto5/src/p5/detector/yolox.py."""

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

from .coco_classes import COCO_CLASSES
from .model_loader import ModelConfig, load_session, read_config
from .preprocessing import preprocess
from .types import Detection

_STRIDES = (8, 16, 32)


def _decode(raw: np.ndarray, input_size: tuple[int, int]) -> np.ndarray:
    grids = []
    strides = []
    for stride in _STRIDES:
        rows = input_size[0] // stride
        cols = input_size[1] // stride
        xv, yv = np.meshgrid(np.arange(cols), np.arange(rows))
        grids.append(np.stack((xv, yv), axis=2).reshape(-1, 2))
        strides.append(np.full((rows * cols, 1), stride))
    grid = np.concatenate(grids)
    stride = np.concatenate(strides)
    decoded = raw.astype(np.float64)
    decoded[:, :2] = (decoded[:, :2] + grid) * stride
    with np.errstate(over="ignore"):
        decoded[:, 2:4] = np.exp(decoded[:, 2:4]) * stride
    return decoded


def _nms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> list[int]:
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = np.argsort(-scores, kind="stable")
    keep = []
    while order.size > 0:
        best, rest = order[0], order[1:]
        keep.append(int(best))
        width = np.maximum(0.0, np.minimum(x2[best], x2[rest]) - np.maximum(x1[best], x1[rest]) + 1)
        height = np.maximum(
            0.0, np.minimum(y2[best], y2[rest]) - np.maximum(y1[best], y1[rest]) + 1
        )
        intersection = width * height
        iou = intersection / (areas[best] + areas[rest] - intersection)
        order = rest[iou <= threshold]
    return keep


class InferenceEngine:
    """Recibe un frame BGR uint8 y devuelve detecciones reales y tiempos por etapa."""

    def __init__(self, config: ModelConfig) -> None:
        if not 0.0 <= config.score_threshold <= 1.0:
            raise ValueError("score_threshold debe estar entre 0 y 1")
        if not 0.0 <= config.nms_threshold <= 1.0:
            raise ValueError("nms_threshold debe estar entre 0 y 1")
        if min(config.input_size) <= 0 or any(dim % 32 for dim in config.input_size):
            raise ValueError("input_size debe ser positivo y divisible entre 32")
        self.config = config
        self.session = load_session(config)
        self.input_name = self.session.get_inputs()[0].name

    @classmethod
    def from_config(cls, path: str | Path = "config/model.yaml") -> "InferenceEngine":
        return cls(read_config(path))

    def predict(self, frame: np.ndarray) -> dict[str, object]:
        """Mide solo session.run en inference_time_ms; las otras etapas van separadas."""
        start = perf_counter()
        tensor, ratio = preprocess(frame, self.config.input_size, self.config.median_kernel)
        preprocess_end = perf_counter()
        raw = self.session.run(None, {self.input_name: tensor[np.newaxis]})[0]
        inference_end = perf_counter()
        detections = self._postprocess(raw, ratio, frame.shape[:2])
        postprocess_end = perf_counter()
        confidence = max((d.confidence for d in detections), default=None)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config.version,
            "detections": [d.to_dict() for d in detections],
            "confidence": confidence,
            "preprocessing_time_ms": (preprocess_end - start) * 1000,
            "inference_time_ms": (inference_end - preprocess_end) * 1000,
            "postprocessing_time_ms": (postprocess_end - inference_end) * 1000,
        }

    def _postprocess(
        self, raw: np.ndarray, ratio: float, image_size: tuple[int, int]
    ) -> tuple[Detection, ...]:
        cells = sum(
            (self.config.input_size[0] // stride) * (self.config.input_size[1] // stride)
            for stride in _STRIDES
        )
        expected_shape = (1, cells, 5 + len(COCO_CLASSES))
        if raw.shape != expected_shape:
            raise ValueError(f"salida del modelo {raw.shape}; se esperaba {expected_shape}")
        decoded = _decode(raw[0], self.config.input_size)
        if not np.isfinite(decoded).all():
            raise ValueError("el modelo produjo valores no finitos")
        probabilities = decoded[:, 4:]
        if probabilities.min() < 0.0 or probabilities.max() > 1.0:
            raise ValueError("scores fuera de [0, 1]")
        class_indices = probabilities[:, 1:].argmax(axis=1)
        scores = probabilities[:, 0] * probabilities[np.arange(cells), class_indices + 1]
        candidates = scores > self.config.score_threshold
        if not candidates.any():
            return ()
        centers, sizes = decoded[candidates, :2], decoded[candidates, 2:4]
        boxes = np.concatenate((centers - sizes / 2, centers + sizes / 2), axis=1) / ratio
        kept_scores = scores[candidates]
        kept_classes = class_indices[candidates]
        height, width = image_size
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, height)
        detections = []
        for index in _nms(boxes, kept_scores, self.config.nms_threshold):
            x1, y1, x2, y2 = (float(value) for value in boxes[index])
            if x2 > x1 and y2 > y1:
                class_id = int(kept_classes[index])
                detections.append(
                    Detection(
                        class_id=class_id,
                        class_name=COCO_CLASSES[class_id],
                        confidence=float(kept_scores[index]),
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return tuple(detections)
