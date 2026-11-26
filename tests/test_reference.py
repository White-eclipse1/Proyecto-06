from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.events.models import Event
from src.inference.types import Detection
from src.monitoring import MonitoringConfig
from src.monitoring.reference import ChangeState, assess_windows, build_reference
from src.persistence import Database, EventRepository, ReferenceRepository

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def config() -> MonitoringConfig:
    return MonitoringConfig("monitoring-v1", 0.6, 0.8, 2, 2, "camera-test", True, 0.2, 2)


def event(index: int, confidence: float, *, model: str = "0.1.1rc0") -> Event:
    return Event(
        event_id=f"reference-test-{index}",
        timestamp=(BASE + timedelta(seconds=index)).isoformat(),
        source_id="camera-test", model_version=model, config_version="monitoring-v1",
        state="UNCERTAIN", confidence=confidence, confidence_zone="UNCERTAIN",
        detections=(Detection(0, "person", confidence, (0, 0, 10, 10)),),
        read_time_ms=1, preprocessing_time_ms=1, inference_time_ms=10,
        postprocessing_time_ms=1,
    )


def test_reference_from_scored_events_and_persists_identity(tmp_path):
    events = [event(1, 0.8), event(2, 0.6)]
    reference = build_reference(events, config())
    assert reference.sample_count == 2
    assert reference.window_size == 2
    assert reference.mean_confidence == pytest.approx(0.7)
    assert reference.event_ids == tuple(e.event_id for e in events)
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    for item in events:
        EventRepository(database).save_event(item)
    repository = ReferenceRepository(database)
    repository.save(reference)
    assert repository.latest("camera-test", "0.1.1rc0", "monitoring-v1") == reference
    assert repository.latest("camera-test", "other-model", "monitoring-v1") is None


def test_reference_requires_minimum_observations():
    assert build_reference([event(1, 0.8)], config()) is None


def test_incompatible_identity_is_rejected():
    reference = build_reference([event(1, 0.8), event(2, 0.8)], config())
    with pytest.raises(ValueError, match="identidad incompatible"):
        build_reference([event(1, 0.8), event(2, 0.8, model="other")], config())
    with pytest.raises(ValueError, match="identidad incompatible"):
        assess_windows(reference, [event(3, 0.5, model="other")], config())
    with pytest.raises(ValueError, match="identidad incompatible"):
        assess_windows(reference, [replace(event(3, 0.5), config_version="other-config")], config())


def test_sustained_change_requires_two_consecutive_windows():
    reference = build_reference([event(1, 0.8), event(2, 0.8)], config())
    current = [event(3, 0.5), event(4, 0.5), event(5, 0.4), event(6, 0.4)]
    states = [window.state for window in assess_windows(reference, current, config())]
    assert states == [ChangeState.OBSERVING_CHANGE, ChangeState.SUSTAINED_CONFIDENCE_CHANGE]


def test_change_not_sustained_resets_to_normal():
    reference = build_reference([event(1, 0.8), event(2, 0.8)], config())
    current = [event(3, 0.5), event(4, 0.5), event(5, 0.75), event(6, 0.85)]
    states = [window.state for window in assess_windows(reference, current, config())]
    assert states == [ChangeState.OBSERVING_CHANGE, ChangeState.NORMAL]


def test_window_with_too_few_scores_is_insufficient():
    reference = build_reference([event(1, 0.8), event(2, 0.8)], config())
    result = assess_windows(reference, [event(3, 0.4)], config())[0]
    assert result.state == ChangeState.INSUFFICIENT_DATA
    assert result.mean_confidence is None


def test_consecutive_windows_continue_across_runs(tmp_path):
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    repository = EventRepository(database)
    baseline = [event(1, 0.8), event(2, 0.8)]
    first_run = [event(3, 0.5), event(4, 0.5)]
    second_run = [event(5, 0.4), event(6, 0.4)]
    for item in baseline + first_run + second_run:
        repository.save_event(item)
    reference = build_reference(baseline, config())
    ReferenceRepository(database).save(reference)
    after = (baseline[-1].timestamp, baseline[-1].event_id)
    series = repository.list_by_identity(
        "camera-test", "0.1.1rc0", "monitoring-v1", after=after,
    )
    assert series == first_run + second_run
    assert [result.state for result in assess_windows(reference, series, config())] == [
        ChangeState.OBSERVING_CHANGE, ChangeState.SUSTAINED_CONFIDENCE_CHANGE,
    ]
