import logging
import os
from pathlib import Path
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response
from app.processing.question_cropper import QuestionCropper
from app.repositories.question_repo import QuestionRepository
from app.repositories.test_repo import TestRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["Questions"])

# In-memory path cache: resolves question images in <0.2ms with zero MongoDB roundtrips
_image_path_cache: Dict[str, str] = {}


@router.get("/{question_id}/image")
async def get_question_image(question_id: str):
    """Serves high-fidelity visual question snippet in WebP format.

    Fast Path (<0.2ms): Serves directly from memory-cached disk path with immutable headers.
    """
    cached_path = _image_path_cache.get(question_id)
    if cached_path and os.path.isfile(cached_path):
        return FileResponse(
            path=cached_path,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    question_repo = QuestionRepository()
    q = await question_repo.get_by_id(question_id)
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )

    # 1. Primary path: Pre-rendered WebP snippet exists
    if q.image_path and os.path.isfile(q.image_path):
        _image_path_cache[question_id] = q.image_path
        return FileResponse(
            path=q.image_path,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    # Check conventional storage path: storage_data/test_<external_test_id>/questions/q_<num>.webp
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    conventional_path = base_dir / "storage_data" / f"test_{q.external_test_id}" / "questions" / f"q_{q.question_number}.webp"
    if conventional_path.is_file():
        _image_path_cache[question_id] = str(conventional_path)
        return FileResponse(
            path=str(conventional_path),
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    # 2. Fallback path: Dynamically render from original PDF
    test_repo = TestRepository()
    test_doc = await test_repo.get_by_id(q.test_id)
    ext_id = test_doc.external_test_id if test_doc else q.external_test_id

    # Locate source question paper PDF
    pdf_path = base_dir / "storage_data" / f"test_{ext_id}" / "question_paper.pdf"
    if not pdf_path.is_file():
        # Try alternate path without 'test_' prefix
        pdf_path = base_dir / "storage_data" / ext_id / "question_paper.pdf"

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source question paper PDF not found for dynamic rendering.",
        )

    # If bounding box is missing, provide a safe default rect for that page
    bbox = q.bounding_box or [30.0, 50.0, 565.0, 780.0]

    output_file = str(conventional_path)
    webp_bytes = QuestionCropper.render_crop_webp(
        pdf_path=str(pdf_path),
        page_num=q.source_page,
        bbox=bbox,
        output_path=output_file,
    )

    if not webp_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render question snippet image.",
        )

    # Update question model with cached image path
    await question_repo.update(
        question_id,
        {
            "image_path": output_file,
            "image_url": f"/api/v1/questions/{question_id}/image",
        },
    )

    return Response(
        content=webp_bytes,
        media_type="image/webp",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )
