from typing import Any

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    path: str
    record_count: int
    preview: list[dict[str, Any]]


class SampleDataResponse(BaseModel):
    historical_claims: DatasetSummary
    rules: DatasetSummary
    realtime_claims: DatasetSummary

