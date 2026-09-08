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
