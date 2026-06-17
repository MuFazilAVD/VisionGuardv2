import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.claims import router as claims_router
from app.api.sample_data import router as sample_data_router
from app.api.training import router as training_router
from app.utils.config import get_settings

API_PREFIX = "/visionguardv2/api"
HEALTH_PATH = "/visionguardv2/health"
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def create_app() -> FastAPI:
    configure_logging()
    logger.info("Creating VisionGuard FastAPI app")
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
    logger.info("CORS configured for %d origin(s)", len(settings.cors_origins))

    app.include_router(training_router, prefix=f"{API_PREFIX}/training", tags=["training"])
    app.include_router(claims_router, prefix=f"{API_PREFIX}/claims", tags=["claims"])
    app.include_router(sample_data_router, prefix=API_PREFIX, tags=["sample-data"])
    logger.info("API routers registered under %s", API_PREFIX)

    @app.get(HEALTH_PATH)
    def health() -> dict[str, str]:
        logger.info("Health check requested")
        return {"status": "ok"}

    logger.info("VisionGuard FastAPI app ready")
    return app


app = create_app()
