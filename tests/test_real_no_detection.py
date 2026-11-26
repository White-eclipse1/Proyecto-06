"""Verifica NO_DETECTION con el modelo real sobre una imagen lisa."""

import numpy as np
import pytest

from src.events import EventBuilder
from src.inference import InferenceEngine
from src.monitoring import load_config
from src.persistence import Database, EventRepository


def test_blank_frame_with_real_model_has_no_detection(tmp_path):
    from pathlib import Path

    if not Path("modelo/yolox_tiny.onnx").is_file():
        pytest.skip("descargar primero los pesos con scripts/get_model.py")
    result = InferenceEngine.from_config().predict(np.full((480, 640, 3), 128, dtype=np.uint8))
    assert result["detections"] == []
    assert result["confidence"] is None
    event = EventBuilder(load_config()).build(result)
    database = Database(tmp_path / "monitoring.db")
    database.initialize()
    repository = EventRepository(database)
    repository.save_event(event)
    assert repository.get_event(event.event_id).confidence_zone == "NO_DETECTION"
