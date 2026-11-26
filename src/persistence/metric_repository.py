"""Almacena observaciones primarias y permite recálculo por corrida o fuente."""

from contextlib import closing

from src.events.models import Event
from src.metrics.models import MetricObservation

from .database import Database
from .repositories import EventRepository


class MetricRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_many(self, observations: list[MetricObservation]) -> None:
        with closing(self.database.connect()) as connection, connection:
            connection.executemany(
                """INSERT INTO metric_observations
                (observation_id, timestamp, event_id, source_id, metric_group,
                 metric_name, value, unit, run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        o.observation_id, o.timestamp, o.event_id, o.source_id,
                        o.metric_group, o.metric_name, o.value, o.unit, o.run_id,
                    ) for o in observations
                ],
            )

    def list_observations(
        self, *, run_id: str | None = None, source_id: str | None = None,
        metric_group: str | None = None,
    ) -> list[MetricObservation]:
        clauses = []
        params = []
        for column, value in (("run_id", run_id), ("source_id", source_id),
                              ("metric_group", metric_group)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM metric_observations{where} ORDER BY timestamp, observation_id",
                params,
            ).fetchall()
        return [MetricObservation(**dict(row)) for row in rows]

    def latest_run_id(self, source_id: str | None = None) -> str | None:
        clause = " AND source_id = ?" if source_id else ""
        params = (source_id,) if source_id else ()
        with closing(self.database.connect()) as connection:
            row = connection.execute(
                "SELECT run_id FROM metric_observations "
                "WHERE metric_name = 'run_start_epoch_seconds'" + clause +
                " ORDER BY timestamp DESC, observation_id DESC LIMIT 1",
                params,
            ).fetchone()
        return row["run_id"] if row else None

    def events_for_run(self, run_id: str) -> list[Event]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT DISTINCT event_id FROM metric_observations "
                "WHERE run_id = ? AND event_id IS NOT NULL",
                (run_id,),
            ).fetchall()
        events = [EventRepository(self.database).get_event(row["event_id"]) for row in rows]
        return sorted((event for event in events if event is not None),
                      key=lambda event: (event.timestamp, event.event_id))
