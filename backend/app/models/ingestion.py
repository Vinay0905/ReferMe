from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import Field
from app.models.common import BaseMongoModel, utc_now


class IngestionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class IngestionJobModel(BaseMongoModel):
    status: IngestionStatus = IngestionStatus.RUNNING
    start_time: datetime = Field(default_factory=utc_now)
    end_time: Optional[datetime] = None
    discovered_count: int = 0
    succeeded_count: int = 0
    partial_count: int = 0
    failed_count: int = 0
    error_summary: List[Dict[str, str]] = Field(default_factory=list)
    parser_version: str = "v1"
