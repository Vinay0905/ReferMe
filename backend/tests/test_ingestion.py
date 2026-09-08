import pytest
from app.ingestion.orchestrator import IngestionOrchestrator
from app.integrations.allen.client import AllenClient
from app.models.common import ProcessingStatus
from app.models.ingestion import IngestionStatus
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.ingestion_repo import IngestionJobRepository
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository


def test_allen_client_parse_card():
    raw_card = {
        "test_id": "9876",
        "title": "MINOR TEST - 3 (DLP)",
        "status": "UPCOMING",
        "labels": [
            {"text": "25 Oct"},
            {"text": "180 Min"},
            {"text": "Offline"}
        ],
        "category": "DLP",
        "link_cta": {
            "action": {
                "data": {"uri": "/api/v1/tests/9876/syllabus"}
            }
        }
    }
    parsed = AllenClient.parse_test_card(raw_card)

    assert parsed.test_id == "9876"
    assert parsed.title == "MINOR TEST - 3 (DLP)"
    assert parsed.date_str == "25 Oct"
    assert parsed.duration_minutes == 180
    assert parsed.mode == "Offline"
    assert parsed.syllabus_uri == "/api/v1/tests/9876/syllabus"


@pytest.mark.asyncio
async def test_allen_client_mock_mode():
    client = AllenClient(mock_mode=True)
    tests = await client.list_tests()
    assert len(tests) == 3
    assert tests[0].test_id == "test_101"

    all_tests = await client.list_all_tests()
    assert len(all_tests) == 3

    syllabus_bytes = await client.get_syllabus_pdf("test_101")
    assert syllabus_bytes is not None
    assert len(syllabus_bytes) > 100

    qp_bytes = await client.get_question_paper_pdf("test_101")
    assert qp_bytes is not None
    assert len(qp_bytes) > 100


def test_allen_client_contextual_headers(monkeypatch):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "ALLEN_CLIENT_TYPE", "web")
    monkeypatch.setattr(settings, "ALLEN_DEVICE_ID", "device-xyz")
    monkeypatch.setattr(settings, "ALLEN_BATCH_LIST", "batch-1,batch-2")
    monkeypatch.setattr(settings, "ALLEN_COURSE_ID", "course-42")

    client = AllenClient(auth_token="dummy-jwt")
    headers = client._get_headers()

    assert headers["Authorization"] == "Bearer dummy-jwt"
    assert headers["x-client-type"] == "web"
    assert headers["x-device-id"] == "device-xyz"
    assert headers["x-selected-batch-list"] == "batch-1,batch-2"
    assert headers["x-selected-course-id"] == "course-42"


@pytest.mark.asyncio
async def test_ingestion_orchestrator_mock_run(tmp_path, monkeypatch):
    # Route storage to temporary test directory
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))

    client = AllenClient(mock_mode=True)
    orchestrator = IngestionOrchestrator(allen_client=client)

    job = await orchestrator.run(max_tests=2)

    assert job.status == IngestionStatus.COMPLETED
    assert job.discovered_count == 2
    assert job.succeeded_count == 2
    assert job.failed_count == 0

    # Verify TestRepository persisted tests
    test_repo = TestRepository()
    test_doc = await test_repo.get_by_external_id("allen", "test_101")
    assert test_doc is not None
    assert test_doc.has_syllabus is True
    assert test_doc.has_question_paper is True
    assert test_doc.processing_status == ProcessingStatus.READY

    # Verify TopicRepository populated canonical topics
    topic_repo = TopicRepository()
    all_topics = await topic_repo.find_all()
    assert len(all_topics) > 0

    # Verify Relationships in TestTopicRepository
    rel_repo = TestTopicRepository()
    test_topics = await rel_repo.find_by_test_id(str(test_doc.id))
    assert len(test_topics) > 0
    assert all(t.test_id == str(test_doc.id) for t in test_topics)

    # Verify ArtifactRepository recorded both syllabus and question paper
    artifact_repo = ArtifactRepository()
    artifacts = await artifact_repo.find_all({"test_id": str(test_doc.id)})
    assert len(artifacts) == 2
    kinds = {a.kind.value for a in artifacts}
    assert "syllabus" in kinds
    assert "question_paper" in kinds


@pytest.mark.asyncio
async def test_ingestion_idempotency(tmp_path, monkeypatch):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))

    client = AllenClient(mock_mode=True)
    orchestrator = IngestionOrchestrator(allen_client=client)

    # Run twice
    job1 = await orchestrator.run(max_tests=1)
    job2 = await orchestrator.run(max_tests=1)

    assert job1.status == IngestionStatus.COMPLETED
    assert job2.status == IngestionStatus.COMPLETED

    test_repo = TestRepository()
    tests = await test_repo.find_all()
    # Still exactly 1 test, not duplicated
    assert len(tests) == 1

    rel_repo = TestTopicRepository()
    relations = await rel_repo.find_by_test_id(str(tests[0].id))
    # Relationships were replaced cleanly, not duplicated
    distinct_keys = {r.canonical_key for r in relations}
    assert len(relations) == len(distinct_keys)


@pytest.mark.asyncio
async def test_allen_client_pagination_loop(monkeypatch):
    from unittest.mock import AsyncMock
    from app.integrations.allen.client import RawAllenTestCard

    client = AllenClient(mock_mode=False, auth_token="fake-token")

    async def fake_list_tests(status="all", mode="all", page_number=1, page_size=25):
        if page_number == 1:
            return [
                RawAllenTestCard(test_id="1", title="Test 1"),
                RawAllenTestCard(test_id="2", title="Test 2"),
            ]
        elif page_number == 2:
            return [
                RawAllenTestCard(test_id="3", title="Test 3"),
            ]
        return []

    monkeypatch.setattr(client, "list_tests", fake_list_tests)

    # page_size=2: page 1 returns 2 (full), page 2 returns 1 (< page_size, terminates)
    results = await client.list_all_tests(page_size=2, max_pages=10)
    assert len(results) == 3
    assert [r.test_id for r in results] == ["1", "2", "3"]
