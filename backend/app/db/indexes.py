import logging
from pymongo import ASCENDING, IndexModel
from app.db.mongo import get_database

logger = logging.getLogger(__name__)


async def create_indexes():
    """Idempotently provisions all required MongoDB compound & unique indexes."""
    db = get_database()
    logger.info("Ensuring MongoDB indexes...")

    # tests: unique external source + ID, date index, status index
    await db["tests"].create_indexes([
        IndexModel(
            [("external_source", ASCENDING), ("external_test_id", ASCENDING)],
            unique=True,
            name="idx_tests_external_unique"
        ),
        IndexModel([("date", ASCENDING)], name="idx_tests_date"),
        IndexModel([("processing_status", ASCENDING)], name="idx_tests_status")
    ])

    # topics: unique canonical_key, subject + name
    await db["topics"].create_indexes([
        IndexModel([("canonical_key", ASCENDING)], unique=True, name="idx_topics_canonical_key_unique"),
        IndexModel([("subject", ASCENDING), ("name", ASCENDING)], name="idx_topics_subject_name")
    ])

    # test_topics: unique (test_id, topic_id), topic_id lookup, test_id lookup
    await db["test_topics"].create_indexes([
        IndexModel([("test_id", ASCENDING), ("topic_id", ASCENDING)], unique=True, name="idx_test_topics_unique"),
        IndexModel([("topic_id", ASCENDING)], name="idx_test_topics_by_topic"),
        IndexModel([("test_id", ASCENDING)], name="idx_test_topics_by_test"),
        IndexModel([("canonical_key", ASCENDING)], name="idx_test_topics_canonical_key"),
        IndexModel([("subject", ASCENDING)], name="idx_test_topics_subject")
    ])

    # artifacts: unique (source, stable_object_key, kind), test_id + kind
    await db["artifacts"].create_indexes([
        IndexModel(
            [("source", ASCENDING), ("stable_object_key", ASCENDING), ("kind", ASCENDING)],
            unique=True,
            name="idx_artifacts_unique_key"
        ),
        IndexModel([("test_id", ASCENDING), ("kind", ASCENDING)], name="idx_artifacts_test_kind")
    ])

    # syllabus_snapshots: test_id, content_hash
    await db["syllabus_snapshots"].create_indexes([
        IndexModel([("test_id", ASCENDING)], name="idx_snapshots_test_id"),
        IndexModel([("content_hash", ASCENDING)], name="idx_snapshots_hash")
    ])

    logger.info("MongoDB indexes successfully created.")
