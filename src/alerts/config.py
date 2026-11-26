"""Configuración explícita de reglas de alertas."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import Severity


@dataclass(frozen=True)
class LowConfidenceRuleConfig:
    enabled: bool
    minimum_events: int
    window_size: int
    severity: Severity
    reason: str
    suggested_action: str

    def __post_init__(self) -> None:
        if not 1 <= self.minimum_events <= self.window_size:
            raise ValueError("low_confidence: 1 <= minimum_events <= window_size requerido")


@dataclass(frozen=True)
class SustainedRuleConfig:
    enabled: bool
    severity: Severity
    reason: str
    suggested_action: str


@dataclass(frozen=True)
class AlertConfig:
    version: str
    low_confidence: LowConfidenceRuleConfig
    sustained_confidence_change: SustainedRuleConfig


def load_alert_config(path: str | Path = "config/alerts.yaml") -> AlertConfig:
    try:
        with Path(path).open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        low = data["alerts"]["low_confidence"]
        sustained = data["alerts"]["sustained_confidence_change"]
        if not isinstance(low["enabled"], bool) or not isinstance(sustained["enabled"], bool):
            raise ValueError("alerts.enabled debe ser booleano")
        return AlertConfig(
            version=str(data["config"]["version"]),
            low_confidence=LowConfidenceRuleConfig(
                enabled=low["enabled"],
                minimum_events=int(low["minimum_events"]),
                window_size=int(low["window_size"]),
                severity=Severity(low["severity"]),
                reason=str(low["reason"]),
                suggested_action=str(low["suggested_action"]),
            ),
            sustained_confidence_change=SustainedRuleConfig(
                enabled=sustained["enabled"],
                severity=Severity(sustained["severity"]),
                reason=str(sustained["reason"]),
                suggested_action=str(sustained["suggested_action"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"configuración de alertas inválida en {path}: {error}") from error
