# C1: operación aceptada por la política configurada

La imagen de entrada es `input/seq02-0001.jpg`, copia exacta de
`Proyecto5/data/p5-eval-v1/secuencias/seq02/seq02-0001.jpg`. SHA-256: `de5d68269a9d172fcb7a02514ed6a8363221326bd6eb2ff435f11fa9c64e1e14`.

Selección: Frame exterior de la secuencia de evaluación P5 con una persona visible; su score real supera el umbral superior. La zona `ACCEPTED_BY_POLICY` no afirma que la predicción sea correcta.

Ejecutar desde la raíz:

```powershell
python scripts/run_scenario.py --scenario normal
```

Esta corrida usó el archivo interno del repositorio. La evidencia vigente es la corrida `68d02f03-6c07-47a7-8d8a-c014d6ae44aa`;
las reejecuciones anteriores se conservan en `runs/`.
El working tree estaba limpio antes de la corrida.

| Campo | Valor |
| --- | --- |
| Git commit | `a9c862f215c168bbbc49c62b836e1aee3927946f` |
| Git branch | `main` |
| Git limpio antes de la corrida | `True` |
| Modelo | `YOLOX-Tiny` `0.1.1rc0` |
| SHA-256 del modelo | `427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` |
| Configuración | `monitoring-v1` |
| Threshold inferior | `0.6` |
| Threshold superior | `0.8` |
| Fuente | `scenario-c1-8ae08c4c-2137-4b37-a9bc-3a080f250bbd` |
| Event ID | `3f58257b-7de3-460b-8822-29e3eba3e77c` |
| Confidence | `0.8417058511793911` |
| Confidence zone | `ACCEPTED_BY_POLICY` |
| Detecciones | `3` |
| Alertas del evento | `0` |

Ninguna alerta para este evento.

Detecciones registradas:

- `person` (class_id `0`), confidence `0.8417058511793911`.
- `backpack` (class_id `24`), confidence `0.29074179876634787`.
- `person` (class_id `0`), confidence `0.1810876666496739`.

Métricas de esta corrida:

| Grupo y métrica | Valor | Estado |
| --- | --- | --- |
| G1 · inference_time_ms | `33.24550006072968` | `OK` |
| G2 · processing_fps | `null` | `INSUFFICIENT_DATA` |
| G3 · process_cpu_percent | `520.8` | `OK` |
| G4 · low_confidence_ratio | `0.0` | `OK` |
| G5 · traceability_coverage | `1.0` | `OK` |
| G6 · last_report_age_seconds | `0.0407099723815918` | `OK` |
| G7 · active_alerts | `0` | `OK` |

`metrics.json` contiene G1–G7 recalculadas desde las observaciones SQLite de esta corrida. Algunas
métricas, como G2 con un solo frame, pueden tener `INSUFFICIENT_DATA`; se conserva ese estado real.
`event.json` documenta la fila persistida. `portal_event.json` y
`portal_alerts.json` provienen de consultas reales a la API FastAPI.
Las copias exactas de las configuraciones usadas están en `config_snapshot/`.

Para verificarlo visualmente, ejecutar `python scripts/run_portal.py`, abrir
`http://127.0.0.1:8000/events/3f58257b-7de3-460b-8822-29e3eba3e77c` y la lista `http://127.0.0.1:8000/alerts`. La captura asociada está en
`capturas/` cuando la política decidió conservarla.

No se editaron scores, detecciones ni thresholds para obtener este resultado.
