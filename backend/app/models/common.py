from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, Field


def py_object_id_validator(val: Any) -> str:
    if val is None:
        return ""
    return str(val)


PyObjectId = Annotated[str, BeforeValidator(py_object_id_validator)]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseMongoModel(BaseModel):
    id: PyObjectId = Field(default="", alias="_id")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class Subject(str, Enum):
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"


class ProcessingStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SYLLABUS_PENDING = "SYLLABUS_PENDING"
    SYLLABUS_FETCHED = "SYLLABUS_FETCHED"
    SYLLABUS_PARSED = "SYLLABUS_PARSED"
    TOPICS_PROCESSED = "TOPICS_PROCESSED"
    QUESTION_PAPER_PENDING = "QUESTION_PAPER_PENDING"
    READY = "READY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
