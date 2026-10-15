from app.domain.models import FinalOpinionModel, MeasurementPointModel, PointStatusModel, ProcessedPointModel


FLOAT_TOLERANCE = 1e-7


class MetrologyProcessorService:
    """Applies the AV3 business rules without depending on the web or Excel layers."""

    def process(self, points: list[MeasurementPointModel]) -> tuple[list[ProcessedPointModel], FinalOpinionModel]:
        if not points:
            raise ValueError("A planilha precisa conter ao menos um ponto de ensaio.")

        processed: list[ProcessedPointModel] = []
        for point in points:
            if not point.readings:
                raise ValueError(f"O ponto '{point.parameter}' nao possui leituras validas.")

            average = sum(point.readings) / len(point.readings)
            systematic_error = average - point.nominal
            status = (
                PointStatusModel.WITHIN_TOLERANCE
                if abs(systematic_error) <= point.lea + FLOAT_TOLERANCE
                else PointStatusModel.OUTSIDE_TOLERANCE
            )
            processed.append(
                ProcessedPointModel(
                    parameter=point.parameter,
                    nominal=round(point.nominal, 4),
                    readings=tuple(round(value, 4) for value in point.readings),
                    average=round(average, 4),
                    systematic_error=round(systematic_error, 4),
                    lea=round(point.lea, 4),
                    status=status,
                )
            )

        opinion = (
            FinalOpinionModel.APPROVED
            if all(point.status == PointStatusModel.WITHIN_TOLERANCE for point in processed)
            else FinalOpinionModel.REJECTED
        )
        return processed, opinion