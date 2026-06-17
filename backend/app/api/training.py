import logging

from fastapi import APIRouter

from app.schemas.training import TrainingResponse, TrainingStatus
from app.services.training_service import TrainingService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/retrain", response_model=TrainingResponse)
def retrain() -> dict:
    logger.info("Training retrain request received")
    result = TrainingService().retrain()
    logger.info("Training retrain request completed with status=%s", result.get("status"))
    return result


@router.get("/status", response_model=TrainingStatus)
def status() -> dict:
    logger.info("Training status request received")
    result = TrainingService().status()
    logger.info("Training status request completed: trained=%s", result.get("trained"))
    return result
