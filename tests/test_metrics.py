from dataclasses import replace
from datetime import datetime, timedelta, timezone
from math import isfinite

import pytest

from src.events.models import Event
from src.inference.types import Detection
from src.metrics import MetricsCollector, MetricObservation, MetricStatus, calculate_metrics
from src.metrics.collector import is_traceable
from src.persistence import Database, EventRepository, MetricRepository

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
RUN = "run-test"
SOURCE = "camera-test"


def event(index: int, confidence: float | None, zone: str) -> Event:
    detections = () if confidence is None else (
        Detection(0, "person", confidence, (1.0, 2.0, 3.0, 4.0)),
    )
    return Event(
        event_id=f"test-event-{index}",
        timestamp=(BASE + timedelta(seconds=index)).isoformat(),
        source_id=SOURCE,
        model_version="0.1.1rc0",
        config_version="monitoring-v1",
        state=zone,
        confidence=confidence,
        confidence_zone=zone,
        detections=detections,
        read_time_ms=1.0,
        preprocessing_time_ms=2.0,
        inference_time_ms=10.0,
        postprocessing_time_ms=3.0,
    )


def obs(group: str, name: str, value: float, *, linked: Event | None = None,
        timestamp: str | None = None) -> MetricObservation:
    return MetricObservation.create(
        timestamp or (linked.timestamp if linked else BASE.isoformat()),
        linked.event_id if linked else None,
        SOURCE, group, name, value, "test-unit", RUN,
    )


def calculate(observations, events=(), reports=(), at=BASE + timedelta(seconds=20)):
    return {result.metric_group: result for result in calculate_metrics(
        list(observations), list(events), list(reports),
        source_id=SOURCE, run_id=RUN, as_of=at,
    )}


def test_g1_mean_of_real_timing_observations():
    metrics = calculate([obs("G1", "inference_time_ms", 10),
                         obs("G1", "inference_time_ms", 30)])
    assert metrics["G1"].value == 20
    assert metrics["G1"].eligible_count == 2


def test_g2_known_run_duration_and_population():
    observations = [
        obs("G2", "run_start_epoch_seconds", BASE.timestamp()),
        obs("G2", "processed_frame", 1, linked=event(1, 0.7, "UNCERTAIN")),
        obs("G2", "processed_frame", 1, linked=event(2, 0.7, "UNCERTAIN")),
        obs("G2", "run_elapsed_seconds", 4, timestamp=(BASE + timedelta(seconds=4)).isoformat()),
    ]
    metric = calculate(observations)["G2"]
    assert metric.value == 0.5
    assert metric.observation_count == 2
    assert metric.window_start == BASE.isoformat()


@pytest.mark.parametrize("duration", [0, -1])
def test_g2_invalid_duration_is_insufficient(duration):
    observations = [obs("G2", "run_start_epoch_seconds", BASE.timestamp()),
                    obs("G2", "processed_frame", 1), obs("G2", "processed_frame", 1),
                    obs("G2", "run_elapsed_seconds", duration)]
    metric = calculate(observations)["G2"]
    assert metric.value is None
    assert metric.status == MetricStatus.INSUFFICIENT_DATA


def test_g2_one_frame_is_insufficient():
    observations = [obs("G2", "run_start_epoch_seconds", BASE.timestamp()),
                    obs("G2", "processed_frame", 1), obs("G2", "run_elapsed_seconds", 2)]
    assert calculate(observations)["G2"].status == MetricStatus.INSUFFICIENT_DATA


def test_g3_collects_cpu_of_current_process():
    collector = MetricsCollector(RUN, SOURCE)
    samples = collector.collect_event(event(1, 0.7, "UNCERTAIN"))
    cpu = next(item for item in samples if item.metric_name == "process_cpu_percent")
    assert cpu.event_id == "test-event-1"
    assert cpu.source_id == SOURCE
    assert isfinite(cpu.value) and cpu.value >= 0


def test_g4_ratio_excludes_no_detection_and_model_error():
    events = [event(1, 0.4, "LOW_CONFIDENCE"), event(2, 0.7, "UNCERTAIN"),
              event(3, 0.9, "ACCEPTED_BY_POLICY"), event(4, None, "NO_DETECTION"),
              event(5, None, "MODEL_ERROR")]
    observations = [obs("G2", "processed_frame", 1, linked=e) for e in events]
    observations += [obs("G4", "frame_confidence", e.confidence, linked=e)
                     for e in events if e.confidence is not None]
    metric = calculate(observations, events)["G4"]
    assert metric.value == pytest.approx(1 / 3)
    assert metric.eligible_count == 3
    assert metric.observation_count == 5


def test_g4_without_scored_results_is_null():
    empty = event(1, None, "NO_DETECTION")
    metric = calculate([obs("G2", "processed_frame", 1, linked=empty)], [empty])["G4"]
    assert metric.value is None
    assert metric.status == MetricStatus.INSUFFICIENT_DATA


def test_g5_complete_and_no_detection_are_traceable():
    scored = event(1, 0.4, "LOW_CONFIDENCE")
    empty = event(2, None, "NO_DETECTION")
    assert is_traceable(scored)
    assert is_traceable(empty)
    assert not is_traceable(replace(scored, source_id=""))
    rows = [obs("G5", "traceability_complete", 1, linked=scored),
            obs("G5", "traceability_complete", 1, linked=empty)]
    assert calculate(rows, [scored, empty])["G5"].value == 1


def test_g6_age_from_latest_report_of_source():
    report = obs("G6", "report_epoch_seconds", (BASE + timedelta(seconds=5)).timestamp(),
                 timestamp=(BASE + timedelta(seconds=5)).isoformat())
    metric = calculate([], reports=[report], at=BASE + timedelta(seconds=15))["G6"]
    assert metric.value == 10
    assert metric.status == MetricStatus.OK


def test_g6_without_report_is_insufficient():
    metric = calculate([])["G6"]
    assert metric.value is None
    assert metric.status == MetricStatus.INSUFFICIENT_DATA


def test_g6_historical_as_of_ignores_later_reports():
    old = obs("G6", "report_epoch_seconds", (BASE + timedelta(seconds=5)).timestamp())
    later = obs("G6", "report_epoch_seconds", (BASE + timedelta(seconds=30)).timestamp())
    metric = calculate([], reports=[old, later], at=BASE + timedelta(seconds=15))["G6"]
    assert metric.value == 10
    assert metric.eligible_count == 1


def test_metric_observations_persist_with_event_foreign_key(tmp_path):
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    recorded = event(1, 0.4, "LOW_CONFIDENCE")
    EventRepository(database).save_event(recorded)
    row = obs("G1", "inference_time_ms", 10, linked=recorded)
    repository = MetricRepository(database)
    repository.save_many([row])
    assert repository.list_observations(run_id=RUN) == [row]
    assert repository.events_for_run(RUN) == [recorded]


def test_no_nonfinite_primary_values():
    with pytest.raises(ValueError, match="finito"):
        obs("G1", "inference_time_ms", float("nan"))
