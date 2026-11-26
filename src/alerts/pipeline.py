"""Conecta evento persistido, captura selectiva y regla de alerta."""

from dataclasses import dataclass

import numpy as np

from src.captures import CapturePolicy, CaptureStore
from src.events.models import Event
from src.persistence.alert_repository import AlertRepository
from src.persistence.repositories import EventRepository

from .engine import AlertEngine
from .models import Alert
from .rules import RuleStatus


@dataclass(frozen=True)
class AlertPipelineResult:
    event: Event
    alert: Alert | None
    alert_created: bool
    rule_status: RuleStatus
    capture_reasons: tuple[str, ...]


class AlertPipeline:
    def __init__(
        self, event_repository: EventRepository, alert_repository: AlertRepository,
        capture_policy: CapturePolicy, capture_store: CaptureStore,
        alert_engine: AlertEngine,
    ) -> None:
        self.events = event_repository
        self.alerts = alert_repository
        self.capture_policy = capture_policy
        self.capture_store = capture_store
        self.alert_engine = alert_engine

    def process(
        self, event_id: str, frame: np.ndarray, *, normal_index: int | None = None,
        scenario_evidence: bool = False,
    ) -> AlertPipelineResult:
        event = self.events.get_event(event_id)
        if event is None:
            raise ValueError(f"evento no encontrado: {event_id}")
        recent = self.events.recent_scored_by_identity(
            event.source_id, event.model_version, event.config_version,
            self.alert_engine.config.low_confidence.window_size,
        )
        outcome = self.alert_engine.evaluate_event(event, recent)
        decision = self.capture_policy.decide(
            event, alert=outcome.alert is not None,
            normal_index=normal_index, scenario_evidence=scenario_evidence,
        )
        reference = self.capture_store.save(event.event_id, frame) if decision.capture else None
        saved_alert = None
        created = False
        if outcome.alert is not None:
            saved_alert, created = self.alerts.save_alert(
                outcome.alert, image_reference=reference,
            )
        elif reference is not None:
            self.events.set_image_reference(event.event_id, reference)
        updated = self.events.get_event(event.event_id)
        assert updated is not None
        if updated.image_reference is not None and reference is not None:
            self.capture_store.resolve(updated.image_reference)
        return AlertPipelineResult(
            updated, saved_alert, created, outcome.status, decision.reasons,
        )
