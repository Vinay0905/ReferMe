import pytest
from httpx import ASGITransport, AsyncClient
from app.config import get_settings
from app.ingestion.orchestrator import IngestionOrchestrator
from app.integrations.allen.client import AllenClient
from app.main import app
from app.repositories.question_repo import QuestionRepository
from app.repositories.question_topic_repo import QuestionTopicRepository
from app.repositories.test_repo import TestRepository
from app.repositories.topic_repo import TopicRepository


@pytest.mark.asyncio
async def test_question_ingestion_and_api(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))

    # Run ingestion with mock client
    client = AllenClient(mock_mode=True)
    orchestrator = IngestionOrchestrator(allen_client=client)
    job = await orchestrator.run(max_tests=1)

    assert job.discovered_count == 1
    assert job.succeeded_count == 1

    # Verify questions persisted
    test_repo = TestRepository()
    tests = await test_repo.find_all()
    assert len(tests) == 1
    test_id = str(tests[0].id)

    q_repo = QuestionRepository()
    questions = await q_repo.find_by_test_id(test_id)
    assert len(questions) > 0
    q1 = questions[0]
    assert q1.question_number == 1
    assert q1.question_text != ""
    assert len(q1.options) == 4

    # Verify question_topics persisted
    qt_repo = QuestionTopicRepository()
    rels = await qt_repo.find_by_test_id(test_id)
    assert len(rels) > 0
    first_rel = rels[0]
    assert first_rel.question_id != ""
    assert first_rel.topic_id != ""
    assert first_rel.confidence > 0

    # Verify Idempotency: Run ingestion a second time
    job2 = await orchestrator.run(max_tests=1)
    assert job2.succeeded_count == 1

    # Counts must NOT have duplicated
    questions_after = await q_repo.find_by_test_id(test_id)
    assert len(questions_after) == len(questions)

    rels_after = await qt_repo.find_by_test_id(test_id)
    assert len(rels_after) == len(rels)
    current_rel = rels_after[0]

    # ---------------------------------------------------------------------
    # Test API: GET /api/v1/topics/{topic_identifier}/questions
    # ---------------------------------------------------------------------
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        topic_id = current_rel.topic_id
        canonical_key = current_rel.canonical_key

        # 1. Query by topic ObjectId
        resp1 = await http_client.get(f"/api/v1/topics/{topic_id}/questions?page=1&page_size=10")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["total"] >= 1
        assert len(data1["items"]) >= 1
        assert data1["items"][0]["id"] == current_rel.question_id
        assert data1["items"][0]["canonical_key"] == canonical_key


        # 2. Query by canonical_key
        resp2 = await http_client.get(f"/api/v1/topics/{canonical_key}/questions")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["total"] == data1["total"]

        # 3. Filter by test_id
        resp3 = await http_client.get(f"/api/v1/topics/{topic_id}/questions?test_id={test_id}")
        assert resp3.status_code == 200
        assert resp3.json()["total"] >= 1

        # 4. Non-existent topic -> 404
        resp4 = await http_client.get("/api/v1/topics/non_existent_topic_9999/questions")
        assert resp4.status_code == 404

        # 5. Topic with no questions -> returns empty list with total=0
        topic_repo = TopicRepository()
        all_topics = await topic_repo.find_all()
        # Find or create a topic with 0 questions
        empty_topic_id = "000000000000000000000000"
        for t in all_topics:
            c = await qt_repo.count_by_topic_id(str(t.id))
            if c == 0:
                empty_topic_id = str(t.id)
                break

        if empty_topic_id != "000000000000000000000000":
            resp5 = await http_client.get(f"/api/v1/topics/{empty_topic_id}/questions")
            assert resp5.status_code == 200
            assert resp5.json()["total"] == 0
            assert resp5.json()["items"] == []

        # ---------------------------------------------------------------------
        # Test API: GET /api/v1/tests/{test_identifier}/questions
        # ---------------------------------------------------------------------
        resp_test_q = await http_client.get(f"/api/v1/tests/{test_id}/questions")
        assert resp_test_q.status_code == 200
        test_q_data = resp_test_q.json()
        assert test_q_data["total"] == len(questions)
        assert len(test_q_data["items"]) == len(questions)
        assert test_q_data["items"][0]["question_number"] == 1
        assert test_q_data["items"][0]["test_id"] == test_id

        # Query by external_test_id
        ext_id = tests[0].external_test_id
        resp_ext = await http_client.get(f"/api/v1/tests/{ext_id}/questions")
        assert resp_ext.status_code == 200
        assert resp_ext.json()["total"] == len(questions)

        # 404 for non-existent test
        resp_404 = await http_client.get("/api/v1/tests/non_existent_test_999/questions")
        assert resp_404.status_code == 404
