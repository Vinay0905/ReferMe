from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional
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

    # Ingestion & ALLEN Integration
    ALLEN_BASE_URL: str = "https://api.allen-live.in"
    ALLEN_AUTH_TOKEN: str = ""  # Bearer token from user session
    ALLEN_MOCK_MODE: bool = False  # When True or when token is empty, uses mock data
    ALLEN_CLIENT_TYPE: str = "web"
    ALLEN_DEVICE_ID: Optional[str] = None
    ALLEN_BATCH_LIST: Optional[str] = None
    ALLEN_COURSE_ID: Optional[str] = None

    # Multi-Course Tracks
    COURSE_12TH_ID: str = "363233"
    COURSE_12TH_NAME: str = "Leader Test Series"
    COURSE_11TH_ID: str = "cr_SUqkwoRLxGJ1jV8Ix60b3"
    COURSE_11TH_BATCH_LIST: str = "bt_2Fsslkpec8p0kxgacLsCc"
    COURSE_11TH_NAME: str = "Nurture Test Series"

    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGES: int = 20  # Safety pagination bound
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
