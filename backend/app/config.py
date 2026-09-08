from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "ALLEN NEET Test ↔ Topic Intelligence System"
    API_V1_STR: str = "/api/v1"

    # MongoDB Atlas
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "referme_neet_dev"

    # Storage
    STORAGE_PROVIDER: Literal["local", "gridfs", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./storage_data"

    # Ingestion settings
    DEFAULT_PAGE_SIZE: int = 25
    MAX_CONCURRENT_REQUESTS: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 30

    @property
    def storage_path(self) -> Path:
        path = Path(self.LOCAL_STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
