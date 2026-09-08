from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel
from app.models.artifact import ArtifactKind
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.test_repo import TestRepository
from app.storage.local import get_storage_provider

router = APIRouter(prefix="/tests", tags=["Artifacts"])


class ArtifactSummaryResponse(BaseModel):
    kind: str
    source: str
    size_bytes: int
    sha256: str
    available: bool
    download_url: str


@router.get("/{test_identifier}/artifacts", response_model=List[ArtifactSummaryResponse])
async def list_test_artifacts(
    test_identifier: str,
):
    """Lists all stored artifacts (syllabus, question paper) for a given test."""
    test_repo = TestRepository()
    test = await test_repo.get_by_id_or_external_id(test_identifier)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_identifier}' not found."
        )

    artifact_repo = ArtifactRepository()
    artifacts = await artifact_repo.find_all({"test_id": str(test.id)})

    summaries = []
    for art in artifacts:
        summaries.append(
            ArtifactSummaryResponse(
                kind=art.kind.value,
                source=art.source,
                size_bytes=art.size_bytes,
                sha256=art.sha256,
                available=True,
                download_url=f"/api/v1/tests/{test.external_test_id}/artifacts/{art.kind.value}"
            )
        )
    return summaries


@router.get("/{test_identifier}/artifacts/{kind}")
async def get_test_artifact_file(
    test_identifier: str,
    kind: str,
):
    """Streams the binary PDF for a test artifact (syllabus or question_paper) directly for viewing or download."""
    if kind not in [ArtifactKind.SYLLABUS.value, ArtifactKind.QUESTION_PAPER.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid artifact kind '{kind}'. Valid kinds are 'syllabus' and 'question_paper'."
        )

    test_repo = TestRepository()
    test = await test_repo.get_by_id_or_external_id(test_identifier)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_identifier}' not found."
        )

    artifact_repo = ArtifactRepository()
    artifact = await artifact_repo.get_by_test_and_kind(str(test.id), ArtifactKind(kind))
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{kind}' for test '{test.name}' ({test_identifier}) has not been acquired or is not available."
        )

    storage = get_storage_provider()
    content = await storage.get(artifact.storage_key)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact file not found in storage provider for key '{artifact.storage_key}'."
        )

    safe_title = "".join(c for c in test.name if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")
    filename = f"{safe_title}_{kind}.pdf"

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Content-Type": "application/pdf",
        "Content-Length": str(len(content)),
        "Cache-Control": "public, max-age=86400",
    }

    return Response(content=content, media_type="application/pdf", headers=headers)
