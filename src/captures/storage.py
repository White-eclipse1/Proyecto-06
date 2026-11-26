"""Guarda capturas con nombre UUID único y comprueba referencias resolubles."""

from pathlib import Path
from uuid import UUID

import cv2
import numpy as np


class CaptureStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory).resolve()

    def save(self, event_id: str, frame: np.ndarray) -> str:
        UUID(event_id)
        if not isinstance(frame, np.ndarray) or frame.dtype != np.uint8 or frame.ndim != 3:
            raise ValueError("la captura debe ser una imagen BGR uint8")
        if frame.shape[2] != 3 or min(frame.shape[:2]) < 1:
            raise ValueError("la captura debe tener tres canales y tamaño positivo")
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{event_id}.jpg"
        if path.exists():
            self.resolve(str(path))
            return str(path)
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise ValueError("no se pudo codificar la captura JPEG")
        try:
            with path.open("xb") as file:
                file.write(encoded.tobytes())
        except FileExistsError:
            self.resolve(str(path))
            return str(path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        self.resolve(str(path))
        return str(path)

    def resolve(self, reference: str) -> Path:
        path = Path(reference).resolve()
        if not path.is_relative_to(self.directory) or not path.is_file():
            raise ValueError(f"referencia de captura no resoluble: {reference}")
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"captura no decodificable: {reference}")
        return path
