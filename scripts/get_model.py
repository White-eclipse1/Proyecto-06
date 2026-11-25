"""Obtiene el mismo artefacto verificado que utiliza Proyecto 5."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference.weights import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--path", str(ROOT / "modelo" / "yolox_tiny.onnx"), *sys.argv[1:]]))
