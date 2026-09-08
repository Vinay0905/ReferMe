from datetime import datetime
from typing import List
from pydantic import Field
from app.models.common import BaseMongoModel, Subject, utc_now


class TopicModel(BaseMongoModel):
    subject: Subject
    name: str  # Display name, e.g., "Electric Power"
    canonical_key: str  # Unique key, e.g., "physics:electric-power"
    aliases: List[str] = Field(default_factory=list)
    test_count: int = 0  # Denormalized counter for quick UI rendering
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
