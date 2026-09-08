from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.common import Subject
from app.schemas.test import TestResponse


class TopicResponse(BaseModel):
    id: str
    subject: Subject
    name: str
    canonical_key: str
    aliases: List[str] = Field(default_factory=list)
    test_count: int = 0
    target_classes: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime
    updated_at: datetime


class TopicTestItem(BaseModel):
    test_id: str
    external_test_id: str
    name: str
    date: Optional[str] = None
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    target_class: Optional[str] = "12th"
    has_syllabus: bool = False
    has_question_paper: bool = False
    source_text: Optional[str] = None
    source_section: Optional[str] = None


class TopicWithTestsResponse(BaseModel):
    topic: TopicResponse
    total_tests: int
    tests: List[TopicTestItem]
