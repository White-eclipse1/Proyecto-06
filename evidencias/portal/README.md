# Evidencia del portal local

Desde la raíz del repositorio, tras generar eventos y alertas reales en `data/monitoring.db`:

```powershell
python scripts/run_portal.py
```

URL local: `http://127.0.0.1:8000`.

- Eventos: `http://127.0.0.1:8000/events`. Abrir el ID de un evento para comprobar confidence, zona, detecciones, tiempos e imagen vinculada si existe.
- Alertas: `http://127.0.0.1:8000/alerts`. Abrir una regla para ver la alerta y seguir el enlace al evento relacionado; desde él se abre la captura.
- API: `GET /api/events`, `GET /api/events/{event_id}`, `GET /api/alerts` y `GET /api/alerts/{alert_id}`. Los listados admiten `limit` y `offset`.

Las páginas consultan SQLite en el momento de la solicitud. Las capturas se sirven solo cuando el archivo está en el directorio configurado y está vinculado al evento solicitado. No se adjuntan capturas visuales finales en esta fase.
