"""Imagen real -> inferencia -> zona -> evento -> SQLite -> lectura -> JSON."""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.events import EventBuilder  # noqa: E402
from src.inference import InferenceEngine  # noqa: E402
from src.inference.preprocessing import read_image  # noqa: E402
from src.monitoring import load_config  # noqa: E402
from src.persistence import Database, EventRepository  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Comprueba inferencia y persistencia SQLite.")
    parser.add_argument("--input", required=True, help="Ruta de una imagen real.")
    parser.add_argument("--database", default=str(ROOT / "data" / "monitoring.db"))
    parser.add_argument("--source-id", help="ID de la fuente; por defecto, config/monitoring.yaml.")
    args = parser.parse_args(argv)
    try:
        config = load_config(ROOT / "config" / "monitoring.yaml")
        builder = EventBuilder(config)
        engine = InferenceEngine.from_config(ROOT / "config" / "model.yaml")
        read_start = perf_counter()
        frame = read_image(args.input)
        read_time_ms = (perf_counter() - read_start) * 1000
        database = Database(args.database)
        database.initialize()
        repository = EventRepository(database)
        try:
            prediction = engine.predict(frame)
        except Exception as error:
            event = builder.model_error(
                error,
                model_version=engine.config.version,
                source_id=args.source_id,
                image_reference=str(Path(args.input).resolve()),
                read_time_ms=read_time_ms,
            )
            repository.save_event(event)
            recovered = repository.get_event(event.event_id)
            if recovered != event:
                raise RuntimeError("el evento MODEL_ERROR recuperado no coincide con el generado")
            print(json.dumps({"status": "model_error", "event": recovered.to_dict(), "persisted": True}))
            return 1
        event = builder.build(
            prediction,
            source_id=args.source_id,
            image_reference=str(Path(args.input).resolve()),
            read_time_ms=read_time_ms,
        )
        repository.save_event(event)
        recovered = repository.get_event(event.event_id)
        if recovered != event:
            raise RuntimeError("el evento recuperado no coincide con el generado")
        print(json.dumps({"status": "ok", "event": recovered.to_dict(), "persisted": True}))
        return 0
    except Exception as error:
        print(f"Error del pipeline de eventos: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
