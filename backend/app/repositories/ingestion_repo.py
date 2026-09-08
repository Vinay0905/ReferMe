from typing import Optional
from bson import ObjectId
from app.models.ingestion import IngestionJobModel
from app.repositories.base import BaseRepository


class IngestionJobRepository(BaseRepository[IngestionJobModel]):
    def __init__(self):
        super().__init__("ingestion_jobs", IngestionJobModel)

    async def update_job(self, job: IngestionJobModel):
        query = {"_id": ObjectId(job.id) if ObjectId.is_valid(job.id) else job.id}
        doc = job.model_dump(by_alias=True, exclude={"id"})
        await self.collection.update_one(query, {"$set": doc})
