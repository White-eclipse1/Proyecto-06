"""Ejecuta y empaqueta C1/C2 con inferencia real y respuestas de la API local."""

import argparse
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from scripts.run_monitoring_sample import main as run_sample  # noqa: E402
from src.alerts import load_alert_config  # noqa: E402
from src.captures import CaptureStore, load_capture_config  # noqa: E402
from src.inference.model_loader import read_config as read_model_config  # noqa: E402
from src.monitoring import load_config  # noqa: E402
from src.persistence import AlertRepository, Database, EventRepository, MetricRepository  # noqa: E402
from src.portal import create_app  # noqa: E402

EVIDENCE = ROOT / "evidencias" / "escenarios"
CONFIG_FILES = ("model.yaml", "monitoring.yaml", "metrics.yaml", "capture.yaml", "alerts.yaml")
SCENARIOS = {
    "normal": {
        "directory": "normal", "input": "seq02-0001.jpg", "source_prefix": "scenario-c1",
        "provenance": "Proyecto5/data/p5-eval-v1/secuencias/seq02/seq02-0001.jpg",
        "purpose": "C1: operación aceptada por la política configurada",
        "selection": "Frame exterior de la secuencia de evaluación P5 con una persona visible; su score real supera el umbral superior.",
    },
    "low-confidence": {
        "directory": "baja-confianza", "input": "camara-nueva.jpg", "source_prefix": "scenario-c2",
        "provenance": "Proyecto4/evidencias/EDGE-01/camara-nueva.jpg",
        "purpose": "C2: baja confianza real y alerta vinculada",
        "selection": "Imagen de cámara P4 que produce una detección real por debajo del umbral inferior.",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_sha256(path: Path) -> str:
    """Identidad de YAML estable entre checkouts LF y CRLF de Git en Windows."""
    with path.open("r", encoding="utf-8", newline=None) as file:
        return hashlib.sha256(file.read().encode("utf-8")).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def identity() -> dict[str, object]:
    monitoring = load_config(ROOT / "config" / "monitoring.yaml")
    model = read_model_config(ROOT / "config" / "model.yaml")
    capture = load_capture_config(ROOT / "config" / "capture.yaml")
    alerts = load_alert_config(ROOT / "config" / "alerts.yaml")
    actual_hash = sha256(model.path)
    if actual_hash != model.sha256:
        raise ValueError("el SHA-256 del modelo no coincide con config/model.yaml")
    return {
        "model_name": model.name, "model_version": model.version, "model_sha256": actual_hash,
        "model_file": str(model.path.relative_to(ROOT)).replace("\\", "/"),
        "config_version": monitoring.version,
        "lower_threshold": monitoring.lower_threshold,
        "upper_threshold": monitoring.upper_threshold,
        "alerts_config_version": alerts.version,
        "capture_config_version": capture.version,
        "alert_rules": {
            "low_confidence": {
                "enabled": alerts.low_confidence.enabled,
                "minimum_events": alerts.low_confidence.minimum_events,
                "window_size": alerts.low_confidence.window_size,
                "severity": alerts.low_confidence.severity.value,
                "reason": alerts.low_confidence.reason,
                "suggested_action": alerts.low_confidence.suggested_action,
            },
            "sustained_confidence_change": {
                "enabled": alerts.sustained_confidence_change.enabled,
                "severity": alerts.sustained_confidence_change.severity.value,
                "reason": alerts.sustained_confidence_change.reason,
                "suggested_action": alerts.sustained_confidence_change.suggested_action,
            },
        },
        "capture_policy": {
            "directory": capture.directory.relative_to(ROOT).as_posix(),
            "low_confidence": capture.low_confidence,
            "normal_sample_every": capture.normal_sample_every,
            "scenario_evidence": capture.scenario_evidence,
        },
        "config_sha256": {name: config_sha256(ROOT / "config" / name) for name in CONFIG_FILES},
    }


def validate_same_identity(first: dict[str, object], second: dict[str, object]) -> None:
    for field in ("model_version", "model_sha256", "config_version", "lower_threshold",
                  "upper_threshold", "alerts_config_version", "capture_config_version", "config_sha256"):
        if first[field] != second[field]:
            raise ValueError(f"C1 y C2 usan distinta identidad de configuración: {field}")
    for field in ("model_name", "alert_rules", "capture_policy"):
        if field in first and field in second and first[field] != second[field]:
            raise ValueError(f"C1 y C2 usan distinta identidad de configuración: {field}")


def api_json(client: TestClient, url: str) -> dict[str, object]:
    response = client.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"API {url} devolvió HTTP {response.status_code}")
    return response.json()


def all_alert_pages(client: TestClient) -> list[dict[str, object]]:
    pages = []
    offset = 0
    while True:
        url = f"/api/alerts?limit=100&offset={offset}"
        body = api_json(client, url)
        pages.append({"url": url, "status_code": 200, "body": body})
        offset += len(body["items"])
        if offset >= body["count"]:
            return pages
        if not body["items"]:
            raise RuntimeError("paginación de alertas incompleta")


def make_readme(
    spec: dict[str, str], manifest: dict[str, object], result: dict[str, object],
    event: dict[str, object], report: dict[str, object],
) -> str:
    model = manifest["identity"]
    outcome = ("Ninguna alerta para este evento." if result["alert_id"] is None else
               f"Alerta `LOW_CONFIDENCE_ALERT` `{result['alert_id']}` vinculada al evento.")
    alert_file = ("`alert.json` conserva la alerta persistida. " if result["alert_id"] else "")
    portal_files = ("`portal_alert.json`" if result["alert_id"] else "`portal_alerts.json`")
    alert_url = (f"`http://127.0.0.1:8000/alerts/{result['alert_id']}`" if result["alert_id"]
                 else "la lista `http://127.0.0.1:8000/alerts`")
    interpretation = ("La zona `ACCEPTED_BY_POLICY` no afirma que la predicción sea correcta."
                      if manifest["scenario"] == "normal" else
                      "La zona `LOW_CONFIDENCE` expresa un score bajo; no confirma si las clases son correctas.")
    detections = "\n".join(
        f"- `{item['class_name']}` (class_id `{item['class_id']}`), confidence `{item['confidence']}`."
        for item in event["detections"]
    )
    metrics = "\n".join(
        f"| {item['metric_group']} · {item['metric_name']} | `{json.dumps(item['value'])}` | `{item['status']}` |"
        for item in report["metrics"]
    )
    git_note = ("El working tree tenía cambios sin commit; el estado exacto previo está en `manifest.json`."
                if not manifest["git"]["clean"] else "El working tree estaba limpio antes de la corrida.")
    return f"""# {spec['purpose']}

La imagen de entrada es `input/{spec['input']}`, copia exacta de
`{spec['provenance']}`. SHA-256: `{manifest['input_sha256']}`.

Selección: {spec['selection']} {interpretation}

Ejecutar desde la raíz:

```powershell
python scripts/run_scenario.py --scenario {manifest['scenario']}
```

Esta corrida usó el archivo interno del repositorio. La evidencia vigente es la corrida `{manifest['run_id']}`;
las reejecuciones anteriores se conservan en `runs/`.
{git_note}

| Campo | Valor |
| --- | --- |
| Git commit | `{manifest['git']['commit']}` |
| Git branch | `{manifest['git']['branch']}` |
| Git limpio antes de la corrida | `{manifest['git']['clean']}` |
| Modelo | `{model['model_name']}` `{model['model_version']}` |
| SHA-256 del modelo | `{model['model_sha256']}` |
| Configuración | `{model['config_version']}` |
| Threshold inferior | `{model['lower_threshold']}` |
| Threshold superior | `{model['upper_threshold']}` |
| Fuente | `{manifest['source_id']}` |
| Event ID | `{result['event_id']}` |
| Confidence | `{result['confidence']}` |
| Confidence zone | `{result['confidence_zone']}` |
| Detecciones | `{result['detection_count']}` |
| Alertas del evento | `{result['alert_count']}` |

{outcome}

Detecciones registradas:

{detections}

Métricas de esta corrida:

| Grupo y métrica | Valor | Estado |
| --- | --- | --- |
{metrics}

`metrics.json` contiene G1–G7 recalculadas desde las observaciones SQLite de esta corrida. Algunas
métricas, como G2 con un solo frame, pueden tener `INSUFFICIENT_DATA`; se conserva ese estado real.
`event.json` documenta la fila persistida. {alert_file}`portal_event.json` y
{portal_files} provienen de consultas reales a la API FastAPI.
Las copias exactas de las configuraciones usadas están en `config_snapshot/`.

Para verificarlo visualmente, ejecutar `python scripts/run_portal.py`, abrir
`http://127.0.0.1:8000/events/{result['event_id']}` y {alert_url}. La captura asociada está en
`capturas/` cuando la política decidió conservarla.

No se editaron scores, detecciones ni thresholds para obtener este resultado.
"""


def promote(bundle: Path, destination: Path) -> None:
    # Cada corrida permanece intacta en runs/<run_id>; el nivel superior señala la vigente.
    for path in bundle.iterdir():
        if path.is_file():
            shutil.copy2(path, destination / path.name)
        elif path.is_dir():
            shutil.copytree(path, destination / path.name, dirs_exist_ok=True)


def update_overview() -> None:
    manifests = {}
    for scenario, spec in SCENARIOS.items():
        path = EVIDENCE / spec["directory"] / "manifest.json"
        if path.is_file():
            manifests[scenario] = json.loads(path.read_text(encoding="utf-8"))
    if len(manifests) == 2:
        validate_same_identity(manifests["normal"]["identity"], manifests["low-confidence"]["identity"])
    write_json(EVIDENCE / "manifest.json", {
        "schema_version": "scenario-evidence-v1",
        "same_model_and_config": len(manifests) == 2,
        "identity": next(iter(manifests.values()))["identity"],
        "git_by_scenario": {name: value["git"] for name, value in manifests.items()},
        "scenarios": {name: {
            "manifest": f"{SCENARIOS[name]['directory']}/manifest.json",
            "run_id": value["run_id"], "event_id": value["event_id"],
            "source_id": value["source_id"],
        } for name, value in manifests.items()},
    })
    if len(manifests) == 2:
        c1, c2 = manifests["normal"], manifests["low-confidence"]
        portal = ROOT / "evidencias" / "portal" / "CAPTURAS-PENDIENTES.md"
        portal.write_text(
            "# Capturas visuales pendientes\n\n"
            "Iniciar `python scripts/run_portal.py` y capturar manualmente:\n\n"
            "1. Lista `http://127.0.0.1:8000/events`.\n"
            f"2. Detalle C1 `http://127.0.0.1:8000/events/{c1['event_id']}`.\n"
            f"3. Detalle C2 `http://127.0.0.1:8000/events/{c2['event_id']}`.\n"
            "4. Lista `http://127.0.0.1:8000/alerts`.\n"
            f"5. Detalle de alerta C2 `http://127.0.0.1:8000/alerts/{c2['alert_id']}` con el enlace al evento.\n"
            f"6. Evento C2 `http://127.0.0.1:8000/events/{c2['event_id']}` mostrando la imagen.\n\n"
            "IDs de la corrida definitiva actual; si se reejecuta un escenario, este documento se actualiza.\n",
            encoding="utf-8",
        )


def run(scenario: str) -> dict[str, object]:
    spec = SCENARIOS[scenario]
    destination = EVIDENCE / spec["directory"]
    input_path = destination / "input" / spec["input"]
    if not input_path.is_file():
        raise FileNotFoundError(f"falta el input interno: {input_path}")
    previous_manifest = destination / "manifest.json"
    if previous_manifest.is_file():
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        if sha256(input_path) != previous["input_sha256"]:
            raise ValueError("el input interno cambió respecto a la corrida anterior")
    current_identity = identity()
    other = "low-confidence" if scenario == "normal" else "normal"
    other_manifest = EVIDENCE / SCENARIOS[other]["directory"] / "manifest.json"
    if other_manifest.is_file():
        validate_same_identity(json.loads(other_manifest.read_text(encoding="utf-8"))["identity"], current_identity)
    git = {
        "commit": git_output("rev-parse", "HEAD"),
        "branch": git_output("branch", "--show-current"),
        "status_porcelain_before": git_output("status", "--short").splitlines(),
    }
    git["clean"] = not git["status_porcelain_before"]
    source_id = f"{spec['source_prefix']}-{uuid4()}"
    before_hashes = current_identity["config_sha256"]
    captured_output = io.StringIO()
    with contextlib.redirect_stdout(captured_output):
        exit_code = run_sample(["--input", str(input_path), "--source-id", source_id])
    if exit_code != 0:
        raise RuntimeError("falló el pipeline de monitoreo real")
    report = json.loads(captured_output.getvalue())
    if {name: config_sha256(ROOT / "config" / name) for name in CONFIG_FILES} != before_hashes:
        raise RuntimeError("la configuración cambió durante la ejecución")
    database = Database(ROOT / "data" / "monitoring.db")
    observed = MetricRepository(database).events_for_run(report["run_id"])
    if len(observed) != 1:
        raise RuntimeError("la corrida debe contener exactamente un evento")
    event = EventRepository(database).get_event(observed[0].event_id)
    assert event is not None
    matching = [alert for alert in AlertRepository(database).list_alerts(limit=None)
                if alert.event_id == event.event_id]
    if event.source_id != source_id or event.model_version != current_identity["model_version"] or event.config_version != current_identity["config_version"]:
        raise RuntimeError("identidad del evento distinta a la registrada")
    expected = "ACCEPTED_BY_POLICY" if scenario == "normal" else "LOW_CONFIDENCE"
    if event.confidence is None or event.confidence_zone != expected:
        raise RuntimeError(f"resultado inesperado de inferencia real: {event.confidence_zone}")
    if scenario == "normal" and (event.confidence < current_identity["upper_threshold"] or matching):
        raise RuntimeError("C1 no satisface la política normal sin alerta")
    if scenario == "low-confidence" and (event.confidence >= current_identity["lower_threshold"] or
                                           len(matching) != 1 or matching[0].rule_id != "LOW_CONFIDENCE_ALERT"):
        raise RuntimeError("C2 no produjo la alerta de baja confianza esperada")
    capture_store = CaptureStore(load_capture_config(ROOT / "config" / "capture.yaml").directory)
    image = capture_store.resolve(event.image_reference) if event.image_reference else None
    if scenario == "low-confidence" and image is None:
        raise RuntimeError("C2 no conservó una captura resoluble")
    client = TestClient(create_app(database.path, capture_store.directory))
    portal_event = api_json(client, f"/api/events/{event.event_id}")
    if portal_event["event_id"] != event.event_id or portal_event["confidence"] != event.confidence:
        raise RuntimeError("la API no recuperó el evento real")
    portal_alert = None
    alert_pages = None
    if matching:
        portal_alert = api_json(client, f"/api/alerts/{matching[0].alert_id}")
        if portal_alert["event_id"] != event.event_id or portal_alert["image_url"] != portal_event["image_reference"]:
            raise RuntimeError("la cadena alerta → evento → imagen no coincide")
    else:
        alert_pages = all_alert_pages(client)
        if any(item["event_id"] == event.event_id for page in alert_pages for item in page["body"]["items"]):
            raise RuntimeError("la API muestra una alerta para C1")
    if image and (portal_event["image_reference"] != f"/captures/{event.event_id}.jpg" or
                  client.get(portal_event["image_reference"]).status_code != 200):
        raise RuntimeError("la API no puede servir la captura vinculada")
    run_id = report["run_id"]
    bundle = destination / "runs" / run_id
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle / "input").mkdir()
    shutil.copy2(input_path, bundle / "input" / input_path.name)
    (bundle / "config_snapshot").mkdir()
    for name in CONFIG_FILES:
        shutil.copy2(ROOT / "config" / name, bundle / "config_snapshot" / name)
    if image:
        (bundle / "capturas").mkdir()
        shutil.copy2(image, bundle / "capturas" / image.name)
    input_hash = sha256(input_path)
    manifest = {
        "schema_version": "scenario-evidence-v1", "scenario": scenario,
        "run_id": run_id, "event_id": event.event_id,
        "alert_id": matching[0].alert_id if matching else None,
        "source_id": source_id, "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": f"input/{input_path.name}", "input_sha256": input_hash,
        "source_provenance": spec["provenance"], "identity": current_identity,
        "git": git,
        "capture": f"capturas/{image.name}" if image else None,
        "capture_sha256": sha256(image) if image else None,
    }
    event_json = event.to_dict()
    event_json["image_reference"] = manifest["capture"]
    result = {
        "status": "ok", "scenario": scenario, "run_id": run_id,
        "event_id": event.event_id, "alert_id": manifest["alert_id"],
        "confidence": event.confidence, "confidence_zone": event.confidence_zone,
        "detection_count": event.detection_count, "alert_count": len(matching),
        "capture": manifest["capture"],
        "metric_statuses": {metric["metric_group"]: metric["status"] for metric in report["metrics"]},
    }
    write_json(bundle / "manifest.json", manifest)
    write_json(bundle / "result.json", result)
    write_json(bundle / "event.json", event_json)
    write_json(bundle / "metrics.json", report)
    write_json(bundle / "portal_event.json", portal_event)
    if matching:
        write_json(bundle / "alert.json", matching[0].to_dict())
        write_json(bundle / "portal_alert.json", portal_alert)
    else:
        write_json(bundle / "portal_alerts.json", {
            "event_id_checked": event.event_id, "requests": alert_pages,
            "matching_alert_ids": [],
        })
    (bundle / "README.md").write_text(make_readme(spec, manifest, result, event_json, report), encoding="utf-8")
    promote(bundle, destination)
    update_overview()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera evidencia C1/C2 desde inputs internos reales.")
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.scenario), ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        print(f"Error del escenario: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
