import logging

from fastapi import APIRouter

from app.schemas.sample_data import SampleDataResponse
from app.services.sample_data_service import SampleDataService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sample-data", response_model=SampleDataResponse)
def sample_data() -> dict:
    logger.info("Sample data request received")
    result = SampleDataService().ensure_sample_data()
    logger.info(
        "Sample data request completed: historical=%s rules=%s realtime=%s",
        result["historical_claims"]["record_count"],
        result["rules"]["record_count"],
        result["realtime_claims"]["record_count"],
    )
    return result
