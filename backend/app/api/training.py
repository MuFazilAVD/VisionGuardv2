from fastapi import APIRouter

from app.schemas.training import TrainingResponse, TrainingStatus
from app.services.training_service import TrainingService

router = APIRouter()


@router.post("/retrain", response_model=TrainingResponse)
def retrain() -> dict:
    return TrainingService().retrain()


@router.get("/status", response_model=TrainingStatus)
def status() -> dict:
    return TrainingService().status()

