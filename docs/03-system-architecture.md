# 03 — System Architecture

## 1. Architectural Style

Use a modular monolith for V1.

This provides:
- low operational complexity;
- fast local development;
- simple deployment;
- clear boundaries;
- easy future extraction of services if scale demands it.

## 2. Components

```text
                         ┌─────────────────────┐
                         │       ALLEN         │
                         │ APIs + S3 artifacts │
                         └──────────┬──────────┘
                                    │
                             authenticated
                               ingestion
                                    │
                         ┌──────────▼──────────┐
                         │   ALLEN Adapter      │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │ Ingestion Services   │
                         │ fetch/parse/normalize│
                         └──────────┬──────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │           MongoDB            │
                     │ tests/topics/relationships   │
                     │ jobs/artifact metadata       │
                     └──────────────┬──────────────┘
                                    │
                              FastAPI API
                                    │
                         ┌──────────▼──────────┐
                         │ Next.js Frontend     │
                         └─────────────────────┘
```

## 3. Boundary Rules

### Frontend
Never directly depend on ALLEN.

### FastAPI
Owns:
- product API;
- validation;
- authorization if later required;
- topic/test queries;
- artifact access orchestration.

### Ingestion
Owns:
- ALLEN authentication/session;
- external API calls;
- artifact acquisition;
- PDF parsing;
- normalization;
- persistence.

### MongoDB
Owns application state and search relationships.

### Artifact storage
Owns binary PDFs.

## 4. Recommended Internal Modules

```text
app/
  api/
  domain/
  services/
  repositories/
  integrations/
    allen/
  ingestion/
  processing/
  storage/
  models/
  core/
```

The exact folder structure can evolve, but ALLEN integration must remain isolated.

## 5. Data Flow

### Ingestion

```text
ALLEN test list
  ↓
test metadata
  ↓
for each test:
  fetch syllabus metadata/artifact
  ↓
download syllabus
  ↓
extract text/structure
  ↓
normalize topics
  ↓
upsert test + syllabus + topics + relationships
  ↓
resolve question paper
  ↓
store/reference artifact
```

### Query

```text
User
 ↓
Next.js
 ↓
FastAPI
 ↓
MongoDB indexed query
 ↓
JSON response
```

No ALLEN call occurs during normal topic/test browsing.

## 6. Caching

V1 should rely primarily on persistent normalized data.

Optional HTTP/application caching may be added later.

Do not cache temporary signed URLs longer than their validity.

## 7. Consistency

A test should not appear as fully processed if its required syllabus has failed.

Represent processing state explicitly.

Recommended statuses:

```text
DISCOVERED
SYLLABUS_PENDING
SYLLABUS_FETCHED
SYLLABUS_PARSED
TOPICS_PROCESSED
QUESTION_PAPER_PENDING
READY
PARTIAL
FAILED
```

## 8. Extensibility

The architecture should allow:
- a new external source;
- a new PDF parser;
- a new topic-normalization strategy;
- a different artifact store;
without rewriting the query layer.
