from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from app.db.mongo import get_database

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, collection_name: str, model_cls: Type[T]):
        self.collection_name = collection_name
        self.model_cls = model_cls

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return get_database()[self.collection_name]

    async def get_by_id(self, doc_id: str) -> Optional[T]:
        query = {"_id": ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id}
        doc = await self.collection.find_one(query)
        if doc:
            return self.model_cls(**doc)
        return None

    async def insert(self, entity: T) -> str:
        doc = entity.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def find_all(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50,
        sort: Optional[List] = None
    ) -> List[T]:
        cursor = self.collection.find(filter_query or {})
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)

        items = []
        async for doc in cursor:
            items.append(self.model_cls(**doc))
        return items

    async def count(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filter_query or {})

    async def update(self, doc_id: str, fields: Dict[str, Any]) -> bool:
        query = {"_id": ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id}
        result = await self.collection.update_one(query, {"$set": fields})
        return result.modified_count > 0
