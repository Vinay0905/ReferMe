from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import Field
from app.models.common import BaseMongoModel, Subject, utc_now


class NormalizationMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    ALIAS = "alias"
    MANUAL = "manual"
    AI_SUGGESTED = "ai_suggested"


class TestTopicModel(BaseMongoModel):
    __test__ = False
    test_id: str  # References tests._id
    external_test_id: str  # For quick index and debugging
    topic_id: str  # References topics._id
    canonical_key: str
    subject: Subject
    source_text: str  # Exact wording as extracted from syllabus PDF
    source_section: Optional[str] = None
    syllabus_snapshot_id: Optional[str] = None
    normalization_method: NormalizationMethod = NormalizationMethod.DETERMINISTIC
    normalization_version: str = "v1"
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=utc_now)
