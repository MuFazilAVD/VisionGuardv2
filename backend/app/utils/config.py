import logging
import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_OPENAI_BASE_URL = "https://d2brdeqy144bwg.cloudfront.net/myllm/v1"
PRODUCTION_APP_ORIGINS = (
    "https://d2brdeqy144bwg.cloudfront.net",
    "https://d3bkb5k71wphsh.cloudfront.net",
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    openai_base_url: str
    openai_api_key: str
    openai_model: str
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    logger.info("Loading application settings from environment")
    origins = os.getenv(
        "APP_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    )
    cors_origins = [origin.strip().rstrip("/") for origin in origins.split(",") if origin.strip()]
    for production_origin in PRODUCTION_APP_ORIGINS:
        if production_origin not in cors_origins:
            cors_origins.append(production_origin)

    settings = Settings(
        openai_base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
        cors_origins=cors_origins,
    )
    logger.info(
        "Settings loaded: cors_origins=%d openai_model_configured=%s api_key_configured=%s",
        len(settings.cors_origins),
        bool(settings.openai_model),
        bool(settings.openai_api_key),
    )
    return settings
