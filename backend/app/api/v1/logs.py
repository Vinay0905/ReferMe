import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.core.logging_config import APP_LOG_PATH, ERRORS_LOG_PATH

router = APIRouter(prefix="/logs", tags=["Centralized Logs"])
client_logger = logging.getLogger("referme.client")


class ClientLogPayload(BaseModel):
    level: str = Field(default="ERROR", description="Log severity level: INFO, WARN, ERROR")
    message: str = Field(..., description="Description of the client-side error or event")
    url: Optional[str] = Field(default=None, description="Active page or requested API URL")
    component: Optional[str] = Field(default=None, description="UI Component name where error occurred")
    stack: Optional[str] = Field(default=None, description="Stack trace or extra debug context")
    user_agent: Optional[str] = Field(default=None, description="Browser user agent")


class LogEntryResponse(BaseModel):
    lines: List[str]
    count: int
    file: str


@router.post("/client", status_code=status.HTTP_202_ACCEPTED)
async def record_client_log(payload: ClientLogPayload):
    """Receives frontend error telemetry and writes it into the central server log."""
    msg = f"[CLIENT] {payload.message}"
    if payload.url:
        msg += f" | URL: {payload.url}"
    if payload.component:
        msg += f" | Component: {payload.component}"
    if payload.stack:
        msg += f"\n  Stack: {payload.stack}"

    lvl = payload.level.upper()
    if lvl == "INFO":
        client_logger.info(msg)
    elif lvl in ("WARN", "WARNING"):
        client_logger.warning(msg)
    else:
        client_logger.error(msg)

    return {"status": "recorded"}


@router.get("/recent", response_model=LogEntryResponse)
async def get_recent_logs(
    lines: int = Query(default=50, ge=1, le=500, description="Number of recent log lines to retrieve"),
    stream: str = Query(default="app", pattern="^(app|errors)$", description="Log stream: 'app' or 'errors'"),
):
    """Retrieves the latest log lines from app.log or errors.log for inspection and diagnostics."""
    target_path = ERRORS_LOG_PATH if stream == "errors" else APP_LOG_PATH

    if not target_path.exists():
        return LogEntryResponse(lines=[], count=0, file=target_path.name)

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        all_lines = [line for line in content.splitlines() if line.strip()]
        recent = all_lines[-lines:]
        return LogEntryResponse(lines=recent, count=len(recent), file=target_path.name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read log file: {e}",
        )
