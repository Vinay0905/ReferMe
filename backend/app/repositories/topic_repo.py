from typing import Optional
from bson import ObjectId
from app.models.topic import TopicModel
from app.repositories.base import BaseRepository


class TopicRepository(BaseRepository[TopicModel]):
    def __init__(self):
        super().__init__("topics", TopicModel)

    async def get_by_canonical_key(self, canonical_key: str) -> Optional[TopicModel]:
        doc = await self.collection.find_one({"canonical_key": canonical_key})
        if doc:
            return self.model_cls(**doc)
        return None

    async def upsert_canonical(self, topic: TopicModel) -> str:
        """Upserts a topic by canonical_key. Preserves existing test_count."""
        existing = await self.get_by_canonical_key(topic.canonical_key)
        if existing:
            return str(existing.id)
        doc = topic.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def increment_test_count(self, topic_id: str, count: int = 1):
        query = {"_id": ObjectId(topic_id) if ObjectId.is_valid(topic_id) else topic_id}
        await self.collection.update_one(query, {"$inc": {"test_count": count}})

    async def update_test_count(self, topic_id: str, count: int):
        query = {"_id": ObjectId(topic_id) if ObjectId.is_valid(topic_id) else topic_id}
        await self.collection.update_one(query, {"$set": {"test_count": count}})
