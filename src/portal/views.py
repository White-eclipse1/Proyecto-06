"""Vistas HTML escapadas para la consulta local de eventos y alertas."""

from collections.abc import Callable
from html import escape

from src.alerts.models import Alert
from src.events.models import Event


def h(value: object) -> str:
    return escape(str(value), quote=True)


def text(value: object | None) -> str:
    return "—" if value is None else h(value)


def confidence(value: float | None) -> str:
    return "—" if value is None else f"{value:.4f}"


def badge(value: str) -> str:
    tone = {
        "LOW_CONFIDENCE": "warning", "WARNING": "warning", "CRITICAL": "critical",
        "ACTIVE": "warning", "RESOLVED": "success", "ACCEPTED_BY_POLICY": "success",
        "NORMAL": "success", "MODEL_ERROR": "critical",
    }.get(value, "neutral")
    return f'<span class="badge badge-{tone}">{h(value)}</span>'


def layout(title: str, active: str, body: str) -> str:
    event_current = ' aria-current="page"' if active == "events" else ""
    alert_current = ' aria-current="page"' if active == "alerts" else ""
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(title)} · Centro de Monitoreo CV</title>
<link rel="stylesheet" href="/static/style.css"></head>
<body><header class="site-header"><div class="header-inner">
<a class="brand" href="/events"><span class="brand-mark" aria-hidden="true">◉</span><span>Centro de Monitoreo <strong>CV</strong></span></a>
<nav aria-label="Navegación principal"><a href="/events"{event_current}>Eventos</a><a href="/alerts"{alert_current}>Alertas</a></nav>
</div></header><main class="container">{body}</main>
<footer class="site-footer"><div class="container">Consulta local · Datos persistidos en SQLite</div></footer>
</body></html>"""


def heading(kicker: str, title: str, description: str) -> str:
    return (f'<div class="page-head"><div><p class="eyebrow">{h(kicker)}</p>'
            f'<h1>{h(title)}</h1><p class="lede">{h(description)}</p></div></div>')


def pagination(base: str, count: int, offset: int, shown: int) -> str:
    if count == 0:
        return ""
    first = min(offset + 1, count)
    last = min(offset + shown, count)
    previous = (f'<a href="{base}?offset={max(0, offset - 20)}">Anterior</a>'
                if offset > 0 else '<span class="disabled">Anterior</span>')
    following = (f'<a href="{base}?offset={offset + 20}">Siguiente</a>'
                 if offset + shown < count and shown > 0 else '<span class="disabled">Siguiente</span>')
    return (f'<div class="pagination"><span>Mostrando {first}–{last} de {count}</span>'
            f'<div>{previous}{following}</div></div>')


def events_page(
    items: list[Event], count: int, offset: int, image_url: Callable[[Event], str | None],
) -> str:
    rows = "".join(
        f'<tr><td class="date-cell">{h(event.timestamp)}</td>'
        f'<td><a class="id-link" href="/events/{h(event.event_id)}" title="{h(event.event_id)}">{h(event.event_id[:8])}</a></td>'
        f'<td>{h(event.source_id)}</td><td class="numeric">{confidence(event.confidence)}</td>'
        f'<td>{badge(event.confidence_zone)}</td><td class="numeric">{event.detection_count}</td>'
        f'<td>{badge(event.state)}</td><td>{"Disponible" if image_url(event) else "—"}</td></tr>'
        for event in items
    )
    content = (f'<div class="panel table-panel"><div class="table-scroll"><table><thead><tr>'
               '<th>Fecha UTC</th><th>Evento</th><th>Fuente</th><th>Confidence</th>'
               '<th>Zona</th><th>Detecciones</th><th>Estado</th><th>Imagen</th>'
               f'</tr></thead><tbody>{rows}</tbody></table></div>{pagination("/events", count, offset, len(items))}</div>'
               if items else ('<div class="empty panel"><h2>Sin eventos</h2><p>Aún no hay eventos registrados en SQLite.</p></div>'
                              if count == 0 else '<div class="empty panel"><h2>Sin eventos en esta página</h2><a href="/events">Volver al inicio</a></div>'))
    return layout("Eventos", "events", heading("Registro de inferencias", "Eventos", "Consulta de inferencias y su evidencia persistida.") +
                  f'<div class="count-line">{count} eventos registrados</div>' + content)


def alerts_page(items: list[Alert], count: int, offset: int) -> str:
    def related_event(alert: Alert) -> str:
        if alert.event_id is None:
            return "—"
        return f'<a href="/events/{h(alert.event_id)}">{h(alert.event_id[:8])}</a>'

    rows = "".join(
        f'<tr><td class="date-cell">{h(alert.timestamp)}</td>'
        f'<td>{badge(alert.severity)}</td>'
        f'<td><a class="id-link" href="/alerts/{h(alert.alert_id)}">{h(alert.rule_id)}</a></td>'
        f'<td class="reason-cell">{h(alert.reason)}</td><td>{badge(alert.status)}</td>'
        f'<td>{h(alert.source_id)}</td>'
        f'<td>{related_event(alert)}</td></tr>'
        for alert in items
    )
    content = (f'<div class="panel table-panel"><div class="table-scroll"><table><thead><tr>'
               '<th>Fecha UTC</th><th>Severidad</th><th>Regla</th><th>Motivo</th>'
               '<th>Estado</th><th>Fuente</th><th>Evento</th>'
               f'</tr></thead><tbody>{rows}</tbody></table></div>{pagination("/alerts", count, offset, len(items))}</div>'
               if items else ('<div class="empty panel"><h2>Sin alertas</h2><p>Aún no hay alertas registradas en SQLite.</p></div>'
                              if count == 0 else '<div class="empty panel"><h2>Sin alertas en esta página</h2><a href="/alerts">Volver al inicio</a></div>'))
    return layout("Alertas", "alerts", heading("Reglas de monitoreo", "Alertas", "Alertas reales generadas por las reglas configuradas.") +
                  f'<div class="count-line">{count} alertas registradas</div>' + content)


def facts(pairs: list[tuple[str, object | None]]) -> str:
    return '<dl class="facts">' + "".join(
        f'<div><dt>{h(label)}</dt><dd>{text(value)}</dd></div>' for label, value in pairs
    ) + '</dl>'


def event_detail_page(event: Event, image: str | None) -> str:
    detections = "".join(
        f'<tr><td>{h(d.class_name)}</td><td>{d.class_id}</td>'
        f'<td class="numeric">{confidence(d.confidence)}</td>'
        f'<td class="mono">{h(", ".join(f"{n:.2f}" for n in d.bbox))}</td></tr>'
        for d in event.detections
    )
    detection_section = (
        '<div class="table-scroll"><table><thead><tr><th>Clase</th><th>ID de clase</th>'
        f'<th>Confidence</th><th>Bounding box [x1, y1, x2, y2]</th></tr></thead><tbody>{detections}</tbody></table></div>'
        if detections else '<p class="muted">Este evento no contiene detecciones.</p>'
    )
    image_section = (f'<img class="capture" src="{h(image)}" alt="Captura asociada al evento {h(event.event_id)}">'
                     if image else '<p class="muted">Sin captura disponible para este evento.</p>')
    body = (f'<a class="back-link" href="/events">Volver a eventos</a>'
            + heading("Detalle de inferencia", "Evento", "Datos originales de SQLite y captura vinculada, si existe.")
            + f'<p class="full-id">{h(event.event_id)}</p>'
            + '<section class="panel section"><h2>Datos del evento</h2>'
            + facts([("Fecha UTC", event.timestamp), ("Fuente", event.source_id),
                     ("Modelo", event.model_version), ("Configuración", event.config_version),
                     ("Estado", event.state), ("Confidence", confidence(event.confidence)),
                     ("Zona", event.confidence_zone), ("Detecciones", event.detection_count)])
            + '</section><section class="panel section"><h2>Tiempos</h2>'
            + facts([("Lectura", event.read_time_ms), ("Preprocesamiento", event.preprocessing_time_ms),
                     ("Inferencia", event.inference_time_ms), ("Posprocesamiento", event.postprocessing_time_ms)])
            + '<p class="hint">Valores en milisegundos.</p></section>'
            + f'<section class="panel section"><h2>Detecciones</h2>{detection_section}</section>'
            + f'<section class="panel section"><h2>Imagen asociada</h2>{image_section}</section>')
    return layout("Detalle de evento", "events", body)


def alert_detail_page(alert: Alert, event: Event | None, image: str | None) -> str:
    related = (f'<a class="action-link" href="/events/{h(event.event_id)}">Abrir evento {h(event.event_id[:8])}</a>'
               if event else '<p class="muted">Esta alerta no tiene un evento individual asociado.</p>')
    image_section = (f'<a class="capture-link" href="/events/{h(event.event_id)}">'
                     f'<img class="capture" src="{h(image)}" alt="Captura vinculada a la alerta"></a>'
                     if image and event else '<p class="muted">Sin captura disponible.</p>')
    body = (f'<a class="back-link" href="/alerts">Volver a alertas</a>'
            + heading("Detalle de regla", "Alerta", "Motivo, acción sugerida y trazabilidad al evento.")
            + f'<p class="full-id">{h(alert.alert_id)}</p>'
            + '<section class="panel section"><h2>Datos de la alerta</h2>'
            + facts([("Fecha UTC", alert.timestamp), ("Regla", alert.rule_id),
                     ("Severidad", alert.severity), ("Motivo", alert.reason),
                     ("Acción sugerida", alert.suggested_action), ("Estado", alert.status),
                     ("Fuente", alert.source_id), ("Configuración", alert.config_version),
                     ("Evento", alert.event_id), ("Ventana", alert.window_id)])
            + f'</section><section class="panel section"><h2>Evento relacionado</h2>{related}</section>'
            + f'<section class="panel section"><h2>Imagen asociada</h2>{image_section}</section>')
    return layout("Detalle de alerta", "alerts", body)


def not_found_page(kind: str) -> str:
    return layout("No encontrado", "", '<div class="empty panel not-found"><h1>' + h(kind) +
                  ' no encontrado</h1><p>El identificador solicitado no existe en SQLite.</p>'
                  '<a class="action-link" href="/events">Ver eventos</a></div>')
