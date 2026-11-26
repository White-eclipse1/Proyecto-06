# Capturas selectivas y alertas

## Política de capturas

`config/capture.yaml` fija la versión, el directorio `data/captures/`, la captura por `LOW_CONFIDENCE` y `normal_sample_every: 20`. El pipeline también conserva una imagen cuando una regla genera una alerta y cuando se solicita explícitamente evidencia de escenario. Solo `ACCEPTED_BY_POLICY` participa en el muestreo normal; el contador corresponde a esa fuente durante la corrida. No se conserva cada frame.

Cada JPEG lleva el UUID del evento: `data/captures/<event_id>.jpg`. `CaptureStore` usa creación exclusiva, comprueba que la imagen puede decodificarse y no sobrescribe un nombre existente. La ruta absoluta guardada en `events.image_reference` resuelve al archivo real. Las capturas locales se excluyen de Git; una exportación seleccionada puede copiarse a `evidencias/imagenes/` con el mismo UUID.

**No automatic expiration is configured.** No hay TTL, cron, borrado por edad ni rutina de limpieza de capturas. Su eliminación requiere una acción manual. Si falla una inserción SQLite después de escribir una captura nueva, la transacción revierte el vínculo de base de datos; el archivo puede quedar sin vínculo y debe revisarse manualmente.

## Reglas

`config/alerts.yaml` declara `alerts-v1`. `LOW_CONFIDENCE_ALERT` está activa con `minimum_events: 1`, `window_size: 1`, severidad `WARNING` y acción sugerida explícita. Solo evalúa eventos con score real y zona `LOW_CONFIDENCE`. Si se configura un mínimo mayor, se usan los últimos eventos puntuados de la misma fuente y versiones; si faltan eventos, la regla devuelve `INSUFFICIENT_DATA` sin crear alerta. `UNCERTAIN`, `ACCEPTED_BY_POLICY`, `NO_DETECTION` y `MODEL_ERROR` no disparan esta regla.

La regla opcional `SUSTAINED_CONFIDENCE_CHANGE_ALERT` puede evaluar un estado de ventana, pero está desactivada por defecto. Se refiere a un cambio de confianza respecto a una referencia; no declara drift confirmado.

## Persistencia y trazabilidad

La tabla `alerts` conserva UUID, timestamp UTC, regla, severidad, motivo, acción sugerida, `ACTIVE` o `RESOLVED`, fuente, versión de configuración y `event_id` o `window_id`/`reference_id`. `event_id` es clave foránea hacia `events`. Índices únicos sobre `(rule_id,event_id)` y `(rule_id,window_id)` hacen idempotente la creación. `AlertRepository.save_alert()` devuelve `(alerta, creada)`; al reprocesar el mismo evento devuelve la alerta existente con `creada=False`.

El pipeline guarda primero el evento. Después evalúa la regla, decide la captura —incluido el motivo `ALERT`— y, si hay alerta, actualiza `events.image_reference` e inserta `alerts` en una sola transacción. El repositorio exige una imagen existente para `LOW_CONFIDENCE_ALERT`, incluso si se llama directamente, antes de guardar la alerta. `get_alert()`, `list_alerts()` y `list_active_alerts()` permiten verificar la cadena `alert → event → image` desde SQLite. Las claves foráneas se activan en cada conexión.

## Ejecución y exportación

Desde la raíz de P6, con los pesos instalados:

```powershell
python scripts/test_alert_pipeline.py --input "ruta\imagen.jpg" --source-id "fuente" --export
```

El JSON muestra `alert_created`, `rule_status`, `image_reference`, `image_exists`, la alerta recuperada y `g7_active_alerts`. Una imagen sin regla aplicable termina correctamente con `alert_created=false`.

`--export` escribe las alertas reales de la fuente en `evidencias/alertas/alertas.json`, un evento en `evidencias/eventos/<event_id>.json` y, si se conservó, su JPEG en `evidencias/imagenes/<event_id>.jpg`. El JSON exportado del evento apunta a `../imagenes/<event_id>.jpg` y contiene el SHA-256 de esa copia. `scripts/recalculate_metrics.py --export` actualiza G7 desde la tabla `alerts` y exporta también las alertas reales.

No existe todavía portal, envío de correo, SMS, Slack, reconocimiento manual ni mitigación automática.
