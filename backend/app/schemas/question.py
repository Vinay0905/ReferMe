from typing import List, Optional
from pydantic import BaseModel
from app.models.common import Subject
from app.models.relationship import QuestionClassificationMethod


class QuestionItemResponse(BaseModel):
    id: str
    test_id: str
    external_test_id: str
    test_name: Optional[str] = None
    question_number: int
    subject_question_number: Optional[int] = None
    subject: Subject
    question_text: str
    options: List[str]
    answer: Optional[str] = None
    source_page: int
    bounding_box: Optional[List[float]] = None
    image_url: Optional[str] = None
    canonical_key: str
    classification_method: QuestionClassificationMethod
    confidence: float
