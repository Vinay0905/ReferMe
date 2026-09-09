from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.models.common import BaseMongoModel, Subject, utc_now


class QuestionModel(BaseMongoModel):
    __test__ = False
    test_id: str  # References tests._id
    external_test_id: str  # e.g. "test_5uK46Afnka7K"
    question_number: int  # Global question number (1..180)
    subject_question_number: Optional[int] = None  # Question number within subject (1..45/90)
    subject: Subject
    question_text: str
    options: List[str] = Field(default_factory=list)
    answer: Optional[str] = None  # e.g. "1", "2", "3", "4"
    artifact_id: Optional[str] = None  # References artifacts._id
    source_page: int = 1
    bounding_box: Optional[List[float]] = None  # [x0, y0, x1, y1] coordinates on source_page
    overflow_page: Optional[int] = None  # Next page if question spills over
    overflow_bounding_box: Optional[List[float]] = None  # [x0, y0, x1, y1] on overflow_page
    image_url: Optional[str] = None  # e.g. "/api/v1/questions/{id}/image"
    image_path: Optional[str] = None  # relative or absolute path on disk
    normalized_question_text: str = ""
    fingerprint: str = ""  # SHA-256 hex digest
    parser_version: str = "v1"
    classification_status: str = "UNRESOLVED"  # "RESOLVED", "PARTIAL", "UNRESOLVED"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
