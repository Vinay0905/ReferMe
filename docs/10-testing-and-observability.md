# 10 — Testing and Observability

## 1. Testing Pyramid

### Unit tests
Focus on:
- syllabus parsing;
- normalization;
- canonical topic mapping;
- validation;
- retry logic.

### Integration tests
Focus on:
- MongoDB repositories;
- ingestion persistence;
- relationship queries;
- artifact metadata.

### API tests
Focus on:
- topic → tests;
- test → topics;
- test detail;
- artifact resolution;
- pagination;
- error cases.

### End-to-end tests
At least one happy path:

```text
topic search → tests → test detail → PDF action
```

## 2. ALLEN Fixtures

Never make the entire test suite depend on live ALLEN.

Store sanitized fixture responses for:
- test list;
- syllabus action;
- result insights;
- representative edge cases.

Use recorded/synthetic fixtures according to content/licensing constraints.

## 3. Parser Regression Tests

Every syllabus format change discovered in production should become a fixture/regression test.

## 4. Ingestion Metrics

Track:
- discovered tests;
- processed tests;
- failed tests;
- syllabus download failures;
- parser failures;
- question-paper failures;
- topic counts;
- ingestion duration;
- retry counts.

## 5. Logging

Use structured logs.

Include:
- timestamp;
- level;
- job ID;
- test ID;
- operation;
- duration;
- result.

Exclude secrets.

## 6. Alerts

Future production alerts:
- repeated ALLEN authentication failure;
- high parser failure rate;
- sudden zero-topic parses;
- ingestion backlog;
- artifact download failure spike.

## 7. Health

Application health should distinguish:
- process alive;
- database reachable;
- artifact store reachable;
- ingestion subsystem configured.

Do not expose sensitive diagnostic details.

## 8. Reproducibility

Store parser/normalization versions with processed data.

This lets us answer:
"Why did this test have these topics?"
