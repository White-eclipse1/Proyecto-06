"""Recalcula G1–G6 desde SQLite sin cargar YOLOX."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.metrics.reporting import export_report, recalculate  # noqa: E402
from src.monitoring import load_config  # noqa: E402
from src.persistence import Database  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recalcula métricas desde datos primarios de SQLite.")
    parser.add_argument("--database", default=str(ROOT / "data" / "monitoring.db"))
    parser.add_argument("--source-id")
    parser.add_argument("--run-id")
    parser.add_argument("--as-of", help="ISO-8601 con zona horaria; fija G6 para reproducirlo.")
    parser.add_argument("--export", action="store_true", help="Escribe CSV y JSON en evidencias/metricas.")
    args = parser.parse_args(argv)
    try:
        source_id = args.source_id or load_config(ROOT / "config" / "monitoring.yaml").default_source_id
        as_of = datetime.fromisoformat(args.as_of) if args.as_of else None
        report, observations = recalculate(
            Database(args.database), source_id=source_id, run_id=args.run_id, as_of=as_of,
        )
        if args.export:
            paths = export_report(report, observations, ROOT / "evidencias" / "metricas")
            report["exported_files"] = [str(path) for path in paths]
        print(json.dumps(report, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        print(f"Error de recálculo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
