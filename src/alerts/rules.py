"""Resultado de evaluación de una regla, incluso cuando faltan datos."""

from dataclasses import dataclass
from enum import StrEnum

from .models import Alert


class RuleStatus(StrEnum):
    TRIGGERED = "TRIGGERED"
    NOT_TRIGGERED = "NOT_TRIGGERED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class RuleOutcome:
    status: RuleStatus
    alert: Alert | None = None

    @property
    def alert_created(self) -> bool:
        return self.alert is not None
