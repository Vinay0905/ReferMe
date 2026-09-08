from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel
from app.ingestion.orchestrator import IngestionOrchestrator
from app.integrations.allen.client import AllenClient
from app.models.ingestion import IngestionJobModel
from app.repositories.ingestion_repo import IngestionJobRepository

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class IngestTriggerRequest(BaseModel):
    status: str = "all"
    mode: str = "all"
    limit: Optional[int] = None
    mock: Optional[bool] = None


class IngestTriggerResponse(BaseModel):
    message: str
    job_id: str
    status: str


async def _run_background_ingest(
    status_filter: str,
    mode_filter: str,
    limit: Optional[int],
    mock: Optional[bool]
):
    client = AllenClient(mock_mode=mock) if mock is not None else None
    orchestrator = IngestionOrchestrator(allen_client=client)
    await orchestrator.run(
        status=status_filter,
        mode=mode_filter,
        max_tests=limit
    )


@router.post("/run", response_model=IngestTriggerResponse, summary="Trigger test ingestion in the background")
async def trigger_ingestion(
    req: IngestTriggerRequest,
    background_tasks: BackgroundTasks
):
    job_repo = IngestionJobRepository()
    # Create initial job placeholder
    job = IngestionJobModel()
    job_id = await job_repo.insert(job)

    # Dispatch to background task
    background_tasks.add_task(
        _run_background_ingest,
        req.status,
        req.mode,
        req.limit,
        req.mock
    )

    return IngestTriggerResponse(
        message="Ingestion process started in background.",
        job_id=job_id,
        status="RUNNING"
    )


@router.get("/jobs", response_model=List[IngestionJobModel], summary="List past ingestion runs")
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    job_repo = IngestionJobRepository()
    return await job_repo.find_all(skip=skip, limit=limit, sort=[("start_time", -1)])


@router.get("/jobs/{job_id}", response_model=IngestionJobModel, summary="Get details and progress of an ingestion job")
async def get_job(job_id: str):
    job_repo = IngestionJobRepository()
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")
    return job
