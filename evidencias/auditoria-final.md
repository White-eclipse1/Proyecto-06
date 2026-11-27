# Proyecto 6 — Auditoría final de requisitos base

Fecha de cierre: 27 de noviembre de 2026. Revisión auditada inicialmente: `84fba5b6df8f1f3eb6157f94c7f0b3fd71363cf1`. Commit actual, que ya incluye la corrección LF/CRLF: `f356c05668f94d74785a34c92282b72cb3c733ec` (`main`). Las cinco capturas y los ajustes documentales de cierre están en el árbol de trabajo, aún sin commit. Esta es una **autoevaluación técnica y no una calificación oficial**. No se asignan puntos por extras.

| Criterio | Estimación | Estado | Fundamento |
| --- | ---: | --- | --- |
| R1 Fuente visual y modelo | 15/15 | COMPLETO | Imágenes reales incluidas; YOLOX-Tiny ONNX, preprocessing, clases, runtime, procedencia y SHA documentados. |
| R2 Métricas G1–G7 | 25/25 | COMPLETO | M1–M5, fuente primaria, exclusiones, ventanas, resultados y recálculo documentados para los siete grupos. |
| R3 Confidence monitoring | 15/15 | COMPLETO | Umbrales 0.60/0.80, estados separados, referencia real y lógica de cambio sostenido. |
| R4 Eventos e imágenes | 15/15 | COMPLETO | Evento, detecciones, SQLite, API y captura selectiva C2 con archivo real y hash. |
| R5 Alertas | 15/15 | COMPLETO | Regla, persistencia, estado, enlace al evento e imagen, deduplicación y G7=0 válido. |
| R6 C1 y C2 | 10/10 | COMPLETO | Las corridas definitivas y las seis vistas manuales están documentadas en cinco PNG del árbol actual; el detalle C2 incluye la imagen. |
| R7 Git y reproducción | 5/5 | COMPLETO | Instalación y pruebas en clon aislado correctas; la corrección LF/CRLF ya está versionada en `f356c05`. |
| **Total base estimado** | **100/100** | | |

**Total base técnico estimado: 100/100.** El mapa de cada subcriterio, comando e ID se encuentra en `evidencias/indice.md`. La estimación se refiere al **árbol de trabajo actual**: las cinco capturas recién añadidas deben incluirse al versionar la entrega.

## Evidencia técnica revisada

- **R1:** `config/model.yaml`, `modelo/README.md`, `REUSE.md`, `src/inference/` y `scripts/test_inference.py` identifican YOLOX-Tiny `0.1.1rc0`, detección de objetos COCO-80, entrada 416×416, BGR/median/letterbox, ONNX Runtime CPU, descarga pública y validación SHA-256. El input C1 interno produjo tres detecciones y confidence `0.8417058511793911`. La fuente implementada es imagen o secuencia de imágenes; la cámara en vivo sigue pendiente y no se cuenta como implementada.
- **R2:** `config/metrics.yaml`, `docs/metrics.md`, `src/metrics/`, `scripts/recalculate_metrics.py`, `evidencias/metricas/observaciones.csv` y `resultados.json` contienen G1–G7. La corrida real `a31662fc-7bc4-4778-a045-7a48cde6aa3a` procesó 128 frames. Sus valores son G1 `19.693599211677792`, G2 `21.044066159249688`, G3 `783.41171875`, G4 `0.391304347826087`, G5 `1.0`, G6 `0.15181684494018555`, G7 `45`, todos `OK`. G3 usa CPU **del proceso** y puede superar 100% en varios núcleos; no representa el porcentaje total del equipo. No se evalúan accuracy, precision, recall, F1, IoU ni mAP.
- **R3:** Los límites 0.60/0.80 son una política operativa. Entre 128 frames reales hubo 45 `LOW_CONFIDENCE`, 32 `UNCERTAIN`, 38 `ACCEPTED_BY_POLICY` y 13 `NO_DETECTION`; 115 tuvieron score. La referencia `d7ff261f-6133-4b6e-839c-e9de13b154c7` usa 20 observaciones y media `0.6135873986254348`. `window_size=20`, `minimum_observations=10`, dos ventanas consecutivas y caída relativa de 20% están configurados. Cinco ventanas observadas fueron `NORMAL`; no se afirma un cambio sostenido real. `ACCEPTED_BY_POLICY` no significa predicción correcta.
- **R4–R5:** El evento C2 `558a9f31-57a3-4655-9b86-917a329d576c` conserva modelo, configuración, fuente, timestamp, detecciones, confidence y zona. Su imagen de evidencia `evidencias/escenarios/baja-confianza/capturas/558a9f31-57a3-4655-9b86-917a329d576c.jpg` existe y tiene SHA-256 `09aad4e2427670b336b1acf3435931cd158e640a059a8f9d57ae52026671d5a3`. `evidencias/portal/03-lista-eventos.png`, `01-detalle-c1.png` y `02-detalle-c2-con-imagen.png` muestran eventos y la imagen vinculada. La alerta real `1a12681f-a90d-4adf-a2f1-fb0cfc00f291` usa `LOW_CONFIDENCE_ALERT`, `WARNING`, `ACTIVE`, reason y suggested_action; `04-lista-alertas.png` y `05-detalle-alerta-c2.png` muestran lista, detalle y enlace al evento e imagen. `docs/alerts.md` documenta que no hay expiración automática. En C1, G7=0 tiene estado `OK`.
- **R6:** `evidencias/escenarios/manifest.json` marca C1 corrida `68d02f03-6c07-47a7-8d8a-c014d6ae44aa`, evento `3f58257b-7de3-460b-8822-29e3eba3e77c`, confidence `0.8417058511793911`, `ACCEPTED_BY_POLICY`, cero alertas; y C2 corrida `cd0c4669-cfa4-4d84-8014-ec6169af3de5`, evento y alerta arriba, confidence `0.3968369795843003`, `LOW_CONFIDENCE`, una alerta. El manifiesto confirma mismo modelo, SHA, versión `monitoring-v1` y thresholds 0.60/0.80. Las corridas bajo `runs/` son historial y no reemplazan estos IDs definitivos. Los cinco PNG `01`–`05` en `evidencias/portal/` muestran las seis vistas solicitadas; `02-detalle-c2-con-imagen.png` cubre detalle e imagen C2. Archivos, URLs, IDs y hashes están en `evidencias/portal/CAPTURAS-PENDIENTES.md`.
- **R7:** `README.md` incluye instalación, descarga del modelo, inferencia, eventos, monitoreo, métricas, alertas, portal, C1/C2 y pruebas. `REUSE.md` atribuye la reutilización P5 y el trabajo individual de P6 a Mauricio Figueroa. `requirements.txt` y `requirements-dev.txt` se instalaron desde cero en el clon temporal.

## Reproducción aislada e integridad

Se creó un **clon limpio del commit actual `f356c05`**, con `.venv` nuevo y sin copiar la base SQLite ni los pesos del repositorio principal. `requirements-dev.txt` instaló 30 paquetes. `python scripts/get_model.py` descargó los pesos y verificó el SHA-256 **`427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7`**. `scripts/test_inference.py` con el JPEG interno de C1 produjo tres detecciones y confidence `0.8417058511793911`. `run_scenario.py --scenario normal` y `--scenario low-confidence` crearon nuevas corridas aisladas: C1 aceptado sin alerta y C2 bajo con captura y una alerta. El recálculo de G1–G7 con los nuevos `source_id`/`run_id`/`as_of` coincidió con ambos reportes, incluido G7=0 y G7=1. La base `data/monitoring.db` no existía antes y se creó automáticamente con el esquema. El portal iniciado en ese clon respondió HTTP 200 para `/events`, `/alerts`, ambos detalles de evento y el detalle de alerta C2.

El commit inicial `84fba5b` fallaba en Windows al comparar hashes YAML LF/CRLF. La corrección de `scripts/run_scenario.py` y `tests/test_scenarios.py` está **versionada en `f356c05`** y pasó esta reproducción limpia sin copiar archivos corregidos al clon. Normaliza saltos de línea solo al calcular el hash de configuración; conserva hash binario estricto para modelo, inputs y capturas y no altera los IDs definitivos.

Suite completa en el repositorio principal, con `TEMP`/`TMP` externos y subdirectorios distintos para `--basetemp` y `cache_dir`: **68 passed, 0 failed, 0 errors, 1 warning, 4.55 s**. Suite completa en el clon limpio: **68 passed, 0 failed, 0 errors, 1 warning, 4.34 s**. El aviso de ambas fue `StarletteDeprecationWarning` de `fastapi.testclient`/`httpx`. La base SQLite del clon y la del repositorio principal dieron `PRAGMA integrity_check = ok` y `PRAGMA foreign_key_check = 0 errors`. La prueba aislada no sobrescribió las evidencias definitivas.

## Rutas, secretos y dependencias

Una búsqueda de rutas personales entre archivos versionables encontró solo `evidencias/eventos/82a603bd-6b84-4a8e-8edb-3c563f185f9e.json`: su `original_image_reference` es una ruta histórica/documental de P5. No es comando obligatorio de reproducción; el `image_reference` exportado es relativo. No quedaron rutas personales en los comandos de instalación o ejecución.

La búsqueda por nombres/patrones de `.env`, API key, token, password, secret y credential no encontró credenciales versionadas; `tests/test_portal.py` contiene únicamente una ruta `/.env` usada para verificar el rechazo HTTP. No se detectaron dependencias faltantes tras la instalación limpia. La inspección por patrones no sustituye una herramienta especializada de detección de secretos.

## Bloqueantes para 100 base

No se identificaron bloqueantes técnicos para la cobertura de los 100 puntos base.

**Pendiente de entrega:** incluir los cinco PNG y la documentación actualizada al versionar el repositorio. No se hizo commit ni push durante este cierre.

## No bloqueantes / mejoras

- El stream de cámara o video en vivo no está implementado. La fuente reproducible de este proyecto es imagen o secuencia de imágenes, documentada como tal.
- La única warning de la suite es `StarletteDeprecationWarning` en la integración de prueba FastAPI/httpx; no hubo fallos.
- Git puede avisar que convertirá LF a CRLF en archivos de texto al volver a tocarlos; la corrección de hashes YAML ya está versionada y la reproducción limpia pasó. `uv` también avisó que copió paquetes cuando no pudo crear enlaces físicos en la caché; la instalación terminó correctamente.
- El `original_image_reference` absoluto en un JSON histórico puede conservarse como procedencia, siempre que no se use como requisito de ejecución.
