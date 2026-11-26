"""YOLOX real -> evento -> captura -> regla -> alerta -> SQLite -> G7."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.alerts import AlertEngine, load_alert_config  # noqa: E402
from src.alerts.pipeline import AlertPipeline  # noqa: E402
from src.captures import CapturePolicy, CaptureStore, load_capture_config  # noqa: E402
from src.captures.export import export_event_evidence  # noqa: E402
from src.events import EventBuilder  # noqa: E402
from src.inference import InferenceEngine  # noqa: E402
from src.inference.preprocessing import read_image  # noqa: E402
from src.monitoring import load_config  # noqa: E402
from src.persistence import AlertRepository, Database, EventRepository  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prueba real de captura y alertas.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--database", default=str(ROOT / "data" / "monitoring.db"))
    parser.add_argument("--captures-dir", help="Sobrescribe el directorio de capturas.")
    parser.add_argument("--source-id")
    parser.add_argument("--normal-index", type=int)
    parser.add_argument("--scenario-evidence", action="store_true")
    parser.add_argument("--export", action="store_true", help="Exporta alerta, evento e imagen reales.")
    args = parser.parse_args(argv)
    try:
        monitoring = load_config(ROOT / "config" / "monitoring.yaml")
        alert_config = load_alert_config(ROOT / "config" / "alerts.yaml")
        capture_config = load_capture_config(ROOT / "config" / "capture.yaml")
        store = CaptureStore(args.captures_dir or capture_config.directory)
        database = Database(args.database)
        database.initialize()
        events = EventRepository(database)
        alerts = AlertRepository(database)
        engine = InferenceEngine.from_config(ROOT / "config" / "model.yaml")
        read_start = perf_counter()
        frame = read_image(args.input)
        read_time_ms = (perf_counter() - read_start) * 1000
        prediction = engine.predict(frame)
        event = EventBuilder(monitoring).build(
            prediction, source_id=args.source_id, read_time_ms=read_time_ms,
        )
        events.save_event(event)
        pipeline = AlertPipeline(
            events, alerts, CapturePolicy(capture_config), store, AlertEngine(alert_config),
        )
        result = pipeline.process(
            event.event_id, frame, normal_index=args.normal_index,
            scenario_evidence=args.scenario_evidence,
        )
        recovered_event = events.get_event(event.event_id)
        if recovered_event != result.event:
            raise RuntimeError("el evento recuperado no coincide con el procesado")
        recovered_alert = None
        if result.alert is not None:
            recovered_alert = alerts.get_alert(result.alert.alert_id)
            if recovered_alert != result.alert or recovered_alert.event_id != event.event_id:
                raise RuntimeError("la alerta recuperada no coincide con su evento")
        image_exists = False
        if recovered_event.image_reference is not None:
            image_exists = store.resolve(recovered_event.image_reference).is_file()
        if recovered_alert is not None and not image_exists:
            raise RuntimeError("la alerta no tiene una captura resoluble")
        active_count = len(alerts.list_active_alerts(
            source_id=recovered_event.source_id, as_of=datetime.now(timezone.utc),
        ))
        output = {
            "status": "ok", "event_id": event.event_id,
            "confidence": recovered_event.confidence,
            "confidence_zone": recovered_event.confidence_zone,
            "image_reference": recovered_event.image_reference,
            "image_exists": image_exists,
            "capture_reasons": list(result.capture_reasons),
            "rule_status": result.rule_status.value,
            "alert_created": result.alert_created,
            "alert": recovered_alert.to_dict() if recovered_alert else None,
            "g7_active_alerts": active_count,
        }
        if args.export:
            alert_path = alerts.export_alerts(
                ROOT / "evidencias" / "alertas" / "alertas.json",
                source_id=recovered_event.source_id,
            )
            event_path, image_path = export_event_evidence(recovered_event, store, ROOT / "evidencias")
            output["exported_files"] = [str(path) for path in (alert_path, event_path, image_path)
                                        if path is not None]
        print(json.dumps(output, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        print(f"Error del pipeline de alertas: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
