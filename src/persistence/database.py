"""Esquema SQLite mínimo de esta fase."""

import sqlite3
from contextlib import closing
from pathlib import Path


class Database:
    def __init__(self, path: str | Path = "data/monitoring.db") -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    config_version TEXT NOT NULL,
                    state TEXT NOT NULL,
                    confidence REAL,
                    confidence_zone TEXT NOT NULL,
                    detection_count INTEGER NOT NULL CHECK (detection_count >= 0),
                    read_time_ms REAL,
                    preprocessing_time_ms REAL,
                    inference_time_ms REAL,
                    postprocessing_time_ms REAL,
                    image_reference TEXT,
                    error_detail TEXT,
                    CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
                    class_id INTEGER NOT NULL,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
                    bbox_x1 REAL NOT NULL,
                    bbox_y1 REAL NOT NULL,
                    bbox_x2 REAL NOT NULL,
                    bbox_y2 REAL NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_detections_event_id ON detections(event_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)"
            )
