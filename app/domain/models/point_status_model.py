from enum import StrEnum


class PointStatusModel(StrEnum):
    WITHIN_TOLERANCE = "DENTRO_DA_TOLERANCIA"
    OUTSIDE_TOLERANCE = "FORA_DA_TOLERANCIA"