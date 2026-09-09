from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.storage.base import ArtifactStorage


class LocalArtifactStorage(ArtifactStorage):
    """Stores binary PDF artifacts on the local filesystem."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_settings().storage_path

    def _resolve_safe_path(self, storage_key: str) -> Optional[Path]:
        """Resolves path and guarantees it resides within base_dir."""
        if not storage_key:
            return None
        try:
            p = Path(storage_key)
            if not p.is_absolute():
                p = self.base_dir / p
            resolved = p.resolve()
            base_resolved = self.base_dir.resolve()
            if resolved == base_resolved or base_resolved in resolved.parents:
                return resolved
            return None
        except Exception:
            return None

    async def save(self, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        safe_key = key.lstrip("/\\")
        target_path = (self.base_dir / safe_key).resolve()
        base_resolved = self.base_dir.resolve()
        if base_resolved not in target_path.parents and target_path != base_resolved:
            raise ValueError(f"Path traversal detected for key: {key}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return str(target_path)

    async def get(self, storage_key: str) -> Optional[bytes]:
        safe_path = self._resolve_safe_path(storage_key)
        if not safe_path or not safe_path.exists() or not safe_path.is_file():
            return None
        return safe_path.read_bytes()

    async def exists(self, storage_key: str) -> bool:
        safe_path = self._resolve_safe_path(storage_key)
        return bool(safe_path and safe_path.exists() and safe_path.is_file())

    async def delete(self, storage_key: str) -> bool:
        safe_path = self._resolve_safe_path(storage_key)
        if safe_path and safe_path.exists() and safe_path.is_file():
            safe_path.unlink()
            return True
        return False


def get_storage_provider() -> ArtifactStorage:
    settings = get_settings()
    if settings.STORAGE_PROVIDER == "local":
        return LocalArtifactStorage()
    raise NotImplementedError(f"Storage provider '{settings.STORAGE_PROVIDER}' is not implemented yet.")
