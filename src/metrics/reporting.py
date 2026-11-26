"""Lee SQLite, recalcula indicadores y exporta evidencia verificable."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.monitoring import assess_windows, load_config
from src.persistence.database import Database
from src.persistence.metric_repository import MetricRepository
from src.persistence.reference_repository import ReferenceRepository
from src.persistence.repositories import EventRepository

from .calculator import calculate_metrics
from .models import MetricObservation


def recalculate(
    database: Database, *, source_id: str, run_id: str | None = None,
    as_of: datetime | None = None,
) -> tuple[dict[str, object], list[MetricObservation]]:
    database.initialize()
    repository = MetricRepository(database)
    run_id = run_id or repository.latest_run_id(source_id)
    observations = repository.list_observations(run_id=run_id, source_id=source_id) if run_id else []
    events = repository.events_for_run(run_id) if run_id else []
    reports = repository.list_observations(source_id=source_id, metric_group="G6")
    as_of = as_of or datetime.now(timezone.utc)
    results = calculate_metrics(
        observations, events, reports, source_id=source_id, run_id=run_id, as_of=as_of,
    )
    config = load_config(Path(__file__).resolve().parents[2] / "config" / "monitoring.yaml")
    compatible = bool(events) and events[0].config_version == config.version
    reference = (ReferenceRepository(database).latest(source_id, events[0].model_version, config.version)
                 if compatible else None)
    if reference is None:
        windows = assess_windows(None, [], config)
    else:
        event_repository = EventRepository(database)
        baseline_end = event_repository.get_event(reference.event_ids[-1])
        if baseline_end is None:
            raise ValueError("falta el último evento de la referencia")
        series = event_repository.list_by_identity(
            source_id, reference.model_version, reference.config_version,
            after=(baseline_end.timestamp, baseline_end.event_id),
        )
        windows = assess_windows(reference, series, config)
    report = {
        "source_id": source_id,
        "run_id": run_id,
        "as_of": as_of.astimezone(timezone.utc).isoformat(),
        "metrics": [result.to_dict() for result in results],
        "reference": reference.to_dict() if reference else None,
        "reference_status": ("CONFIG_VERSION_MISMATCH" if events and not compatible else
                             "INSUFFICIENT_DATA" if reference is None else "OK"),
        "windows": [window.to_dict() for window in windows],
    }
    return report, observations


def export_report(
    report: dict[str, object], observations: list[MetricObservation], directory: str | Path,
) -> tuple[Path, Path]:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    csv_path = target / "observaciones.csv"
    json_path = target / "resultados.json"
    fields = list(MetricObservation.__dataclass_fields__)
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(observation.to_dict() for observation in observations)
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
    return csv_path, json_path
