from typing import Any, Dict, List, Optional
from app.models.relationship import QuestionTopicModel
from app.repositories.base import BaseRepository


class QuestionTopicRepository(BaseRepository[QuestionTopicModel]):
    __test__ = False

    def __init__(self):
        super().__init__("question_topics", QuestionTopicModel)

    async def find_by_topic_id(
        self,
        topic_id: str,
        test_id: Optional[str] = None,
        subject: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[QuestionTopicModel]:
        filter_query: Dict[str, Any] = {"topic_id": topic_id}
        if test_id:
            filter_query["test_id"] = test_id
        if subject:
            filter_query["subject"] = subject
        return await self.find_all(filter_query, skip=skip, limit=limit, sort=[("confidence", -1), ("created_at", -1)])

    async def count_by_topic_id(
        self,
        topic_id: str,
        test_id: Optional[str] = None,
        subject: Optional[str] = None
    ) -> int:
        filter_query: Dict[str, Any] = {"topic_id": topic_id}
        if test_id:
            filter_query["test_id"] = test_id
        if subject:
            filter_query["subject"] = subject
        return await self.count(filter_query)

    async def find_by_test_id(self, test_id: str) -> List[QuestionTopicModel]:
        return await self.find_all({"test_id": test_id}, limit=1000)

    async def find_by_question_id(self, question_id: str) -> List[QuestionTopicModel]:
        return await self.find_all({"question_id": question_id}, limit=50)

    async def replace_for_test(self, test_id: str, relationships: List[QuestionTopicModel]):
        """Atomically replaces all question-topic relations for a test, guaranteeing idempotency."""
        await self.collection.delete_many({"test_id": test_id})
        if relationships:
            docs = [r.model_dump(by_alias=True, exclude={"id"}) for r in relationships]
            await self.collection.insert_many(docs)
