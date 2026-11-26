"""Referencia de confianza y regla configurable de cambio sostenido."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from statistics import mean
from uuid import uuid4

from src.events.models import Event

from .config import MonitoringConfig


class ChangeState(StrEnum):
    NORMAL = "NORMAL"
    OBSERVING_CHANGE = "OBSERVING_CHANGE"
    SUSTAINED_CONFIDENCE_CHANGE = "SUSTAINED_CONFIDENCE_CHANGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class ConfidenceReference:
    reference_id: str
    created_at: str
    model_version: str
    config_version: str
    source_id: str
    sample_count: int
    window_size: int
    mean_confidence: float
    event_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["event_ids"] = list(self.event_ids)
        return data


@dataclass(frozen=True)
class WindowAssessment:
    window_id: str | None
    state: ChangeState
    reference_id: str | None
    observation_count: int
    mean_confidence: float | None
    relative_drop: float | None
    consecutive_drops: int
    event_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["state"] = self.state.value
        data["event_ids"] = list(self.event_ids)
        return data


def _check_identity(events: list[Event], source_id: str, model_version: str,
                    config_version: str) -> None:
    for event in events:
        if (event.source_id, event.model_version, event.config_version) != (
            source_id, model_version, config_version
        ):
            raise ValueError("identidad incompatible: model_version, config_version o source_id")


def build_reference(events: list[Event], config: MonitoringConfig) -> ConfidenceReference | None:
    """Fija el promedio de las primeras observaciones puntuadas de una serie real."""
    if not events:
        return None
    ordered = sorted(events, key=lambda e: (e.timestamp, e.event_id))
    first = ordered[0]
    _check_identity(ordered, first.source_id, first.model_version, config.version)
    scored = [e for e in ordered if e.confidence is not None and
              e.confidence_zone not in ("MODEL_ERROR", "NO_DETECTION", "MISSING_SCORE")]
    sample = scored[:config.window_size]
    if len(sample) < config.minimum_observations:
        return None
    average = mean(e.confidence for e in sample)
    if average <= 0:
        raise ValueError("la referencia requiere confianza media positiva")
    return ConfidenceReference(
        reference_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        model_version=first.model_version,
        config_version=config.version,
        source_id=first.source_id,
        sample_count=len(sample),
        window_size=config.window_size,
        mean_confidence=average,
        event_ids=tuple(e.event_id for e in sample),
    )


def assess_windows(
    reference: ConfidenceReference | None, events: list[Event], config: MonitoringConfig,
) -> list[WindowAssessment]:
    if reference is None:
        return [WindowAssessment(None, ChangeState.INSUFFICIENT_DATA, None, 0, None, None, 0, ())]
    if reference.config_version != config.version or reference.window_size != config.window_size:
        raise ValueError("identidad incompatible: configuración de referencia diferente")
    _check_identity(events, reference.source_id, reference.model_version, reference.config_version)
    reference_ids = set(reference.event_ids)
    scored = [e for e in sorted(events, key=lambda e: (e.timestamp, e.event_id))
              if e.event_id not in reference_ids and e.confidence is not None and
              e.confidence_zone not in ("MODEL_ERROR", "NO_DETECTION", "MISSING_SCORE")]
    if not scored:
        return [WindowAssessment(None, ChangeState.INSUFFICIENT_DATA,
                                 reference.reference_id, 0, None, None, 0, ())]
    assessments = []
    consecutive = 0
    for offset in range(0, len(scored), config.window_size):
        window = scored[offset:offset + config.window_size]
        ids = tuple(e.event_id for e in window)
        window_id = f"{reference.reference_id}:{ids[0]}:{ids[-1]}"
        if len(window) < config.minimum_observations:
            consecutive = 0
            assessments.append(WindowAssessment(window_id, ChangeState.INSUFFICIENT_DATA,
                                                reference.reference_id, len(window), None, None, 0, ids))
            continue
        average = mean(e.confidence for e in window)
        drop = (reference.mean_confidence - average) / reference.mean_confidence
        if config.sustained_change_enabled and drop >= config.relative_drop:
            consecutive += 1
            state = (ChangeState.SUSTAINED_CONFIDENCE_CHANGE
                     if consecutive >= config.consecutive_windows else ChangeState.OBSERVING_CHANGE)
        else:
            consecutive = 0
            state = ChangeState.NORMAL
        assessments.append(WindowAssessment(window_id, state, reference.reference_id,
                                            len(window), average, drop, consecutive, ids))
    return assessments
