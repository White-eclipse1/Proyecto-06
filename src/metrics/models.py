"""Contratos de datos primarios y resultados recalculables."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from math import isfinite
from uuid import uuid4


class MetricStatus(StrEnum):
    OK = "OK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


@dataclass(frozen=True)
class MetricObservation:
    observation_id: str
    timestamp: str
    event_id: str | None
    source_id: str
    metric_group: str
    metric_name: str
    value: float
    unit: str
    run_id: str

    def __post_init__(self) -> None:
        if not isfinite(self.value):
            raise ValueError("una observación primaria debe tener valor finito")

    @classmethod
    def create(
        cls, timestamp: str, event_id: str | None, source_id: str,
        metric_group: str, metric_name: str, value: float, unit: str, run_id: str,
    ) -> "MetricObservation":
        return cls(str(uuid4()), timestamp, event_id, source_id, metric_group,
                   metric_name, float(value), unit, run_id)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MetricResult:
    metric_group: str
    metric_name: str
    value: float | None
    unit: str
    status: MetricStatus
    window_start: str | None
    window_end: str | None
    observation_count: int
    eligible_count: int
    source_id: str
    run_id: str | None

    def __post_init__(self) -> None:
        if self.value is not None and not isfinite(self.value):
            raise ValueError("el resultado de la métrica debe ser finito o null")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
