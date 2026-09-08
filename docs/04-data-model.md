# 04 — Data Model

## 1. Core Collections

Recommended collections:

- `tests`
- `syllabus_snapshots`
- `topics`
- `test_topics`
- `artifacts`
- `ingestion_jobs`
- optionally `topic_aliases` or embed aliases in topics

## 2. `tests`

Example logical document:

```json
{
  "_id": "internal_id",
  "external_source": "allen",
  "external_test_id": "test_...",
  "name": "MINOR TEST (DLP)",
  "date": "2026-08-30",
  "duration_minutes": 180,
  "mode": "Offline",
  "status": "FINAL_RESULT_GENERATED",
  "category": "DLP",
  "processing_status": "READY",
  "created_at": "...",
  "updated_at": "..."
}
```

Do not assume every field exists for every test.

## 3. `syllabus_snapshots`

A snapshot is immutable evidence of what was processed for a particular test/version.

Suggested fields:

```json
{
  "test_id": "internal_test_id",
  "source": "allen",
  "external_test_id": "test_...",
  "artifact_id": "internal_artifact_id",
  "content_hash": "sha256...",
  "parser_version": "v1",
  "raw_sections": [],
  "extracted_at": "...",
  "created_at": "..."
}
```

If ALLEN replaces a syllabus, do not silently overwrite the only historical evidence.

## 4. `topics`

Canonical topic:

```json
{
  "_id": "topic_id",
  "subject": "Physics",
  "name": "Electric Power",
  "canonical_key": "physics:electric-power",
  "aliases": [],
  "active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

A topic identity should be stable even if display wording changes.

## 5. `test_topics`

Relationship document:

```json
{
  "_id": "relationship_id",
  "test_id": "internal_test_id",
  "topic_id": "topic_id",
  "subject": "Physics",
  "source_text": "Power",
  "source_section": "...",
  "syllabus_snapshot_id": "snapshot_id",
  "normalization_method": "deterministic",
  "normalization_version": "v1",
  "confidence": 1.0
}
```

This is the primary query/index layer.

## 6. `artifacts`

Logical artifact:

```json
{
  "_id": "artifact_id",
  "test_id": "internal_test_id",
  "kind": "syllabus",
  "source": "allen",
  "stable_object_key": "test_.../syllabus.pdf",
  "storage_provider": "gridfs|s3|other",
  "storage_key": "...",
  "sha256": "...",
  "content_type": "application/pdf",
  "size_bytes": 12345,
  "language": "en",
  "created_at": "...",
  "updated_at": "..."
}
```

Do not store temporary signed URLs here as permanent identifiers.

## 7. Indexes

At minimum:

### Tests
- unique `(external_source, external_test_id)`
- date
- status

### Topics
- unique `canonical_key`
- subject + normalized name

### Test topics
- unique `(test_id, topic_id)`
- `topic_id`
- `test_id`
- subject

### Artifacts
- unique `(source, stable_object_key, kind)`
- test_id + kind

## 8. Why a Relationship Collection?

MongoDB can embed topics inside tests, but a dedicated relationship collection makes the two core queries symmetric and efficient:

```text
topic → test_topics → tests
test  → test_topics → topics
```

It also preserves source wording and parser metadata per relationship.

## 9. Versioning

Topic normalization changes should be versioned.

Never mutate source evidence just because canonical naming improves.
