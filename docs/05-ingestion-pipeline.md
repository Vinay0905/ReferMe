# 05 — Ingestion Pipeline

## 1. Goal

Convert ALLEN's external test catalogue and PDFs into durable, normalized application data.

## 2. Pipeline

```text
Discover tests
  ↓
Upsert test metadata
  ↓
Acquire syllabus
  ↓
Hash/store artifact
  ↓
Parse syllabus
  ↓
Extract sections
  ↓
Normalize topics
  ↓
Upsert canonical topics
  ↓
Replace/rebuild relationships for current snapshot
  ↓
Acquire question paper
  ↓
Store/reference artifact
  ↓
Mark test READY
```

## 3. Discovery

Use the observed ALLEN test-list endpoint through a dedicated client.

Parameters should be configurable:
- completion status;
- mode;
- page number;
- page size.

Do not assume page 1 contains all tests.

## 4. Pagination

Implement a pagination abstraction.

Expected behavior should be verified against ALLEN:
- page numbering;
- empty page behavior;
- total-count field, if any;
- maximum page size;
- duplicate handling across pages.

Use a safety bound to avoid infinite pagination.

## 5. Idempotency

External test ID is the primary idempotency key.

For artifacts, use stable source identity plus content hash.

For relationships:
- unique test/topic key;
- rebuild relationships transactionally where practical;
- do not append duplicates.

## 6. Changed Syllabus

If a new syllabus has a different hash:

1. preserve old snapshot if historical retention is desired;
2. create a new snapshot;
3. parse it;
4. rebuild active relationships;
5. update test processing state.

The current snapshot should be clearly identifiable.

## 7. Partial Failure

Examples:

### Syllabus succeeds, question paper fails
Mark `PARTIAL`; retain syllabus/topics.

### PDF download succeeds, parser fails
Retain artifact; mark processing failure; allow reprocessing.

### One test fails
Do not fail the entire batch.

### ALLEN returns authentication error
Stop or pause according to retry policy; do not hammer the service.

## 8. Retries

Retry transient:
- connection reset;
- timeout;
- 429;
- selected 5xx.

Do not blindly retry:
- 401/403;
- malformed response;
- permanent 404.

Use exponential backoff with jitter.

## 9. Rate Limiting

Keep request concurrency conservative.

The ingestion client should have:
- global concurrency limit;
- per-endpoint rate limit;
- retry budget;
- timeout.

Never attempt to evade service-side rate limits.

## 10. Auditability

Each ingestion run should record:
- job ID;
- start/end time;
- number discovered;
- number succeeded;
- number partial;
- number failed;
- error categories;
- parser version.

Do not log credentials or signed URLs.

## 11. Resume

A job should be restartable without redoing successful immutable work unnecessarily.

Artifact hash and processing status are useful checkpoints.

## 12. Scheduled Ingestion

Future production can run:
- periodic discovery;
- targeted refresh;
- manual reprocess.

V1 can begin with a CLI/admin-triggered ingestion job if no scheduler is required yet.
