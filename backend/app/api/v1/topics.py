import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.common import Subject
from app.models.topic import TopicModel
from app.repositories.question_repo import QuestionRepository
from app.repositories.question_topic_repo import QuestionTopicRepository
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.common import PaginatedResponse
from app.schemas.question import QuestionItemResponse
from app.schemas.topic import (
    TopicResponse,
    TopicTestItem,
    TopicWithTestsResponse,
)


router = APIRouter(prefix="/topics", tags=["Topics"])


def _to_topic_response(topic: TopicModel) -> TopicResponse:
    return TopicResponse(
        id=str(topic.id),
        subject=topic.subject,
        name=topic.name,
        canonical_key=topic.canonical_key,
        aliases=topic.aliases,
        test_count=topic.test_count,
        target_classes=getattr(topic, "target_classes", []) or [],
        active=topic.active,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
    )


@router.get("", response_model=PaginatedResponse[TopicResponse])
async def list_topics(
    q: Optional[str] = Query(None, description="Search topics by name, canonical key, or alias"),
    subject: Optional[str] = Query(None, description="Filter by subject: physics, chemistry, biology"),
    target_class: Optional[str] = Query(None, description="Filter by target class (e.g. '11th', '12th')"),
    sort_by: str = Query("test_count", description="Field to sort by: test_count, name, created_at"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """Lists and searches topics with filtering by subject and popularity sorting."""
    topic_repo = TopicRepository()
    filter_query: Dict[str, Any] = {"active": True}

    if subject:
        filter_query["subject"] = {"$regex": f"^{re.escape(subject.strip())}$", "$options": "i"}

    if target_class and target_class.lower() != "all":
        filter_query["target_classes"] = target_class

    if q:
        escaped_q = re.escape(q.strip())
        filter_query["$or"] = [
            {"name": {"$regex": escaped_q, "$options": "i"}},
            {"canonical_key": {"$regex": escaped_q, "$options": "i"}},
            {"aliases": {"$regex": escaped_q, "$options": "i"}},
        ]

    sort_direction = -1 if order.lower() == "desc" else 1
    sort_field = sort_by if sort_by in ["test_count", "name", "created_at"] else "test_count"
    sort_criteria = [(sort_field, sort_direction)]
    # Secondary sort by name
    if sort_field != "name":
        sort_criteria.append(("name", 1))

    total = await topic_repo.count(filter_query)
    skip = (page - 1) * page_size

    topics = await topic_repo.find_all(filter_query, skip=skip, limit=page_size, sort=sort_criteria)
    items = [_to_topic_response(t) for t in topics]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{topic_identifier}", response_model=TopicResponse)
async def get_topic(
    topic_identifier: str,
):
    """Retrieves topic details by MongoDB ID (_id) or canonical key (e.g. 'physics:rotational-motion')."""
    topic_repo = TopicRepository()
    topic = await topic_repo.get_by_id_or_canonical_key(topic_identifier)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_identifier}' not found."
        )
    return _to_topic_response(topic)


@router.get("/{topic_identifier}/tests", response_model=TopicWithTestsResponse)
async def get_topic_tests(
    topic_identifier: str,
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit tests returned"),
):
    """Bidirectional Lookup: Returns every test whose syllabus includes this topic."""
    topic_repo = TopicRepository()
    topic = await topic_repo.get_by_id_or_canonical_key(topic_identifier)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_identifier}' not found."
        )

    test_topic_repo = TestTopicRepository()
    test_repo = TestRepository()

    # Query all relations for this topic
    rels = await test_topic_repo.find_by_topic_id(str(topic.id), skip=skip, limit=limit)
    total_matches = await test_topic_repo.count({"topic_id": str(topic.id)})

    test_items: List[TopicTestItem] = []
    # Fetch test details for each matched relationship
    for r in rels:
        test_doc = await test_repo.get_by_id(r.test_id)
        if test_doc:
            test_items.append(
                TopicTestItem(
                    test_id=str(test_doc.id),
                    external_test_id=test_doc.external_test_id,
                    name=test_doc.name,
                    date=test_doc.date,
                    duration_minutes=test_doc.duration_minutes,
                    mode=test_doc.mode,
                    status=test_doc.status,
                    category=test_doc.category,
                    target_class=getattr(test_doc, "target_class", "12th") or "12th",
                    has_syllabus=test_doc.has_syllabus,
                    has_question_paper=test_doc.has_question_paper,
                    source_text=r.source_text,
                    source_section=r.source_section,
                )
            )

    return TopicWithTestsResponse(
        topic=_to_topic_response(topic),
        total_tests=total_matches,
        tests=test_items,
    )


@router.get("/{topic_identifier}/questions", response_model=PaginatedResponse[QuestionItemResponse])
async def get_topic_questions(
    topic_identifier: str,
    test_id: Optional[str] = Query(None, description="Filter by test ID or external test ID"),
    subject: Optional[str] = Query(None, description="Filter by subject: physics, chemistry, biology"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Retrieves all questions testing this topic via indexed MongoDB queries.

    Performs zero runtime classification.
    """
    topic_repo = TopicRepository()
    topic = await topic_repo.get_by_id_or_canonical_key(topic_identifier)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_identifier}' not found."
        )

    test_repo = TestRepository()
    resolved_test_id = None
    if test_id:
        test_doc = await test_repo.get_by_id_or_external_id(test_id)
        if test_doc:
            resolved_test_id = str(test_doc.id)
        else:
            resolved_test_id = test_id

    subject_filter = None
    if subject:
        # Standardize subject filter
        s_lower = subject.lower()
        if s_lower == "physics":
            subject_filter = Subject.PHYSICS
        elif s_lower == "chemistry":
            subject_filter = Subject.CHEMISTRY
        elif s_lower == "biology":
            subject_filter = Subject.BIOLOGY

    skip = (page - 1) * page_size
    question_topic_repo = QuestionTopicRepository()
    question_repo = QuestionRepository()

    total = await question_topic_repo.count_by_topic_id(
        topic_id=str(topic.id),
        test_id=resolved_test_id,
        subject=subject_filter
    )

    rels = await question_topic_repo.find_by_topic_id(
        topic_id=str(topic.id),
        test_id=resolved_test_id,
        subject=subject_filter,
        skip=skip,
        limit=page_size
    )

    if not rels:
        return PaginatedResponse.create(items=[], total=total, page=page, page_size=page_size)

    # Batch fetch questions by ID (no N+1!)
    q_ids = [r.question_id for r in rels]
    questions = await question_repo.get_by_ids(q_ids)
    q_by_id = {str(q.id): q for q in questions}

    # Batch fetch tests by ID
    unique_test_ids = {r.test_id for r in rels}
    test_names_by_id: Dict[str, str] = {}
    for tid in unique_test_ids:
        t_doc = await test_repo.get_by_id(tid)
        if t_doc:
            test_names_by_id[tid] = t_doc.name

    items: List[QuestionItemResponse] = []
    for r in rels:
        q_doc = q_by_id.get(r.question_id)
        if q_doc:
            items.append(
                QuestionItemResponse(
                    id=str(q_doc.id),
                    test_id=r.test_id,
                    external_test_id=r.external_test_id or q_doc.external_test_id,
                    test_name=test_names_by_id.get(r.test_id),
                    question_number=q_doc.question_number,
                    subject_question_number=q_doc.subject_question_number,
                    subject=q_doc.subject,
                    question_text=q_doc.question_text,
                    options=q_doc.options,
                    answer=q_doc.answer,
                    source_page=q_doc.source_page,
                    bounding_box=q_doc.bounding_box,
                    image_url=q_doc.image_url or f"/api/v1/questions/{str(q_doc.id)}/image",
                    canonical_key=r.canonical_key,
                    classification_method=r.classification_method,
                    confidence=r.confidence,
                )
            )

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)

