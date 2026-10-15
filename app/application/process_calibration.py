from app.domain.ports import MeasurementReader
from app.domain.services import MetrologyProcessorService


class ProcessCalibration:
    def __init__(self, reader: MeasurementReader, processor: MetrologyProcessorService | None = None) -> None:
        self.reader = reader
        self.processor = processor or MetrologyProcessorService()

    def execute(self, file_bytes: bytes) -> dict:
        metadata, points = self.reader.read(file_bytes)
        processed_points, opinion = self.processor.process(points)
        return {
            "metadata": metadata,
            "resultados": [point.as_dict() for point in processed_points],
            "parecer_final": opinion.value,
        }