from dataclasses import dataclass
from typing import Any

from .point_status_model import PointStatusModel


@dataclass(frozen=True)
class ProcessedPointModel:
    parameter: str
    nominal: float
    readings: tuple[float, ...]
    average: float
    systematic_error: float
    lea: float
    status: PointStatusModel

    def as_dict(self) -> dict[str, Any]:
        return {
            "parametro": self.parameter,
            "nominal": self.nominal,
            "leituras": list(self.readings),
            "media": self.average,
            "erro_sistematico": self.systematic_error,
            "lea": self.lea,
            "status": self.status.value,
        }