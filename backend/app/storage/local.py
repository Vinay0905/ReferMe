from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.storage.base import ArtifactStorage


class LocalArtifactStorage(ArtifactStorage):
    """Stores binary PDF artifacts on the local filesystem."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_settings().storage_path

    async def save(self, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        safe_key = key.lstrip("/")
        target_path = self.base_dir / safe_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return str(target_path.resolve())

    async def get(self, storage_key: str) -> Optional[bytes]:
        path = Path(storage_key)
        if not path.exists():
            return None
        return path.read_bytes()

    async def exists(self, storage_key: str) -> bool:
        return Path(storage_key).exists()

    async def delete(self, storage_key: str) -> bool:
        path = Path(storage_key)
        if path.exists():
            path.unlink()
            return True
        return False


def get_storage_provider() -> ArtifactStorage:
    settings = get_settings()
    if settings.STORAGE_PROVIDER == "local":
        return LocalArtifactStorage()
    raise NotImplementedError(f"Storage provider '{settings.STORAGE_PROVIDER}' is not implemented yet.")
