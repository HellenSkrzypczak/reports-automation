from fastapi import APIRouter, File, HTTPException, UploadFile

from app.application.process_calibration import ProcessCalibration


def create_router(process_calibration: ProcessCalibration) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["calibracoes"])

    @router.post("/calibrations/process")
    async def process_calibration_file(file: UploadFile = File(...)) -> dict:
        if not file.filename or not file.filename.lower().endswith(".xlsx"):
            raise HTTPException(status_code=415, detail="Envie somente arquivos .xlsx.")
        try:
            return process_calibration.execute(await file.read())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router