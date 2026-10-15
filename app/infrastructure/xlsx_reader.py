from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from app.domain.models import MeasurementPoint


ALIASES = {
    "parameter": ("parametro", "parâmetro", "caracteristica", "característica"),
    "nominal": ("nominal", "valor nominal", "valor_nominal"),
    "lea": ("lea", "limite de erro admissivel", "limite de erro admissível"),
    "upper_tolerance": ("tol +", "tol. +", "tolerancia superior", "tolerância superior", "upper tol"),
    "lower_tolerance": ("tol -", "tol. -", "tolerancia inferior", "tolerância inferior", "lower tol"),
    "reading": ("medida", "medição", "medicao", "leitura", "valor obtido"),
}


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _find_column(headers: list[Any], aliases: tuple[str, ...]) -> int | None:
    normalized_headers = [_normalized(header) for header in headers]
    normalized_aliases = {_normalized(alias) for alias in aliases}
    for index, header in enumerate(normalized_headers):
        if header in normalized_aliases:
            return index
    return None


def _number(value: Any, field: str, row_number: int) -> float:
    if value is None or str(value).strip() == "":
        raise ValueError(f"Campo '{field}' ausente na linha {row_number}.")
    try:
        return float(str(value).replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Campo '{field}' invalido na linha {row_number}.") from exc


def read_measurements(file_bytes: bytes, sheet_name: str | None = None) -> tuple[dict[str, str], list[MeasurementPoint]]:
    workbook = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    worksheet = workbook[sheet_name] if sheet_name and sheet_name in workbook.sheetnames else workbook[workbook.sheetnames[0]]
    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        raise ValueError("A planilha esta vazia.")

    header_row_index = next(
        (index for index, row in enumerate(rows) if _find_column(list(row), ALIASES["parameter"]) is not None),
        None,
    )
    if header_row_index is None:
        raise ValueError("Nao foi encontrada uma linha de cabecalho com 'Parametro'.")

    headers = list(rows[header_row_index])
    parameter_column = _find_column(headers, ALIASES["parameter"])
    nominal_column = _find_column(headers, ALIASES["nominal"])
    lea_column = _find_column(headers, ALIASES["lea"])
    upper_tolerance_column = _find_column(headers, ALIASES["upper_tolerance"])
    lower_tolerance_column = _find_column(headers, ALIASES["lower_tolerance"])
    reading_columns = [
        index for index, header in enumerate(headers) if any(
            _normalized(alias) in _normalized(header) for alias in ALIASES["reading"]
        )
    ]
    has_lea = lea_column is not None or upper_tolerance_column is not None or lower_tolerance_column is not None
    if parameter_column is None or nominal_column is None or not has_lea or not reading_columns:
        raise ValueError("A planilha deve conter parametro, nominal, LEA (ou tolerancias) e ao menos uma leitura.")

    points: list[MeasurementPoint] = []
    for row_number, row in enumerate(rows[header_row_index + 1 :], start=header_row_index + 2):
        parameter = str(row[parameter_column] or "").strip()
        if not parameter or parameter.lower() in {"nan", "none", "observacao", "observação"}:
            continue
        readings = tuple(_number(row[index], "leitura", row_number) for index in reading_columns if index < len(row) and row[index] is not None)
        if lea_column is not None:
            lea = abs(_number(row[lea_column], "LEA", row_number))
        else:
            tolerance_values = []
            for column, field in ((upper_tolerance_column, "tolerancia superior"), (lower_tolerance_column, "tolerancia inferior")):
                if column is not None and column < len(row) and row[column] is not None:
                    tolerance_values.append(abs(_number(row[column], field, row_number)))
            if not tolerance_values:
                raise ValueError(f"LEA ausente na linha {row_number}.")
            lea = max(tolerance_values)

        points.append(
            MeasurementPoint(
                parameter=parameter,
                nominal=_number(row[nominal_column], "nominal", row_number),
                readings=readings,
                lea=lea,
            )
        )

    metadata = {"cliente": "Nao informado", "tecnico": "Nao informado"}
    metadata_aliases = {
        "cliente": ("cliente", "solicitante", "setor cliente"),
        "tecnico": ("tecnico", "técnico", "executante", "metrologista"),
    }
    for row in rows[:header_row_index]:
        for index, cell in enumerate(row):
            label = _normalized(cell)
            for key, aliases in metadata_aliases.items():
                if any(_normalized(alias) in label for alias in aliases):
                    values = [value for value in row[index + 1 :] if value is not None and str(value).strip()]
                    if values:
                        metadata[key] = str(values[0]).strip()
    return metadata, points


class XlsxMeasurementReader:
    def read(self, file_bytes: bytes) -> tuple[dict[str, str], list[MeasurementPoint]]:
        return read_measurements(file_bytes)
