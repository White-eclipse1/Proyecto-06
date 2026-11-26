"""Configuración versionada de capturas."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CaptureConfig:
    version: str
    directory: Path
    low_confidence: bool
    normal_sample_every: int
    scenario_evidence: bool

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("capture config.version no puede estar vacío")
        if self.normal_sample_every < 1:
            raise ValueError("capture.normal_sample_every debe ser >= 1")


def load_capture_config(path: str | Path = "config/capture.yaml") -> CaptureConfig:
    config_path = Path(path).resolve()
    try:
        with config_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        capture = data["capture"]
        if not isinstance(capture["low_confidence"], bool) or not isinstance(
            capture["scenario_evidence"], bool
        ):
            raise ValueError("las opciones de captura deben ser booleanas")
        directory = Path(data["config"]["directory"])
        if not directory.is_absolute():
            directory = config_path.parent.parent / directory
        return CaptureConfig(
            version=str(data["config"]["version"]),
            directory=directory.resolve(),
            low_confidence=capture["low_confidence"],
            normal_sample_every=int(capture["normal_sample_every"]),
            scenario_evidence=capture["scenario_evidence"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"configuración de capturas inválida en {config_path}: {error}") from error
