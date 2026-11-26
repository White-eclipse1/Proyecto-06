"""API y páginas locales de consulta sobre la base SQLite de monitoreo."""

import sqlite3
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from src.alerts.models import Alert
from src.captures.config import load_capture_config
from src.events.models import Event
from src.persistence import AlertRepository, Database, EventRepository

from .views import alert_detail_page, alerts_page, event_detail_page, events_page, not_found_page

ROOT = Path(__file__).resolve().parents[2]
STYLE = Path(__file__).parent / "static" / "style.css"


class ReadOnlyDatabase(Database):
    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        return connection


def create_app(
    database_path: str | Path | None = None, captures_dir: str | Path | None = None,
) -> FastAPI:
    """Construye una instancia aislable para pruebas sin escribir desde el portal."""
    database = ReadOnlyDatabase(database_path or ROOT / "data" / "monitoring.db")
    capture_dir = Path(captures_dir or load_capture_config(ROOT / "config" / "capture.yaml").directory).resolve()
    events = EventRepository(database)
    alerts = AlertRepository(database)
    app = FastAPI(title="Centro de Monitoreo CV", version="1.0", docs_url=None, redoc_url=None)

    def image_url(event: Event) -> str | None:
        reference = event.image_reference
        if reference is None:
            return None
        path = Path(reference).resolve()
        expected = capture_dir / f"{event.event_id}.jpg"
        if path == expected and path.is_relative_to(capture_dir) and path.is_file():
            return f"/captures/{event.event_id}.jpg"
        return None

    def event_data(event: Event) -> dict[str, object]:
        data = event.to_dict()
        # Nunca se entrega la ruta absoluta almacenada en SQLite.
        data["image_reference"] = image_url(event)
        # El detalle de un fallo del modelo puede contener rutas del host.
        data.pop("error_detail", None)
        return data

    def alert_data(alert: Alert) -> dict[str, object]:
        data = alert.to_dict()
        event = events.get_event(alert.event_id) if alert.event_id else None
        data["event_url"] = f"/events/{alert.event_id}" if event else None
        data["image_url"] = image_url(event) if event else None
        return data

    @app.get("/", include_in_schema=False)
    def home() -> RedirectResponse:
        return RedirectResponse("/events", status_code=302)

    @app.get("/static/style.css", include_in_schema=False)
    def style() -> FileResponse:
        return FileResponse(STYLE, media_type="text/css")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/events")
    def api_events(
        limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    ) -> dict[str, object]:
        items, count = events.list_events_page(limit, offset)
        return {"items": [event_data(item) for item in items], "count": count,
                "limit": limit, "offset": offset}

    @app.get("/api/events/{event_id}")
    def api_event(event_id: str) -> dict[str, object]:
        event = events.get_event(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        return event_data(event)

    @app.get("/api/alerts")
    def api_alerts(
        limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    ) -> dict[str, object]:
        items, count = alerts.list_alerts_page(limit, offset)
        return {"items": [alert_data(item) for item in items], "count": count,
                "limit": limit, "offset": offset}

    @app.get("/api/alerts/{alert_id}")
    def api_alert(alert_id: str) -> dict[str, object]:
        alert = alerts.get_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        return alert_data(alert)

    @app.get("/captures/{filename}", include_in_schema=False)
    def capture(filename: str) -> FileResponse:
        if not filename.endswith(".jpg"):
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        try:
            event_id = str(UUID(filename[:-4]))
        except ValueError as error:
            raise HTTPException(status_code=404, detail="Captura no encontrada") from error
        if filename != f"{event_id}.jpg":
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        event = events.get_event(event_id)
        if event is None or image_url(event) != f"/captures/{filename}":
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        return FileResponse(capture_dir / filename, media_type="image/jpeg")

    @app.get("/events", response_class=HTMLResponse, include_in_schema=False)
    def event_list(offset: int = Query(0, ge=0)) -> HTMLResponse:
        items, count = events.list_events_page(20, offset)
        return HTMLResponse(events_page(items, count, offset, image_url))

    @app.get("/events/{event_id}", response_class=HTMLResponse, include_in_schema=False)
    def event_detail(event_id: str) -> HTMLResponse:
        event = events.get_event(event_id)
        if event is None:
            return HTMLResponse(not_found_page("Evento"), status_code=404)
        return HTMLResponse(event_detail_page(event, image_url(event)))

    @app.get("/alerts", response_class=HTMLResponse, include_in_schema=False)
    def alert_list(offset: int = Query(0, ge=0)) -> HTMLResponse:
        items, count = alerts.list_alerts_page(20, offset)
        return HTMLResponse(alerts_page(items, count, offset))

    @app.get("/alerts/{alert_id}", response_class=HTMLResponse, include_in_schema=False)
    def alert_detail(alert_id: str) -> HTMLResponse:
        alert = alerts.get_alert(alert_id)
        if alert is None:
            return HTMLResponse(not_found_page("Alerta"), status_code=404)
        event = events.get_event(alert.event_id) if alert.event_id else None
        return HTMLResponse(alert_detail_page(alert, event, image_url(event) if event else None))

    return app


app = create_app()
