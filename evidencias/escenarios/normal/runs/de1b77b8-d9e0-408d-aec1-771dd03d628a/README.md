# C1: operación aceptada por la política configurada

La imagen de entrada es `input/seq02-0001.jpg`, copia exacta de
`Proyecto5/data/p5-eval-v1/secuencias/seq02/seq02-0001.jpg`. SHA-256: `de5d68269a9d172fcb7a02514ed6a8363221326bd6eb2ff435f11fa9c64e1e14`.

Selección: Frame exterior de la secuencia de evaluación P5 con una persona visible; su score real supera el umbral superior. La zona `ACCEPTED_BY_POLICY` no afirma que la predicción sea correcta.

Ejecutar desde la raíz:

```powershell
python scripts/run_scenario.py --scenario normal
```

Esta corrida usó el archivo interno del repositorio. La evidencia vigente es la corrida `de1b77b8-d9e0-408d-aec1-771dd03d628a`;
las reejecuciones anteriores se conservan en `runs/`.

| Campo | Valor |
| --- | --- |
| Git commit | `067787ccf983cd2a013862f134589876dd0bf5ed` |
| Git branch | `main` |
| Git limpio antes de la corrida | `False` |
| Modelo | `0.1.1rc0` |
| SHA-256 del modelo | `427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` |
| Configuración | `monitoring-v1` |
| Threshold inferior | `0.6` |
| Threshold superior | `0.8` |
| Fuente | `scenario-c1-45d66ba6-228c-481f-b296-e464566d0986` |
| Event ID | `b5a2140c-8609-4b94-a6c4-78b27c0d20f4` |
| Confidence | `0.8417058511793911` |
| Confidence zone | `ACCEPTED_BY_POLICY` |
| Detecciones | `3` |
| Alertas del evento | `0` |

Ninguna alerta para este evento.

`metrics.json` contiene G1–G7 recalculadas desde las observaciones SQLite de esta corrida. Algunas
métricas, como G2 con un solo frame, pueden tener `INSUFFICIENT_DATA`; se conserva ese estado real.
`event.json` y `alert.json` documentan las filas persistidas; `portal_event.json` y
`portal_alert.json` (o `portal_alerts.json` en C1) provienen de consultas reales a la API FastAPI.
Las copias exactas de las configuraciones usadas están en `config_snapshot/`.

Para verificarlo visualmente, ejecutar `python scripts/run_portal.py`, abrir
`http://127.0.0.1:8000/events/b5a2140c-8609-4b94-a6c4-78b27c0d20f4` y, si existe alerta,
`http://127.0.0.1:8000/alerts/None`. La captura asociada está en
`capturas/` cuando la política decidió conservarla.

No se editaron scores, detecciones ni thresholds para obtener este resultado.
