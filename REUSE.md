# Reutilización desde Proyecto 5

Origen consultado en modo de solo lectura: el repositorio `Equipo03-Proyecto05` de P5. Las rutas de origen de la tabla son relativas a su raíz.

| Componente | Ruta original P5 | Ruta destino P6 | Cambios |
|---|---|---|---|
| Identidad y descarga verificada de pesos | `Proyecto5/src/p5/detector/weights.py` | `src/inference/weights.py`, `scripts/get_model.py` | Se cambió la ruta por defecto a `modelo/yolox_tiny.onnx`; el script de P6 llama la misma verificación. |
| Clases COCO | `Proyecto5/src/p5/detector/coco_classes.py` | `src/inference/coco_classes.py` | Copia íntegra; conserva el orden de los 80 índices de salida. |
| Model loader | `Proyecto5/src/p5/detector/yolox.py` (`from_weights`) | `src/inference/model_loader.py` | Separado; verifica hash y tamaño antes de crear la sesión ONNX de CPU. |
| Preprocessing y lectura | `Proyecto5/src/p5/detector/yolox.py` (`read_image`, `preprocess`, `_preprocess`) | `src/inference/preprocessing.py` | Separado; conserva BGR, mediana 3×3, letterbox, CHW float32. Añade validación explícita de frame. |
| Inference y postprocessing | `Proyecto5/src/p5/detector/yolox.py` (`_infer`, `_decode`, `_nms`, `_postprocess`) | `src/inference/inference.py` | Adaptado a `InferenceEngine.predict(frame)`; añade tiempos por etapa, timestamp, versión y `class_id`. Conserva el cálculo de scores y cajas. |
| Tipos de detección | `Proyecto5/src/p5/detector/models.py` | `src/inference/types.py` | Adaptado al JSON de P6: `class_id`, `class_name`, `confidence`, `bbox`. |
| Comando de prueba | `Proyecto5/src/p5/detector/__main__.py` | `scripts/test_inference.py` | Nuevo script con `--input`, lectura, JSON y código de error. |
| Configuración de modelo | `Proyecto5/docs/A1-02_PROCEDENCIA.md`, `Proyecto5/docs/A1-01_DETECTOR.md`, `Proyecto5/src/p5/detector/yolox.py` | `config/model.yaml`, `modelo/README.md` | Datos verificados y ruta de pesos de P6. |
| Dependencias de inferencia | `Proyecto5/pyproject.toml`, `Proyecto5/requirements.lock.txt` | `requirements.txt` | Solo NumPy, ONNX Runtime, OpenCV headless y PyYAML; se excluyen dependencias de política y pruebas. |

El archivo ONNX no estaba presente en la copia local de P5. P6 lo obtuvo del release de YOLOX indicado por P5 y verificó su SHA-256. No se copiaron datasets completos, políticas, casos, métricas, benchmark, control del carrito, portal ni infraestructura cloud. Dos imágenes originales seleccionadas para C1/C2 se conservan en `evidencias/escenarios/` con procedencia y SHA-256; no se alteraron.

Código nuevo de P6: la interfaz `predict(frame)`, el JSON con `inference_time_ms`, el script de prueba, la configuración local y esta documentación. La salida de una imagen de prueba coincidió exactamente con la del `YoloxDetector` original de P5 usando los mismos pesos y dependencias.
