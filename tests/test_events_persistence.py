import sqlite3
from dataclasses import replace
from datetime import datetime
from uuid import UUID

import pytest

from src.events import EventBuilder
from src.inference.types import Detection
from src.monitoring import MonitoringConfig
from src.persistence import Database, EventRepository


@pytest.fixture
def config():
    return MonitoringConfig("monitoring-v1", 0.60, 0.80, 20, 10, "local-image")


@pytest.fixture
def repository(tmp_path):
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    return EventRepository(database)


def prediction(detections, confidence):
    return {
        "timestamp": "2026-11-25T12:00:00+00:00",
        "model_version": "0.1.1rc0",
        "detections": detections,
        "confidence": confidence,
        "preprocessing_time_ms": 4.0,
        "inference_time_ms": 30.0,
        "postprocessing_time_ms": 3.0,
    }


def test_event_round_trip_keeps_every_detection(config, repository):
    detections = [
        {"class_id": 72, "class_name": "refrigerator", "confidence": 0.70, "bbox": [1, 2, 30, 40]},
        {"class_id": 27, "class_name": "tie", "confidence": 0.25, "bbox": [5, 6, 10, 20]},
    ]
    event = EventBuilder(config).build(
        prediction(detections, 0.70), read_time_ms=7.0, image_reference="image.jpg"
    )
    UUID(event.event_id)
    assert datetime.fromisoformat(event.timestamp).utcoffset().total_seconds() == 0
    assert event.confidence_zone == "UNCERTAIN"
    assert event.detection_count == 2
    repository.save_event(event)
    recovered = repository.get_event(event.event_id)
    assert recovered == event
    assert [d.to_dict() for d in recovered.detections] == detections
    assert repository.list_events(limit=1) == [event]


def test_no_detection_is_null_and_distinct_from_low_confidence(config, repository):
    event = EventBuilder(config).build(prediction([], None))
    repository.save_event(event)
    recovered = repository.get_event(event.event_id)
    assert recovered.confidence is None
    assert recovered.confidence_zone == "NO_DETECTION"
    assert recovered.detections == ()
    assert recovered.detection_count == 0


def test_invalid_detection_rolls_back_event_and_previous_detection(config, repository):
    event = EventBuilder(config).build(
        prediction([{"class_id": 1, "class_name": "bicycle", "confidence": 0.8, "bbox": [1, 2, 3, 4]}], 0.8)
    )
    invalid = replace(event.detections[0], confidence=-0.1)
    broken = replace(event, detections=(event.detections[0], invalid))
    with pytest.raises(sqlite3.IntegrityError):
        repository.save_event(broken)
    assert repository.get_event(event.event_id) is None
    with repository.database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM detections").fetchone()[0] == 0


def test_model_error_has_explicit_state_and_no_score(config, repository):
    event = EventBuilder(config).model_error(RuntimeError("falló el modelo"), model_version="0.1.1rc0")
    repository.save_event(event)
    recovered = repository.get_event(event.event_id)
    assert recovered == event
    assert recovered.state == "MODEL_ERROR"
    assert recovered.confidence is None
    assert recovered.detection_count == 0


def test_foreign_keys_are_enabled(repository):
    with repository.database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO detections
                (event_id, class_id, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
                VALUES ('missing', 0, 'person', 0.5, 0, 0, 1, 1)"""
            )
