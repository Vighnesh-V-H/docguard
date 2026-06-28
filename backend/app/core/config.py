from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "DocGuard AI"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/docguard")
    DATABASE_ECHO: bool = False
    
    PRESIDIO_LANGUAGE: str = "en"
    SPACY_MODEL: str = "en_core_web_lg"
    
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()