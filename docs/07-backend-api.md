# 07 — Backend API

## 1. Principle

Expose a clean application API. Do not mirror ALLEN's API blindly.

## 2. Proposed Endpoints

### Tests

```http
GET /api/v1/tests
GET /api/v1/tests/{test_id}
```

Optional filters:
- date;
- subject/topic;
- status;
- search;
- pagination.

### Topics

```http
GET /api/v1/topics
GET /api/v1/topics/{topic_id}
```

### Topic → Tests

```http
GET /api/v1/topics/{topic_id}/tests
```

### Test → Topics

```http
GET /api/v1/tests/{test_id}/topics
```

### Artifacts

Possible pattern:

```http
GET /api/v1/tests/{test_id}/artifacts
GET /api/v1/tests/{test_id}/artifacts/{kind}
```

where `kind` is one of:
- `syllabus`
- `question_paper`

Exact artifact delivery semantics depend on final storage.

## 3. Response Principle

Return application models, not raw ALLEN payloads.

Example test response:

```json
{
  "id": "...",
  "name": "MINOR TEST (DLP)",
  "date": "2026-08-30",
  "duration_minutes": 180,
  "mode": "Offline",
  "has_syllabus": true,
  "has_question_paper": true
}
```

## 4. Pagination

All list endpoints should have predictable pagination.

Recommended:
- `page`
- `page_size`

Cap page size server-side.

## 5. Search

V1 can use:
- exact canonical topic;
- normalized text search;
- prefix/controlled filters.

Do not add vector search unless requirements change.

## 6. Errors

Use consistent HTTP errors:

- `400` invalid request;
- `404` missing test/topic/artifact;
- `409` state/conflict where relevant;
- `422` validation;
- `429` if application-level rate limiting is introduced;
- `500` unexpected server error.

Do not expose upstream credentials or raw sensitive upstream responses.

## 7. API Performance

Topic/test relationship endpoints should use indexed MongoDB queries.

Avoid N+1:
- fetch relationship IDs in one query;
- fetch referenced tests/topics efficiently;
- consider aggregation when appropriate.

## 8. Health

Provide internal health endpoints such as:

```http
GET /health
GET /ready
```

Do not expose sensitive dependency diagnostics publicly.

## 9. OpenAPI

FastAPI's generated OpenAPI should remain accurate and intentional.

Use Pydantic response models rather than returning arbitrary dictionaries.
