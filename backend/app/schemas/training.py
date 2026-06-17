from typing import Any

from pydantic import BaseModel


class TrainingResponse(BaseModel):
    status: str
    trained_at: str
    metrics: dict[str, Any]
    artifact_version: str


class TrainingStatus(BaseModel):
    trained: bool
    last_training_date: str | None
    metrics: dict[str, Any] | None
    artifact_version: str | None
    artifacts: list[str]

