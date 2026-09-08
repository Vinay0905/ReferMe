from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from app.models.common import BaseMongoModel, utc_now


class ArtifactKind(str, Enum):
    SYLLABUS = "syllabus"
    QUESTION_PAPER = "question_paper"


class ArtifactModel(BaseMongoModel):
    test_id: str  # References tests._id
    external_test_id: str
    kind: ArtifactKind
    source: str = "allen"
    stable_object_key: str  # e.g., "test_12345/syllabus.pdf"
    storage_provider: str = "local"
    storage_key: str  # File path or object key
    sha256: str
    content_type: str = "application/pdf"
    size_bytes: int
    language: str = "en"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SyllabusSnapshotModel(BaseMongoModel):
    test_id: str
    external_test_id: str
    artifact_id: Optional[str] = None
    content_hash: str
    parser_version: str = "v1"
    raw_sections: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)
