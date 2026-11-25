"""Prueba de inferencia real sobre una imagen: python scripts/test_inference.py --input foto.jpg."""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference import InferenceEngine  # noqa: E402
from src.inference.preprocessing import read_image  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ejecuta YOLOX-Tiny sobre una imagen.")
    parser.add_argument("--input", required=True, help="Ruta de la imagen.")
    args = parser.parse_args(argv)
    try:
        engine = InferenceEngine.from_config(ROOT / "config" / "model.yaml")
        start = perf_counter()
        frame = read_image(args.input)
        read_time_ms = (perf_counter() - start) * 1000
        result = engine.predict(frame)
        result["read_time_ms"] = read_time_ms
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:
        print(f"Error de inferencia: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
