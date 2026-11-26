"""Alertas idempotentes con vínculo transaccional a evento e imagen."""

import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from src.alerts.models import Alert, AlertStatus, Severity

from .database import Database


def _from_row(row) -> Alert:
    return Alert(
        alert_id=row["alert_id"], timestamp=row["timestamp"], rule_id=row["rule_id"],
        severity=Severity(row["severity"]), reason=row["reason"],
        suggested_action=row["suggested_action"], status=AlertStatus(row["status"]),
        source_id=row["source_id"], config_version=row["config_version"],
        event_id=row["event_id"], window_id=row["window_id"],
        reference_id=row["reference_id"], resolved_at=row["resolved_at"],
    )


class AlertRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_alert(self, alert: Alert, *, image_reference: str | None = None) -> tuple[Alert, bool]:
        if image_reference is not None and not Path(image_reference).is_file():
            raise ValueError(f"image_reference no existe: {image_reference}")
        if image_reference is not None and alert.event_id is None:
            raise ValueError("una alerta de ventana no puede actualizar la imagen de un evento")
        with closing(self.database.connect()) as connection, connection:
            if alert.event_id is not None:
                event = connection.execute(
                    "SELECT image_reference FROM events WHERE event_id = ?", (alert.event_id,)
                ).fetchone()
                if event is None:
                    raise ValueError(f"evento no encontrado: {alert.event_id}")
                if image_reference is not None:
                    if event["image_reference"] not in (None, image_reference):
                        raise ValueError("el evento ya tiene otra image_reference")
                    connection.execute(
                        "UPDATE events SET image_reference = ? WHERE event_id = ?",
                        (image_reference, alert.event_id),
                    )
                effective_reference = image_reference or event["image_reference"]
                if (alert.rule_id == "LOW_CONFIDENCE_ALERT" and
                        (effective_reference is None or not Path(effective_reference).is_file())):
                    raise ValueError("LOW_CONFIDENCE_ALERT requiere una imagen existente")
                existing = connection.execute(
                    "SELECT * FROM alerts WHERE rule_id = ? AND event_id = ?",
                    (alert.rule_id, alert.event_id),
                ).fetchone()
            else:
                existing = connection.execute(
                    "SELECT * FROM alerts WHERE rule_id = ? AND window_id = ?",
                    (alert.rule_id, alert.window_id),
                ).fetchone()
            if existing is not None:
                return _from_row(existing), False
            connection.execute(
                """INSERT INTO alerts (
                    alert_id, timestamp, rule_id, severity, reason, suggested_action,
                    status, source_id, config_version, event_id, window_id, reference_id, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (alert.alert_id, alert.timestamp, alert.rule_id, alert.severity.value,
                 alert.reason, alert.suggested_action, alert.status.value,
                 alert.source_id, alert.config_version, alert.event_id,
                 alert.window_id, alert.reference_id, alert.resolved_at),
            )
        return alert, True

    def get_alert(self, alert_id: str) -> Alert | None:
        with closing(self.database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)
            ).fetchone()
        return _from_row(row) if row is not None else None

    def list_alerts(self, limit: int | None = 20, *, source_id: str | None = None) -> list[Alert]:
        if limit is not None and limit < 1:
            raise ValueError("limit debe ser >= 1")
        query = "SELECT * FROM alerts"
        params: list[object] = []
        if source_id is not None:
            query += " WHERE source_id = ?"
            params.append(source_id)
        query += " ORDER BY timestamp DESC, alert_id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with closing(self.database.connect()) as connection:
            return [_from_row(row) for row in connection.execute(query, params)]

    def list_alerts_page(self, limit: int = 20, offset: int = 0) -> tuple[list[Alert], int]:
        if limit < 1 or offset < 0:
            raise ValueError("limit debe ser >= 1 y offset >= 0")
        with closing(self.database.connect()) as connection:
            count = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            items = [
                _from_row(row) for row in connection.execute(
                    "SELECT * FROM alerts ORDER BY timestamp DESC, alert_id DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            ]
        return items, count

    def list_active_alerts(
        self, *, source_id: str | None = None, as_of: datetime | None = None,
    ) -> list[Alert]:
        query = "SELECT * FROM alerts WHERE status = 'ACTIVE'"
        params: list[object] = []
        if source_id is not None:
            query += " AND source_id = ?"
            params.append(source_id)
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of debe tener zona horaria")
            query += " AND timestamp <= ?"
            params.append(as_of.astimezone(timezone.utc).isoformat())
        query += " ORDER BY timestamp DESC, alert_id DESC"
        with closing(self.database.connect()) as connection:
            return [_from_row(row) for row in connection.execute(query, params)]

    def export_alerts(self, path: str | Path, *, source_id: str | None = None) -> Path:
        alerts = self.list_alerts(limit=None, source_id=source_id)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as file:
            json.dump([alert.to_dict() for alert in alerts], file, ensure_ascii=False,
                      indent=2, allow_nan=False)
            file.write("\n")
        return target
