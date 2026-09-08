import hashlib
import logging
from typing import List, Optional
from app.integrations.allen.client import AllenClient, RawAllenTestCard
from app.models.artifact import ArtifactKind, ArtifactModel, SyllabusSnapshotModel
from app.models.common import ProcessingStatus, utc_now
from app.models.ingestion import IngestionJobModel, IngestionStatus
from app.models.relationship import TestTopicModel
from app.models.test import TestModel
from app.models.topic import TopicModel
from app.processing.extractor import PDFTextExtractor
from app.processing.normalizer import TopicNormalizer
from app.processing.parser import SyllabusParser
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.ingestion_repo import IngestionJobRepository
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.storage.local import get_storage_provider

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Orchestrates test discovery, artifact acquisition, PDF parsing,

    topic normalization, and symmetric relationship indexing.
    """

    def __init__(
        self,
        allen_client: Optional[AllenClient] = None,
        test_repo: Optional[TestRepository] = None,
        topic_repo: Optional[TopicRepository] = None,
        test_topic_repo: Optional[TestTopicRepository] = None,
        artifact_repo: Optional[ArtifactRepository] = None,
        job_repo: Optional[IngestionJobRepository] = None,
        target_class: str = "12th",
        course_id: Optional[str] = None,
        course_name: Optional[str] = None,
    ):
        self.allen_client = allen_client or AllenClient()
        self.test_repo = test_repo or TestRepository()
        self.topic_repo = topic_repo or TopicRepository()
        self.test_topic_repo = test_topic_repo or TestTopicRepository()
        self.artifact_repo = artifact_repo or ArtifactRepository()
        self.job_repo = job_repo or IngestionJobRepository()
        self.target_class = target_class
        self.course_id = course_id
        self.course_name = course_name
        self.storage = get_storage_provider()
        self.normalizer = TopicNormalizer()

    async def run(
        self,
        status: str = "all",
        mode: str = "all",
        max_tests: Optional[int] = None
    ) -> IngestionJobModel:
        """Executes a full ingestion run and returns the recorded audit job."""
        job = IngestionJobModel(
            status=IngestionStatus.RUNNING,
            parser_version=SyllabusParser.VERSION,
            start_time=utc_now()
        )
        job_id = await self.job_repo.insert(job)
        job.id = job_id
        logger.info(f"Starting Ingestion Job {job_id} (status={status}, mode={mode})...")

        try:
            # Step 1: Discover test cards (across all available pages)
            test_cards = await self.allen_client.list_all_tests(status=status, mode=mode)
            if max_tests:
                test_cards = test_cards[:max_tests]

            job.discovered_count = len(test_cards)
            logger.info(f"Discovered {len(test_cards)} tests to ingest.")

            for card in test_cards:
                try:
                    await self._process_single_test(card, job)
                except Exception as test_err:
                    logger.error(f"Failed processing test {card.test_id}: {test_err}", exc_info=True)
                    job.failed_count += 1
                    job.error_summary.append({
                        "test_id": card.test_id,
                        "error": str(test_err)
                    })

            # Finalize job status
            if job.failed_count == 0 and job.discovered_count > 0:
                job.status = IngestionStatus.COMPLETED
            elif job.succeeded_count > 0 or job.partial_count > 0:
                job.status = IngestionStatus.PARTIAL
            else:
                job.status = IngestionStatus.FAILED

        except Exception as global_err:
            logger.critical(f"Fatal error during ingestion job {job_id}: {global_err}", exc_info=True)
            job.status = IngestionStatus.FAILED
            job.error_summary.append({"fatal": str(global_err)})

        finally:
            job.end_time = utc_now()
            await self.job_repo.update_job(job)
            logger.info(
                f"Ingestion Job {job.id} finished: Status={job.status.value}, "
                f"Succeeded={job.succeeded_count}, Partial={job.partial_count}, Failed={job.failed_count}"
            )

        return job

    async def _process_single_test(self, card: RawAllenTestCard, job: IngestionJobModel):
        external_test_id = card.test_id
        logger.info(f"Processing test: {card.title} (ID: {external_test_id})...")

        # Step 2: Upsert basic test metadata
        test_entity = TestModel(
            external_source="allen",
            external_test_id=external_test_id,
            name=card.title,
            date=card.date_str,
            duration_minutes=card.duration_minutes,
            mode=card.mode,
            status=card.status,
            category=card.category,
            target_class=self.target_class,
            course_id=self.course_id,
            course_name=self.course_name,
            processing_status=ProcessingStatus.SYLLABUS_PENDING,
            updated_at=utc_now()
        )
        test_id = await self.test_repo.upsert(test_entity)
        test_entity.id = test_id

        # Step 3: Fetch syllabus PDF
        syllabus_pdf_bytes = await self.allen_client.get_syllabus_pdf(external_test_id)
        if syllabus_pdf_bytes:
            syllabus_hash = hashlib.sha256(syllabus_pdf_bytes).hexdigest()

            # Step 4: Store syllabus PDF artifact
            stable_syllabus_key = f"test_{external_test_id}/syllabus.pdf"
            saved_storage_key = await self.storage.save(stable_syllabus_key, syllabus_pdf_bytes)

            artifact = ArtifactModel(
                test_id=test_id,
                external_test_id=external_test_id,
                kind=ArtifactKind.SYLLABUS,
                source="allen",
                stable_object_key=stable_syllabus_key,
                storage_provider="local",
                storage_key=saved_storage_key,
                sha256=syllabus_hash,
                content_type="application/pdf",
                size_bytes=len(syllabus_pdf_bytes),
                updated_at=utc_now()
            )
            await self.artifact_repo.upsert_artifact(artifact)
            test_entity.has_syllabus = True

            # Step 5: Extract and parse syllabus text
            extraction = PDFTextExtractor.extract(syllabus_pdf_bytes)
            parsed_syllabus = SyllabusParser.parse(extraction)

            if parsed_syllabus.is_valid:
                # Step 6: Normalize topics & construct relationships
                normalized_topics = self.normalizer.normalize_all(parsed_syllabus.topics)
                relationships: List[TestTopicModel] = []

                for norm in normalized_topics:
                    # Upsert canonical topic in Topic collection
                    topic_entity = TopicModel(
                        subject=norm.subject,
                        name=norm.name,
                        canonical_key=norm.canonical_key,
                        target_classes=[self.target_class] if self.target_class else [],
                        updated_at=utc_now()
                    )
                    canonical_topic_id = await self.topic_repo.upsert_canonical(topic_entity, target_class=self.target_class)

                    # Build relationship document
                    rel = TestTopicModel(
                        test_id=test_id,
                        external_test_id=external_test_id,
                        topic_id=canonical_topic_id,
                        canonical_key=norm.canonical_key,
                        subject=norm.subject,
                        source_text=norm.raw_source_text,
                        source_section=norm.section_name,
                        normalization_method=norm.method,
                        normalization_version=SyllabusParser.VERSION,
                        confidence=norm.confidence
                    )
                    relationships.append(rel)

                # Step 7: Atomically replace relations for this test
                existing_rels = await self.test_topic_repo.find_by_test_id(test_id)
                old_topic_ids = {r.topic_id for r in existing_rels if r.topic_id}

                await self.test_topic_repo.replace_for_test(test_id, relationships)

                # Step 8: Update topic counts for all affected topics
                new_topic_ids = {r.topic_id for r in relationships if r.topic_id}
                affected_topic_ids = old_topic_ids.union(new_topic_ids)

                for affected_id in affected_topic_ids:
                    count = await self.test_topic_repo.count({"topic_id": affected_id})
                    await self.topic_repo.update_test_count(affected_id, count)
            else:
                logger.warning(f"Failed to parse topics from syllabus for test {external_test_id}: {parsed_syllabus.warning}")
        else:
            logger.warning(f"Syllabus PDF not available for test {external_test_id}.")

        # Step 9: Attempt question paper acquisition
        qp_bytes = await self.allen_client.get_question_paper_pdf(external_test_id)
        if qp_bytes:
            stable_qp_key = f"test_{external_test_id}/question_paper.pdf"
            qp_storage_key = await self.storage.save(stable_qp_key, qp_bytes)
            qp_artifact = ArtifactModel(
                test_id=test_id,
                external_test_id=external_test_id,
                kind=ArtifactKind.QUESTION_PAPER,
                source="allen",
                stable_object_key=stable_qp_key,
                storage_provider="local",
                storage_key=qp_storage_key,
                sha256=hashlib.sha256(qp_bytes).hexdigest(),
                size_bytes=len(qp_bytes),
                updated_at=utc_now()
            )
            await self.artifact_repo.upsert_artifact(qp_artifact)
            test_entity.has_question_paper = True

        # Step 10: Mark test status
        if test_entity.has_syllabus and test_entity.has_question_paper:
            test_entity.processing_status = ProcessingStatus.READY
            job.succeeded_count += 1
        elif test_entity.has_syllabus or test_entity.has_question_paper:
            test_entity.processing_status = ProcessingStatus.PARTIAL
            job.partial_count += 1
        else:
            test_entity.processing_status = ProcessingStatus.FAILED
            job.failed_count += 1
            job.error_summary.append({"test_id": external_test_id, "error": "Neither syllabus nor question paper available"})

        await self.test_repo.upsert(test_entity)
        logger.info(f"Successfully processed test {external_test_id}: syllabus={test_entity.has_syllabus}, qp={test_entity.has_question_paper}.")
