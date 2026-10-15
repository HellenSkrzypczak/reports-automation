from typing import Protocol

from app.domain.models import MeasurementPointModel


class MeasurementReader(Protocol):
    def read(self, file_bytes: bytes) -> tuple[dict[str, str], list[MeasurementPointModel]]:
        """Read input data and translate it into domain objects."""