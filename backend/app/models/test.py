from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.common import BaseMongoModel, ProcessingStatus, utc_now


class TestModel(BaseMongoModel):
    __test__ = False
    external_source: str = "allen"
    external_test_id: str
    name: str
    date: Optional[str] = None  # Formatted date or raw string from card (e.g. "13 Sep")
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None  # e.g., "Offline", "Online"
    status: Optional[str] = None  # e.g., "UPCOMING", "FINAL_RESULT_GENERATED"
    category: Optional[str] = None  # e.g., "DLP", "MINOR", "MAJOR"
    target_class: Optional[str] = "12th"  # e.g., "12th", "11th"
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    processing_status: ProcessingStatus = ProcessingStatus.DISCOVERED
    has_syllabus: bool = False
    has_question_paper: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
