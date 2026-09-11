import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.common import Subject
from app.models.relationship import QuestionClassificationMethod
from app.models.test import TestModel
from app.repositories.question_repo import QuestionRepository
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.common import PaginatedResponse
from app.schemas.question import QuestionItemResponse
from app.schemas.test import (
    TestDetailResponse,
    TestResponse,
    TestTopicItem,
    TestTopicsResponse,
)

router = APIRouter(prefix="/tests", tags=["Tests"])


def _to_test_response(test: TestModel) -> TestResponse:
    return TestResponse(
        id=str(test.id),
        external_test_id=test.external_test_id,
        name=test.name,
        date=test.date,
        duration_minutes=test.duration_minutes,
        mode=test.mode,
        status=test.status,
        category=test.category,
        target_class=getattr(test, "target_class", "12th") or "12th",
        course_id=getattr(test, "course_id", None),
        course_name=getattr(test, "course_name", None),
        processing_status=test.processing_status,
        has_syllabus=test.has_syllabus,
        has_question_paper=test.has_question_paper,
        created_at=test.created_at,
        updated_at=test.updated_at,
    )


@router.get("", response_model=PaginatedResponse[TestResponse])
async def list_tests(
    q: Optional[str] = Query(None, description="Search tests by title or name"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., UPCOMING, FINAL_RESULT_GENERATED)"),
    mode: Optional[str] = Query(None, description="Filter by mode (e.g., Offline, Online)"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., DLP, MINOR)"),
    target_class: Optional[str] = Query(None, description="Filter by class: '12th' or '11th'"),
    has_syllabus: Optional[bool] = Query(None, description="Filter by syllabus availability"),
    has_question_paper: Optional[bool] = Query(None, description="Filter by question paper availability"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Lists tests with filtering, search, and pagination."""
    test_repo = TestRepository()
    filter_query: Dict[str, Any] = {}

    if q:
        filter_query["name"] = {"$regex": re.escape(q.strip()), "$options": "i"}
    if status:
        filter_query["status"] = status
    if mode:
        filter_query["mode"] = {"$regex": f"^{re.escape(mode.strip())}$", "$options": "i"}
    if category:
        filter_query["category"] = {"$regex": f"^{re.escape(category.strip())}$", "$options": "i"}
    if target_class and target_class.lower() != "all":
        filter_query["target_class"] = {"$regex": f"^{re.escape(target_class.strip())}$", "$options": "i"}
    if has_syllabus is not None:
        filter_query["has_syllabus"] = has_syllabus
    if has_question_paper is not None:
        filter_query["has_question_paper"] = has_question_paper

    total = await test_repo.count(filter_query)
    skip = (page - 1) * page_size
    sort_criteria = [("created_at", -1)]

    tests = await test_repo.find_all(filter_query, skip=skip, limit=page_size, sort=sort_criteria)
    items = [_to_test_response(t) for t in tests]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{test_identifier}", response_model=TestDetailResponse)
async def get_test(
    test_identifier: str,
):
    """Retrieves test details by internal ID (_id) or external ALLEN test ID."""
    test_repo = TestRepository()
    test = await test_repo.get_by_id_or_external_id(test_identifier)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_identifier}' not found."
        )

    test_topic_repo = TestTopicRepository()
    rels = await test_topic_repo.find_by_test_id(str(test.id))

    by_subject: Dict[str, int] = {}
    for r in rels:
        subj = r.subject.value
        by_subject[subj] = by_subject.get(subj, 0) + 1

    base_resp = _to_test_response(test)
    return TestDetailResponse(
        **base_resp.model_dump(),
        total_topics=len(rels),
        topics_count_by_subject=by_subject,
    )


@router.get("/{test_identifier}/topics", response_model=TestTopicsResponse)
async def get_test_topics(
    test_identifier: str,
):
    """Retrieves all topics in a test's syllabus grouped by Subject (Physics, Chemistry, Biology)."""
    test_repo = TestRepository()
    test = await test_repo.get_by_id_or_external_id(test_identifier)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_identifier}' not found."
        )

    test_topic_repo = TestTopicRepository()
    topic_repo = TopicRepository()

    rels = await test_topic_repo.find_by_test_id(str(test.id))

    # Pre-fetch topic details for display names
    topic_ids = [r.topic_id for r in rels if r.topic_id]
    topic_map = {}
    for tid in set(topic_ids):
        topic_doc = await topic_repo.get_by_id(tid)
        if topic_doc:
            topic_map[tid] = topic_doc.name

    subjects_dict: Dict[str, List[TestTopicItem]] = {
        "physics": [],
        "chemistry": [],
        "biology": []
    }

    for r in rels:
        subj_key = r.subject.value.lower()
        if subj_key not in subjects_dict:
            subjects_dict[subj_key] = []

        item_name = topic_map.get(r.topic_id) or r.canonical_key.split(":")[-1].replace("-", " ").title()
        subjects_dict[subj_key].append(
            TestTopicItem(
                topic_id=r.topic_id,
                name=item_name,
                canonical_key=r.canonical_key,
                subject=r.subject,
                source_text=r.source_text,
                source_section=r.source_section,
                confidence=r.confidence,
            )
        )

    return TestTopicsResponse(
        test_id=str(test.id),
        external_test_id=test.external_test_id,
        test_name=test.name,
        total_topics=len(rels),
        subjects=subjects_dict,
    )


@router.get("/{test_identifier}/questions", response_model=PaginatedResponse[QuestionItemResponse])
async def get_test_questions(
    test_identifier: str,
    subject: Optional[str] = Query(None, description="Filter by subject: physics, chemistry, biology"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(200, ge=1, le=500, description="Items per page"),
):
    """Retrieves all questions belonging to this test paper, ordered by question number."""
    test_repo = TestRepository()
    test = await test_repo.get_by_id_or_external_id(test_identifier)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_identifier}' not found."
        )

    question_repo = QuestionRepository()
    filter_query: Dict[str, Any] = {
        "$or": [
            {"test_id": str(test.id)},
            {"external_test_id": test.external_test_id}
        ]
    }

    if subject:
        s_lower = subject.lower()
        if s_lower == "physics":
            filter_query["subject"] = Subject.PHYSICS
        elif s_lower == "chemistry":
            filter_query["subject"] = Subject.CHEMISTRY
        elif s_lower == "biology":
            filter_query["subject"] = Subject.BIOLOGY

    total = await question_repo.count(filter_query)
    skip = (page - 1) * page_size
    questions = await question_repo.find_all(
        filter_query,
        skip=skip,
        limit=page_size,
        sort=[("question_number", 1)]
    )

    items: List[QuestionItemResponse] = [
        QuestionItemResponse(
            id=str(q.id),
            test_id=str(test.id),
            external_test_id=test.external_test_id,
            test_name=test.name,
            question_number=q.question_number,
            subject_question_number=q.subject_question_number,
            subject=q.subject,
            question_text=q.question_text,
            options=q.options or [],
            answer=q.answer,
            source_page=q.source_page,
            bounding_box=q.bounding_box,
            image_url=q.image_url or f"/api/v1/questions/{str(q.id)}/image",
            canonical_key=getattr(q, "canonical_key", "") or "",
            classification_method=getattr(q, "classification_method", QuestionClassificationMethod.DETERMINISTIC),
            confidence=getattr(q, "confidence", 1.0),
        )
        for q in questions
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
