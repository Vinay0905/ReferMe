from abc import ABC, abstractmethod
from typing import Optional


class ArtifactStorage(ABC):
    """Abstract interface for storing and retrieving PDF artifacts."""

    @abstractmethod
    async def save(self, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        """Saves content bytes under a logical key. Returns the permanent storage identifier/path."""
        pass

    @abstractmethod
    async def get(self, storage_key: str) -> Optional[bytes]:
        """Retrieves content bytes for a stored artifact."""
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Checks if an artifact exists in storage."""
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Deletes an artifact if present. Returns True if deleted, False otherwise."""
        pass
