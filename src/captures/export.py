"""Exporta un evento y su captura conservando el vínculo verificable."""

import hashlib
import json
import shutil
from pathlib import Path

from src.events.models import Event

from .storage import CaptureStore


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_event_evidence(
    event: Event, store: CaptureStore, evidence_root: str | Path,
) -> tuple[Path, Path | None]:
    root = Path(evidence_root)
    events_dir = root / "eventos"
    images_dir = root / "imagenes"
    events_dir.mkdir(parents=True, exist_ok=True)
    exported_image = None
    payload = event.to_dict()
    if event.image_reference is not None:
        source = store.resolve(event.image_reference)
        images_dir.mkdir(parents=True, exist_ok=True)
        exported_image = images_dir / f"{event.event_id}.jpg"
        if exported_image.exists():
            if _sha256(exported_image) != _sha256(source):
                raise ValueError("la imagen exportada ya existe con otro contenido")
        else:
            try:
                with source.open("rb") as reader, exported_image.open("xb") as writer:
                    shutil.copyfileobj(reader, writer)
            except Exception:
                exported_image.unlink(missing_ok=True)
                raise
        payload["original_image_reference"] = event.image_reference
        payload["image_reference"] = f"../imagenes/{exported_image.name}"
        payload["image_sha256"] = _sha256(exported_image)
    event_path = events_dir / f"{event.event_id}.json"
    if event_path.exists():
        if json.loads(event_path.read_text(encoding="utf-8")) != payload:
            raise ValueError("la evidencia del evento ya existe con otro contenido")
    else:
        with event_path.open("x", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write("\n")
    return event_path, exported_image
