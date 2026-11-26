"""Contrato de alerta y estados explícitos."""

from dataclasses import asdict, dataclass
from enum import StrEnum


class AlertStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Alert:
    alert_id: str
    timestamp: str
    rule_id: str
    severity: Severity
    reason: str
    suggested_action: str
    status: AlertStatus
    source_id: str
    config_version: str
    event_id: str | None = None
    window_id: str | None = None
    reference_id: str | None = None
    resolved_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        return data
