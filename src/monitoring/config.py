"""Configuración versionada del monitoreo inicial."""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MonitoringConfig:
    version: str
    lower_threshold: float
    upper_threshold: float
    window_size: int
    minimum_observations: int
    default_source_id: str
    sustained_change_enabled: bool = True
    relative_drop: float = 0.20
    consecutive_windows: int = 2

    def __post_init__(self) -> None:
        if not (
            isfinite(self.lower_threshold)
            and isfinite(self.upper_threshold)
            and 0 <= self.lower_threshold < self.upper_threshold <= 1
        ):
            raise ValueError(
                "confidence: se requiere 0 <= lower_threshold < upper_threshold <= 1"
            )
        if self.window_size < 1 or not 1 <= self.minimum_observations <= self.window_size:
            raise ValueError("monitoring: se requiere 1 <= minimum_observations <= window_size")
        if not self.version or not self.default_source_id:
            raise ValueError("config.version y source.default_id no pueden estar vacíos")
        if not isfinite(self.relative_drop) or not 0 < self.relative_drop <= 1:
            raise ValueError("sustained_change.relative_drop debe estar en (0, 1]")
        if self.consecutive_windows < 1:
            raise ValueError("sustained_change.consecutive_windows debe ser >= 1")


def load_config(path: str | Path = "config/monitoring.yaml") -> MonitoringConfig:
    with Path(path).open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    try:
        change = data["sustained_change"]
        if not isinstance(change["enabled"], bool):
            raise ValueError("sustained_change.enabled debe ser booleano")
        return MonitoringConfig(
            version=str(data["config"]["version"]),
            lower_threshold=float(data["confidence"]["lower_threshold"]),
            upper_threshold=float(data["confidence"]["upper_threshold"]),
            window_size=int(data["monitoring"]["window_size"]),
            minimum_observations=int(data["monitoring"]["minimum_observations"]),
            default_source_id=str(data["source"]["default_id"]),
            sustained_change_enabled=change["enabled"],
            relative_drop=float(change["relative_drop"]),
            consecutive_windows=int(change["consecutive_windows"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"configuración de monitoreo inválida en {path}: {error}") from error
