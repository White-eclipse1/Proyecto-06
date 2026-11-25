from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    # Coordenadas xyxy en píxeles de la imagen original.
    bbox: tuple[float, float, float, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": list(self.bbox),
        }
