"""Adquiere observaciones de eventos reales y del proceso de P6."""

from datetime import datetime, timezone
from math import isfinite
from time import perf_counter

import psutil

from src.events.models import Event

from .models import MetricObservation


def is_traceable(event: Event) -> bool:
    required = (
        event.event_id, event.timestamp, event.source_id, event.model_version,
        event.config_version, event.state, event.confidence_zone,
    )
    if not all(required) or event.detection_count != len(event.detections):
        return False
    if event.state in ("NO_DETECTION", "MODEL_ERROR"):
        return event.confidence is None and not event.detections
    if event.confidence is None or not isfinite(event.confidence) or not event.detections:
        return False
    if event.confidence != max(d.confidence for d in event.detections):
        return False
    return all(
        d.class_id >= 0 and bool(d.class_name) and isfinite(d.confidence)
        and 0 <= d.confidence <= 1 and len(d.bbox) == 4
        and all(isfinite(coordinate) for coordinate in d.bbox)
        for d in event.detections
    )


class MetricsCollector:
    def __init__(self, run_id: str, source_id: str) -> None:
        self.run_id = run_id
        self.source_id = source_id
        self.process = psutil.Process()
        self.process.cpu_percent(interval=None)  # primera llamada solo inicializa el intervalo
        self.started_at = datetime.now(timezone.utc)
        self.started_perf = perf_counter()

    def run_start(self) -> MetricObservation:
        return MetricObservation.create(
            self.started_at.isoformat(), None, self.source_id, "G2",
            "run_start_epoch_seconds", self.started_at.timestamp(), "seconds", self.run_id,
        )

    def collect_event(self, event: Event) -> list[MetricObservation]:
        if event.source_id != self.source_id:
            raise ValueError("source_id del evento no coincide con la corrida")
        timestamp = event.timestamp
        common = (timestamp, event.event_id, event.source_id)
        observations = [
            MetricObservation.create(
                *common, "G3", "process_cpu_percent",
                self.process.cpu_percent(interval=None), "percent", self.run_id,
            ),
            MetricObservation.create(
                *common, "G5", "traceability_complete",
                int(is_traceable(event)), "boolean", self.run_id,
            ),
            MetricObservation.create(
                *common, "G6", "report_epoch_seconds",
                datetime.fromisoformat(timestamp).timestamp(), "seconds", self.run_id,
            ),
        ]
        if event.state != "MODEL_ERROR":
            observations.append(MetricObservation.create(
                *common, "G2", "processed_frame", 1, "frame", self.run_id,
            ))
        if event.inference_time_ms is not None:
            observations.append(MetricObservation.create(
                *common, "G1", "inference_time_ms", event.inference_time_ms,
                "ms/inference", self.run_id,
            ))
        if event.confidence is not None:
            observations.append(MetricObservation.create(
                *common, "G4", "frame_confidence", event.confidence, "score", self.run_id,
            ))
        return observations

    def run_end(self) -> MetricObservation:
        elapsed = perf_counter() - self.started_perf
        return MetricObservation.create(
            datetime.now(timezone.utc).isoformat(), None, self.source_id, "G2",
            "run_elapsed_seconds", elapsed, "seconds", self.run_id,
        )
