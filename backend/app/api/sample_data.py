from fastapi import APIRouter

from app.schemas.sample_data import SampleDataResponse
from app.services.sample_data_service import SampleDataService

router = APIRouter()


@router.get("/sample-data", response_model=SampleDataResponse)
def sample_data() -> dict:
    return SampleDataService().ensure_sample_data()

