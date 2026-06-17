import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_OPENAI_BASE_URL = "https://d2brdeqy144bwg.cloudfront.net/myllm/v1"


@dataclass(frozen=True)
class Settings:
    openai_base_url: str
    openai_api_key: str
    openai_model: str
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = os.getenv(
        "APP_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    )
    return Settings(
        openai_base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )

