# Agent.md
# ALLEN NEET Test ↔ Topic Intelligence System

> **Purpose:** Master context and operating contract for the coding agent.
>
> **Read first.** Before implementing or changing code, read this file and then read the relevant documents under `docs/`. Do not treat undocumented assumptions as facts.

---

## 1. Project Mission

Build a fast, reliable application that turns ALLEN NEET test syllabi into a searchable **Test ↔ Topic knowledge graph**.

The primary user needs are:

1. Select a NEET topic → see every test whose syllabus contains that topic.
2. Select a test → see every topic covered by that test.
3. Open the relevant syllabus PDF and question-paper/solution PDF for a test.

The application is not intended to answer NEET questions, teach concepts, or perform semantic RAG over question papers in V1.

---

## 2. V1 Product Definition

### Required

- Test catalogue.
- Test metadata: name, date, duration, mode/status where useful.
- One syllabus snapshot per test.
- Extracted/normalized topics from each syllabus.
- Test ↔ topic relationships.
- Topic → tests lookup.
- Test → topics lookup.
- Access to the syllabus PDF.
- Access to the question-paper/solution PDF.
- Reliable ingestion/update mechanism.
- Fast application-side reads.
- MongoDB-backed persistence.
- Python + FastAPI backend.

### Artifact model

For each test, V1 needs exactly two logical artifacts:

1. `syllabus`
2. `question_paper`

ALLEN may call the second file `Solution.pdf` or expose it through an "Answer key" action. In this application, its logical meaning is **question paper / answer paper PDF**. Do not create a third mandatory artifact type for a separate answer key.

---

## 3. Explicit Non-Goals

Do not add these to V1 unless explicitly requested:

- RAG.
- Vector database.
- Embeddings.
- LLM-powered normal user search.
- AI-generated NEET explanations.
- AI question solving.
- Automatic question classification from every question.
- Full browser automation as the primary ingestion mechanism.
- Scraping the rendered UI when an API/HTTP route exists.
- User accounts/authentication unless required by the product.
- Payments.
- Social features.
- Analytics-heavy infrastructure.
- Premature microservices.
- Kubernetes.
- Event buses.
- Complex distributed systems.

AI may be introduced later for difficult syllabus normalization/fuzzy matching, but deterministic processing is the default.

---

## 4. Core User Workflows

### Workflow A: Topic → Tests

1. User opens topic search/browse.
2. User selects a topic.
3. Backend finds all normalized topic records linked to that topic.
4. Backend returns matching tests.
5. User selects a test.
6. User can open its syllabus and question paper.

### Workflow B: Test → Topics

1. User opens test catalogue.
2. User selects a test.
3. Backend returns all topics extracted from that test's syllabus.
4. User can filter/browse those topics.
5. User can open either artifact.

### Workflow C: Test → Artifact

1. User requests a syllabus or question paper.
2. Backend resolves the stored artifact reference.
3. Backend serves the file or generates/obtains a fresh temporary access URL according to the chosen storage architecture.
4. The frontend displays the PDF.

The frontend must not depend directly on ALLEN's private API contract.

---

## 5. Architecture Principles

Use a modular monolith for V1.

Logical layers:

```text
Frontend
   ↓
FastAPI API
   ↓
Application / Service Layer
   ↓
Repositories + Domain Models
   ↓
MongoDB
   +
Artifact Storage
   ↑
Ingestion / ALLEN Adapter
   ↓
ALLEN APIs / S3
```

The ALLEN integration is an **external-source adapter**, not the application's database.

The rest of the application should not know ALLEN-specific URL quirks wherever that knowledge can be isolated.

---

## 6. Technology Direction

### Chosen

- Backend: Python
- API framework: FastAPI
- Database: MongoDB

### Strongly preferred

- Frontend: Next.js + TypeScript
- Validation/modeling: Pydantic
- Async HTTP client: `httpx`
- Browser fallback: Playwright, only where necessary
- Testing: pytest
- Lint/format/type tooling: Ruff + mypy/pyright as appropriate

### Storage

MongoDB must store metadata and relationships.

PDF storage is a separate architectural decision. MongoDB GridFS is acceptable for a small V1 if its storage limits remain acceptable, but it is not a separate free storage pool. Long-term, object storage is preferable.

Never persist temporary ALLEN signed S3 URLs as permanent artifact URLs.

---

## 7. ALLEN Reverse-Engineering Status

See `docs/02-allen-reverse-engineering.md`.

Important observed behavior:

- ALLEN has a student-test listing API.
- Test cards expose test IDs and syllabus actions.
- Syllabus retrieval uses an API endpoint and ultimately a signed S3 PDF.
- Result insights can expose an English/Hindi PDF action for a missed test.
- The question-paper PDF is hosted in a separate S3 bucket.
- ALLEN uses temporary signed URLs.
- Authenticated requests may require session-specific headers/credentials.

Treat these as observations of the current system, not guaranteed permanent public API contracts.

---

## 8. Data Model Principle

The fundamental relationship is:

```text
Test
  ↕
TestTopic
  ↕
CanonicalTopic
```

A test owns a **syllabus snapshot**. The snapshot is the source evidence for the test's topics.

Do not model a topic as simply a free-form string attached to a test. We need stable canonical topic identities plus the original syllabus wording.

---

## 9. Topic Principle

Topic extraction should preserve:

- original subject;
- original syllabus wording;
- normalized/canonical topic;
- hierarchy where available;
- extraction source;
- parser version;
- confidence/status.

The system must be able to reprocess old syllabi when topic-normalization rules improve without losing the original evidence.

---

## 10. Ingestion Principle

Prefer:

1. direct authenticated HTTP/API calls;
2. direct artifact retrieval;
3. deterministic PDF text extraction;
4. structured parsing;
5. browser automation only when HTTP/API access cannot reproduce required behavior.

Do not begin with Firecrawl or an LLM.

Ingestion must be:

- idempotent;
- resumable;
- observable;
- rate-limited;
- failure-tolerant;
- explicit about partial success.

---

## 11. Security Rules

Never place any of the following in source control:

- Bearer tokens.
- Cookies.
- Device identifiers when secret/sensitive.
- ALLEN session credentials.
- Signed S3 URLs.
- AWS security tokens.
- `.env` files containing secrets.

The reverse-engineering notes must use redacted placeholders.

Temporary signed URLs expire and must be treated as ephemeral.

If ALLEN requires authenticated access, credentials belong in environment/secret management and the integration layer.

---

## 12. AI / RAG Policy

### V1 rule

**No AI is required for normal application operation.**

Normal user query:

```text
topic → indexed MongoDB relationship → tests
```

not:

```text
topic → embedding → vector DB → LLM → tests
```

AI may later assist with:

- synonym normalization;
- mapping ALLEN wording to canonical NEET topic names;
- resolving ambiguous syllabus fragments;
- suggesting aliases.

Any AI-assisted normalization must preserve the original text and be reviewable/reproducible.

---

## 13. External Source Rule

ALLEN is an external dependency that can change.

Therefore:

- isolate ALLEN-specific code;
- do not scatter ALLEN URLs through the application;
- centralize endpoint definitions;
- centralize request headers;
- log response/status metadata without logging credentials;
- make parsers tolerant of nonessential presentation changes;
- fail loudly when required fields disappear;
- maintain fixtures for observed responses.

---

## 14. Performance Goal

The user-facing topic/test lookup should be fast because it is a database lookup, not a live ALLEN request.

Do not make a normal search depend on:

- fetching ALLEN;
- downloading a PDF;
- running OCR;
- running an LLM.

Those operations belong to ingestion/preprocessing.

---

## 15. Documentation Map

Read:

- `docs/01-project-requirements.md` — product scope and requirements.
- `docs/02-allen-reverse-engineering.md` — observed ALLEN behavior.
- `docs/03-system-architecture.md` — architecture and boundaries.
- `docs/04-data-model.md` — MongoDB collections and relationships.
- `docs/05-ingestion-pipeline.md` — ingestion workflow.
- `docs/06-pdf-and-topic-processing.md` — PDF extraction/topic parsing.
- `docs/07-backend-api.md` — application API.
- `docs/08-frontend.md` — UI behavior.
- `docs/09-security.md` — secrets, access, and threat model.
- `docs/10-testing-and-observability.md` — tests, logs, monitoring.
- `docs/11-failure-modes-and-edge-cases.md` — edge cases.
- `docs/12-future-ai-and-scaling.md` — future evolution.
- `docs/13-known-unknowns.md` — unresolved assumptions.

---

## 16. Agent Operating Rules

1. Read before coding.
2. Preserve existing decisions unless explicitly changed.
3. Prefer the smallest architecture that satisfies requirements.
4. Do not introduce infrastructure because it sounds sophisticated.
5. Do not invent undocumented ALLEN endpoints.
6. If a fact is marked UNKNOWN, verify it.
7. Keep external-source code isolated.
8. Keep parsing deterministic where possible.
9. Make ingestion idempotent.
10. Never leak secrets into logs.
11. Write tests around parsers and ALLEN fixtures.
12. Do not silently discard malformed syllabus content.
13. Preserve raw source evidence needed for debugging.
14. Do not couple frontend components to ALLEN response shapes.
15. Do not implement AI/RAG without an explicit requirement.
16. When uncertain between two designs, prefer the simpler reversible one.
17. Update documentation when a previously UNKNOWN behavior becomes CONFIRMED.
18. Do not delete useful source evidence merely because a normalized field exists.

---

## 17. Confirmed vs Inferred vs Unknown

### Confirmed

- Test-list API exists at the observed route.
- It returns test cards containing `test_id`.
- Test cards can expose a syllabus fetch action.
- Syllabus is retrieved through an authenticated API flow.
- Syllabus is stored in an ALLEN S3 bucket.
- Syllabus URLs are signed and temporary.
- Question-paper/solution PDF is stored in a separate ALLEN S3 bucket.
- Result-insights endpoint exists for a test/attempt.
- Missed-test result data can expose English/Hindi PDF actions.

### Strongly inferred

- The stable S3 object path can be represented without the temporary query string.
- A per-test syllabus snapshot is the correct persistence model.
- Deterministic extraction is sufficient for much of the syllabus.
- Normal search should be DB-backed.

### Unknown / must verify during implementation

- Complete pagination semantics beyond the observed first page.
- Whether every historical/current test uses exactly the same PDF structure.
- Whether all test types expose question-paper PDFs identically.
- Exact authentication requirements for a standalone ingestion service.
- Whether ALLEN changes endpoint/header requirements by client.
- Whether every syllabus can be parsed without OCR.
- Long-term legality/terms/compliance of automated retrieval for the intended use.
- Exact production artifact-storage provider and cost boundary.

---

## 18. Definition of Done

V1 is done when:

- Tests can be ingested reliably.
- Each test has metadata and a syllabus snapshot.
- Topics can be extracted and normalized.
- Test ↔ topic relationships are queryable.
- Topic → tests works.
- Test → topics works.
- Syllabus PDF opens.
- Question paper PDF opens.
- Re-running ingestion does not duplicate data.
- Partial failures are visible and recoverable.
- Secrets are not committed or logged.
- Parser tests cover representative syllabus structures.
- API tests cover core queries.
- The frontend is not dependent on live ALLEN calls.
- Documentation matches implementation.
