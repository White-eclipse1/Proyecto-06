# Proyecto 6 · Centro de Monitoreo de Computer Vision

## Integración de Servicios de Aprendizaje Automático

**Autor:** Mauricio Figueroa  
**Tipo de entrega:** Individual  
**Proyecto:** Proyecto 6  
**Universidad:** ITESO  

**Estado actual:** base de inferencia real de P5 integrada y probada. Las secciones de monitoreo, métricas G1–G7, eventos, alertas, portal y escenarios C1/C2 describen el alcance futuro; aún no están implementadas ni validadas.

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

- React
- JavaScript / TypeScript

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
- Node.js 18 o superior
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

Para el portal:

```bash
cd src/portal
npm install
```

---

# 9. Configuración

La configuración del monitoreo se mantiene fuera del código.

Ejemplo:

```yaml
source:
  type: camera
  sampling_interval_ms: 500

model:
  version: "P6-model"
  confidence_output_floor: 0.10

confidence:
  lower_threshold: 0.60
  upper_threshold: 0.80

monitoring:
  window_size: 20
  minimum_observations: 10

alerts:
  low_confidence:
    enabled: true
    severity: warning
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

---

# 13. Referencia y cambio sostenido

El sistema mantiene una referencia de confianza obtenida de una ejecución identificada.

La referencia conserva:

```text
model_version
configuration_version
source
window
sample_count
confidence observations
timestamp
```

La monitorización utiliza ventanas de observaciones para identificar cambios sostenidos.

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

Cada observación relevante genera un evento persistente.

Ejemplo conceptual:

```json
{
  "event_id": "evt-001",
  "timestamp": "2026-11-25T12:00:00Z",
  "source_id": "camera-01",
  "model_version": "model-v1",
  "config_version": "config-v1",
  "state": "LOW_CONFIDENCE",
  "prediction": "person",
  "confidence": 0.54,
  "confidence_zone": "LOW_CONFIDENCE",
  "image_reference": "data/captures/evt-001.jpg"
}
```

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

No se conserva obligatoriamente cada frame.

Las capturas se guardan principalmente cuando ocurre alguno de estos casos:

- baja confianza;
- generación de alerta;
- escenario C1;
- escenario C2;
- muestra representativa de operación normal.

Cada imagen se vincula con su evento mediante un identificador o referencia resoluble.

Las capturas utilizadas como evidencia **no tienen expiración automática**.

---

# 16. Alertas

Las alertas se generan utilizando reglas explícitas.

Ejemplo:

```text
Regla:
LOW_CONFIDENCE

Condición:
confidence < lower_threshold

Datos mínimos:
inferencias reales del modelo

Severidad:
WARNING

Acción sugerida:
Revisar la captura y las condiciones de la fuente visual.
```

Una alerta conserva al menos:

```json
{
  "alert_id": "alert-001",
  "timestamp": "2026-11-25T12:00:00Z",
  "rule_id": "low-confidence",
  "severity": "warning",
  "reason": "Confidence below configured lower threshold",
  "suggested_action": "Review capture and visual conditions",
  "event_id": "evt-001"
}
```

Las alertas se almacenan y pueden consultarse desde el portal.

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
last_report_age =
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

---

# 19. Recalcular métricas

Las observaciones primarias se conservan en:

```text
evidencias/metricas/
```

Para recalcular una muestra:

```bash
python scripts/recalculate_metrics.py
```

El script genera resultados reproducibles a partir de los datos almacenados.

Los resultados finales se almacenan en formato estructurado, por ejemplo:

```text
evidencias/metricas/resultados.json
evidencias/metricas/observaciones.csv
```

---

# 20. Ejecución

## Inferencia real disponible

Desde la raíz del repositorio, con una imagen propia o la imagen de prueba utilizada en la validación:

```powershell
python scripts/test_inference.py --input "C:\Users\mafig\OneDrive - ITESO\Desktop\mlops\proyecto2\Equipo03-Proyecto05\Proyecto4\evidencias\EDGE-01\camara-nueva.jpg"
```

El JSON incluye `detections` con clase, confianza y caja, `confidence` máxima real (o `null` sin detecciones), `inference_time_ms` para la llamada al modelo y tiempos separados de lectura y procesamiento. También se puede usar `InferenceEngine.from_config("config/model.yaml").predict(frame)` con un frame BGR `uint8`. El script devuelve código distinto de cero ante cualquier fallo.

Los comandos siguientes corresponden a etapas futuras del proyecto y todavía no se pueden ejecutar:

## Iniciar backend

```bash
uvicorn src.main:app --reload
```

## Iniciar portal

```bash
cd src/portal
npm run dev
```

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
