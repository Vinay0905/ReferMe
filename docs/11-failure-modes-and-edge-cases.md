# 11 — Failure Modes and Edge Cases

## 1. ALLEN Changes Endpoint

Symptom:
- 404/401/403;
- schema mismatch.

Action:
- fail clearly;
- capture safe diagnostic metadata;
- do not silently treat an empty response as no tests;
- update adapter and fixtures.

## 2. Pagination Stops Unexpectedly

Never infer completion solely from "first page returned fewer than page_size" unless verified.

Prefer known pagination metadata when available; otherwise use conservative empty-page termination with duplicate/safety checks.

## 3. Duplicate Tests

Use `(source, external_test_id)` uniqueness.

## 4. Same Name, Different Test

Test name is not identity.

Use external test ID.

## 5. Date Changes

Update metadata without changing identity.

## 6. Syllabus Changes

Create a new snapshot/hash and reprocess.

## 7. Missing Syllabus

Keep the test record but mark it incomplete.

Do not invent topics.

## 8. Missing Question Paper

Keep syllabus/topic functionality working.

Show question-paper unavailability clearly.

## 9. PDF Download Returns HTML

Validate:
- status;
- content type;
- magic bytes;
- minimum size.

Do not send an HTML error page into the PDF parser.

## 10. Empty PDF

Store failure status and preserve diagnostics.

## 11. Text Extraction Garbage

Run validation and sanity checks.

Do not generate thousands of bogus topics from parser noise.

## 12. Subject Heading Missing

Use layout/position/context if deterministic extraction cannot represent the heading.

Do not immediately use an LLM.

## 13. Ambiguous Topic

If deterministic normalization cannot safely choose a canonical topic:
- preserve original text;
- mark unresolved;
- optionally map later through reviewed rules/AI.

## 14. Duplicate Source Wording

Deduplicate at the relationship level while retaining source evidence.

## 15. Temporary Signed URL Expired

Obtain a fresh signed URL through the external flow.

Never assume the old URL remains valid.

## 16. Rate Limiting

Back off.

Do not increase concurrency to "push through" 429s.

## 17. Partial Batch

One failure must not erase successful tests.

## 18. Database Failure

Do not mark external processing complete until persistence succeeds.

## 19. Crash Mid-Test

Idempotent checkpoints must allow safe restart.

## 20. Future Syllabus Format

Detect via parser validation and quarantine/review rather than silently producing bad data.
