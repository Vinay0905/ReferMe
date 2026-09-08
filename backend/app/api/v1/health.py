from fastapi import APIRouter, HTTPException, status
from app.db.mongo import get_database

router = APIRouter()


@router.get("/health", summary="Basic health check")
async def health():
    return {"status": "ok", "service": "referme-neet-backend"}


@router.get("/ready", summary="Readiness check for database connectivity")
async def ready():
    try:
        db = get_database()
        await db.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not reachable: {str(exc)}"
        )
