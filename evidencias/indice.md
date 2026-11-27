# Proyecto 6 — Índice de evidencias

Revisión auditada: `84fba5b6df8f1f3eb6157f94c7f0b3fd71363cf1` (`main`). Este índice usa rutas relativas a la raíz del repositorio. La evaluación técnica y las condiciones pendientes están en `evidencias/auditoria-final.md`. Los IDs de abajo son los **definitivos** indicados por `evidencias/escenarios/manifest.json`; las carpetas `runs/` son historial.

| Criterio | Estado | Evidencia principal |
| --- | --- | --- |
| R1 | COMPLETO | `README.md` §10–11; `config/model.yaml`; `modelo/README.md`; `scripts/test_inference.py` |
| R2 | COMPLETO | `docs/metrics.md`; `config/metrics.yaml`; `evidencias/metricas/resultados.json` |
| R3 | COMPLETO | `config/monitoring.yaml`; `src/monitoring/`; `evidencias/metricas/resultados.json` |
| R4 | COMPLETO | `src/events/`; `src/persistence/`; `docs/alerts.md`; `evidencias/escenarios/baja-confianza/` |
| R5 | COMPLETO | `config/alerts.yaml`; `src/alerts/`; `evidencias/escenarios/baja-confianza/alert.json` |
| R6 | PARCIAL | `evidencias/escenarios/normal/`; `evidencias/escenarios/baja-confianza/`; faltan capturas visuales manuales |
| R7 | PARCIAL | `README.md`; `REUSE.md`; `scripts/run_scenario.py`; reproducción en clon aislado aprobada con corrección aún sin commit |

## R1 — Fuente visual y modelo

| Subcriterio | Qué demuestra | Archivo(s) | ID/corrida | Comando de verificación | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| R1.1 Fuente | `--input` procesa una imagen; `--input-dir` procesa imágenes en orden. Captura selectiva configurable. | `README.md` §10 y §20; `scripts/run_monitoring_sample.py`; `config/capture.yaml` | Inputs C1/C2 en `evidencias/escenarios/` | `python scripts/run_monitoring_sample.py --help` | Opciones `--input`, `--input-dir`, `--source-id`; no cámara en vivo declarada como implementada. |
| R1.2 Inferencia real | YOLOX-Tiny produce detecciones, clases, cajas y scores desde los JPEG originales. | `src/inference/`; `evidencias/escenarios/normal/input/seq02-0001.jpg`; `evidencias/escenarios/baja-confianza/input/camara-nueva.jpg` | C1 `3f58257b-7de3-460b-8822-29e3eba3e77c`; C2 `558a9f31-57a3-4655-9b86-917a329d576c` | `python scripts/test_inference.py --input evidencias/escenarios/normal/input/seq02-0001.jpg` | C1 confidence `0.8417058511793911`, tres detecciones; sin mocks. |
| R1.3 Identidad y procedencia | Nombre, versión, tarea, 80 clases COCO, BGR/mediana/letterbox, ONNX Runtime CPU, origen, tamaño, descarga y SHA-256 verificado. | `config/model.yaml`; `modelo/README.md`; `REUSE.md`; `src/inference/weights.py`; `scripts/get_model.py` | Modelo `0.1.1rc0`; SHA-256 `427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` | `python scripts/get_model.py --verify-only` | Hash y tamaño coinciden antes de crear la sesión de inferencia. |

## R2 — Métricas G1–G7

Inventario: `config/metrics.yaml`. M1–M5 de cada fila están documentados en `docs/metrics.md`; el cálculo y la adquisición están en `src/metrics/`, y el resultado real de 128 frames en `evidencias/metricas/resultados.json` (corrida `a31662fc-7bc4-4778-a045-7a48cde6aa3a`). Las observaciones primarias están en `evidencias/metricas/observaciones.csv` y en SQLite durante la ejecución. **REC** es el comando de recálculo indicado bajo la tabla; aplica a cada fila sin ejecutar YOLOX.

| Grupo/métrica | M1 Definición y unidad | M2 Fuente primaria | M3 Fórmula | Exclusiones | Ventana | Archivo de evidencia | Comando | M1–M5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 `inference_time_ms` | Tiempo medio de `session.run`, ms/inferencia | Tiempos reales de `InferenceEngine` → `metric_observations` G1 | `AVG(inference_time_ms)` | Lectura, preprocesamiento y posprocesamiento; faltantes | Corrida `run_id` | `evidencias/metricas/resultados.json`; `observaciones.csv` | REC | Verificados |
| G2 `processing_fps` | Frames procesados por segundo | `processed_frame`, inicio y duración de `MetricsCollector` | `COUNT(processed_frame)/run_elapsed_seconds` | `MODEL_ERROR`; menos de 2 frames ⇒ `INSUFFICIENT_DATA` | Corrida desde inicio hasta fin | Mismos archivos | REC | Verificados |
| G3 `process_cpu_percent` | CPU media del proceso, %, puede exceder 100 en multinúcleo | `psutil.Process().cpu_percent()` → G3 | `AVG(process_cpu_percent)` | Sin muestras ⇒ `INSUFFICIENT_DATA`; 0 real es válido | Timestamps de la corrida | Mismos archivos; `docs/metrics.md` §G3 | REC | Verificados |
| G4 `low_confidence_ratio` | Proporción de eventos puntuados bajos | `frame_confidence` G4 + `events.confidence_zone` | `LOW_CONFIDENCE / scored_eligible` | `NO_DETECTION`, `MODEL_ERROR`, `MISSING_SCORE` sin score | Corrida | Mismos archivos; `events` SQLite | REC | Verificados |
| G5 `traceability_coverage` | Fracción de eventos completos | `traceability_complete` G5 + evento/detecciones | `SUM(complete)/COUNT(eligible)` | Sin eventos ⇒ `INSUFFICIENT_DATA` | Corrida | Mismos archivos; `events` y `detections` | REC | Verificados |
| G6 `last_report_age_seconds` | Edad del último reporte de fuente, segundos | `report_epoch_seconds` G6 + `as_of` | `as_of - MAX(timestamp <= as_of)` | Reportes posteriores a `as_of`; sin reporte ⇒ insuficiente | Último reporte → `as_of` | `resultados.json` conserva `as_of` | REC | Verificados |
| G7 `active_alerts` | Alertas activas de fuente, count | `alerts` SQLite | `COUNT(status=ACTIVE, timestamp<=as_of)` | Otras fuentes; cero es `OK` | Todas las corridas de fuente hasta `as_of` | `evidencias/alertas/alertas.json`; `resultados.json` | REC | Verificados |

**REC:**

```powershell
python scripts/recalculate_metrics.py --source-id batch-final --run-id a31662fc-7bc4-4778-a045-7a48cde6aa3a --as-of 2026-11-26T02:11:23.536701+00:00
```

Resultado esperado: G1 `19.6935992117`, G2 `21.0440661592`, G3 `783.41171875` (CPU del proceso multinúcleo), G4 `0.3913043478`, G5 `1.0`, G6 `0.1518168449`, G7 `45`; todos `OK`. G3 no representa CPU total del equipo limitada a 100%. Las métricas de calidad predictiva (accuracy, precision, recall, F1, IoU, mAP) no forman parte de G1–G7.

## R3 — Monitoreo de confidence

| Subcriterio | Qué demuestra | Archivo(s) | ID/corrida | Comando de verificación | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| R3.1 Umbrales | `lower=0.60`, `upper=0.80` configurables y validados; justificación operativa con 115 eventos puntuados y referencia real, sin atribuir accuracy. | `config/monitoring.yaml`; `README.md` §9 y §12; `evidencias/metricas/resultados.json` | Batch `a31662fc-7bc4-4778-a045-7a48cde6aa3a` | `python -m pytest tests/test_monitoring.py -q` | 45 bajos, 32 inciertos, 38 aceptados y 13 sin detección entre 128 frames. |
| R3.2 Estados | Zonas `LOW_CONFIDENCE`, `UNCERTAIN`, `ACCEPTED_BY_POLICY`; `NO_DETECTION` y `MODEL_ERROR` separados. Aceptación por política no equivale a predicción correcta. | `src/monitoring/confidence.py`; `src/events/builder.py`; `README.md` §12 | C1/C2 definitivos | `python -m pytest tests/test_monitoring.py tests/test_events_persistence.py -q` | Zonas calculadas con scores reales; ausencia de score no se fuerza a cero. |
| R3.3 Referencia y cambio | Media real de primeras observaciones elegibles, `window_size=20`, `minimum_observations=10`, estado insuficiente y dos caídas consecutivas para cambio sostenido; identidad por modelo/config/fuente. | `config/monitoring.yaml`; `src/monitoring/reference.py`; `docs/metrics.md`; `evidencias/metricas/resultados.json` | Referencia `d7ff261f-6133-4b6e-839c-e9de13b154c7`, media `0.6135873986`, muestra 20 | REC y `python -m pytest tests/test_reference.py -q` | Cinco ventanas reales `NORMAL`; lógica de cambio y `INSUFFICIENT_DATA` probada. No se afirma drift confirmado. |

## R4 — Eventos e imágenes

| Subcriterio | Qué demuestra | Archivo(s) | ID/corrida | Comando de verificación | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| R4.1 Evento persistido | UUID, UTC, fuente, versiones, estado, detecciones con cajas, confidence y zona; lectura desde SQLite y API. | `src/events/models.py`; `src/persistence/repositories.py`; `evidencias/escenarios/baja-confianza/event.json`; `portal_event.json` | C2 evento `558a9f31-57a3-4655-9b86-917a329d576c` | `python -m pytest tests/test_events_persistence.py tests/test_portal.py -q` | Evento y detecciones se recuperan; `GET /api/events/{event_id}` coincide. |
| R4.2 Captura vinculada | Captura selectiva sin TTL; `event.image_reference` resuelve a JPEG dentro de `data/captures/`; copia portátil de evidencia con SHA-256. | `config/capture.yaml`; `src/captures/`; `docs/alerts.md`; `evidencias/escenarios/baja-confianza/capturas/558a9f31-57a3-4655-9b86-917a329d576c.jpg` | C2 evento anterior; captura SHA-256 `09aad4e2427670b336b1acf3435931cd158e640a059a8f9d57ae52026671d5a3` | `python -m pytest tests/test_alerts_captures.py tests/test_portal.py -q` | Vínculo evento → captura resoluble; no se sirve una ruta ajena al directorio configurado. |

## R5 — Alertas

| Subcriterio | Qué demuestra | Archivo(s) | ID/corrida | Comando de verificación | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| R5.1 Regla | `LOW_CONFIDENCE_ALERT` evalúa eventos con score real y zona baja; configuración explícita `minimum_events=1`, `window_size=1`, severidad `WARNING`, motivo y acción. Datos insuficientes no crean alerta; cambio sostenido opcional desactivado. | `config/alerts.yaml`; `src/alerts/`; `docs/alerts.md` | C2 definitivo | `python -m pytest tests/test_alerts_captures.py -q` | No alerta para `NO_DETECTION`, error o evento aceptado; regla configurable. |
| R5.2 Persistencia y portal | UUID/UTC/status/fuente/evento, FK y unicidad `(rule_id,event_id)`; alerta → evento → imagen por API. | `src/persistence/database.py`; `src/persistence/alert_repository.py`; `evidencias/escenarios/baja-confianza/alert.json`; `portal_alert.json` | Alerta C2 `1a12681f-a90d-4adf-a2f1-fb0cfc00f291` | `python -m pytest tests/test_alerts_captures.py tests/test_portal.py -q` | Una alerta `ACTIVE`, sin duplicado y vinculada al evento C2. |
| R5.3 G7 cero | Ausencia de alertas activas consultables produce `value=0`, `status=OK`. | `docs/metrics.md` §G7; `evidencias/escenarios/normal/metrics.json`; `tests/test_alerts_captures.py` | C1 corrida `68d02f03-6c07-47a7-8d8a-c014d6ae44aa` | `python -m pytest tests/test_alerts_captures.py tests/test_scenarios.py -q` | G7 C1 = 0 `OK`; G7 C2 = 1 `OK`. |

## R6 — Demostraciones C1 y C2

La validación sin escribir en las evidencias definitivas es `python -m pytest tests/test_scenarios.py -q`. Para generar **nuevas** corridas, ejecutar los comandos siguientes únicamente en un clon aislado: el script reemplaza el puntero superior al último `run_id` y conserva corridas previas en `runs/`.

| Caso | Qué demuestra | Archivo(s) | ID/corrida definitiva | Comando en clon aislado | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| C1 | Input real P5 → YOLOX → evento → zona aceptada → G1–G7 → API. Confidence alta expresa política, no exactitud. | `evidencias/escenarios/normal/{input,manifest.json,result.json,event.json,metrics.json,portal_event.json,portal_alerts.json,config_snapshot}` | Evento `3f58257b-7de3-460b-8822-29e3eba3e77c`; corrida `68d02f03-6c07-47a7-8d8a-c014d6ae44aa` | `python scripts/run_scenario.py --scenario normal` | `0.8417058511793911`, `ACCEPTED_BY_POLICY`, sin alerta, G7=0. |
| C2 | Input real P4 → YOLOX → baja confianza → evento/captura → alerta → API. | `evidencias/escenarios/baja-confianza/{input,manifest.json,result.json,event.json,alert.json,metrics.json,portal_event.json,portal_alert.json,config_snapshot,capturas}` | Evento `558a9f31-57a3-4655-9b86-917a329d576c`; alerta `1a12681f-a90d-4adf-a2f1-fb0cfc00f291`; corrida `cd0c4669-cfa4-4d84-8014-ec6169af3de5` | `python scripts/run_scenario.py --scenario low-confidence` | `0.3968369795843003`, `LOW_CONFIDENCE`, una alerta e imagen resoluble, G7=1. |

`evidencias/escenarios/manifest.json` confirma el mismo modelo/SHA, `monitoring-v1`, thresholds `0.60/0.80`, configuración de alertas/capturas y hashes de YAML de ambos casos. Los JPEG originales y sus SHA-256 constan en cada manifiesto. Faltan las seis capturas visuales manuales detalladas en `evidencias/portal/CAPTURAS-PENDIENTES.md`.

## R7 — Git, instalación y reproducción

| Subcriterio | Qué demuestra | Archivo(s) | ID/corrida | Comando de verificación | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| R7.1 Autoría y reutilización | Entrega individual de Mauricio Figueroa; procedencia y adaptación de inferencia P5; componentes P6 propios. | `README.md` §3–6; `REUSE.md`; `modelo/README.md` | Revisión auditada `84fba5b` | Leer los tres documentos. | Frontera P5/P6 explícita; no se atribuye autoría de pesos públicos. |
| R7.2 Dependencias y modelo | Un venv nuevo instala `requirements-dev.txt`; `get_model.py` descarga pesos y verifica SHA-256. | `requirements.txt`; `requirements-dev.txt`; `scripts/get_model.py`; `config/model.yaml` | Clon temporal de la revisión auditada + corrección de YAML | `python scripts/get_model.py --verify-only` después de instalar | SHA-256 esperado, sin usar el modelo local del repositorio principal. |
| R7.3 Flujo desde cero | Inferencia, C1/C2, SQLite nuevo, recálculo, portal y pruebas. | `README.md` §8, §20–24; `scripts/`; `tests/` | Clon temporal; nuevas corridas separadas de IDs definitivos | `python scripts/test_inference.py --input evidencias/escenarios/normal/input/seq02-0001.jpg`; comandos C1/C2 anteriores; REC con el nuevo `source_id`/`run_id`; `python -m pytest -q` | SQLite se crea sin copiar la base local; `integrity_check=ok`, `foreign_key_check=0`; 68 tests pasan. |

En Windows, fijar `TEMP`/`TMP` en un directorio externo y usar **subdirectorios distintos** para `--basetemp` y `cache_dir`, según `README.md` §20. La reproducción de un clon limpio requiere la corrección de `scripts/run_scenario.py` y `tests/test_scenarios.py` presente en este árbol de trabajo; el commit auditado por sí solo falla al comparar YAML LF con CRLF. No se hizo commit ni push durante esta auditoría.
