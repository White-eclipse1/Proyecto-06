# Proyecto 6 · Centro de Monitoreo de Computer Vision

## Integración de Servicios de Aprendizaje Automático

**Autor:** Mauricio Figueroa  
**Tipo de entrega:** Individual  
**Proyecto:** Proyecto 6  
**Universidad:** ITESO  

**Estado actual:** inferencia real de P5, eventos y detecciones en SQLite, métricas G1–G7 recalculables, referencia de confianza, capturas selectivas, alertas persistentes y portal local de eventos y alertas implementados y probados. C1 → completed; C2 → completed con entradas reales, configuración fija y evidencia en [evidencias/escenarios/manifest.json](evidencias/escenarios/manifest.json). Stream en vivo y capturas visuales finales del portal siguen pendientes.

Reproducir las demostraciones desde los inputs copiados al repositorio:

```powershell
python scripts/run_scenario.py --scenario normal
python scripts/run_scenario.py --scenario low-confidence
```

---

## 1. Descripción

Este proyecto implementa un **centro de monitoreo para un sistema de Computer Vision**.

El sistema recibe una fuente visual, ejecuta inferencias reales utilizando un modelo de visión por computadora y registra información operativa que permite observar el comportamiento del servicio y del modelo.

El flujo principal es:

```text
Fuente visual
     ↓
Captura / muestreo
     ↓
Modelo de Computer Vision
     ↓
Predicción + confianza
     ↓
Sistema de monitoreo
 ├── Métricas
 ├── Clasificación de confianza
 ├── Eventos
 ├── Capturas
 └── Reglas de alerta
     ↓
Persistencia
     ↓
Portal de monitoreo
 ├── Eventos
 └── Alertas
```

El objetivo del proyecto **no es volver a evaluar la calidad predictiva del modelo**, sino monitorear su operación y conservar evidencia trazable de las inferencias, eventos, métricas y alertas generadas.

---

# 2. Objetivos

Los objetivos principales son:

- procesar una fuente visual como stream;
- ejecutar inferencias reales sobre los frames recibidos;
- monitorear métricas operativas del sistema;
- conservar la confianza producida por el modelo;
- clasificar los resultados en tres zonas de confianza;
- generar eventos trazables;
- conservar capturas relevantes;
- generar alertas mediante reglas configurables;
- consultar eventos y alertas desde un portal;
- demostrar los escenarios obligatorios:
  - C1 · Operación normal;
  - C2 · Baja confianza;
- conservar evidencia suficiente para reproducir y auditar los resultados.

---

# 3. Alcance

El proyecto utiliza una tarea de:

**Detección de objetos.**

Se reutilizan componentes desarrollados previamente para el Proyecto 5, principalmente:

- integración del modelo;
- procesamiento de imágenes;
- lógica de inferencia;
- clases y preprocesamiento asociados al modelo;
- componentes reutilizables del portal o backend.

El código específico de monitoreo, eventos, métricas, confianza, alertas, persistencia, escenarios y evidencias corresponde al desarrollo individual del Proyecto 6.

No forma parte del alcance base:

- volver a entrenar el modelo;
- calcular accuracy;
- precision;
- recall;
- F1;
- IoU;
- AP/mAP;
- crear nuevas anotaciones;
- demostrar calidad predictiva;
- utilizar obligatoriamente AWS;
- utilizar obligatoriamente GPU;
- desplegar obligatoriamente en nube.

---

# 4. Autoría y reutilización

## Autor

Mauricio Figueroa

Este proyecto corresponde a una **entrega individual**.

## Componentes reutilizados

Se reutilizan componentes del Proyecto 5 relacionados con la ejecución del modelo de Computer Vision.

La reutilización se limita principalmente a la infraestructura necesaria para producir inferencias reales.

El sistema de monitoreo desarrollado para P6 añade:

- instrumentación;
- métricas;
- eventos;
- clasificación de confianza;
- persistencia;
- capturas vinculadas;
- reglas de alerta;
- alertas persistentes;
- consultas desde portal;
- escenarios C1/C2;
- evidencia reproducible.

---

# 5. Arquitectura

```text
                    ┌─────────────────────┐
                    │    Fuente visual    │
                    │ cámara / video /    │
                    │ secuencia imágenes  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Capture / Stream    │
                    │ Sampling            │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Modelo CV           │
                    │ Inferencia real     │
                    └──────────┬──────────┘
                               │
                    prediction / confidence
                               │
                               ▼
                ┌─────────────────────────────┐
                │     Monitoring Pipeline     │
                │                             │
                │  G1-G7 Metrics              │
                │  Confidence Zones           │
                │  Event Generator            │
                │  Capture Policy             │
                │  Alert Rules                │
                └──────────────┬──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │   Persistencia   │
                     │ eventos/alertas  │
                     │ imágenes/métricas│
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │      Portal      │
                     │                  │
                     │ Eventos          │
                     │ Alertas          │
                     └──────────────────┘
```

---

# 6. Tecnologías

La implementación propuesta utiliza:

### Backend y monitoreo

- Python 3
- FastAPI
- OpenCV
- NumPy
- Pandas
- psutil
- SQLite

### Computer Vision

- Modelo reutilizado del Proyecto 5
- runtime correspondiente al artefacto utilizado

### Portal

- FastAPI
- HTML y CSS servidos localmente

### Evidencia

- JSON
- JSONL
- CSV
- imágenes conservadas
- capturas del portal

El proyecto no depende de una plataforma cloud específica para poder ser evaluado.

---

# 7. Estructura del repositorio

```text
Proyecto6/
│
├── README.md
│
├── requirements.txt
│
├── config/
│   ├── monitoring.yaml
│   ├── thresholds.yaml
│   └── alerts.yaml
│
├── modelo/
│   ├── README.md
│   └── [modelo o instrucciones de descarga]
│
├── src/
│   ├── inference/
│   ├── monitoring/
│   ├── events/
│   ├── alerts/
│   ├── persistence/
│   ├── scenarios/
│   └── portal/
│
├── data/
│   ├── captures/
│   └── monitoring.db
│
├── scripts/
│   ├── run_monitor.py
│   ├── run_scenario_c1.py
│   ├── run_scenario_c2.py
│   └── recalculate_metrics.py
│
└── evidencias/
    ├── indice.md
    │
    ├── metricas/
    │   ├── observaciones.csv
    │   └── resultados.json
    │
    ├── escenarios/
    │   ├── normal/
    │   └── baja-confianza/
    │
    ├── eventos/
    │
    ├── alertas/
    │
    ├── imagenes/
    │
    ├── portal/
    │
    └── extras/
```

Los nombres de archivos pueden variar durante la implementación, pero se conservará la misma separación lógica.

---

# 8. Instalación

## Requisitos

- Python 3.12 para las versiones fijadas del pipeline de inferencia
- Git

Clonar el repositorio:

```bash
git clone <URL_REPOSITORIO>
cd Proyecto6
```

Crear ambiente virtual:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Obtener y verificar los pesos públicos del modelo:

```powershell
python scripts/get_model.py
```

El portal se instala con `requirements.txt`; no necesita Node.js.

---

# 9. Configuración

La configuración de esta fase está en `config/monitoring.yaml`. Los umbrales son configurables y se validan al cargar (`0 <= lower_threshold < upper_threshold <= 1`). Las ventanas y la regla de cambio sostenido también se configuran allí.

Configuración inicial:

```yaml
config:
  version: monitoring-v1

confidence:
  lower_threshold: 0.60
  upper_threshold: 0.80

monitoring:
  window_size: 20
  minimum_observations: 10

source:
  default_id: local-image

sustained_change:
  enabled: true
  relative_drop: 0.20
  consecutive_windows: 2
```

Los valores `0.60` y `0.80` son la configuración inicial propuesta.

Antes de generar las evidencias finales de C1 y C2 se conservará la configuración utilizada y se documentará su justificación utilizando observaciones reales del modelo.

---

# 10. Fuente visual

El sistema admite una fuente visual funcional como stream.

La implementación puede utilizar:

- cámara del carrito del Proyecto 5;
- webcam;
- cámara externa;
- archivo de video;
- secuencia de imágenes.

La fuente utilizada en la entrega final será documentada mediante:

```text
source_id
source_type
sampling_policy
timestamp
configuration_version
```

Si se utiliza video o una secuencia de imágenes, los frames se suministran progresivamente utilizando una frecuencia o política de reproducción definida.

---

# 11. Modelo

El modelo se ejecuta realmente sobre las imágenes recibidas.

Información verificada del artefacto:

```text
Modelo: YOLOX-Tiny preentrenado en COCO
Versión: release 0.1.1rc0
Archivo: modelo/yolox_tiny.onnx (descarga local, excluida de Git)
SHA-256 local: 427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7
Runtime: onnxruntime 1.31.1, CPUExecutionProvider
Clases: 80 clases COCO, orden en src/inference/coco_classes.py
Preprocesamiento: BGR, mediana 3×3, letterbox 416×416 con relleno 114,
                  CHW float32, rango 0–255 sin normalización
Origen: Proyecto 5 / release YOLOX 0.1.1rc0 de Megvii-BaseDetection
```

El modelo puede encontrarse directamente en el repositorio o recuperarse siguiendo las instrucciones documentadas en:

```text
modelo/README.md
```

No se generan scores artificiales para demostrar los escenarios.

La procedencia completa está en [modelo/README.md](modelo/README.md), la configuración en [config/model.yaml](config/model.yaml) y los cambios respecto a P5 en [REUSE.md](REUSE.md).

---

# 12. Monitoreo de confianza

Cada inferencia conserva la confianza producida realmente por el modelo.

Se utilizan dos thresholds configurables:

```text
LOWER_THRESHOLD = 0.60
UPPER_THRESHOLD = 0.80
```

Las zonas se interpretan de la siguiente manera:

```text
score < LOWER_THRESHOLD
→ LOW_CONFIDENCE

LOWER_THRESHOLD <= score < UPPER_THRESHOLD
→ UNCERTAIN

score >= UPPER_THRESHOLD
→ ACCEPTED_BY_POLICY
```

`ACCEPTED_BY_POLICY` significa únicamente que la confianza satisface la política configurada.

No significa que la predicción sea necesariamente correcta.

Los siguientes estados se conservan independientemente:

```text
NO_DETECTION
MODEL_ERROR
INVALID_INPUT
MISSING_SCORE
INSUFFICIENT_DATA
```

La `confidence` a nivel de frame es la máxima entre las detecciones conservadas por el detector. Cada detección mantiene su score individual; solo se aplica el piso de salida `0.10` del detector, sin descartar detecciones por los umbrales de monitoreo. Un frame sin detecciones tiene `confidence=null` y `NO_DETECTION`, distinto de `LOW_CONFIDENCE`. `MODEL_ERROR` representa un fallo real del modelo sin score. `ACCEPTED_BY_POLICY` indica únicamente que se superó el umbral; no equivale a una predicción correcta. `INVALID_INPUT`, `MISSING_SCORE` e `INSUFFICIENT_DATA` siguen como estados previstos para fases posteriores.

---

# 13. Referencia y cambio sostenido

La referencia y la regla de ventanas están implementadas. La referencia se construye solo si existen al menos `minimum_observations` resultados puntuados reales de la misma fuente, versión de modelo y versión de configuración. Usa la media de hasta `window_size` confidences y guarda los IDs de los eventos de la muestra en SQLite. Describe comportamiento de confidence, no accuracy.

El sistema mantiene una referencia de confianza obtenida de una ejecución identificada.

La referencia conserva:

```text
reference_id
model_version
config_version
source_id
window_size
sample_count
mean_confidence
event_ids
created_at
```

La monitorización utiliza ventanas no superpuestas de resultados puntuados. Una caída relativa de al menos 20% en dos ventanas válidas consecutivas produce `SUSTAINED_CONFIDENCE_CHANGE`. Una sola caída produce `OBSERVING_CHANGE`; una ventana sin caída produce `NORMAL`. No se genera una alerta.

La regla final utilizada se encuentra versionada en:

```text
config/monitoring.yaml
```

Cuando no existe el mínimo de observaciones necesario, el sistema reporta:

```text
INSUFFICIENT_DATA
```

y no interpreta esa situación como operación normal.

---

# 14. Eventos

Cada ejecución correcta puede generar un evento con UUID v4, timestamp ISO-8601 UTC, fuente, versiones del modelo y configuración, zona, confianza máxima, tiempos por etapa, referencia de imagen y todas las detecciones (`class_id`, `class_name`, `confidence`, `bbox`). Un fallo de inferencia puede representarse como `MODEL_ERROR`, sin score ni detecciones. El evento y sus detecciones se guardan en una transacción en las tablas `events` y `detections`; se recuperan con `EventRepository.get_event(event_id)` y se enumeran con `list_events(limit=...)`. `Database.initialize()` crea las tablas automáticamente en `data/monitoring.db` o en la ruta indicada. Esa base local está excluida de Git.

Los eventos permiten relacionar:

```text
fuente
→ inferencia
→ resultado
→ confianza
→ configuración
→ imagen
→ alerta
```

Los eventos pueden consultarse desde el portal.

---

# 15. Política de conservación de imágenes

La política versionada está en `config/capture.yaml`; el directorio por defecto es `data/captures/` y puede configurarse. Las imágenes se nombran con el UUID del evento y se guardan sin sobrescribir archivos existentes. `event.image_reference` apunta al archivo real y se verifica antes de persistir una alerta.

No se conserva obligatoriamente cada frame.

Las capturas se guardan principalmente cuando ocurre alguno de estos casos:

- baja confianza;
- generación de alerta;
- escenario C1;
- escenario C2;
- muestra representativa de operación normal.

Cada imagen se vincula con su evento mediante un identificador o referencia resoluble.

La muestra normal conserva cada vigésimo evento `ACCEPTED_BY_POLICY`, según `normal_sample_every`. Las capturas por evidencia de escenario se solicitan explícitamente. **No automatic expiration is configured**: las capturas no tienen TTL ni eliminación programada.

---

# 16. Alertas

La regla `LOW_CONFIDENCE_ALERT` está definida en `config/alerts.yaml`: una detección con score real y zona `LOW_CONFIDENCE` crea una alerta `ACTIVE` de severidad `WARNING`. La configuración declara `minimum_events=1` y `window_size=1`; si se eleva el mínimo y faltan observaciones, devuelve `INSUFFICIENT_DATA`. `NO_DETECTION` y `MODEL_ERROR` no activan esta regla. La regla opcional basada en `SUSTAINED_CONFIDENCE_CHANGE` está desactivada por defecto.

Cada alerta tiene UUID, timestamp UTC, regla, severidad (`INFO`, `WARNING` o `CRITICAL`), motivo, acción sugerida, estado (`ACTIVE` o `RESOLVED`), fuente, versión de configuración y referencia al evento o ventana. SQLite impide duplicados de la misma regla y evento. La inserción de la alerta y la actualización de `image_reference` comparten una transacción. Las alertas se consultan mediante `AlertRepository` y el portal local. La política y exportación están detalladas en [docs/alerts.md](docs/alerts.md).

---

# 17. Portal

El portal incluye como funcionalidad base dos consultas:

## Eventos

Permite visualizar eventos generados por el pipeline de monitoreo.

Información mostrada:

- ID;
- fecha/hora;
- fuente;
- modelo;
- estado;
- predicción;
- confianza;
- zona;
- referencia de imagen.

## Alertas

Permite consultar las alertas persistidas.

Información mostrada:

- ID;
- fecha/hora;
- regla;
- severidad;
- motivo;
- acción sugerida;
- evento relacionado.

---

# 18. Métricas G1–G7

Para cada grupo aplicable se designa una métrica base.

G1–G6 se calculan desde `metric_observations`, `events` y `detections` de SQLite. G7 cuenta alertas `ACTIVE` desde `alerts`, con cero como valor válido. Las definiciones M1–M5 y comandos de verificación están en [docs/metrics.md](docs/metrics.md). [config/metrics.yaml](config/metrics.yaml) conserva el inventario G1–G7.

Cada métrica incluye:

- definición;
- unidad;
- fórmula;
- población;
- ventana;
- exclusiones;
- método de adquisición;
- observaciones primarias;
- cálculo;
- trazabilidad;
- procedimiento para recalcular una muestra.

## G1 · Salud y rendimiento

### Métrica base: Tiempo de inferencia

Mide el tiempo empleado exclusivamente en la ejecución del modelo.

```text
inference_time_ms =
inference_end - inference_start
```

Unidad:

```text
ms / inferencia
```

---

## G2 · Captura y procesamiento del stream

### Métrica base: FPS de procesamiento

Mide la cantidad de frames que completan inferencia durante una ventana.

```text
processing_fps =
processed_frames / elapsed_seconds
```

Unidad:

```text
frames / segundo
```

---

## G3 · Uso de recursos

### Métrica base: Uso de CPU del proceso

Mide la utilización de CPU asociada al proceso de monitoreo durante las observaciones.

Unidad:

```text
%
```

Instrumentación:

```text
psutil
```

---

## G4 · Comportamiento de las predicciones

### Métrica base: Proporción de baja confianza

Mide la proporción de resultados puntuados cuya confianza se encuentra por debajo del threshold inferior.

```text
low_confidence_ratio =
low_confidence_results / eligible_scored_results
```

Los frames sin score no se incluyen silenciosamente en el denominador y se registran mediante un estado independiente.

---

## G5 · Datos y trazabilidad

### Métrica base: Cobertura de trazabilidad

Mide la proporción de eventos que contienen los campos y referencias necesarias para reconstruir su recorrido.

```text
traceability_coverage =
complete_traceable_events / eligible_events
```

---

## G6 · Fuentes y versiones

### Métrica base: Tiempo desde el último reporte

Mide la antigüedad del evento más reciente producido por la fuente.

```text
last_report_age_seconds =
current_time - latest_event_timestamp
```

Unidad:

```text
segundos
```

---

## G7 · Alertas

### Métrica base: Alertas activas

Mide la cantidad de alertas que permanecen activas durante la consulta o ventana definida.

```text
active_alerts =
count(alert.status == ACTIVE)
```

Si no hay alertas activas y SQLite se consultó correctamente, G7 devuelve `0` con estado `OK`.

---

# 19. Recalcular métricas

Las observaciones primarias se conservan en `metric_observations` de SQLite, vinculadas con `event_id`, `source_id` y `run_id`. El siguiente comando recalcula sin ejecutar YOLOX:

```powershell
python scripts/recalculate_metrics.py --source-id "local-image" --run-id "<run_id>" --as-of "<ISO-8601-UTC>" --export
```

`--as-of` fija el instante de G6 para repetir el resultado; sin él, la edad del último reporte cambia con el tiempo. Con datos insuficientes se devuelve `value=null` y `INSUFFICIENT_DATA`. `--export` escribe datos reales de SQLite en:

```text
evidencias/metricas/resultados.json
evidencias/metricas/observaciones.csv
```

También exporta `evidencias/alertas/alertas.json` con alertas existentes. G7 se recalcula desde la tabla `alerts` sin ejecutar YOLOX.

---

# 20. Ejecución

## Inferencia real disponible

Desde la raíz del repositorio, con una imagen propia o la imagen de prueba utilizada en la validación:

```powershell
python scripts/test_inference.py --input "ruta\imagen.jpg"
```

El JSON incluye `detections` con clase, confianza y caja, `confidence` máxima real (o `null` sin detecciones), `inference_time_ms` para la llamada al modelo y tiempos separados de lectura y procesamiento. También se puede usar `InferenceEngine.from_config("config/model.yaml").predict(frame)` con un frame BGR `uint8`. El script devuelve código distinto de cero ante cualquier fallo.

## Evento y SQLite disponibles

```powershell
python scripts/test_event_pipeline.py --input "ruta\imagen.jpg"
```

La salida JSON presenta el evento leído de SQLite y `persisted=true` solo si coincide con el generado. Puede usarse otra ruta con `--database` y otra fuente con `--source-id`. Para ejecutar las pruebas: `python -m pytest -q --basetemp=.pytest-tmp` tras instalar `requirements-dev.txt`.

## Muestra real de monitoreo disponible

```powershell
python scripts/run_monitoring_sample.py --input-dir "ruta\imagenes" --source-id "local-image" --export
```

Se aceptan varias imágenes con `--input` repetido. El script aplica capturas selectivas y reglas de alerta, genera observaciones primarias, calcula G1–G7 y devuelve la referencia y el estado de sus ventanas. `--export` guarda CSV y JSON de evidencia desde SQLite.

## Capturas y alertas disponibles

```powershell
python scripts/test_alert_pipeline.py --input "ruta\imagen.jpg" --source-id "alert-demo" --export
```

El JSON confirma evento, captura resoluble, alerta recuperada y G7. Una imagen que no cumpla la regla devuelve `alert_created=false` con código de salida `0`. `--export` copia una muestra vinculada a `evidencias/eventos/` y `evidencias/imagenes/`.

## Iniciar portal local

```powershell
python scripts/run_portal.py
```

Abrir `http://127.0.0.1:8000/events` para eventos y `http://127.0.0.1:8000/alerts` para alertas. Las páginas de detalle enlazan alerta → evento → captura cuando existe. La API de solo lectura ofrece `GET /api/events`, `GET /api/events/{event_id}`, `GET /api/alerts` y `GET /api/alerts/{alert_id}`; las listas aceptan `limit` y `offset`. `--database` y `--captures-dir` permiten elegir una base y capturas locales distintas. El portal no ejecuta inferencia ni escribe registros; requiere una base SQLite ya generada.

El comando siguiente corresponde a una etapa futura del proyecto:

## Ejecutar pipeline de monitoreo

```bash
python scripts/run_monitor.py
```

---

# 21. Escenarios obligatorios

## C1 · Operación normal

### Objetivo

Demostrar funcionamiento normal del pipeline utilizando inferencias reales.

### Flujo

```text
Fuente visual
→ inferencia real
→ confidence zone
→ métricas
→ evento
→ persistencia
→ portal
```

### Ejecutar

```bash
python scripts/run_scenario_c1.py
```

### Evidencia

```text
evidencias/escenarios/normal/
```

Debe conservar:

- entrada o captura;
- configuración;
- versión del modelo;
- inferencias;
- eventos;
- métricas;
- imágenes seleccionadas;
- consulta del portal.

---

# 22. C2 · Baja confianza

### Objetivo

Demostrar que una inferencia real de baja confianza activa correctamente la política de monitoreo.

Las puntuaciones **no se modifican ni inyectan artificialmente**.

Se utilizan imágenes o condiciones visuales que producen naturalmente puntuaciones bajas, por ejemplo:

- iluminación reducida;
- oclusión;
- cambio de distancia;
- cambio de orientación;
- escena difícil;
- secuencia previamente seleccionada.

### Flujo

```text
Imagen difícil
→ modelo real
→ score bajo
→ LOW_CONFIDENCE
→ evento
→ captura
→ regla de alerta
→ alerta persistida
→ portal
```

### Ejecutar

```bash
python scripts/run_scenario_c2.py
```

### Evidencia

```text
evidencias/escenarios/baja-confianza/
```

Debe conservar:

- entrada;
- salida real del modelo;
- confidence;
- thresholds;
- configuración;
- evento;
- captura vinculada;
- alerta;
- consulta en portal.

---

# 23. Evidencias

El índice principal se encuentra en:

```text
evidencias/indice.md
```

Este archivo relaciona los criterios de evaluación con:

- rutas;
- IDs;
- comandos;
- configuración;
- resultados;
- revisión Git;
- evidencia visual.

Estructura:

```text
evidencias/
├── indice.md
├── metricas/
├── escenarios/
│   ├── normal/
│   └── baja-confianza/
├── eventos/
├── alertas/
├── imagenes/
├── portal/
└── extras/
```

---

# 24. Revisión Git

Versión utilizada para la evidencia final
