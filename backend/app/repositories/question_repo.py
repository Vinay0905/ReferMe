from typing import List, Optional
from bson import ObjectId
from app.models.question import QuestionModel
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[QuestionModel]):
    __test__ = False

    def __init__(self):
        super().__init__("questions", QuestionModel)

    async def find_by_test_id(self, test_id: str) -> List[QuestionModel]:
        return await self.find_all({"test_id": test_id}, limit=500, sort=[("question_number", 1)])

    async def find_by_external_test_id(self, external_test_id: str) -> List[QuestionModel]:
        return await self.find_all({"external_test_id": external_test_id}, limit=500, sort=[("question_number", 1)])

    async def find_by_fingerprint(self, fingerprint: str) -> List[QuestionModel]:
        return await self.find_all({"fingerprint": fingerprint}, limit=50)

    async def get_by_ids(self, question_ids: List[str]) -> List[QuestionModel]:
        if not question_ids:
            return []
        object_ids = [ObjectId(qid) for qid in question_ids if ObjectId.is_valid(qid)]
        string_ids = [qid for qid in question_ids if not ObjectId.is_valid(qid)]

        query = {"$or": []}
        if object_ids:
            query["$or"].append({"_id": {"$in": object_ids}})
        if string_ids:
            query["$or"].append({"_id": {"$in": string_ids}})
        if not query["$or"]:
            return []

        cursor = self.collection.find(query)
        items: List[QuestionModel] = []
        async for doc in cursor:
            items.append(self.model_cls(**doc))
        return items

    async def replace_for_test(self, test_id: str, questions: List[QuestionModel]) -> List[str]:
        """Atomically replaces all questions for a given test, ensuring idempotency."""
        await self.collection.delete_many({"test_id": test_id})
        if not questions:
            return []
        docs = [q.model_dump(by_alias=True, exclude={"id"}) for q in questions]
        result = await self.collection.insert_many(docs)
        inserted_ids = [str(oid) for oid in result.inserted_ids]
        # Attach the inserted ids back to the entities
        for q, q_id in zip(questions, inserted_ids):
            q.id = q_id
        return inserted_ids
