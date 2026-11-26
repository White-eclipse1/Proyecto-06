# C2: baja confianza real y alerta vinculada

La imagen de entrada es `input/camara-nueva.jpg`, copia exacta de
`Proyecto4/evidencias/EDGE-01/camara-nueva.jpg`. SHA-256: `605479b4a5e4f8d28efee22f8933c5576328b7162869c4222b1cb751a289b21a`.

Selección: Imagen de cámara P4 que produce una detección real por debajo del umbral inferior. La zona `ACCEPTED_BY_POLICY` no afirma que la predicción sea correcta.

Ejecutar desde la raíz:

```powershell
python scripts/run_scenario.py --scenario low-confidence
```

Esta corrida usó el archivo interno del repositorio. La evidencia vigente es la corrida `d525d386-5792-4651-aa73-58ea28c418c2`;
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
| Fuente | `scenario-c2-ece75df9-216c-4883-8a9e-072d75ea8019` |
| Event ID | `54b835ae-e4d6-4558-bd35-a2094517d7d1` |
| Confidence | `0.3968369795843003` |
| Confidence zone | `LOW_CONFIDENCE` |
| Detecciones | `2` |
| Alertas del evento | `1` |

Alerta `LOW_CONFIDENCE_ALERT` `677730e5-8870-4b51-8c60-19d284ebf29e` vinculada al evento.

`metrics.json` contiene G1–G7 recalculadas desde las observaciones SQLite de esta corrida. Algunas
métricas, como G2 con un solo frame, pueden tener `INSUFFICIENT_DATA`; se conserva ese estado real.
`event.json` y `alert.json` documentan las filas persistidas; `portal_event.json` y
`portal_alert.json` (o `portal_alerts.json` en C1) provienen de consultas reales a la API FastAPI.
Las copias exactas de las configuraciones usadas están en `config_snapshot/`.

Para verificarlo visualmente, ejecutar `python scripts/run_portal.py`, abrir
`http://127.0.0.1:8000/events/54b835ae-e4d6-4558-bd35-a2094517d7d1` y, si existe alerta,
`http://127.0.0.1:8000/alerts/677730e5-8870-4b51-8c60-19d284ebf29e`. La captura asociada está en
`capturas/` cuando la política decidió conservarla.

No se editaron scores, detecciones ni thresholds para obtener este resultado.
