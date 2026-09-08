import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.common import Subject
from app.models.topic import TopicModel
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.common import PaginatedResponse
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
        active=topic.active,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
    )


@router.get("", response_model=PaginatedResponse[TopicResponse])
async def list_topics(
    q: Optional[str] = Query(None, description="Search topics by name, canonical key, or alias"),
    subject: Optional[str] = Query(None, description="Filter by subject: physics, chemistry, biology"),
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
