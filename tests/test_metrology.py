from io import BytesIO

from openpyxl import Workbook

from app.domain.models import FinalOpinion, MeasurementPoint, PointStatus
from app.domain.services import MetrologyProcessorService
from app.infrastructure.xlsx_reader import read_measurements


def test_processes_average_error_lea_and_approved_opinion():
    points = [MeasurementPoint("P1", 10.0, (10.2, 10.4), 0.3)]

    processed, opinion = MetrologyProcessorService().process(points)

    assert processed[0].average == 10.3
    assert processed[0].systematic_error == 0.3
    assert processed[0].status == PointStatus.WITHIN_TOLERANCE
    assert opinion == FinalOpinion.APPROVED


def test_rejects_when_any_point_is_outside_lea():
    points = [
        MeasurementPoint("P1", 10.0, (10.0, 10.1), 0.2),
        MeasurementPoint("P2", 20.0, (20.4, 20.5), 0.2),
    ]

    processed, opinion = MetrologyProcessorService().process(points)

    assert processed[1].status == PointStatus.OUTSIDE_TOLERANCE
    assert opinion == FinalOpinion.REJECTED


def test_reads_xlsx_with_metadata_and_tolerance_columns():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Cliente", "Schulz S.A."])
    sheet.append(["Tecnico Executante", "Maria"])
    sheet.append([])
    sheet.append(["Parametro", "Nominal", "Tol +", "Tol -", "Medida 1", "Medida 2"])
    sheet.append(["P1", 10, 0.2, -0.2, 10.1, 10.3])

    buffer = BytesIO()
    workbook.save(buffer)

    metadata, points = read_measurements(buffer.getvalue())

    assert metadata == {"cliente": "Schulz S.A.", "tecnico": "Maria"}
    assert points[0].parameter == "P1"
    assert points[0].lea == 0.2
    assert points[0].readings == (10.1, 10.3)
