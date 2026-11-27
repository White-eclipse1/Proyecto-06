"""Comprueba que los paquetes definitivos C1/C2 son trazables y reproducibles."""

import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID

import pytest

from scripts.run_scenario import CONFIG_FILES, config_sha256, sha256, validate_same_identity

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidencias" / "escenarios"
DIRS = {"normal": BASE / "normal", "low-confidence": BASE / "baja-confianza"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", ["normal", "low-confidence"])
def test_scenario_package_contains_real_input_config_and_api_ids(scenario):
    directory = DIRS[scenario]
    manifest = read_json(directory / "manifest.json")
    result = read_json(directory / "result.json")
    event = read_json(directory / "event.json")
    portal_event = read_json(directory / "portal_event.json")
    metrics = read_json(directory / "metrics.json")
    UUID(manifest["run_id"])
    UUID(manifest["event_id"])
    assert manifest["scenario"] == result["scenario"] == scenario
    assert manifest["event_id"] == result["event_id"] == event["event_id"] == portal_event["event_id"]
    assert manifest["source_id"] == event["source_id"] == portal_event["source_id"] == metrics["source_id"]
    assert manifest["run_id"] == metrics["run_id"]
    assert len(manifest["git"]["commit"]) == 40
    assert manifest["git"]["branch"]
    assert isinstance(manifest["git"]["status_porcelain_before"], list)
    assert len(event["detections"]) == result["detection_count"]
    assert portal_event["confidence"] == event["confidence"] == result["confidence"]
    assert (directory / "README.md").is_file()
    input_file = directory / manifest["input"]
    assert input_file.is_file() and sha256(input_file) == manifest["input_sha256"]
    archive = directory / "runs" / manifest["run_id"]
    assert read_json(archive / "manifest.json") == manifest
    assert sha256(archive / manifest["input"]) == manifest["input_sha256"]
    for name in CONFIG_FILES:
        expected = manifest["identity"]["config_sha256"][name]
        assert config_sha256(directory / "config_snapshot" / name) == expected
        assert config_sha256(archive / "config_snapshot" / name) == expected
    assert {metric["metric_group"] for metric in metrics["metrics"]} == {
        "G1", "G2", "G3", "G4", "G5", "G6", "G7",
    }


def test_c1_and_c2_use_identical_thresholds_and_model():
    c1 = read_json(DIRS["normal"] / "manifest.json")
    c2 = read_json(DIRS["low-confidence"] / "manifest.json")
    overview = read_json(BASE / "manifest.json")
    validate_same_identity(c1["identity"], c2["identity"])
    assert overview["same_model_and_config"] is True
    assert overview["git_by_scenario"]["normal"]["commit"] == c1["git"]["commit"]
    assert overview["git_by_scenario"]["low-confidence"]["commit"] == c2["git"]["commit"]
    assert overview["identity"]["alert_rules"]["low_confidence"]["enabled"] is True
    assert overview["identity"]["capture_policy"]["normal_sample_every"] == 20
    assert c1["identity"]["lower_threshold"] == c2["identity"]["lower_threshold"] == 0.60
    assert c1["identity"]["upper_threshold"] == c2["identity"]["upper_threshold"] == 0.80
    assert c1["identity"]["model_sha256"] == sha256(ROOT / "modelo" / "yolox_tiny.onnx")
    changed = deepcopy(c2["identity"])
    changed["lower_threshold"] = 0.59
    with pytest.raises(ValueError, match="lower_threshold"):
        validate_same_identity(c1["identity"], changed)


def test_c1_has_no_event_alert_and_preserves_insufficient_data():
    directory = DIRS["normal"]
    result = read_json(directory / "result.json")
    report = read_json(directory / "metrics.json")
    api_alerts = read_json(directory / "portal_alerts.json")
    assert result["confidence"] >= 0.80
    assert result["confidence_zone"] == "ACCEPTED_BY_POLICY"
    assert result["alert_id"] is None and result["alert_count"] == 0
    assert api_alerts["event_id_checked"] == result["event_id"]
    assert api_alerts["matching_alert_ids"] == []
    assert all(item["event_id"] != result["event_id"]
               for request in api_alerts["requests"] for item in request["body"]["items"])
    assert all(request["status_code"] == 200 for request in api_alerts["requests"])
    by_group = {metric["metric_group"]: metric for metric in report["metrics"]}
    assert by_group["G2"]["status"] == "INSUFFICIENT_DATA" and by_group["G2"]["value"] is None
    assert by_group["G7"]["value"] == 0


def test_c2_alert_event_image_and_portal_json_match():
    directory = DIRS["low-confidence"]
    manifest = read_json(directory / "manifest.json")
    result = read_json(directory / "result.json")
    event = read_json(directory / "event.json")
    alert = read_json(directory / "alert.json")
    portal_event = read_json(directory / "portal_event.json")
    portal_alert = read_json(directory / "portal_alert.json")
    report = read_json(directory / "metrics.json")
    UUID(manifest["alert_id"])
    assert result["confidence"] < 0.60 and result["confidence_zone"] == "LOW_CONFIDENCE"
    assert result["alert_id"] == alert["alert_id"] == portal_alert["alert_id"]
    assert alert["rule_id"] == "LOW_CONFIDENCE_ALERT"
    assert alert["event_id"] == portal_alert["event_id"] == event["event_id"]
    assert portal_alert["event_url"] == f"/events/{event['event_id']}"
    assert portal_alert["image_url"] == portal_event["image_reference"] == f"/captures/{event['event_id']}.jpg"
    assert event["image_reference"] == manifest["capture"]
    capture = directory / manifest["capture"]
    assert capture.is_file() and sha256(capture) == manifest["capture_sha256"]
    assert sha256(directory / "runs" / manifest["run_id"] / manifest["capture"]) == manifest["capture_sha256"]
    by_group = {metric["metric_group"]: metric for metric in report["metrics"]}
    assert by_group["G7"]["value"] == 1
