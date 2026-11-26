"""API y vistas del portal contra SQLite temporal con registros persistidos."""

import sqlite3
from dataclasses import replace
from uuid import uuid4

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.alerts.models import Alert, AlertStatus, Severity
from src.captures.storage import CaptureStore
from src.events.models import Event
from src.inference.types import Detection
from src.persistence import AlertRepository, Database, EventRepository
from src.portal import create_app
from src.portal.app import ReadOnlyDatabase


def event(timestamp: str, source: str = "camara-01") -> Event:
    return Event(
        event_id=str(uuid4()), timestamp=timestamp, source_id=source,
        model_version="0.1.1rc0", config_version="monitoring-v1",
        state="LOW_CONFIDENCE", confidence=0.3968,
        confidence_zone="LOW_CONFIDENCE",
        detections=(Detection(72, "refrigerator", 0.3968, (1.0, 2.0, 30.0, 40.0)),),
        read_time_ms=2.0, preprocessing_time_ms=3.0,
        inference_time_ms=18.0, postprocessing_time_ms=2.5,
    )


def populated_portal(tmp_path):
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    events = EventRepository(database)
    alerts = AlertRepository(database)
    captures = CaptureStore(tmp_path / "captures")
    low = event("2026-11-25T12:00:00+00:00", "<script>camara</script>")
    normal = replace(
        event("2026-11-25T12:01:00+00:00"), event_id=str(uuid4()),
        state="ACCEPTED_BY_POLICY", confidence=0.91, confidence_zone="ACCEPTED_BY_POLICY",
    )
    events.save_event(low)
    events.save_event(normal)
    image = captures.save(low.event_id, np.full((12, 16, 3), 100, dtype=np.uint8))
    alert = Alert(
        alert_id=str(uuid4()), timestamp="2026-11-25T12:00:01+00:00",
        rule_id="LOW_CONFIDENCE_ALERT", severity=Severity.WARNING,
        reason="Low confidence", suggested_action="Review image",
        status=AlertStatus.ACTIVE, source_id=low.source_id,
        config_version="alerts-v1", event_id=low.event_id,
    )
    alerts.save_alert(alert, image_reference=image)
    return TestClient(create_app(database.path, captures.directory)), low, normal, alert, image


def test_api_events_returns_sqlite_data_pagination_and_detections(tmp_path):
    client, low, normal, _, image = populated_portal(tmp_path)
    page = client.get("/api/events", params={"limit": 1, "offset": 0})
    assert page.status_code == 200
    assert page.json()["count"] == 2
    assert page.json()["items"][0]["event_id"] == normal.event_id
    second = client.get("/api/events", params={"limit": 1, "offset": 1}).json()
    assert second["items"][0]["event_id"] == low.event_id
    detail = client.get(f"/api/events/{low.event_id}").json()
    assert detail["detection_count"] == 1
    assert detail["detections"][0]["class_name"] == "refrigerator"
    assert detail["detections"][0]["bbox"] == [1.0, 2.0, 30.0, 40.0]
    assert detail["image_reference"] == f"/captures/{low.event_id}.jpg"
    assert image not in client.get(f"/api/events/{low.event_id}").text
    assert client.get(f"/api/events/{normal.event_id}").json()["image_reference"] is None


def test_api_alerts_link_to_real_event_and_image(tmp_path):
    client, low, _, alert, image = populated_portal(tmp_path)
    listing = client.get("/api/alerts", params={"limit": 1, "offset": 0})
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["items"][0]["alert_id"] == alert.alert_id
    assert client.get("/api/alerts", params={"limit": 1, "offset": 1}).json()["items"] == []
    detail_response = client.get(f"/api/alerts/{alert.alert_id}")
    detail = detail_response.json()
    assert detail["event_id"] == low.event_id
    assert detail["event_url"] == f"/events/{low.event_id}"
    assert detail["image_url"] == f"/captures/{low.event_id}.jpg"
    assert detail["suggested_action"] == "Review image"
    assert image not in detail_response.text


def test_pages_show_persisted_data_and_navigable_chain(tmp_path):
    client, low, _, alert, _ = populated_portal(tmp_path)
    events_page = client.get("/events")
    alerts_page = client.get("/alerts")
    assert events_page.status_code == alerts_page.status_code == 200
    assert client.get("/static/style.css").status_code == 200
    assert low.event_id[:8] in events_page.text
    assert "LOW_CONFIDENCE_ALERT" in alerts_page.text
    assert "&lt;script&gt;camara&lt;/script&gt;" in events_page.text
    assert "<script>camara</script>" not in events_page.text
    alert_detail = client.get(f"/alerts/{alert.alert_id}")
    assert f'href="/events/{low.event_id}"' in alert_detail.text
    assert f'src="/captures/{low.event_id}.jpg"' in alert_detail.text
    event_detail = client.get(f"/events/{low.event_id}")
    assert "refrigerator" in event_detail.text
    assert "1.00, 2.00, 30.00, 40.00" in event_detail.text
    capture = client.get(f"/captures/{low.event_id}.jpg")
    assert capture.status_code == 200
    assert capture.headers["content-type"] == "image/jpeg"
    assert capture.content.startswith(b"\xff\xd8")


def test_empty_state_and_not_found(tmp_path):
    database = Database(tmp_path / "empty.db")
    database.initialize()
    client = TestClient(create_app(database.path, tmp_path / "captures"))
    assert client.get("/api/events").json() == {"items": [], "count": 0, "limit": 20, "offset": 0}
    assert client.get("/api/alerts").json()["count"] == 0
    assert "Sin eventos" in client.get("/events").text
    assert "Sin alertas" in client.get("/alerts").text
    assert client.get("/api/events/missing").status_code == 404
    assert client.get("/api/alerts/missing").status_code == 404
    assert client.get("/events/missing").status_code == 404
    assert client.get("/alerts/missing").status_code == 404


def test_capture_route_rejects_unlinked_and_outside_files(tmp_path):
    client, low, normal, _, _ = populated_portal(tmp_path)
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"private")
    database = Database(tmp_path / "monitoring.db")
    EventRepository(database).set_image_reference(normal.event_id, str(outside))
    assert client.get(f"/api/events/{normal.event_id}").json()["image_reference"] is None
    assert client.get(f"/captures/{normal.event_id}.jpg").status_code == 404
    assert client.get("/captures/../outside.jpg").status_code == 404
    assert client.get("/captures/not-a-uuid.jpg").status_code == 404
    assert client.get(f"/captures/{low.event_id}.jpg").status_code == 200
    assert client.get("/.env").status_code == 404
    assert client.get("/data/monitoring.db").status_code == 404
    assert client.post("/api/alerts").status_code == 405
    assert client.get("/api/events?limit=0").status_code == 422
    assert client.get("/api/alerts?offset=-1").status_code == 422


def test_portal_database_is_read_only(tmp_path):
    database = Database(tmp_path / "empty.db")
    database.initialize()
    with ReadOnlyDatabase(database.path).connect() as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM events")
