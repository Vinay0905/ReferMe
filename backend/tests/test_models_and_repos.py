import pytest
from app.models.common import ProcessingStatus, Subject
from app.models.relationship import TestTopicModel
from app.models.test import TestModel
from app.models.topic import TopicModel
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.storage.local import LocalArtifactStorage


@pytest.mark.asyncio
async def test_test_repo_upsert():
    repo = TestRepository()
    test = TestModel(
        external_source="allen",
        external_test_id="test_9999",
        name="MINOR TEST 1",
        mode="Offline",
        processing_status=ProcessingStatus.DISCOVERED,
    )
    test_id = await repo.upsert(test)
    assert test_id != ""

    fetched = await repo.get_by_external_id("allen", "test_9999")
    assert fetched is not None
    assert fetched.name == "MINOR TEST 1"
    assert fetched.processing_status == ProcessingStatus.DISCOVERED


@pytest.mark.asyncio
async def test_topic_and_relationship():
    topic_repo = TopicRepository()
    rel_repo = TestTopicRepository()

    topic = TopicModel(
        subject=Subject.PHYSICS,
        name="Electric Current",
        canonical_key="physics:electric-current",
    )
    topic_id = await topic_repo.upsert_canonical(topic)
    assert topic_id != ""

    rel = TestTopicModel(
        test_id="test_internal_1",
        external_test_id="test_9999",
        topic_id=topic_id,
        canonical_key="physics:electric-current",
        subject=Subject.PHYSICS,
        source_text="Current Electricity - Electric Current",
    )
    await rel_repo.replace_for_test("test_internal_1", [rel])

    results = await rel_repo.find_by_topic_id(topic_id)
    assert len(results) == 1
    assert results[0].canonical_key == "physics:electric-current"
    assert results[0].source_text == "Current Electricity - Electric Current"


@pytest.mark.asyncio
async def test_local_storage(tmp_path):
    storage = LocalArtifactStorage(base_dir=tmp_path)
    sample_pdf_bytes = b"%PDF-1.4 sample content for testing"
    saved_path = await storage.save("test_9999/syllabus.pdf", sample_pdf_bytes)

    assert await storage.exists(saved_path)
    content = await storage.get(saved_path)
    assert content == sample_pdf_bytes
