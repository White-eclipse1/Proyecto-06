import json
import os
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

from src.alerts import AlertEngine, AlertStatus, RuleStatus, Severity, load_alert_config
from src.alerts.pipeline import AlertPipeline
from src.captures import CaptureConfig, CapturePolicy, CaptureStore
from src.captures.export import export_event_evidence
from src.events.models import Event
from src.inference.types import Detection
from src.metrics.reporting import recalculate
from src.monitoring.reference import ChangeState, WindowAssessment
from src.persistence import AlertRepository, Database, EventRepository


def make_event(confidence: float | None, zone: str) -> Event:
    detections = () if confidence is None else (
        Detection(0, "person", confidence, (1.0, 2.0, 30.0, 40.0)),
    )
    return Event(
        event_id=str(uuid4()), timestamp=datetime.now(timezone.utc).isoformat(),
        source_id="test-camera", model_version="0.1.1rc0", config_version="monitoring-v1",
        state=zone, confidence=confidence, confidence_zone=zone, detections=detections,
        read_time_ms=1.0, preprocessing_time_ms=2.0,
        inference_time_ms=10.0, postprocessing_time_ms=3.0,
    )


def capture_policy(tmp_path, every=20):
    return CapturePolicy(CaptureConfig("capture-test", tmp_path / "captures", True, every, True))


def frame(value=128):
    return np.full((80, 100, 3), value, dtype=np.uint8)


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "monitoring.db")
    db.initialize()
    return db


def test_capture_policy_low_alert_normal_sample_and_scenario(tmp_path):
    policy = capture_policy(tmp_path, every=3)
    low = make_event(0.4, "LOW_CONFIDENCE")
    accepted = make_event(0.9, "ACCEPTED_BY_POLICY")
    assert policy.decide(low).reasons == ("LOW_CONFIDENCE",)
    assert policy.decide(low, alert=True).reasons == ("LOW_CONFIDENCE", "ALERT")
    assert not policy.decide(accepted, normal_index=2).capture
    assert policy.decide(accepted, normal_index=3).reasons == ("NORMAL_SAMPLE",)
    assert policy.decide(accepted, scenario_evidence=True).reasons == ("SCENARIO_EVIDENCE",)


def test_capture_has_unique_name_resolves_and_does_not_expire(tmp_path):
    store = CaptureStore(tmp_path / "captures")
    event_id = str(uuid4())
    reference = store.save(event_id, frame(90))
    first_bytes = Path(reference).read_bytes()
    assert Path(reference).name == f"{event_id}.jpg"
    assert store.resolve(reference).is_file()
    os.utime(reference, (1, 1))
    assert store.save(event_id, frame(220)) == reference
    assert Path(reference).read_bytes() == first_bytes
    assert Path(reference).exists()


@pytest.mark.parametrize("score,zone", [
    (0.7, "UNCERTAIN"), (0.9, "ACCEPTED_BY_POLICY"),
    (None, "NO_DETECTION"), (None, "MODEL_ERROR"),
])
def test_low_rule_ignores_non_low_or_unscored_events(score, zone):
    event = make_event(score, zone)
    outcome = AlertEngine(load_alert_config()).evaluate_event(event, [event])
    assert outcome.status == RuleStatus.NOT_TRIGGERED
    assert outcome.alert is None


def test_low_confidence_creates_configured_alert():
    event = make_event(0.4, "LOW_CONFIDENCE")
    outcome = AlertEngine(load_alert_config()).evaluate_event(event, [event])
    assert outcome.status == RuleStatus.TRIGGERED
    assert outcome.alert.rule_id == "LOW_CONFIDENCE_ALERT"
    assert outcome.alert.severity == Severity.WARNING
    assert outcome.alert.status == AlertStatus.ACTIVE
    assert outcome.alert.event_id == event.event_id
    assert datetime.fromisoformat(outcome.alert.timestamp).utcoffset().total_seconds() == 0


def test_disabled_and_insufficient_low_confidence_rule():
    event = make_event(0.4, "LOW_CONFIDENCE")
    config = load_alert_config()
    disabled = replace(config, low_confidence=replace(config.low_confidence, enabled=False))
    assert AlertEngine(disabled).evaluate_event(event, [event]).status == RuleStatus.DISABLED
    needs_two = replace(config, low_confidence=replace(
        config.low_confidence, minimum_events=2, window_size=2,
    ))
    result = AlertEngine(needs_two).evaluate_event(event, [event])
    assert result.status == RuleStatus.INSUFFICIENT_DATA
    assert result.alert is None


def test_optional_sustained_change_rule_is_disabled_by_default():
    assessment = WindowAssessment(
        "window-1", ChangeState.SUSTAINED_CONFIDENCE_CHANGE, "reference-1",
        20, 0.4, 0.25, 2, (),
    )
    config = load_alert_config()
    assert AlertEngine(config).evaluate_window(
        assessment, source_id="test-camera",
    ).status == RuleStatus.DISABLED
    enabled = replace(config, sustained_confidence_change=replace(
        config.sustained_confidence_change, enabled=True,
    ))
    outcome = AlertEngine(enabled).evaluate_window(assessment, source_id="test-camera")
    assert outcome.status == RuleStatus.TRIGGERED
    assert outcome.alert.event_id is None
    assert outcome.alert.window_id == "window-1"


def test_pipeline_persists_alert_image_and_is_idempotent(database, tmp_path):
    event = make_event(0.4, "LOW_CONFIDENCE")
    events = EventRepository(database)
    events.save_event(event)
    alerts = AlertRepository(database)
    store = CaptureStore(tmp_path / "captures")
    pipeline = AlertPipeline(events, alerts, capture_policy(tmp_path), store,
                             AlertEngine(load_alert_config()))
    first = pipeline.process(event.event_id, frame())
    second = pipeline.process(event.event_id, frame(200))
    assert first.alert_created is True
    assert second.alert_created is False
    assert first.alert == second.alert
    assert first.event.image_reference == second.event.image_reference
    assert store.resolve(first.event.image_reference).is_file()
    assert alerts.get_alert(first.alert.alert_id) == first.alert
    assert events.get_event(event.event_id).image_reference == first.event.image_reference
    assert len(alerts.list_active_alerts(source_id="test-camera")) == 1
    assert len(alerts.list_alerts(limit=None)) == 1


def test_alert_foreign_key_rejects_missing_event(database):
    event = make_event(0.4, "LOW_CONFIDENCE")
    alert = AlertEngine(load_alert_config()).evaluate_event(event, [event]).alert
    with pytest.raises(ValueError, match="evento no encontrado"):
        AlertRepository(database).save_alert(alert)
    with database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO alerts
                (alert_id, timestamp, rule_id, severity, reason, suggested_action,
                 status, source_id, config_version, event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid4()), alert.timestamp, alert.rule_id, "WARNING", alert.reason,
                 alert.suggested_action, "ACTIVE", alert.source_id,
                 alert.config_version, event.event_id),
            )


def test_low_alert_requires_real_capture(database):
    event = make_event(0.4, "LOW_CONFIDENCE")
    EventRepository(database).save_event(event)
    alert = AlertEngine(load_alert_config()).evaluate_event(event, [event]).alert
    with pytest.raises(ValueError, match="requiere una imagen existente"):
        AlertRepository(database).save_alert(alert)
    assert AlertRepository(database).list_alerts(limit=None) == []


def test_alert_insert_failure_rolls_back_event_image_update(database, tmp_path):
    first = make_event(0.4, "LOW_CONFIDENCE")
    second = make_event(0.4, "LOW_CONFIDENCE")
    events = EventRepository(database)
    events.save_event(first)
    events.save_event(second)
    alert_engine = AlertEngine(load_alert_config())
    repository = AlertRepository(database)
    existing = alert_engine.evaluate_event(first, [first]).alert
    first_reference = CaptureStore(tmp_path / "captures").save(first.event_id, frame())
    repository.save_alert(existing, image_reference=first_reference)
    duplicate_id = replace(alert_engine.evaluate_event(second, [second]).alert,
                           alert_id=existing.alert_id)
    reference = CaptureStore(tmp_path / "captures").save(second.event_id, frame())
    with pytest.raises(sqlite3.IntegrityError):
        repository.save_alert(duplicate_id, image_reference=reference)
    assert events.get_event(second.event_id).image_reference is None
    assert len(repository.list_alerts(limit=None)) == 1


def test_g7_counts_active_and_zero_is_ok(database):
    empty, _ = recalculate(database, source_id="test-camera")
    g7 = empty["metrics"][-1]
    assert (g7["metric_group"], g7["value"], g7["status"]) == ("G7", 0, "OK")
    event = make_event(0.4, "LOW_CONFIDENCE")
    EventRepository(database).save_event(event)
    alert = AlertEngine(load_alert_config()).evaluate_event(event, [event]).alert
    capture = CaptureStore(database.path.parent / "captures").save(event.event_id, frame())
    AlertRepository(database).save_alert(alert, image_reference=capture)
    current, _ = recalculate(database, source_id="test-camera")
    assert current["metrics"][-1]["value"] == 1
    other, _ = recalculate(database, source_id="another-camera")
    assert other["metrics"][-1]["value"] == 0


def test_export_alert_event_and_image(database, tmp_path):
    event = make_event(0.4, "LOW_CONFIDENCE")
    events = EventRepository(database)
    events.save_event(event)
    alerts = AlertRepository(database)
    store = CaptureStore(tmp_path / "captures")
    processed = AlertPipeline(events, alerts, capture_policy(tmp_path), store,
                              AlertEngine(load_alert_config())).process(event.event_id, frame())
    alert_file = alerts.export_alerts(tmp_path / "evidencias" / "alertas" / "alertas.json")
    event_file, image_file = export_event_evidence(
        processed.event, store, tmp_path / "evidencias",
    )
    exported_alerts = json.loads(alert_file.read_text(encoding="utf-8"))
    exported_event = json.loads(event_file.read_text(encoding="utf-8"))
    assert exported_alerts[0]["event_id"] == event.event_id
    assert (event_file.parent / exported_event["image_reference"]).resolve() == image_file.resolve()
    assert image_file.is_file()
    assert exported_event["event_id"] == event.event_id
