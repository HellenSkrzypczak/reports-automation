
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import create_router
from app.application.process_calibration import ProcessCalibration
from app.infrastructure.xlsx_reader import XlsxMeasurementReader

app = FastAPI(
    title="Reports Automation API",
    version="0.1.0",
    description="Processa planilhas XLSX de calibracao e retorna resultados metrologicos.",
)

# Permite que o React acesse a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    create_router(
        ProcessCalibration(XlsxMeasurementReader())
    )
)


@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    return {"status": "ok"}
