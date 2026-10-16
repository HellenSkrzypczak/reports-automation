
from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from typing import Any

from openpyxl import load_workbook

from app.domain.models import MeasurementPoint


ALIASES = {
    "parameter": (
        "parametro", "parâmetro",
        "caracteristica", "característica",
        "dimension",
    ),
    "nominal": ("nominal", "valor nominal", "valor_nominal"),
    "lea": (
        "lea",
        "limite de erro admissivel",
        "limite de erro admissível",
    ),
    "upper_tolerance": (
        "tol +", "tol. +",
        "tolerancia superior", "tolerância superior",
        "upper tol", "+tol",
    ),
    "lower_tolerance": (
        "tol -", "tol. -",
        "tolerancia inferior", "tolerância inferior",
        "lower tol", "-tol",
    ),
    "reading": (
        "medida", "medição", "medicao",
        "leitura", "valor obtido", "meas",
    ),
}


def _normalized(value: Any) -> str:
    return " ".join(
        str(value or "").strip().lower().replace("_", " ").split()
    )


def _find_column(
    headers: list[Any],
    aliases: tuple[str, ...],
) -> int | None:
    normalized_headers = [_normalized(header) for header in headers]
    normalized_aliases = {_normalized(alias) for alias in aliases}

    for index, header in enumerate(normalized_headers):
        if header in normalized_aliases:
            return index

    return None


def _number(value: Any, field: str, row_number: int) -> float:
    if value is None or str(value).strip() == "":
        raise ValueError(
            f"Campo '{field}' ausente na linha {row_number}."
        )

    try:
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Campo '{field}' inválido na linha {row_number}."
        ) from exc


def _prepare_xlsx(file_bytes: bytes) -> bytes:
    """Converte os namespaces Strict OOXML para os aceitos pelo openpyxl."""
    replacements = (
        (
            b"http://purl.oclc.org/ooxml/spreadsheetml/main",
            b"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        ),
        (
            b"http://purl.oclc.org/ooxml/officeDocument/relationships",
            b"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        ),
    )

    source = BytesIO(file_bytes)
    output = BytesIO()

    with ZipFile(source, "r") as original:
        with ZipFile(output, "w", ZIP_DEFLATED) as converted:
            for item in original.infolist():
                content = original.read(item.filename)

                if item.filename.endswith((".xml", ".rels")):
                    for old, new in replacements:
                        content = content.replace(old, new)

                converted.writestr(item, content)

    return output.getvalue()


def read_measurements(
    file_bytes: bytes,
    sheet_name: str | None = None,
) -> tuple[dict[str, str], list[MeasurementPoint]]:
    if not file_bytes:
        raise ValueError("O arquivo enviado está vazio.")

    try:
        prepared_bytes = _prepare_xlsx(file_bytes)
        workbook = load_workbook(
            BytesIO(prepared_bytes),
            read_only=True,
            data_only=True,
        )
    except Exception as exc:
        raise ValueError(
            "Não foi possível ler o arquivo Excel enviado. "
            "Verifique se o arquivo XLSX é válido."
        ) from exc

    try:
        if not workbook.sheetnames:
            raise ValueError(
                "O arquivo Excel não possui abas disponíveis."
            )

        # Usa Importação quando ela existir; caso contrário,
        # mantém o comportamento anterior ou respeita a aba informada.
        if sheet_name:
            if sheet_name not in workbook.sheetnames:
                raise ValueError(
                    f"A aba '{sheet_name}' não foi encontrada. "
                    f"Abas disponíveis: {', '.join(workbook.sheetnames)}"
                )
            worksheet = workbook[sheet_name]
        elif "Importação" in workbook.sheetnames:
            worksheet = workbook["Importação"]
        elif "Importacao" in workbook.sheetnames:
            worksheet = workbook["Importacao"]
        else:
            worksheet = workbook[workbook.sheetnames[0]]

        rows = list(worksheet.iter_rows(values_only=True))

        if not rows:
            raise ValueError("A planilha está vazia.")

        header_row_index = next(
            (
                index
                for index, row in enumerate(rows)
                if _find_column(
                    list(row), ALIASES["parameter"]
                ) is not None
            ),
            None,
        )

        if header_row_index is None:
            raise ValueError(
                "Não foi encontrada uma coluna de característica "
                "ou DIMENSION na linha de cabeçalho."
            )

        headers = list(rows[header_row_index])

        parameter_column = _find_column(
            headers, ALIASES["parameter"]
        )
        nominal_column = _find_column(
            headers, ALIASES["nominal"]
        )
        lea_column = _find_column(headers, ALIASES["lea"])
        upper_column = _find_column(
            headers, ALIASES["upper_tolerance"]
        )
        lower_column = _find_column(
            headers, ALIASES["lower_tolerance"]
        )

        reading_columns = [
            index
            for index, header in enumerate(headers)
            if header is not None
            and any(
                _normalized(alias) in _normalized(header)
                for alias in ALIASES["reading"]
            )
        ]

        has_tolerance = (
            lea_column is not None
            or upper_column is not None
            or lower_column is not None
        )

        if (
            parameter_column is None
            or nominal_column is None
            or not has_tolerance
            or not reading_columns
        ):
            raise ValueError(
                "A planilha deve conter DIMENSION, NOMINAL, "
                "+TOL/-TOL ou LEA e ao menos uma coluna de medição."
            )

        points: list[MeasurementPoint] = []

        for row_number, row in enumerate(
            rows[header_row_index + 1:],
            start=header_row_index + 2,
        ):
            parameter_value = (
                row[parameter_column]
                if parameter_column < len(row)
                else None
            )
            parameter = str(parameter_value or "").strip()

            if not parameter:
                continue

            if parameter.lower() in {
                "nan", "none", "observacao", "observação"
            }:
                continue

            nominal = _number(
                row[nominal_column]
                if nominal_column < len(row)
                else None,
                "nominal",
                row_number,
            )

            readings = tuple(
                _number(row[index], "leitura", row_number)
                for index in reading_columns
                if index < len(row)
                and row[index] is not None
                and str(row[index]).strip() != ""
            )

            if not readings:
                raise ValueError(
                    f"Nenhuma medição encontrada para '{parameter}' "
                    f"na linha {row_number}."
                )

            if lea_column is not None:
                lea = abs(
                    _number(
                        row[lea_column]
                        if lea_column < len(row)
                        else None,
                        "LEA",
                        row_number,
                    )
                )
            else:
                tolerance_values = []

                for column, field in (
                    (upper_column, "tolerância superior"),
                    (lower_column, "tolerância inferior"),
                ):
                    if (
                        column is not None
                        and column < len(row)
                        and row[column] is not None
                        and str(row[column]).strip() != ""
                    ):
                        tolerance_values.append(
                            abs(_number(row[column], field, row_number))
                        )

                if not tolerance_values:
                    raise ValueError(
                        f"Tolerâncias ausentes na linha {row_number}."
                    )

                lea = max(tolerance_values)

            points.append(
                MeasurementPoint(
                    parameter=parameter,
                    nominal=nominal,
                    readings=readings,
                    lea=lea,
                )
            )

        if not points:
            raise ValueError(
                "Nenhum ponto de medição válido foi encontrado."
            )

        metadata = {
            "cliente": "Não informado",
            "tecnico": "Não informado",
        }

        metadata_aliases = {
            "cliente": ("cliente", "solicitante", "setor cliente"),
            "tecnico": (
                "tecnico", "técnico", "executante", "metrologista"
            ),
        }

        for row in rows[:header_row_index]:
            for index, cell in enumerate(row):
                label = _normalized(cell)

                for key, aliases in metadata_aliases.items():
                    if any(
                        _normalized(alias) in label
                        for alias in aliases
                    ):
                        values = [
                            value
                            for value in row[index + 1:]
                            if value is not None
                            and str(value).strip()
                        ]

                        if values:
                            metadata[key] = str(values[0]).strip()

        return metadata, points

    finally:
        workbook.close()


class XlsxMeasurementReader:
    def read(
        self,
        file_bytes: bytes,
    ) -> tuple[dict[str, str], list[MeasurementPoint]]:
        return read_measurements(file_bytes)
