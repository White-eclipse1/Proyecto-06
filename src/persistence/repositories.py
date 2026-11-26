"""Consultas SQLite de eventos con escritura atómica de sus detecciones."""

import sqlite3
from contextlib import closing
from pathlib import Path

from src.events.models import Event
from src.inference.types import Detection

from .database import Database


class EventRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_event(self, event: Event) -> None:
        with closing(self.database.connect()) as connection, connection:
            connection.execute(
                """
                INSERT INTO events (
                    event_id, timestamp, source_id, model_version, config_version,
                    state, confidence, confidence_zone, detection_count, read_time_ms,
                    preprocessing_time_ms, inference_time_ms, postprocessing_time_ms,
                    image_reference, error_detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp,
                    event.source_id,
                    event.model_version,
                    event.config_version,
                    event.state,
                    event.confidence,
                    event.confidence_zone,
                    event.detection_count,
                    event.read_time_ms,
                    event.preprocessing_time_ms,
                    event.inference_time_ms,
                    event.postprocessing_time_ms,
                    event.image_reference,
                    event.error_detail,
                ),
            )
            connection.executemany(
                """
                INSERT INTO detections (
                    event_id, class_id, class_name, confidence,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        event.event_id,
                        detection.class_id,
                        detection.class_name,
                        detection.confidence,
                        *detection.bbox,
                    )
                    for detection in event.detections
                ),
            )

    def _get_with_connection(self, connection: sqlite3.Connection, event_id: str) -> Event | None:
        row = connection.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
        if row is None:
            return None
        detection_rows = connection.execute(
            "SELECT * FROM detections WHERE event_id = ? ORDER BY id", (event_id,)
        ).fetchall()
        if len(detection_rows) != row["detection_count"]:
            raise ValueError(f"conteo de detecciones inconsistente para {event_id}")
        detections = tuple(
            Detection(
                class_id=d["class_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=(d["bbox_x1"], d["bbox_y1"], d["bbox_x2"], d["bbox_y2"]),
            )
            for d in detection_rows
        )
        return Event(
            event_id=row["event_id"],
            timestamp=row["timestamp"],
            source_id=row["source_id"],
            model_version=row["model_version"],
            config_version=row["config_version"],
            state=row["state"],
            confidence=row["confidence"],
            confidence_zone=row["confidence_zone"],
            detections=detections,
            read_time_ms=row["read_time_ms"],
            preprocessing_time_ms=row["preprocessing_time_ms"],
            inference_time_ms=row["inference_time_ms"],
            postprocessing_time_ms=row["postprocessing_time_ms"],
            image_reference=row["image_reference"],
            error_detail=row["error_detail"],
        )

    def get_event(self, event_id: str) -> Event | None:
        with closing(self.database.connect()) as connection:
            return self._get_with_connection(connection, event_id)

    def set_image_reference(self, event_id: str, reference: str) -> Event:
        if not Path(reference).is_file():
            raise ValueError(f"image_reference no existe: {reference}")
        with closing(self.database.connect()) as connection, connection:
            current = connection.execute(
                "SELECT image_reference FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if current is None:
                raise ValueError(f"evento no encontrado: {event_id}")
            if current["image_reference"] not in (None, reference):
                raise ValueError("el evento ya tiene otra image_reference")
            connection.execute(
                "UPDATE events SET image_reference = ? WHERE event_id = ?", (reference, event_id)
            )
        updated = self.get_event(event_id)
        assert updated is not None
        return updated

    def list_events(self, limit: int = 20) -> list[Event]:
        if limit < 1:
            raise ValueError("limit debe ser mayor o igual a 1")
        with closing(self.database.connect()) as connection:
            ids = connection.execute(
                "SELECT event_id FROM events ORDER BY timestamp DESC, event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                event
                for row in ids
                if (event := self._get_with_connection(connection, row["event_id"])) is not None
            ]

    def list_events_page(self, limit: int = 20, offset: int = 0) -> tuple[list[Event], int]:
        if limit < 1 or offset < 0:
            raise ValueError("limit debe ser >= 1 y offset >= 0")
        with closing(self.database.connect()) as connection:
            count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            ids = connection.execute(
                "SELECT event_id FROM events ORDER BY timestamp DESC, event_id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            items = [
                event for row in ids
                if (event := self._get_with_connection(connection, row["event_id"])) is not None
            ]
        return items, count

    def list_by_identity(
        self, source_id: str, model_version: str, config_version: str,
        *, after: tuple[str, str] | None = None,
    ) -> list[Event]:
        """Recupera una serie ordenada sin mezclar fuentes ni versiones."""
        query = (
            "SELECT event_id FROM events WHERE source_id = ? AND model_version = ? "
            "AND config_version = ?"
        )
        params: list[str] = [source_id, model_version, config_version]
        if after is not None:
            query += " AND (timestamp > ? OR (timestamp = ? AND event_id > ?))"
            params.extend([after[0], after[0], after[1]])
        query += " ORDER BY timestamp, event_id"
        with closing(self.database.connect()) as connection:
            ids = connection.execute(query, params).fetchall()
            return [
                event for row in ids
                if (event := self._get_with_connection(connection, row["event_id"])) is not None
            ]

    def recent_scored_by_identity(
        self, source_id: str, model_version: str, config_version: str, limit: int,
    ) -> list[Event]:
        if limit < 1:
            raise ValueError("limit debe ser >= 1")
        with closing(self.database.connect()) as connection:
            ids = connection.execute(
                """SELECT event_id FROM events WHERE source_id = ? AND model_version = ?
                AND config_version = ? AND confidence IS NOT NULL
                ORDER BY timestamp DESC, event_id DESC LIMIT ?""",
                (source_id, model_version, config_version, limit),
            ).fetchall()
            return list(reversed([
                event for row in ids
                if (event := self._get_with_connection(connection, row["event_id"])) is not None
            ]))
