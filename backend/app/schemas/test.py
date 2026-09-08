from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.common import ProcessingStatus, Subject


class TestResponse(BaseModel):
    id: str
    external_test_id: str
    name: str
    date: Optional[str] = None
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    processing_status: ProcessingStatus
    has_syllabus: bool = False
    has_question_paper: bool = False
    created_at: datetime
    updated_at: datetime


class TestDetailResponse(TestResponse):
    total_topics: int = 0
    topics_count_by_subject: Dict[str, int] = Field(default_factory=dict)


class TestTopicItem(BaseModel):
    topic_id: str
    name: str
    canonical_key: str
    subject: Subject
    source_text: str
    source_section: Optional[str] = None
    confidence: float = 1.0


class TestTopicsResponse(BaseModel):
    test_id: str
    external_test_id: str
    test_name: str
    total_topics: int
    subjects: Dict[str, List[TestTopicItem]] = Field(
        default_factory=lambda: {
            "physics": [],
            "chemistry": [],
            "biology": []
        }
    )
