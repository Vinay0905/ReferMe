import pytest
from httpx import ASGITransport, AsyncClient
from app.config import get_settings
from app.ingestion.orchestrator import IngestionOrchestrator
from app.integrations.allen.client import AllenClient
from app.main import app


async def seed_data(tmp_path, monkeypatch):
    """Helper to seed the in-memory mock database and point storage to tmp_path."""
    settings = get_settings()
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))
    orchestrator = IngestionOrchestrator(allen_client=AllenClient(mock_mode=True))
    await orchestrator.run(max_tests=2)


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        resp = await client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_list_tests(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tests?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2
        first = data["items"][0]
        assert "id" in first
        assert "external_test_id" in first
        assert "name" in first
        assert first["has_syllabus"] is True


@pytest.mark.asyncio
async def test_test_identifier_resolution(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Fetch list to get internal ID
        list_resp = await client.get("/api/v1/tests")
        test_item = list_resp.json()["items"][0]
        internal_id = test_item["id"]
        external_id = test_item["external_test_id"]

        # 1. Fetch by internal ObjectId
        resp1 = await client.get(f"/api/v1/tests/{internal_id}")
        assert resp1.status_code == 200
        assert resp1.json()["id"] == internal_id
        assert resp1.json()["total_topics"] > 0

        # 2. Fetch by external_test_id
        resp2 = await client.get(f"/api/v1/tests/{external_id}")
        assert resp2.status_code == 200
        assert resp2.json()["external_test_id"] == external_id
        assert resp2.json()["id"] == internal_id

        # 3. Non-existent test
        resp3 = await client.get("/api/v1/tests/non_existent_9999")
        assert resp3.status_code == 404


@pytest.mark.asyncio
async def test_test_topics_grouped_by_subject(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/v1/tests")
        external_id = list_resp.json()["items"][0]["external_test_id"]

        resp = await client.get(f"/api/v1/tests/{external_id}/topics")
        assert resp.status_code == 200
        data = resp.json()

        assert "subjects" in data
        assert "physics" in data["subjects"]
        assert "chemistry" in data["subjects"]
        assert "biology" in data["subjects"]
        assert data["total_topics"] > 0

        # Verify each topic item structure
        for topic_item in data["subjects"]["physics"]:
            assert "canonical_key" in topic_item
            assert topic_item["subject"].lower() == "physics"
            assert "source_text" in topic_item


@pytest.mark.asyncio
async def test_topics_search_and_filter(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All topics
        resp = await client.get("/api/v1/topics?page=1&page_size=100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

        # Subject filter
        resp_phys = await client.get("/api/v1/topics?subject=physics")
        assert resp_phys.status_code == 200
        phys_items = resp_phys.json()["items"]
        assert len(phys_items) > 0
        assert all(item["subject"].lower() == "physics" for item in phys_items)

        # Search filter
        resp_search = await client.get("/api/v1/topics?q=physics")
        assert resp_search.status_code == 200


@pytest.mark.asyncio
async def test_topic_tests_bidirectional_lookup(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get a topic
        resp = await client.get("/api/v1/topics?page=1&page_size=5")
        topic = resp.json()["items"][0]
        canonical_key = topic["canonical_key"]

        # Bidirectional lookup: Topic -> Tests
        resp_tests = await client.get(f"/api/v1/topics/{canonical_key}/tests")
        assert resp_tests.status_code == 200
        lookup_data = resp_tests.json()

        assert lookup_data["topic"]["canonical_key"] == canonical_key
        assert lookup_data["total_tests"] >= 1
        assert len(lookup_data["tests"]) >= 1

        first_test = lookup_data["tests"][0]
        assert "external_test_id" in first_test
        assert "name" in first_test
        assert "source_text" in first_test


@pytest.mark.asyncio
async def test_artifact_listing_and_streaming(tmp_path, monkeypatch):
    await seed_data(tmp_path, monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Fetch test
        list_resp = await client.get("/api/v1/tests")
        external_id = list_resp.json()["items"][0]["external_test_id"]

        # List artifacts
        art_list_resp = await client.get(f"/api/v1/tests/{external_id}/artifacts")
        assert art_list_resp.status_code == 200
        artifacts = art_list_resp.json()
        assert len(artifacts) >= 1
        kinds = {a["kind"] for a in artifacts}
        assert "syllabus" in kinds

        # Stream syllabus PDF
        pdf_resp = await client.get(f"/api/v1/tests/{external_id}/artifacts/syllabus")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert "inline" in pdf_resp.headers["content-disposition"]
        assert len(pdf_resp.content) > 0

        # Stream question paper PDF
        qp_resp = await client.get(f"/api/v1/tests/{external_id}/artifacts/question_paper")
        assert qp_resp.status_code == 200
        assert qp_resp.headers["content-type"] == "application/pdf"
        assert len(qp_resp.content) > 0

        # Invalid artifact kind
        bad_resp = await client.get(f"/api/v1/tests/{external_id}/artifacts/invalid_kind")
        assert bad_resp.status_code == 400
