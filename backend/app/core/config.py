from functools import lru_cache
import os


class Settings:
    def __init__(self) -> None:
        self.APP_NAME = os.getenv("APP_NAME", "DocGuard AI")
        self.API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "text")

        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/docguard",
        )
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        self.PRESIDIO_LANGUAGE = os.getenv("PRESIDIO_LANGUAGE", "en")
        self.SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")
        self.TRANSFORMER_ENABLED = os.getenv("TRANSFORMER_ENABLED", "true").lower() == "true"
        self.TRANSFORMER_MODEL = os.getenv("TRANSFORMER_MODEL", "dslim/bert-base-NER")
        self.TRANSFORMER_MAX_TOKENS = int(os.getenv("TRANSFORMER_MAX_TOKENS", "512"))
        self.TRANSFORMER_OVERLAP_TOKENS = int(os.getenv("TRANSFORMER_OVERLAP_TOKENS", "50"))
        self.TRANSFORMER_TRIGGER_SCORE = float(os.getenv("TRANSFORMER_TRIGGER_SCORE", "0.85"))

        raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        self.CORS_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()