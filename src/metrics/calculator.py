"""Calcula G1–G6 exclusivamente a partir de observaciones/eventos guardados."""

from datetime import datetime, timezone
from statistics import mean

from src.events.models import Event
from src.alerts.models import Alert

from .collector import is_traceable

from .models import MetricObservation as Observation
from .models import MetricResult, MetricStatus


def calculate_metrics(
    observations: list[Observation], events: list[Event],
    source_reports: list[Observation], *, source_id: str, run_id: str | None,
    as_of: datetime, active_alerts: list[Alert] | None = None,
) -> list[MetricResult]:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of debe tener zona horaria")
    as_of = as_of.astimezone(timezone.utc)
    by_name: dict[str, list[Observation]] = {}
    for observation in observations:
        if observation.source_id != source_id:
            raise ValueError("la corrida contiene observaciones de otra fuente")
        by_name.setdefault(observation.metric_name, []).append(observation)
    event_map = {event.event_id: event for event in events}

    def result(group: str, name: str, unit: str, rows: list[Observation],
               value: float | None, eligible: int, status: MetricStatus,
               start: str | None = None, end: str | None = None) -> MetricResult:
        if rows:
            start = start or min(o.timestamp for o in rows)
            end = end or max(o.timestamp for o in rows)
        return MetricResult(group, name, value, unit, status, start, end,
                            len(rows), eligible, source_id, run_id)

    results = []
    times = by_name.get("inference_time_ms", [])
    results.append(result("G1", "inference_time_ms", "ms/inference", times,
                          mean(o.value for o in times) if times else None,
                          len(times), MetricStatus.OK if times else MetricStatus.INSUFFICIENT_DATA))

    frames = by_name.get("processed_frame", [])
    starts = by_name.get("run_start_epoch_seconds", [])
    ends = by_name.get("run_elapsed_seconds", [])
    duration = ends[0].value if len(ends) == 1 else None
    fps_valid = len(frames) >= 2 and len(starts) == 1 and duration is not None and duration > 0
    results.append(result(
        "G2", "processing_fps", "frames/second", frames,
        len(frames) / duration if fps_valid else None,
        len(frames) if fps_valid else 0,
        MetricStatus.OK if fps_valid else MetricStatus.INSUFFICIENT_DATA,
        starts[0].timestamp if len(starts) == 1 else None,
        ends[0].timestamp if len(ends) == 1 else None,
    ))

    cpu = by_name.get("process_cpu_percent", [])
    results.append(result("G3", "process_cpu_percent", "percent", cpu,
                          mean(o.value for o in cpu) if cpu else None,
                          len(cpu), MetricStatus.OK if cpu else MetricStatus.INSUFFICIENT_DATA))

    scored = by_name.get("frame_confidence", [])
    missing_events = [o for o in scored if o.event_id not in event_map or
                      o.value != event_map[o.event_id].confidence]
    eligible = [o for o in scored if o.event_id in event_map and
                event_map[o.event_id].confidence is not None and
                event_map[o.event_id].confidence_zone not in
                ("NO_DETECTION", "MODEL_ERROR", "MISSING_SCORE")]
    if missing_events:
        g4_status = MetricStatus.ERROR
    elif not eligible:
        g4_status = MetricStatus.INSUFFICIENT_DATA
    else:
        g4_status = MetricStatus.OK
    low = sum(event_map[o.event_id].confidence_zone == "LOW_CONFIDENCE" for o in eligible)
    results.append(result("G4", "low_confidence_ratio", "ratio", frames,
                          low / len(eligible) if g4_status == MetricStatus.OK else None,
                          len(eligible), g4_status))

    trace = by_name.get("traceability_complete", [])
    trace_valid = all(
        o.value in (0, 1) and o.event_id in event_map and
        o.value == int(is_traceable(event_map[o.event_id])) for o in trace
    )
    g5_status = (MetricStatus.ERROR if not trace_valid else
                 MetricStatus.OK if trace else MetricStatus.INSUFFICIENT_DATA)
    results.append(result("G5", "traceability_coverage", "ratio", trace,
                          sum(o.value for o in trace) / len(trace) if g5_status == MetricStatus.OK else None,
                          len(trace) if trace_valid else 0, g5_status))

    reports = [o for o in source_reports if o.source_id == source_id and
               o.metric_name == "report_epoch_seconds" and o.value <= as_of.timestamp()]
    latest = max(reports, key=lambda o: o.value) if reports else None
    age = as_of.timestamp() - latest.value if latest else None
    g6_status = MetricStatus.INSUFFICIENT_DATA if latest is None else MetricStatus.OK
    results.append(result("G6", "last_report_age_seconds", "seconds", reports,
                          age if g6_status == MetricStatus.OK else None,
                          len(reports), g6_status,
                          latest.timestamp if latest else None, as_of.isoformat()))
    if active_alerts is None:
        results.append(MetricResult(
            "G7", "active_alerts", None, "count", MetricStatus.INSUFFICIENT_DATA,
            None, as_of.isoformat(), 0, 0, source_id, run_id,
        ))
    else:
        if any(alert.source_id != source_id or alert.status != "ACTIVE" for alert in active_alerts):
            raise ValueError("G7 recibió alertas de otra fuente o estado")
        results.append(MetricResult(
            "G7", "active_alerts", len(active_alerts), "count", MetricStatus.OK,
            min((alert.timestamp for alert in active_alerts), default=None),
            as_of.isoformat(), len(active_alerts), len(active_alerts), source_id, run_id,
        ))
    return results
