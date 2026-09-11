from typing import Optional
from app.models.test import TestModel
from app.repositories.base import BaseRepository


class TestRepository(BaseRepository[TestModel]):
    __test__ = False

    def __init__(self):
        super().__init__("tests", TestModel)

    async def get_by_external_id(self, external_source: str, external_test_id: str) -> Optional[TestModel]:
        doc = await self.collection.find_one({
            "external_source": external_source,
            "external_test_id": external_test_id
        })
        if doc:
            return self.model_cls(**doc)
        return None

    async def get_by_id_or_external_id(self, identifier: str) -> Optional[TestModel]:
        # Try as ObjectId first
        test = await self.get_by_id(identifier)
        if test:
            return test
        # Try as allen external_test_id
        return await self.get_by_external_id("allen", identifier)

    async def get_by_ids(self, test_ids: list[str]) -> list[TestModel]:
        if not test_ids:
            return []
        from bson import ObjectId
        object_ids = [ObjectId(tid) for tid in test_ids if ObjectId.is_valid(tid)]
        string_ids = [tid for tid in test_ids if not ObjectId.is_valid(tid)]

        query = {"$or": []}
        if object_ids:
            query["$or"].append({"_id": {"$in": object_ids}})
        if string_ids:
            query["$or"].append({"_id": {"$in": string_ids}})
            query["$or"].append({"external_test_id": {"$in": string_ids}})
        if not query["$or"]:
            return []

        cursor = self.collection.find(query)
        items: list[TestModel] = []
        async for doc in cursor:
            items.append(self.model_cls(**doc))
        return items

    async def upsert(self, test: TestModel) -> str:
        doc = test.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.update_one(
            {
                "external_source": test.external_source,
                "external_test_id": test.external_test_id
            },
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self.get_by_external_id(test.external_source, test.external_test_id)
        return str(existing.id) if existing else ""
