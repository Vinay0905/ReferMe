from typing import List
from app.models.relationship import TestTopicModel
from app.repositories.base import BaseRepository


class TestTopicRepository(BaseRepository[TestTopicModel]):
    __test__ = False

    def __init__(self):
        super().__init__("test_topics", TestTopicModel)

    async def find_by_test_id(self, test_id: str) -> List[TestTopicModel]:
        return await self.find_all({"test_id": test_id}, limit=500)

    async def find_by_topic_id(self, topic_id: str, skip: int = 0, limit: int = 50) -> List[TestTopicModel]:
        return await self.find_all({"topic_id": topic_id}, skip=skip, limit=limit)

    async def replace_for_test(self, test_id: str, relationships: List[TestTopicModel]):
        """Idempotently replaces all topic relations for a test (e.g. after re-parsing)."""
        await self.collection.delete_many({"test_id": test_id})
        if relationships:
            docs = [r.model_dump(by_alias=True, exclude={"id"}) for r in relationships]
            await self.collection.insert_many(docs)
