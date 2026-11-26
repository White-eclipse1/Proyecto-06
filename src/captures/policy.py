"""Decide qué frames se conservan, sin guardar cada frame normal."""

from dataclasses import dataclass

from src.events.models import Event

from .config import CaptureConfig


@dataclass(frozen=True)
class CaptureDecision:
    reasons: tuple[str, ...]

    @property
    def capture(self) -> bool:
        return bool(self.reasons)


class CapturePolicy:
    def __init__(self, config: CaptureConfig) -> None:
        self.config = config

    def decide(
        self, event: Event, *, alert: bool = False,
        normal_index: int | None = None, scenario_evidence: bool = False,
    ) -> CaptureDecision:
        reasons = []
        if (self.config.low_confidence and event.confidence is not None
                and event.confidence_zone == "LOW_CONFIDENCE"):
            reasons.append("LOW_CONFIDENCE")
        if alert:
            reasons.append("ALERT")
        if (normal_index is not None and normal_index > 0
                and normal_index % self.config.normal_sample_every == 0
                and event.confidence_zone == "ACCEPTED_BY_POLICY"):
            reasons.append("NORMAL_SAMPLE")
        if scenario_evidence and self.config.scenario_evidence:
            reasons.append("SCENARIO_EVIDENCE")
        return CaptureDecision(tuple(reasons))
