import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.db.indexes import create_indexes
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.models.common import utc_now
from app.models.question import QuestionModel
from app.models.relationship import QuestionTopicModel
from app.processing.question_classifier import CandidateTopic, QuestionClassifier
from app.processing.question_cropper import QuestionCropper
from app.processing.question_parser import QuestionPaperParser
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.question_topic_repo import QuestionTopicRepository
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("referme.index_questions")


async def index_stored_question_papers():
    print("=" * 65)
    print("ReferMe: Stored Question Papers ↔ Topics Indexer")
    print("=" * 65)

    await connect_to_mongo()
    await create_indexes()

    settings = get_settings()
    test_repo = TestRepository()
    topic_repo = TopicRepository()
    test_topic_repo = TestTopicRepository()
    artifact_repo = ArtifactRepository()
    question_repo = QuestionRepository()
    question_topic_repo = QuestionTopicRepository()
    classifier = QuestionClassifier()

    tests = await test_repo.find_all(limit=100)
    print(f"Found {len(tests)} tests in database.")

    total_questions_indexed = 0
    total_questions_mapped = 0
    tests_processed = 0

    for test in tests:
        ext_id = test.external_test_id
        test_id = str(test.id)

        # Check for question_paper.pdf on disk
        storage_dir = Path(settings.LOCAL_STORAGE_DIR) / f"test_{ext_id}"
        qp_file = storage_dir / "question_paper.pdf"

        if not qp_file.exists():
            continue

        qp_bytes = qp_file.read_bytes()
        parsed_qp = QuestionPaperParser.parse(qp_bytes)

        if not parsed_qp.is_valid:
            print(f"⚠️ [{ext_id}] Failed to parse: {parsed_qp.warning}")
            continue

        # Look up artifact id if present
        qp_artifact = await artifact_repo.collection.find_one({"test_id": test_id, "kind": "question_paper"})
        artifact_id = str(qp_artifact["_id"]) if qp_artifact else None

        # Prepare directory for pre-generated question WebP crops
        questions_img_dir = storage_dir / "questions"
        questions_img_dir.mkdir(parents=True, exist_ok=True)

        question_entities = []
        for eq in parsed_qp.questions:
            # Determine image path and URL
            img_file = questions_img_dir / f"q_{eq.question_number}.webp"
            
            # Pre-generate WebP crop (Option 3 Primary with seamless cross-page stitch)
            if eq.bounding_box:
                # If question has an overflow region on next page, re-render to ensure seamless stitch
                if not img_file.exists() or eq.overflow_page:
                    QuestionCropper.render_crop_webp(
                        pdf_path=str(qp_file),
                        page_num=eq.source_page,
                        bbox=eq.bounding_box,
                        output_path=str(img_file),
                        overflow_page=eq.overflow_page,
                        overflow_bbox=eq.overflow_bounding_box,
                    )

            q_entity = QuestionModel(
                test_id=test_id,
                external_test_id=ext_id,
                question_number=eq.question_number,
                subject_question_number=eq.subject_question_number,
                subject=eq.subject,
                question_text=eq.question_text,
                options=eq.options,
                answer=eq.answer,
                artifact_id=artifact_id,
                source_page=eq.source_page,
                bounding_box=eq.bounding_box,
                overflow_page=eq.overflow_page,
                overflow_bounding_box=eq.overflow_bounding_box,
                image_url=None,  # Will be wired after question_id is assigned or generated
                image_path=str(img_file) if img_file.exists() else None,
                normalized_question_text=eq.normalized_question_text,
                fingerprint=eq.fingerprint,
                parser_version=QuestionPaperParser.VERSION,
                classification_status="UNRESOLVED",
                updated_at=utc_now()
            )
            question_entities.append(q_entity)

        # Build candidate topics from test's syllabus
        test_topics = await test_topic_repo.find_by_test_id(test_id)
        candidate_topics = []
        for tt in test_topics:
            topic_doc = await topic_repo.get_by_id(tt.topic_id)
            if topic_doc:
                candidate_topics.append(CandidateTopic(
                    topic_id=str(topic_doc.id),
                    canonical_key=topic_doc.canonical_key,
                    name=topic_doc.name,
                    subject=topic_doc.subject,
                    aliases=topic_doc.aliases,
                    source_text=tt.source_text
                ))

        question_topics = []
        resolved_count = 0
        for q_entity, eq in zip(question_entities, parsed_qp.questions):
            matches = classifier.classify_question(
                question=eq,
                candidate_topics=candidate_topics
            )
            if matches:
                q_entity.classification_status = "RESOLVED"
                resolved_count += 1
                for match in matches:
                    question_topics.append(QuestionTopicModel(
                        question_id="",
                        test_id=test_id,
                        external_test_id=ext_id,
                        topic_id=match.topic_id,
                        canonical_key=match.canonical_key,
                        subject=match.subject,
                        classification_method=match.classification_method,
                        confidence=match.confidence,
                        classifier_version="v1",
                        created_at=utc_now()
                    ))

        # Atomically replace questions for this test with updated classification_status & image_urls
        await question_repo.replace_for_test(test_id, question_entities)

        # Wire question_id into question_topics
        qt_idx = 0
        for q_entity, eq in zip(question_entities, parsed_qp.questions):
            matches = classifier.classify_question(
                question=eq,
                candidate_topics=candidate_topics
            )
            for _ in matches:
                question_topics[qt_idx].question_id = str(q_entity.id)
                qt_idx += 1

        # Atomically replace question_topic relationships for this test
        await question_topic_repo.replace_for_test(test_id, question_topics)


        # Update test has_question_paper
        if not test.has_question_paper:
            test.has_question_paper = True
            await test_repo.upsert(test)

        tests_processed += 1
        total_questions_indexed += len(question_entities)
        total_questions_mapped += resolved_count

        print(f"✓ [{ext_id}] {test.name}: {len(question_entities)} questions parsed, {resolved_count} mapped to topics ({len(question_topics)} edges).")

    print("-" * 65)
    print("Indexing Complete!")
    print(f"Tests Processed: {tests_processed}")
    print(f"Total Questions Indexed: {total_questions_indexed}")
    print(f"Total Questions Resolved: {total_questions_mapped} ({total_questions_mapped/max(1, total_questions_indexed)*100:.1f}%)")
    print("=" * 65)

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(index_stored_question_papers())
