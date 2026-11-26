"""Inicia el portal local de Eventos y Alertas."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402

from src.portal import create_app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Portal local de consulta de monitoreo.")
    parser.add_argument("--database", default=str(ROOT / "data" / "monitoring.db"))
    parser.add_argument("--captures-dir", help="Directorio de capturas; por defecto config/capture.yaml.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not Path(args.database).is_file():
        parser.error("la base SQLite no existe; ejecuta primero una muestra de monitoreo")
    app = create_app(args.database, args.captures_dir)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
