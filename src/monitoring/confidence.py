"""Clasificación de un único score de frame; no analiza ventanas temporales."""

from enum import StrEnum
from math import isfinite

from .config import MonitoringConfig


class ConfidenceZone(StrEnum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNCERTAIN = "UNCERTAIN"
    ACCEPTED_BY_POLICY = "ACCEPTED_BY_POLICY"
    NO_DETECTION = "NO_DETECTION"
    MODEL_ERROR = "MODEL_ERROR"


class ConfidenceMonitor:
    def __init__(self, config: MonitoringConfig) -> None:
        self.config = config

    def classify(self, confidence: float | None) -> ConfidenceZone:
        if confidence is None:
            return ConfidenceZone.NO_DETECTION
        if not isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("confidence debe ser un número finito entre 0 y 1, o None")
        if confidence < self.config.lower_threshold:
            return ConfidenceZone.LOW_CONFIDENCE
        if confidence < self.config.upper_threshold:
            return ConfidenceZone.UNCERTAIN
        return ConfidenceZone.ACCEPTED_BY_POLICY
