"""Preprocesamiento adaptado de Proyecto5/src/p5/detector/yolox.py."""

from pathlib import Path

import cv2
import numpy as np


def read_image(path: str | Path) -> np.ndarray:
    """Lee rutas Unicode en Windows y decodifica una imagen BGR."""
    try:
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    except (OSError, cv2.error) as error:
        raise ValueError(f"no se pudo leer la imagen {path}: {error}") from error
    if image is None:
        raise ValueError(f"no es una imagen decodificable: {path}")
    return image


def preprocess(
    image: np.ndarray, input_size: tuple[int, int], median_kernel: int = 3
) -> tuple[np.ndarray, float]:
    """BGR -> mediana -> letterbox inferior/derecha -> CHW float32, rango 0-255."""
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("se esperaba un frame BGR HxWx3")
    if image.dtype != np.uint8 or image.shape[0] == 0 or image.shape[1] == 0:
        raise ValueError("se esperaba un frame BGR uint8 no vacío")
    if median_kernel != 0 and (median_kernel < 3 or median_kernel % 2 == 0):
        raise ValueError("median_kernel debe ser 0 o un impar mayor o igual a 3")

    if median_kernel:
        image = cv2.medianBlur(image, median_kernel)
    input_height, input_width = input_size
    height, width = image.shape[:2]
    ratio = min(input_height / height, input_width / width)
    new_height = max(1, int(height * ratio))
    new_width = max(1, int(width * ratio))
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    padded = np.full((input_height, input_width, 3), 114, dtype=np.uint8)
    padded[:new_height, :new_width] = resized
    return padded.transpose(2, 0, 1).astype(np.float32), ratio
