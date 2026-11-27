# Modelo de inferencia

| Dato | Valor verificado |
|---|---|
| Nombre | YOLOX-Tiny, preentrenado en COCO |
| Versión | Release `0.1.1rc0` de Megvii-BaseDetection/YOLOX |
| Tarea | Detección de objetos |
| Clases | 80 clases COCO, en el orden de `src/inference/coco_classes.py` |
| Pesos | `yolox_tiny.onnx`, 20 219 662 bytes |
| SHA-256 local | `427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7` |
| Runtime | ONNX Runtime `1.31.1`, `CPUExecutionProvider` |
| Entrada/salida | `1×3×416×416` float32 / `1×3549×85` float32 |

El SHA-256 se calculó de la copia descargada en P6 y coincide con el valor registrado en `Proyecto5/src/p5/detector/weights.py`. El archivo no está versionado en Git.

## Procedencia y obtención

Repositorio P5 consultado, sin modificar: `Equipo03-Proyecto05`. Las rutas `Proyecto5/...` de esta sección son relativas a su raíz.

En P5, la ruta de ejecución prevista era `Proyecto5/models/yolox_tiny.onnx`; ese archivo no estaba presente en la copia local inspeccionada. P5 documenta el release y el hash en `Proyecto5/docs/A1-02_PROCEDENCIA.md`, y define la descarga verificada en `Proyecto5/src/p5/detector/weights.py`.

Origen de los pesos: [release oficial de YOLOX 0.1.1rc0](https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_tiny.onnx). Desde la raíz de P6:

```powershell
python scripts/get_model.py
python scripts/get_model.py --verify-only
```

El script guarda los pesos en `modelo/yolox_tiny.onnx` y verifica tamaño y SHA-256 antes de utilizarlos. La descarga se hace a un archivo temporal y solo se coloca en la ruta final si coincide. Después se puede inferir sin red.

## Preprocesamiento

Decodificar como BGR, filtro de mediana 3×3, redimensionar sin deformar con interpolación lineal hasta 416×416, rellenar abajo y a la derecha con 114, convertir de HWC a CHW y float32 sin normalizar (píxeles 0–255). Esta configuración reproduce `Proyecto5/src/p5/detector/yolox.py` y está en `config/model.yaml`.

El posprocesamiento decodifica las mallas de stride 8, 16 y 32, calcula `objectness × probabilidad de clase`, filtra scores mayores a 0.10 y aplica NMS sin distinguir clases con umbral 0.45. Las cajas `bbox` están en formato `xyxy` y píxeles de la imagen original. Si no hay detecciones, `confidence` es `null`.

## Componentes reutilizados

`src/inference/coco_classes.py` y `src/inference/weights.py` son copias adaptadas de P5. `src/inference/preprocessing.py`, `src/inference/inference.py`, `src/inference/model_loader.py` y `src/inference/types.py` adaptan el pipeline de `Proyecto5/src/p5/detector/yolox.py` y `models.py`. El detalle de cada ruta está en [REUSE.md](../REUSE.md).
