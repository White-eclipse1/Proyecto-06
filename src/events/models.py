"""Contrato del evento persistido en SQLite."""

from dataclasses import dataclass

from src.inference.types import Detection


@dataclass(frozen=True)
class Event:
    event_id: str
    timestamp: str
    source_id: str
    model_version: str
    config_version: str
    state: str
    confidence: float | None
    confidence_zone: str
    detections: tuple[Detection, ...]
    read_time_ms: float | None
    preprocessing_time_ms: float | None
    inference_time_ms: float | None
    postprocessing_time_ms: float | None
    image_reference: str | None = None
    error_detail: str | None = None

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source_id": self.source_id,
            "model_version": self.model_version,
            "config_version": self.config_version,
            "state": self.state,
            "confidence": self.confidence,
            "confidence_zone": self.confidence_zone,
            "detections": [d.to_dict() for d in self.detections],
            "detection_count": self.detection_count,
            "read_time_ms": self.read_time_ms,
            "preprocessing_time_ms": self.preprocessing_time_ms,
            "inference_time_ms": self.inference_time_ms,
            "postprocessing_time_ms": self.postprocessing_time_ms,
            "image_reference": self.image_reference,
            "error_detail": self.error_detail,
        }
