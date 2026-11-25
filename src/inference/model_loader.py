"""Carga la configuración y los pesos verificados de YOLOX-Tiny en CPU."""

from dataclasses import dataclass
from pathlib import Path

import onnxruntime
import yaml

from .weights import verify_weights


@dataclass(frozen=True)
class ModelConfig:
    name: str
    version: str
    path: Path
    input_size: tuple[int, int]
    score_threshold: float
    nms_threshold: float
    median_kernel: int
    sha256: str
    size_bytes: int


def read_config(path: str | Path) -> ModelConfig:
    config_path = Path(path).resolve()
    with config_path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    model = data["model"]
    # config/model.yaml: las rutas del proyecto se resuelven desde la raíz de P6.
    root = config_path.parent.parent
    size = model["input_size"]
    return ModelConfig(
        name=str(model["name"]),
        version=str(model["version"]),
        path=root / model["path"],
        input_size=(int(size[0]), int(size[1])),
        score_threshold=float(model["postprocessing"]["score_threshold"]),
        nms_threshold=float(model["postprocessing"]["nms_threshold"]),
        median_kernel=int(model["preprocessing"]["median_kernel"]),
        sha256=str(model["expected_sha256"]),
        size_bytes=int(model["expected_size_bytes"]),
    )


def load_session(config: ModelConfig) -> onnxruntime.InferenceSession:
    verify_weights(config.path, sha256=config.sha256, size=config.size_bytes)
    session = onnxruntime.InferenceSession(
        str(config.path), providers=["CPUExecutionProvider"]
    )
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise RuntimeError(f"se esperaba solo CPU: {session.get_providers()}")
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].shape != [1, 3, *config.input_size]:
        raise RuntimeError(f"entrada inesperada del modelo: {[value.shape for value in inputs]}")
    return session
