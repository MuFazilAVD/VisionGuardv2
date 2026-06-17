from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.claims import router as claims_router
from app.api.sample_data import router as sample_data_router
from app.api.training import router as training_router
from app.utils.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Claims Risk Assessment POC",
        version="1.0.0",
        description="Local FastAPI implementation of the three-layer claims risk assessment engine.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(training_router, prefix="/api/training", tags=["training"])
    app.include_router(claims_router, prefix="/api/claims", tags=["claims"])
    app.include_router(sample_data_router, prefix="/api", tags=["sample-data"])

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

