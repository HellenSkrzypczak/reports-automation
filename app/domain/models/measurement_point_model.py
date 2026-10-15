from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementPointModel:
    parameter: str
    nominal: float
    readings: tuple[float, ...]
    lea: float