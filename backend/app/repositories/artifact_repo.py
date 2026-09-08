from typing import Optional
from app.models.artifact import ArtifactKind, ArtifactModel
from app.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository[ArtifactModel]):
    def __init__(self):
        super().__init__("artifacts", ArtifactModel)

    async def get_by_test_and_kind(self, test_id: str, kind: ArtifactKind) -> Optional[ArtifactModel]:
        doc = await self.collection.find_one({"test_id": test_id, "kind": kind.value})
        if doc:
            return self.model_cls(**doc)
        return None

    async def upsert_artifact(self, artifact: ArtifactModel) -> str:
        doc = artifact.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.update_one(
            {
                "source": artifact.source,
                "stable_object_key": artifact.stable_object_key,
                "kind": artifact.kind.value
            },
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self.collection.find_one({
            "source": artifact.source,
            "stable_object_key": artifact.stable_object_key,
            "kind": artifact.kind.value
        })
        return str(existing["_id"]) if existing else ""
