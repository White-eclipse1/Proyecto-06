"""Muestra real: imágenes -> YOLOX -> eventos -> observaciones -> métricas."""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.events import EventBuilder  # noqa: E402
from src.inference import InferenceEngine  # noqa: E402
from src.inference.preprocessing import read_image  # noqa: E402
from src.metrics import MetricsCollector  # noqa: E402
from src.metrics.reporting import export_report, recalculate  # noqa: E402
from src.monitoring import build_reference, load_config  # noqa: E402
from src.persistence import (  # noqa: E402
    Database, EventRepository, MetricRepository, ReferenceRepository,
)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _inputs(paths: list[str] | None, directory: str | None) -> list[Path]:
    images = [Path(path) for path in paths or []]
    if directory:
        folder = Path(directory)
        if not folder.is_dir():
            raise ValueError(f"no existe la carpeta de imágenes: {folder}")
        images.extend(sorted(path for path in folder.rglob("*")
                             if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES))
    if not images:
        raise ValueError("indica --input una o más veces o --input-dir con imágenes")
    return images


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Registra una muestra real de monitoreo.")
    parser.add_argument("--input", action="append", help="Imagen; puede repetirse.")
    parser.add_argument("--input-dir", help="Carpeta de imágenes, búsqueda recursiva.")
    parser.add_argument("--database", default=str(ROOT / "data" / "monitoring.db"))
    parser.add_argument("--source-id")
    parser.add_argument("--export", action="store_true", help="Exporta CSV y JSON desde SQLite.")
    args = parser.parse_args(argv)
    try:
        images = _inputs(args.input, args.input_dir)
        config = load_config(ROOT / "config" / "monitoring.yaml")
        source_id = args.source_id or config.default_source_id
        engine = InferenceEngine.from_config(ROOT / "config" / "model.yaml")
        database = Database(args.database)
        database.initialize()
        event_repository = EventRepository(database)
        metric_repository = MetricRepository(database)
        reference_repository = ReferenceRepository(database)
        collector = MetricsCollector(str(uuid4()), source_id)
        metric_repository.save_many([collector.run_start()])
        builder = EventBuilder(config)
        events = []
        for path in images:
            read_start = perf_counter()
            frame = read_image(path)
            read_time_ms = (perf_counter() - read_start) * 1000
            prediction = engine.predict(frame)
            event = builder.build(prediction, source_id=source_id,
                                  image_reference=str(path.resolve()), read_time_ms=read_time_ms)
            event_repository.save_event(event)
            metric_repository.save_many(collector.collect_event(event))
            events.append(event)
        metric_repository.save_many([collector.run_end()])
        reference = reference_repository.latest(source_id, engine.config.version, config.version)
        if reference is None:
            reference = build_reference(events, config)
            if reference is not None:
                reference_repository.save(reference)
        report, observations = recalculate(database, source_id=source_id, run_id=collector.run_id)
        report["processed_images"] = len(events)
        report["reference"] = reference.to_dict() if reference else None
        if args.export:
            paths = export_report(report, observations, ROOT / "evidencias" / "metricas")
            report["exported_files"] = [str(path) for path in paths]
        print(json.dumps(report, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        print(f"Error de muestra de monitoreo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
