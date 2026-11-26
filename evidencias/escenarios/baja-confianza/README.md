# C2: baja confianza real y alerta vinculada

La imagen de entrada es `input/camara-nueva.jpg`, copia exacta de
`Proyecto4/evidencias/EDGE-01/camara-nueva.jpg`. SHA-256: `605479b4a5e4f8d28efee22f8933c5576328b7162869c4222b1cb751a289b21a`.

Selección: Imagen de cámara P4 que produce una detección real por debajo del umbral inferior. La zona `LOW_CONFIDENCE` expresa un score bajo; no confirma si las clases son correctas.

Ejecutar desde la raíz:

```powershell
python scripts/run_scenario.py --scenario low-confidence
```

Esta corrida usó el archivo interno del repositorio. La evidencia vigente es la corrida `7ca8f608-6b30-4b5e-ab1f-5b30d0bc75e9`;
las reejecuciones anteriores se conservan en `runs/`.
El working tree tenía cambios sin commit; el estado exacto previo está en `manifest.json`.

| Campo | Valor |
| --- | --- |
| Git commit | `067787ccf983cd2a013862f134589876dd0bf5ed` |
| Git branch | `main` |
| Git limpio antes de la corrida | `False` |
| Modelo | `YOLOX-Tiny` `0.1.1rc0` |
| SHA-256 del modelo | `427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` |
| Configuración | `monitoring-v1` |
| Threshold inferior | `0.6` |
| Threshold superior | `0.8` |
| Fuente | `scenario-c2-d865723c-27cb-43ba-a10d-75057e8d432e` |
| Event ID | `36e70cb2-1b45-433c-9007-a516b8ead519` |
| Confidence | `0.3968369795843003` |
| Confidence zone | `LOW_CONFIDENCE` |
| Detecciones | `2` |
| Alertas del evento | `1` |

Alerta `LOW_CONFIDENCE_ALERT` `bcedf448-91d1-484b-aec6-f2e0636e04d2` vinculada al evento.

Detecciones registradas:

- `refrigerator` (class_id `72`), confidence `0.3968369795843003`.
- `tie` (class_id `27`), confidence `0.2407698662953166`.

Métricas de esta corrida:

| Grupo y métrica | Valor | Estado |
| --- | --- | --- |
| G1 · inference_time_ms | `39.23729993402958` | `OK` |
| G2 · processing_fps | `null` | `INSUFFICIENT_DATA` |
| G3 · process_cpu_percent | `602.7` | `OK` |
| G4 · low_confidence_ratio | `1.0` | `OK` |
| G5 · traceability_coverage | `1.0` | `OK` |
| G6 · last_report_age_seconds | `0.10060501098632812` | `OK` |
| G7 · active_alerts | `1` | `OK` |

`metrics.json` contiene G1–G7 recalculadas desde las observaciones SQLite de esta corrida. Algunas
métricas, como G2 con un solo frame, pueden tener `INSUFFICIENT_DATA`; se conserva ese estado real.
`event.json` documenta la fila persistida. `alert.json` conserva la alerta persistida. `portal_event.json` y
`portal_alert.json` provienen de consultas reales a la API FastAPI.
Las copias exactas de las configuraciones usadas están en `config_snapshot/`.

Para verificarlo visualmente, ejecutar `python scripts/run_portal.py`, abrir
`http://127.0.0.1:8000/events/36e70cb2-1b45-433c-9007-a516b8ead519` y `http://127.0.0.1:8000/alerts/bcedf448-91d1-484b-aec6-f2e0636e04d2`. La captura asociada está en
`capturas/` cuando la política decidió conservarla.

No se editaron scores, detecciones ni thresholds para obtener este resultado.
