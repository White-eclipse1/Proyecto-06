"""Evalúa LOW_CONFIDENCE y, opcionalmente, cambio sostenido."""

from datetime import datetime, timezone
from uuid import uuid4

from src.events.models import Event
from src.monitoring.reference import ChangeState, WindowAssessment

from .config import AlertConfig
from .models import Alert, AlertStatus
from .rules import RuleOutcome, RuleStatus


class AlertEngine:
    def __init__(self, config: AlertConfig) -> None:
        self.config = config

    def evaluate_event(self, event: Event, recent_events: list[Event]) -> RuleOutcome:
        rule = self.config.low_confidence
        if not rule.enabled:
            return RuleOutcome(RuleStatus.DISABLED)
        if event.confidence is None or event.confidence_zone != "LOW_CONFIDENCE":
            return RuleOutcome(RuleStatus.NOT_TRIGGERED)
        identity = (event.source_id, event.model_version, event.config_version)
        if any((e.source_id, e.model_version, e.config_version) != identity for e in recent_events):
            raise ValueError("la regla recibió eventos de identidad incompatible")
        candidates = sorted(
            (e for e in recent_events if e.confidence is not None),
            key=lambda e: (e.timestamp, e.event_id),
        )[-rule.window_size:]
        if event.event_id not in {e.event_id for e in candidates}:
            raise ValueError("el evento evaluado debe estar dentro de la ventana reciente")
        if len(candidates) < rule.minimum_events:
            return RuleOutcome(RuleStatus.INSUFFICIENT_DATA)
        low_count = sum(e.confidence_zone == "LOW_CONFIDENCE" for e in candidates)
        if low_count < rule.minimum_events:
            return RuleOutcome(RuleStatus.NOT_TRIGGERED)
        return RuleOutcome(RuleStatus.TRIGGERED, Alert(
            alert_id=str(uuid4()), timestamp=datetime.now(timezone.utc).isoformat(),
            rule_id="LOW_CONFIDENCE_ALERT", severity=rule.severity,
            reason=rule.reason, suggested_action=rule.suggested_action,
            status=AlertStatus.ACTIVE, source_id=event.source_id,
            config_version=self.config.version, event_id=event.event_id,
        ))

    def evaluate_window(self, assessment: WindowAssessment, *, source_id: str) -> RuleOutcome:
        rule = self.config.sustained_confidence_change
        if not rule.enabled:
            return RuleOutcome(RuleStatus.DISABLED)
        if assessment.state == ChangeState.INSUFFICIENT_DATA:
            return RuleOutcome(RuleStatus.INSUFFICIENT_DATA)
        if assessment.state != ChangeState.SUSTAINED_CONFIDENCE_CHANGE:
            return RuleOutcome(RuleStatus.NOT_TRIGGERED)
        if not assessment.window_id or not assessment.reference_id:
            raise ValueError("la alerta de ventana requiere window_id y reference_id")
        return RuleOutcome(RuleStatus.TRIGGERED, Alert(
            alert_id=str(uuid4()), timestamp=datetime.now(timezone.utc).isoformat(),
            rule_id="SUSTAINED_CONFIDENCE_CHANGE_ALERT", severity=rule.severity,
            reason=rule.reason, suggested_action=rule.suggested_action,
            status=AlertStatus.ACTIVE, source_id=source_id,
            config_version=self.config.version,
            window_id=assessment.window_id, reference_id=assessment.reference_id,
        ))
