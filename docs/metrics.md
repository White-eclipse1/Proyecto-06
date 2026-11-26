# Métricas operativas G1–G6

Estas métricas describen la operación de P6 y el comportamiento de sus salidas. No miden calidad predictiva. El inventario versionado está en `config/metrics.yaml`: G1–G6 están implementadas y G7 figura como aplicable, pendiente del motor de alertas.

Cada fila de `metric_observations` conserva `observation_id`, timestamp UTC, `event_id` cuando corresponde, `source_id`, grupo, nombre, valor finito, unidad y `run_id`. `run_id` identifica una ejecución de `run_monitoring_sample.py`. Los eventos y sus detecciones permanecen en `events` y `detections`. `confidence_references` y `reference_events` guardan la referencia y los IDs exactos que la forman.

Los resultados comparten `value`, `unit`, `status`, `window_start`, `window_end`, `observation_count`, `eligible_count`, `source_id` y `run_id`. `INSUFFICIENT_DATA` tiene `value=null`; `ERROR` señala datos inconsistentes, como una observación que no coincide con su evento. Ningún cálculo sustituye datos ausentes por cero.

## G1 — Tiempo de inferencia

- **M1 Definición:** media aritmética de `inference_time_ms` por corrida, en `ms/inference`. Población: inferencias terminadas con tiempo medido. Ventana: desde la primera hasta la última observación de G1 del `run_id`. Excluye lectura, preprocesamiento y posprocesamiento; el valor fuente mide `session.run`.
- **M2 Adquisición:** `InferenceEngine.predict()` mide con `perf_counter`; `MetricsCollector.collect_event()` copia ese valor a una fila G1 asociada al `event_id`.
- **M3 Cálculo:** `sum(tiempos) / cantidad`. Sin tiempos: `value=null`, `INSUFFICIENT_DATA`.
- **M4 Trazabilidad:** la fila G1 enlaza `event_id`, `source_id`, `run_id` y `events.inference_time_ms`.
- **M5 Verificación:** ejecutar el comando de recálculo al final de este documento y comparar G1 con `AVG(value)` de las filas G1 del mismo `run_id`.

## G2 — FPS de procesamiento

- **M1 Definición:** `processed_frames / run_elapsed_seconds`, en `frames/second`. Población: frames que completaron el pipeline en una corrida; se requieren al menos dos. Ventana: desde el inicio registrado de la corrida hasta su fin. Excluye eventos `MODEL_ERROR` del numerador.
- **M2 Adquisición:** `MetricsCollector` registra `run_start_epoch_seconds`, un `processed_frame=1` por frame y `run_elapsed_seconds` al finalizar. La duración proviene de `perf_counter` y abarca lectura, inferencia y persistencia de la muestra.
- **M3 Cálculo:** conteo de filas `processed_frame` dividido entre `run_elapsed_seconds`. Falta de inicio/fin, menos de dos frames o duración no positiva: `value=null`, `INSUFFICIENT_DATA`.
- **M4 Trazabilidad:** cada frame tiene `event_id`; inicio y duración tienen `event_id=null` y el mismo `run_id`.
- **M5 Verificación:** recalcular desde SQLite y contar las filas `processed_frame` del `run_id`; dividir por su fila `run_elapsed_seconds`.

## G3 — Uso de CPU del proceso

- **M1 Definición:** media de las muestras `process_cpu_percent` de la corrida, en `%`. Población: eventos procesados que tienen muestra de CPU; ventana de sus timestamps. Es CPU del proceso P6, no CPU total del sistema. Puede superar 100% al usar varios núcleos.
- **M2 Adquisición:** `psutil.Process().cpu_percent(interval=None)` se inicializa antes de procesar la primera imagen; se lee después de cada evento. Cada muestra describe el intervalo transcurrido desde la lectura anterior.
- **M3 Cálculo:** media de las muestras. Sin muestras: `value=null`, `INSUFFICIENT_DATA`. Una muestra real de 0% sigue siendo válida.
- **M4 Trazabilidad:** cada muestra G3 enlaza `event_id`, fuente y corrida; el valor original permanece en `metric_observations`.
- **M5 Verificación:** recalcular y comparar G3 con la media de las filas `process_cpu_percent` del `run_id`.

## G4 — Proporción de baja confianza

- **M1 Definición:** `resultados puntuados LOW_CONFIDENCE / resultados puntuados elegibles`, unidad `ratio`. Población: frames con `confidence` real. Ventana: corrida. Excluye `NO_DETECTION`, `MODEL_ERROR` y `MISSING_SCORE` cuando no tienen score.
- **M2 Adquisición:** `MetricsCollector` guarda `frame_confidence` solo cuando el evento tiene score; la zona se conserva en `events`. La confianza del frame es el máximo de las detecciones retenidas por YOLOX.
- **M3 Cálculo:** contar zonas bajas entre observaciones elegibles y dividir por el total elegible. Si no hay puntuadas: `value=null`, `INSUFFICIENT_DATA`. Un `NO_DETECTION` no equivale a score cero.
- **M4 Trazabilidad:** cada `frame_confidence` enlaza su evento; al recalcular se comprueba que el valor guardado coincide con `events.confidence`.
- **M5 Verificación:** ejecutar recálculo, filtrar las filas G4 del `run_id` y contar sus eventos `LOW_CONFIDENCE` en `events`.

## G5 — Cobertura de trazabilidad

- **M1 Definición:** `eventos completos / eventos elegibles`, unidad `ratio`. Población: eventos de la corrida. Ventana: corrida. Un evento es completo si tiene ID, timestamp, fuente, versiones de modelo y configuración, estado y zona; `detection_count` coincide con sus detecciones; cada detección tiene clase, score y caja; para eventos puntuados la confianza del frame coincide con el máximo. `NO_DETECTION` y `MODEL_ERROR` pueden ser completos con confianza nula y cero detecciones.
- **M2 Adquisición:** `MetricsCollector` evalúa cada evento con `is_traceable()` y guarda `traceability_complete` como 1 o 0, ligado al `event_id`.
- **M3 Cálculo:** suma de valores 1 dividida entre cantidad de eventos evaluados. Sin eventos: `value=null`, `INSUFFICIENT_DATA`. El recálculo verifica que la evaluación guardada coincide con el evento recuperado.
- **M4 Trazabilidad:** la fila G5 apunta al evento y a sus detecciones mediante `event_id`, además de `source_id` y `run_id`.
- **M5 Verificación:** recalcular y examinar las filas G5 junto con `events` y `detections`; `NO_DETECTION` con score nulo debe contar como completo si conserva los demás campos.

## G6 — Tiempo desde el último reporte

- **M1 Definición:** `as_of - timestamp del evento más reciente de source_id`, en `seconds`. Población: reportes de esa fuente, incluso de corridas anteriores. Ventana: desde el último evento hasta `as_of`; no se mezclan fuentes.
- **M2 Adquisición:** por evento, `MetricsCollector` guarda `report_epoch_seconds` derivado de su timestamp UTC. El instante `as_of` se imprime y exporta con el resultado.
- **M3 Cálculo:** diferencia en segundos respecto al reporte más reciente de la fuente que no sea posterior a `as_of`. Sin reporte hasta ese instante: `value=null`, `INSUFFICIENT_DATA`. Los reportes posteriores a `as_of` se excluyen para que un recálculo histórico conserve su resultado.
- **M4 Trazabilidad:** cada reporte tiene `event_id` y `source_id`; el resultado conserva `as_of` como `window_end` para repetir exactamente el cálculo.
- **M5 Verificación:** repetir recálculo con el mismo `--as-of`; G6 debe coincidir. Si se omite, la edad crecerá con el tiempo.

## Referencia y ventanas de confianza

La referencia es la media de las primeras hasta `window_size` observaciones puntuadas de una fuente y una identidad `(model_version, config_version, source_id)`. Se necesita al menos `minimum_observations`; si faltan, no se crea una referencia ficticia. Se guardan `reference_id`, hora de creación, identidad, cantidad, tamaño de ventana, media e IDs de los eventos usados. Es una referencia del **comportamiento de confidence**, nunca una estimación de accuracy.

Los eventos posteriores puntuados se agrupan en ventanas consecutivas no superpuestas de hasta `window_size`, incluso si pertenecen a corridas distintas de la misma identidad. Una ventana con menos de `minimum_observations` devuelve `INSUFFICIENT_DATA`. Con la configuración actual, una caída relativa de media `>= 0.20` respecto a la referencia durante dos ventanas válidas consecutivas produce `SUSTAINED_CONFIDENCE_CHANGE`. La primera caída devuelve `OBSERVING_CHANGE`; una ventana sin caída devuelve `NORMAL` y reinicia el contador. Cambiar modelo, configuración o fuente impide usar la referencia anterior; al cambiar reglas o umbrales debe aumentarse `config.version`. No se generan alertas.

## Recálculo y exportación

Desde la raíz de P6, después de generar una muestra real:

```powershell
python scripts/recalculate_metrics.py --source-id "local-image" --run-id "<run_id>" --as-of "<ISO-8601-UTC>" --export
```

El script consulta SQLite y no vuelve a ejecutar YOLOX. `--export` escribe `evidencias/metricas/observaciones.csv` y `evidencias/metricas/resultados.json` desde las filas persistidas. Si no existen datos, los indicadores usan `INSUFFICIENT_DATA`; el CSV contiene solo el encabezado.
