"""Persistencia de referencias y de los eventos que forman cada muestra."""

from contextlib import closing

from src.monitoring.reference import ConfidenceReference

from .database import Database


class ReferenceRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save(self, reference: ConfidenceReference) -> None:
        with closing(self.database.connect()) as connection, connection:
            connection.execute(
                """INSERT INTO confidence_references
                (reference_id, created_at, model_version, config_version, source_id,
                 sample_count, window_size, mean_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (reference.reference_id, reference.created_at, reference.model_version,
                 reference.config_version, reference.source_id, reference.sample_count,
                 reference.window_size, reference.mean_confidence),
            )
            connection.executemany(
                "INSERT INTO reference_events (reference_id, event_id, position) VALUES (?, ?, ?)",
                [(reference.reference_id, event_id, index)
                 for index, event_id in enumerate(reference.event_ids)],
            )

    def latest(self, source_id: str, model_version: str,
               config_version: str) -> ConfidenceReference | None:
        with closing(self.database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM confidence_references WHERE source_id = ?
                AND model_version = ? AND config_version = ?
                ORDER BY created_at DESC, reference_id DESC LIMIT 1""",
                (source_id, model_version, config_version),
            ).fetchone()
            if row is None:
                return None
            event_ids = tuple(r["event_id"] for r in connection.execute(
                "SELECT event_id FROM reference_events WHERE reference_id = ? ORDER BY position",
                (row["reference_id"],),
            ))
        return ConfidenceReference(
            reference_id=row["reference_id"], created_at=row["created_at"],
            model_version=row["model_version"], config_version=row["config_version"],
            source_id=row["source_id"], sample_count=row["sample_count"],
            window_size=row["window_size"], mean_confidence=row["mean_confidence"],
            event_ids=event_ids,
        )
