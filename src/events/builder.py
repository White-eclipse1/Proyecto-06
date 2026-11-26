"""Adapta el resultado existente de InferenceEngine a un evento."""

from datetime import datetime, timezone
from math import isfinite
from uuid import uuid4

from src.inference.types import Detection
from src.monitoring import ConfidenceMonitor, ConfidenceZone, MonitoringConfig

from .models import Event


def _utc_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("el timestamp de inferencia debe incluir zona horaria")
    return parsed.astimezone(timezone.utc).isoformat()


class EventBuilder:
    def __init__(self, config: MonitoringConfig) -> None:
        self.config = config
        self.monitor = ConfidenceMonitor(config)

    def build(
        self,
        prediction: dict[str, object],
        *,
        source_id: str | None = None,
        image_reference: str | None = None,
        read_time_ms: float | None = None,
    ) -> Event:
        """Conserva todas las detecciones y comprueba el score máximo del frame."""
        detections = tuple(
            Detection(
                class_id=int(item["class_id"]),
                class_name=str(item["class_name"]),
                confidence=float(item["confidence"]),
                bbox=tuple(float(coordinate) for coordinate in item["bbox"]),
            )
            for item in prediction["detections"]
        )
        for detection in detections:
            if not 0 <= detection.confidence <= 1 or not isfinite(detection.confidence):
                raise ValueError("confidence de detección inválida")
            if len(detection.bbox) != 4 or not all(isfinite(x) for x in detection.bbox):
                raise ValueError("bbox de detección inválida")
        expected = max((d.confidence for d in detections), default=None)
        confidence = prediction["confidence"]
        if confidence != expected:
            raise ValueError("confidence del frame debe ser el máximo de las detecciones, o None")
        zone = self.monitor.classify(confidence)
        source = source_id or self.config.default_source_id
        if not source:
            raise ValueError("source_id no puede estar vacío")
        return Event(
            event_id=str(uuid4()),
            timestamp=_utc_timestamp(str(prediction["timestamp"])),
            source_id=source,
            model_version=str(prediction["model_version"]),
            config_version=self.config.version,
            state=zone.value,
            confidence=confidence,
            confidence_zone=zone.value,
            detections=detections,
            read_time_ms=read_time_ms,
            preprocessing_time_ms=float(prediction["preprocessing_time_ms"]),
            inference_time_ms=float(prediction["inference_time_ms"]),
            postprocessing_time_ms=float(prediction["postprocessing_time_ms"]),
            image_reference=image_reference,
        )

    def model_error(
        self,
        error: Exception,
        *,
        model_version: str,
        source_id: str | None = None,
        image_reference: str | None = None,
        read_time_ms: float | None = None,
    ) -> Event:
        """Representa un fallo real del modelo sin fabricar confianza ni detecciones."""
        return Event(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_id=source_id or self.config.default_source_id,
            model_version=model_version,
            config_version=self.config.version,
            state=ConfidenceZone.MODEL_ERROR.value,
            confidence=None,
            confidence_zone=ConfidenceZone.MODEL_ERROR.value,
            detections=(),
            read_time_ms=read_time_ms,
            preprocessing_time_ms=None,
            inference_time_ms=None,
            postprocessing_time_ms=None,
            image_reference=image_reference,
            error_detail=str(error),
        )
