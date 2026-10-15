from fastapi import FastAPI

from app.api.routes import create_router
from app.application.process_calibration import ProcessCalibration
from app.infrastructure.xlsx_reader import XlsxMeasurementReader


app = FastAPI(
    title="Reports Automation API",
    version="0.1.0",
    description="Processa planilhas XLSX de calibracao e retorna resultados metrologicos.",
)
app.include_router(create_router(ProcessCalibration(XlsxMeasurementReader())))


@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    return {"status": "ok"}