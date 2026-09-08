# REFERME • ALLEN NEET BIDIRECTIONAL INTELLIGENCE SYSTEM
## The Absolute Engineering Handoff & Technical Codex

> **Document Status**: Production Canon • Absolute Reference • Fully Audited  
> **Last Verified State**: 27 Tests (8 Leader + 19 Nurture), 102 Canonical Topics, 562 Bidirectional Edges  
> **Database**: MongoDB Atlas (`referme_neet_dev`) • **Backend**: FastAPI (Port 8000) • **Frontend**: Next.js 14 (Port 3000)  
> **Target Audience**: Autonomous AI Agents, Senior Full-Stack Engineers, DevOps Engineers

---

## TABLE OF CONTENTS
1. [The 60-Second AI Agent Fast-Track Codex](#1-the-60-second-ai-agent-fast-track-codex)
2. [System Mission & Architectural Philosophy](#2-system-mission--architectural-philosophy)
3. [Runtime Environment & Infrastructure Blueprint](#3-runtime-environment--infrastructure-blueprint)
4. [Complete Codebase Directory Map](#4-complete-codebase-directory-map)
5. [Allen Student Portal Reverse-Engineering Codex](#5-allen-student-portal-reverse-engineering-codex)
6. [Deterministic PDF Extraction & Topic Processing Engine](#6-deterministic-pdf-extraction--topic-processing-engine)
7. [Data Model, MongoDB Collections & Graph Invariants](#7-data-model-mongodb-collections--graph-invariants)
8. [FastAPI Backend Endpoints Specification](#8-fastapi-backend-endpoints-specification)
9. [Frontend Web Studio (Next.js 14) Architecture](#9-frontend-web-studio-nextjs-14-architecture)
10. [The Absolute Ground-Truth System Audit](#10-the-absolute-ground-truth-system-audit)
11. [Operational Runbook: Commands, Ingestion & Auditing](#11-operational-runbook-commands-ingestion--auditing)
12. [Known Quirks, Edge Cases & Failure Recovery Protocols](#12-known-quirks-edge-cases--failure-recovery-protocols)
13. [Handoff Checklist for Resuming Engineers](#13-handoff-checklist-for-resuming-engineers)

---

## 1. The 60-Second AI Agent Fast-Track Codex

If you are an AI Agent with limited context tokens, read this section first:

- **What is this?** A bidirectional intelligence search engine for ALLEN NEET test series. Given an NCERT chapter, it finds all exams testing it; given an exam, it finds all tested chapters, syllabus PDFs, and question papers.
- **Where are files stored?** All downloaded PDFs reside in `backend/storage_data/test_<external_test_id>/` (`syllabus.pdf` and `question_paper.pdf`).
- **Where is data stored?** MongoDB Atlas cluster connected via `MONGODB_URI` in `backend/.env`. Database name: `referme_neet_dev`.
- **Active tracks**:
  - **Class 12th (Leader)**: `course_id="363233"`, `course_name="Leader Test Series"` (8 Tests, 50 Topics).
  - **Class 11th (Nurture)**: `course_id="cr_SUqkwoRLxGJ1jV8Ix60b3"`, `batch_list="bt_2Fsslkpec8p0kxgacLsCc"`, `course_name="Nurture Test Series"` (19 Tests, 73 Topics).
- **Core Numbers**:
  - Total Tests: **27** (8 Leader + 19 Nurture)
  - Total Stored PDFs: **46** (26 Syllabi + 20 Question Papers; 7 Question Papers pending exam conduct; 1 Syllabus unsigned S3 403)
  - Total Unique Canonical Topics: **102** (Physics: 51, Chemistry: 22, Biology: 29)
  - Overlap Invariant: **21 Shared Topics** appear in both 11th and 12th test series (revision overlap).
  - Total Bidirectional Edges: **562** in `test_topics`.
- **Critical File Locations**:
  - Backend API: `backend/app/main.py`
  - Ingestion Orchestrator: `backend/app/ingestion/orchestrator.py`
  - Allen API Client: `backend/app/ingestion/allen_client.py`
  - PDF Extractor (Landscape Bounded): `backend/app/processing/extractor.py`
  - Structural Parser (Ligatures & Chapters): `backend/app/processing/parser.py`
  - Normalizer (Deterministic Slugs): `backend/app/processing/normalizer.py`
  - Frontend Page: `frontend/app/page.tsx`
  - Audit Script: `backend/scripts/audit_database.py`
- **Default Python Env**: `/Users/mast/miniconda3/envs/all/bin/python`.
- **Strict Rule for Testing**: When running background commands, always include `-u` (`python -u ...`) to avoid pipe stdout buffering.

---

## 2. System Mission & Architectural Philosophy

### 2.1 The Domain Problem
ALLEN Career Institute is India's preeminent coaching institution for the **NEET (National Eligibility cum Entrance Test)**. Enrolled students sit for rigorous test series throughout their two-year preparation cycle:
- **Class 12th Track (Leader Test Series / Achiever Series)**: Covers full 12th syllabus and rapid revision of 11th.
- **Class 11th Track (Nurture Test Series / Joint Package)**: Comprehensive foundation across class 11th.

Each track schedules dozens of exams (Minor Tests, Major Tests, Unit Tests, Review Tests, Semi-Major Tests). However, **Allen’s student portal provides zero chapter-level intelligence**:
- Syllabi are buried inside downloadable, multi-column landscape PDF circulars.
- If a student prepares a specific chapter (e.g. *Equilibrium*, *Rotational Motion*, or *Biomolecules*), they **cannot query** which scheduled tests cover that chapter.
- After a test concludes, downloading the question paper and answer key requires navigating disparate UI flows with ephemeral AWS S3 tokens.

### 2.2 The Solution
**ReferMe** is an automated, bidirectional intelligence engine:
1. **Test $\rightarrow$ Topics**: Select any scheduled test to immediately inspect its parsed, ligature-repaired, normalized NCERT topics grouped by Physics, Chemistry, and Biology, alongside the live Question Paper and Syllabus PDF.
2. **Topic $\rightarrow$ Tests (Bidirectional Radar)**: Click any canonical topic to see every past and upcoming exam across both Class 11th and 12th featuring that topic, complete with the exact syllabus line extracted from the original PDF.
3. **Course Track Isolation**: Toggle instantly between **Class 12th (Leader)**, **Class 11th (Nurture)**, and **All Classes**, updating metrics, test cards, and topic clouds with zero layout shift.

```mermaid
flowchart TD
    subgraph External["Allen Live Ecosystem"]
        A[Allen Live REST API\napi.allen-live.in] -->|Auth JWT + Course Headers| B[Test Cards JSON]
        A -->|POST Syllabus| C[AWS S3 Signed Syllabus PDF]
        A -->|GET Result Insights| D[AWS S3 Signed Question Paper PDF]
    end

    subgraph IngestionEngine["Backend Ingestion Pipeline"]
        B --> E[AllenClient Adapter]
        C --> E
        D --> E
        E --> F[Storage Provider\nLocal Disk / storage_data/]
        E --> G[PDFTextExtractor\npdfplumber Landscape Bounding]
        G --> H[SyllabusParser\nLigatures, Disclaimers, Compound Protection]
        H --> I[TopicNormalizer\nDeterministic Slugs & NCERT Taxonomy]
    end

    subgraph DataStore["Persistence Layer (MongoDB Atlas)"]
        F --> J[(artifacts)]
        E --> K[(tests)]
        I --> L[(topics)]
        I --> M[(test_topics\nBidirectional Edges)]
    end

    subgraph APILayer["FastAPI v1 REST Services"]
        K & L & M & J --> N[FastAPI Backend\nPort 8000]
    end

    subgraph UI["Next.js 14 Cyberpunk Studio"]
        N -->|HTTP / JSON| O[Next.js App Router\nPort 3000]
        O --> P[ControlCenter\nCourse Switcher + Search]
        O --> Q[TopicCard & TestCard\n3D Tilt Surfaces]
        O --> R[TopicDetailStudio\nBidirectional Radar Drawer]
        O --> S[PdfStudio\nInline Document Viewer]
    end
```

---

## 3. Runtime Environment & Infrastructure Blueprint

| Component | Setting / Path / Credential |
| :--- | :--- |
| **Operating System** | macOS (Darwin 24.6.0, Apple Silicon / ARM64) |
| **Python Interpreter** | `/Users/mast/miniconda3/envs/all/bin/python` (Python 3.11.14) |
| **Node.js Environment** | Node.js v18+ / v20+ with `npm` |
| **Backend Root** | `/Users/mast/Documents/VInayPrograming/ReferMe/backend` |
| **Frontend Root** | `/Users/mast/Documents/VInayPrograming/ReferMe/frontend` |
| **FastAPI Server** | Port `8000` (`http://localhost:8000` / Docs: `http://localhost:8000/docs`) |
| **Next.js Dev Server** | Port `3000` (`http://localhost:3000`) |
| **Database Instance** | MongoDB Atlas Cluster (Database name: `referme_neet_dev`) |
| **MongoDB Driver** | Motor (Async Python Driver over PyMongo) |
| **Local File Storage** | `/Users/mast/Documents/VInayPrograming/ReferMe/backend/storage_data` |

### Environment Variables (`backend/.env`)
```bash
ENVIRONMENT=development
PROJECT_NAME="ALLEN NEET Test ↔ Topic Intelligence System"
API_V1_STR=/api/v1

# MongoDB Atlas
MONGODB_URI="mongodb+srv://..."  # Cluster connection string
MONGODB_DB_NAME=referme_neet_dev

# Storage
STORAGE_PROVIDER=local
LOCAL_STORAGE_DIR=./storage_data

# Allen Live Integration
ALLEN_BASE_URL="https://api.allen-live.in"
ALLEN_AUTH_TOKEN="eyJhbGci..."   # Active student session Bearer JWT
ALLEN_MOCK_MODE=false            # Set true for offline fixture testing
ALLEN_CLIENT_TYPE=web
ALLEN_DEVICE_ID="2c5a2e65-b1f1-4c6c-ac4b-908113e1152c"

# Multi-Course Tracks
COURSE_12TH_ID="363233"
COURSE_12TH_NAME="Leader Test Series"
COURSE_11TH_ID="cr_SUqkwoRLxGJ1jV8Ix60b3"
COURSE_11TH_BATCH_LIST="bt_2Fsslkpec8p0kxgacLsCc"
COURSE_11TH_NAME="Nurture Test Series"

# Ingestion Guardrails
DEFAULT_PAGE_SIZE=25
MAX_PAGES=20
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT_SECONDS=30
```

---

## 4. Complete Codebase Directory Map

```text
/Users/mast/Documents/VInayPrograming/ReferMe/
│
├── handoff.md                             # THIS DEFINITIVE SYSTEM CODEX
├── README.md                              # High-level developer onboarding
│
├── backend/
│   ├── .env                               # Live credentials & Atlas connection URI
│   ├── requirements.txt                   # Production Python package manifests
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI factory, CORS, and Motor lifespan hooks
│   │   ├── config.py                      # Pydantic Settings class with .env resolution
│   │   ├── cli.py                         # CLI entry point: python -m app.cli [ingest|reset-db]
│   │   │
│   │   ├── api/                           # FastAPI Router Layer
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── api.py                 # Aggregates /tests, /topics, /artifacts
│   │   │       ├── tests.py               # Test listing, detail, and grouped topic queries
│   │   │       ├── topics.py              # Canonical topic listing and bidirectional radar
│   │   │       └── artifacts.py           # Streams binary PDFs from local disk
│   │   │
│   │   ├── db/                            # MongoDB Atlas Data Layer
│   │   │   ├── __init__.py
│   │   │   ├── mongo.py                   # Async MotorClient instance management
│   │   │   └── indexes.py                 # Compound index creation scripts
│   │   │
│   │   ├── ingestion/                     # External Network Integration
│   │   │   ├── __init__.py
│   │   │   ├── allen_client.py            # HTTP client for api.allen-live.in
│   │   │   ├── orchestrator.py            # End-to-end ingestion pipeline runner
│   │   │   └── mock_data.py               # Deterministic test fixtures for CI/CD
│   │   │
│   │   ├── models/                        # Pydantic Schemas & MongoDB Entities
│   │   │   ├── __init__.py
│   │   │   ├── common.py                  # Subject, Track, and Exam Enums
│   │   │   ├── test.py                    # TestModel, TestResponse
│   │   │   ├── topic.py                   # TopicModel, CanonicalTopic
│   │   │   ├── relationship.py            # TestTopicRelationshipModel
│   │   │   ├── artifact.py                # ArtifactModel
│   │   │   └── ingestion.py               # IngestionJobModel
│   │   │
│   │   ├── processing/                    # PDF Text Extraction & Parsing Core
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py               # pdfplumber landscape column bounding
│   │   │   ├── parser.py                  # Ligature repair, disclaimers, compound split protection
│   │   │   └── normalizer.py              # Canonical NCERT topic keying & taxonomy
│   │   │
│   │   ├── repositories/                  # Database Query & Mutation Interfaces
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── test_repository.py
│   │   │   ├── topic_repository.py
│   │   │   ├── test_topic_repository.py
│   │   │   └── artifact_repository.py
│   │   │
│   │   └── storage/                       # Blob Storage Abstraction
│   │       ├── __init__.py
│   │       ├── provider.py                # StorageProvider abstract base class
│   │       └── local.py                   # LocalStorageProvider implementation
│   │
│   ├── storage_data/                      # Local PDF Storage Directory (46 downloaded PDFs)
│   │   ├── test_test_5uK46Afnka7K/        # Contains syllabus.pdf & question_paper.pdf
│   │   └── ... (27 test directories)
│   │
│   ├── scripts/                           # Operational Utilities
│   │   ├── audit_database.py              # Full database & disk integrity auditor
│   │   └── run_ingestion.py               # Ingestion runner script
│   │
│   └── tests/                             # Pytest Unit Test Suite (23 Passing Tests)
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_extractor.py
│       ├── test_parser.py
│       ├── test_normalizer.py
│       ├── test_repositories.py
│       └── test_api.py
│
└── frontend/                              # Next.js 14 Web Studio
    ├── package.json
    ├── tailwind.config.js                 # Cyberpunk palettes & neon box-shadows
    ├── tsconfig.json
    ├── app/
    │   ├── layout.tsx                     # Space void root layout
    │   ├── page.tsx                       # Reactive Studio Command Center
    │   └── globals.css                    # Custom scrollbars & glassmorphism
    ├── components/
    │   ├── ControlCenter.tsx              # Course Selector Dropdown + Search + Pill Switcher
    │   ├── TopicCard.tsx                  # 3D Tilt Topic Surface with Class Badges
    │   ├── TestCard.tsx                   # 3D Tilt Test Surface with Action Buttons
    │   ├── TopicDetailStudio.tsx          # Bidirectional Radar Drawer
    │   ├── PdfStudio.tsx                  # Inline PDF Document Viewer
    │   ├── TiltCard.tsx                   # Interactive Gyroscope / Mouse Angle Wrapper
    │   └── CleanHud.tsx                   # Reactive Metric HUD
    └── lib/
        └── api.ts                         # Typed TypeScript Axios Client
```

---

## 5. Allen Student Portal Reverse-Engineering Codex

Allen's student web portal communicates over HTTPS to `https://api.allen-live.in`. The backend replicates these exact handshake parameters.

### 5.1 Authentication Handshake
- **Protocol**: Bearer Token JWT in `Authorization` header.
- **Required Headers**:
  ```http
  Authorization: Bearer eyJhbGciOiJIUzI1Ni...
  User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
  accept: application/json
  client-type: web
  device-id: 2c5a2e65-b1f1-4c6c-ac4b-908113e1152c
  ```

### 5.2 Test Discovery: Multi-Course Parameter Matrix
To discover tests across tracks, the query parameters and headers must match the student's enrolled courses:

#### Class 12th (Leader Test Series)
- **URL**: `GET https://api.allen-live.in/api/v1/tests/student-tests:byCompletionStatus`
- **Query Params**:
  `status=all&mode=all&page_number=1&page_size=25`
- **Headers**: Standard web headers. Returns 8 Leader tests.

#### Class 11th (Nurture Test Series)
- **URL**: `GET https://api.allen-live.in/api/v1/tests/student-tests:byCompletionStatus`
- **Query Params**:
  `status=all&mode=all&page_number=1&page_size=25`
- **Headers**:
  ```http
  course_id: cr_SUqkwoRLxGJ1jV8Ix60b3
  batch_list: bt_2Fsslkpec8p0kxgacLsCc
  client_type: mweb
  ```
  Returns 19 Nurture tests.

### 5.3 Syllabus PDF Extraction
- **Endpoint**: `POST https://api.allen-live.in/api/v1/tests/syllabus:byTestId`
- **JSON Payload**:
  ```json
  {
    "test_id": "test_5uK46Afnka7K",
    "client_type": "web"
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "syllabus_url": "https://ap-south-1-prod-test-and-assessment-syllabus.s3.ap-south-1.amazonaws.com/..."
    }
  }
  ```
- **TTL**: AWS S3 pre-signed URLs expire after **900 seconds (15 minutes)**. The backend downloads and persists the binary immediately to disk.

### 5.4 Question Paper PDF Extraction
- **Endpoint**: `GET https://api.allen-live.in/api/v1/tests/results/insights?test_id=test_5uK46Afnka7K`
- **Response**: Contains nested object with `question_paper_url` pointing to an AWS S3 signed bucket.
- **Availability**: Question papers are only generated after an exam has been conducted and `FINAL_RESULT_GENERATED` status is reached.

---

## 6. Deterministic PDF Extraction & Topic Processing Engine

Allen's syllabi are generated from vector desktop publishing software, producing multi-column landscape documents with unique artifacts.

### 6.1 Spatial Landscape Bounding (`extractor.py`)
`backend/app/processing/extractor.py`:
1. Inspects page dimensions. Allen NEET landscape syllabi have `width > 700 pt` (standard A4 landscape is 842 pt $\times$ 595 pt).
2. Extracts word bounding boxes:
   - **Header Top**: Min vertical coordinate of words matching `["PHYSICS", "CHEMISTRY", "BIOLOGY"]` (typically `header_top ≈ 215 pt`).
   - **Footer Top**: Min vertical coordinate of disclaimer words matching `"changes"`, `"schedule"`, `"governing"`, `"+91-"`, `"dlp@"` with `top > 450 pt` (typically `footer_top ≈ 506 pt`).
3. Words outside the interval `[header_top - 5, footer_top + 2]` are completely ignored, eliminating headers and disclaimers at the coordinate level.
4. Words inside the interval are partitioned into 3 columns:
   - **Physics Column**: `x0 < 300 pt`
   - **Chemistry Column**: `300 <= x0 < 550 pt`
   - **Biology Column**: `x0 >= 550 pt`

### 6.2 Structural Cleaning & Ligature Repair (`parser.py`)
`backend/app/processing/parser.py`:
1. **Dropped Font Ligatures**:
   - `classication` / `classi cation` $\rightarrow$ `Classification`
   - `owering` $\rightarrow$ `flowering` (e.g. *Sexual Reproduction in Flowering Plants*)
   - `deection` / `de ection` $\rightarrow$ `deflection` (e.g. *Half-Deflection Method*)
   - `oxalicacid` $\rightarrow$ `Oxalic Acid`
2. **Quote Normalization**: Converts backticks (`` ` ``) and typographic quotes (`’`, `‘`) to standard ASCII single quotes (`'`).
3. **Compound Chapter Protection**:
   - In raw syllabi, chapters contain internal commas (e.g. *"Units, Dimensions and Measurements"*, *"Work, Energy and Power"*, *"Acids, bases and the use of indicators"*).
   - If split naively on commas, *"Units, Dimensions and Measurements"* becomes an orphan *"Unit"*, and *"Work, Energy and Power"* becomes *"Work"*.
   - The parser rewrites these into protected forms before comma splitting occurs.
4. **Subject Header & Noise Elimination**: Standalone subject names (`"PHYSICS"`, `"CHEMISTRY"`, `"BIOLOGY"`, `"BOTANY"`, `"ZOOLOGY"`) and section noise (`"Section A"`, `"Part 1"`) are stripped.

### 6.3 Normalization & Canonical Keying (`normalizer.py`)
`backend/app/processing/normalizer.py`:
1. Converts raw titles to canonical kebab-case slugs: `subject:slug` (e.g. `physics:units-dimensions-and-measurements`, `chemistry:chemical-bonding-and-molecular-structure`, `biology:photosynthesis-in-higher-plants`).
2. Applies standard NCERT title casing.
3. Provides deterministic identity matching across all 27 tests.

---

## 7. Data Model, MongoDB Collections & Graph Invariants

The database `referme_neet_dev` on MongoDB Atlas enforces five primary collections with compound indexes.

```mermaid
erDiagram
    tests ||--o{ test_topics : "1 : N"
    topics ||--o{ test_topics : "1 : N"
    tests ||--o{ artifacts : "1 : N"
    ingestion_jobs ||--o{ tests : "records"

    tests {
        ObjectId _id PK
        string external_source "allen"
        string external_test_id UK "e.g. test_5uK46Afnka7K"
        string name "e.g. MAJOR TEST 4"
        string date "e.g. 26 Apr"
        int duration_minutes "180"
        string mode "Offline | CBT | Online"
        string status "FINAL_RESULT_GENERATED"
        string target_class "11th | 12th"
        string course_id "cr_SUqkwoRLxGJ1jV8Ix60b3"
        string course_name "Nurture Test Series"
        string processing_status "READY | PARTIAL | FAILED"
        bool has_syllabus
        bool has_question_paper
        datetime created_at
        datetime updated_at
    }

    topics {
        ObjectId _id PK
        string subject "Physics | Chemistry | Biology"
        string name "e.g. Equilibrium"
        string canonical_key UK "chemistry:equilibrium"
        string[] target_classes "['11th', '12th']"
        int test_count "Occurrences count"
        bool active
        datetime created_at
        datetime updated_at
    }

    test_topics {
        ObjectId _id PK
        string test_id FK "tests._id"
        string external_test_id "test_5uK46Afnka7K"
        string topic_id FK "topics._id"
        string canonical_key "chemistry:equilibrium"
        string subject "Chemistry"
        string source_text "Raw extracted text"
        string source_section "e.g. Experimental Skills"
        string normalization_method "deterministic"
        float confidence "1.0"
        datetime created_at
    }

    artifacts {
        ObjectId _id PK
        string test_id FK "tests._id"
        string external_test_id "test_5uK46Afnka7K"
        string kind "syllabus | question_paper"
        string storage_provider "local"
        string storage_key "storage_data/test_.../syllabus.pdf"
        string sha256 "SHA-256 hash"
        int size_bytes
        datetime created_at
    }

    ingestion_jobs {
        ObjectId _id PK
        string status "COMPLETED | PARTIAL | FAILED"
        int discovered_count
        int succeeded_count
        int partial_count
        int failed_count
        json error_summary
        datetime start_time
        datetime end_time
    }
```

### 7.1 Database Indexes (`db/indexes.py`)
- `tests`:
  - `{"external_source": 1, "external_test_id": 1}` (Unique)
  - `{"target_class": 1, "status": 1}`
- `topics`:
  - `{"canonical_key": 1}` (Unique)
  - `{"subject": 1, "test_count": -1}`
  - `{"target_classes": 1}`
- `test_topics`:
  - `{"test_id": 1, "topic_id": 1}` (Unique)
  - `{"topic_id": 1}`
  - `{"canonical_key": 1}`
- `artifacts`:
  - `{"test_id": 1, "kind": 1}` (Unique)
  - `{"sha256": 1}`

### 7.2 Data Invariants
1. **Idempotent Ingestion**: Running ingestion multiple times on the same course updates existing documents without duplicating test records or topic entities.
2. **Atomic Relationship Replacement**: `TestTopicRepository.replace_for_test(test_id, relationships)` deletes existing relationship documents for that specific `test_id` in a single operation before inserting new ones, eliminating orphaned or phantom edges.
3. **Class Tag Aggregation**: When a topic appears in both Class 11th and Class 12th tests, `TopicRepository.upsert_canonical` uses `$addToSet: {"target_classes": target_class}`, ensuring `target_classes` accurately reflects `["12th", "11th"]`.
4. **Dynamic Test Counts**: The `test_count` field on `TopicModel` represents the exact count of documents in `test_topics` pointing to that topic.

---

## 8. FastAPI Backend Endpoints Specification

All routes are mounted under prefix `/api/v1` in `backend/app/api/v1/`.

### 8.1 System Health
`GET /api/v1/health`
- **Response**: `{"status": "ok", "service": "referme-neet-backend"}`

### 8.2 Tests API (`api/v1/tests.py`)
`GET /api/v1/tests`
- **Query Parameters**:
  - `target_class` (Optional[str]): `"11th"`, `"12th"`, or `"all"`
  - `q` (Optional[str]): Search title or ID
  - `status` (Optional[str]): Filter by status (`"FINAL_RESULT_GENERATED"`, `"UPCOMING"`)
  - `mode` (Optional[str]): Filter by mode (`"Offline"`, `"CBT"`)
  - `has_syllabus` (Optional[bool]): Filter by syllabus availability
  - `has_question_paper` (Optional[bool]): Filter by question paper availability
  - `page` (int, default: 1), `page_size` (int, default: 20)
- **Response**: `PaginatedResponse[TestResponse]`

`GET /api/v1/tests/{test_identifier}`
- Retrieves test by MongoDB ObjectId or `external_test_id`.

`GET /api/v1/tests/{test_identifier}/topics`
- Returns all topics covered by this test, grouped by `physics`, `chemistry`, and `biology`.
- **Response Structure**:
  ```json
  {
    "test_id": "6a9fcd9548a0a0f4f10e4334",
    "external_test_id": "test_5uK46Afnka7K",
    "test_name": "MAJOR TEST",
    "total_topics": 53,
    "subjects": {
      "physics": [
        {
          "topic_id": "...",
          "name": "Units, Dimensions and Measurements",
          "canonical_key": "physics:units-dimensions-and-measurements",
          "subject": "Physics",
          "source_text": "Unit and Measurements",
          "confidence": 1.0
        }
      ],
      "chemistry": [...],
      "biology": [...]
    }
  }
  ```

### 8.3 Topics API (`api/v1/topics.py`)
`GET /api/v1/topics`
- **Query Parameters**:
  - `target_class` (Optional[str]): Filter by `"11th"` or `"12th"`
  - `subject` (Optional[str]): `"Physics"`, `"Chemistry"`, or `"Biology"`
  - `q` (Optional[str]): Search name or canonical key
  - `sort_by` (str, default: `"test_count"`), `order` (str, default: `"desc"`)
  - `page` (int, default: 1), `page_size` (int, default: 50)
- **Response**: `PaginatedResponse[TopicResponse]`

`GET /api/v1/topics/{topic_identifier}/tests`
- **The Bidirectional Lookup Endpoint**: Returns all tests whose syllabus contains this topic.
- **Response**: `TopicWithTestsResponse` containing `topic` details, `total_tests` count, and array of tests with `source_text` snippets.

### 8.4 Artifacts Streamer (`api/v1/artifacts.py`)
`GET /api/v1/tests/{test_identifier}/artifacts/{kind}`
- **Path Parameters**:
  - `test_identifier`: MongoDB ID or `external_test_id`
  - `kind`: `"syllabus"` or `"question_paper"`
- **Response**: Streams binary PDF with header `Content-Type: application/pdf` directly from local storage, enabling inline browser rendering.

---

## 9. Frontend Web Studio (Next.js 14) Architecture

### 9.1 Technology Choices
- **Next.js 14 App Router** (`frontend/app/page.tsx`): Single-page dynamic command center.
- **Tailwind CSS + Custom Cyberpunk Palettes**:
  - Deep Space Void: `#0A0518`
  - Cyber Purple / Neon Indigo: `#3E0F8D`, `#9564DD`
  - Fluorescent Gold / Amber Accent: `#E4DA72`
- **Framer Motion + Gyroscope Tilt**: Surfaces tilt in 3D relative to mouse coordinates (`components/TiltCard.tsx`).
- **Lucide Icons**: Semantic iconography across all controls.

### 9.2 State Coordination & Reactive Filtering (`app/page.tsx`)
The page maintains state for:
- `selectedClass`: `"12th" | "11th" | "all"`
- `viewMode`: `"topics" | "tests"`
- `selectedSubject`: `"all" | "physics" | "chemistry" | "biology"`
- `searchQuery`: Search string

#### Reactive Scoping Architecture
To provide responsive metrics while preserving search flexibility, the frontend computes two tiers of memos:

1. **Class-Scoped Catalog (`classTopics` & `classTests`)**:
   Independent of the search bar or subject tabs, computes the true size of the active course track. Fed directly into `ControlCenter` and `CleanHud` so metrics update immediately when switching courses:
   ```typescript
   const classTopics = useMemo(() => {
     return topics.filter((t) => {
       if (selectedClass === "all") return true;
       return t.target_classes && t.target_classes.map((c) => c.toLowerCase()).includes(selectedClass.toLowerCase());
     });
   }, [topics, selectedClass]);

   const classTests = useMemo(() => {
     return tests.filter((t) => {
       if (selectedClass === "all") return true;
       const testClass = t.target_class?.toLowerCase() || "12th";
       return testClass === selectedClass.toLowerCase();
     });
   }, [tests, selectedClass]);
   ```

2. **Stream-Scoped View (`filteredTopics` & `filteredTests`)**:
   Applies `selectedSubject` and `searchQuery` on top of `selectedClass` to drive the 3D card feed:
   ```typescript
   const filteredTopics = useMemo(() => {
     return topics.filter((t) => {
       const matchesSubject =
         selectedSubject === "all" || t.subject.toLowerCase() === selectedSubject.toLowerCase();
       const matchesClass =
         selectedClass === "all" ||
         (t.target_classes && t.target_classes.map((c) => c.toLowerCase()).includes(selectedClass.toLowerCase()));
       const q = searchQuery.toLowerCase().trim();
       const matchesQuery =
         !q ||
         t.name.toLowerCase().includes(q) ||
         t.canonical_key.toLowerCase().includes(q) ||
         t.aliases?.some((a) => a.toLowerCase().includes(q));

       return matchesSubject && matchesClass && matchesQuery;
     });
   }, [topics, selectedSubject, selectedClass, searchQuery]);
   ```

### 9.3 Visual Badges Matrix
- **Topic Cards (`TopicCard.tsx`)**:
  - `Class 11th & 12th`: Yellow glowing badge for shared chapters (*Equilibrium*, *Units and Measurements*).
  - `Class 11th` / `Class 12th`: Subtle purple badge for class-specific chapters.
- **Test Cards (`TestCard.tsx`)**:
  - `12th • Leader` / `11th • Nurture`: Distinct course badge on top left.
  - Mode badge (`Offline`, `CBT`, `Online`).
  - Status indicator (`UPCOMING` gold glow vs `FINAL_RESULT_GENERATED` purple).
  - Quick action buttons: **View Syllabus PDF** and **View Question Paper PDF**.
- **Topic Detail Studio (`TopicDetailStudio.tsx`)**:
  - Displays which classes test this topic.
  - Lists every scheduled test with course tags and the exact matched syllabus line from the PDF.

---

## 10. The Absolute Ground-Truth System Audit

This section represents the verified, exact ground-truth audit of every test, artifact, topic, and relationship in the live system.

### 10.1 Comprehensive Test Manifest (27 Tests)

| # | External Test ID | Test Title | Course Track | Mode | Status | Syllabus PDF | Question Paper PDF | Topics Indexed |
| :-: | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :-: |
| 1 | `test_rKS8BbPwZFxe` | MINOR TEST (DLP) | 12th • Leader | Offline | UPCOMING | ✓ (1468.2 KB) | ✗ Pending | 9 |
| 2 | `test_jxnew5CjV9Lx` | SEMI MAJOR TEST (DLP) | 12th • Leader | CBT | UPCOMING | ✓ (1479.1 KB) | ✗ Pending | 50 |
| 3 | `test_TmbMepCgpdJZ` | MINOR TEST (DLP) | 12th • Leader | Offline | FINAL_RESULT_GENERATED | ✓ (1469.0 KB) | ✓ (641.1 KB) | 0 (Replaced) |
| 4 | `test_BbR0RFumr53O` | REVIEW TEST ONLINE | 12th • Leader | Online | FINAL_RESULT_GENERATED | ✓ (1473.1 KB) | ✓ (593.3 KB) | 26 |
| 5 | `test_IFErvfdHfGAw` | REVIEW TEST (DLP) | 12th • Leader | CBT | FINAL_RESULT_GENERATED | ✓ (1463.6 KB) | ✓ (668.8 KB) | 26 |
| 6 | `test_s1CQQXVd1Qd3` | MINOR TEST (DLP) | 12th • Leader | Offline | FINAL_RESULT_GENERATED | ✓ (1467.5 KB) | ✓ (872.0 KB) | 7 |
| 7 | `test_HxyA3FFNui4U` | MINOR TEST | 12th • Leader | CBT | FINAL_RESULT_GENERATED | ✓ (1475.3 KB) | ✓ (665.9 KB) | 8 |
| 8 | `test_zPKUFDh5cQxo` | MINOR TEST 01 | 12th • Leader | CBT | FINAL_RESULT_GENERATED | ✓ (1476.6 KB) | ✓ (790.7 KB) | 11 |
| 9 | `test_5uK46Afnka7K` | MAJOR TEST | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (294.7 KB) | ✓ (682.8 KB) | 53 |
| 10 | `test_HNBhux1nfQCl` | MAJOR TEST 4 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (294.7 KB) | ✓ (695.4 KB) | 53 |
| 11 | `test_zxjVgTrujXp0` | AIOT TEST 3 | 11th • Nurture | Offline | CUMULATED | ✓ (294.8 KB) | ✗ Pending | 53 |
| 12 | `test_kIuhK6z4dcyW` | MAJOR TEST 2 | 11th • Nurture | Offline | CUMULATED | ✓ (294.8 KB) | ✗ Pending | 53 |
| 13 | `test_FFC8nh7hgOLS` | MAJOR TEST 1 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (294.8 KB) | ✗ Pending | 53 |
| 14 | `test_l21tMcri8Syb` | SEMI MAJOR TEST 2 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (293.8 KB) | ✗ Pending | 30 |
| 15 | `test_oHi438EEMphH` | REVIEW TEST 4 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (272.1 KB) | ✗ Pending | 16 |
| 16 | `test_6wfuFMTF1H88` | UNIT TEST 8 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (271.3 KB) | ✓ (737.2 KB) | 13 |
| 17 | `test_yQQGKny3ApdG` | UNIT TEST 7 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (271.5 KB) | ✓ (973.1 KB) | 8 |
| 18 | `test_UXoL5gKK8BPd` | REVIEW TEST 3 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (271.3 KB) | ✓ (659.8 KB) | 14 |
| 19 | `test_Fl2I8uJOJ5Hu` | UNIT TEST 6 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (269.5 KB) | ✓ (649.6 KB) | 6 |
| 20 | `test_CRcf1xTcnnQC` | UNIT TEST 5 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (270.0 KB) | ✓ (539.0 KB) | 8 |
| 21 | `test_vK84KklkvEdF` | SEMI MAJOR TEST 1 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (271.1 KB) | ✓ (1674.5 KB) | 23 |
| 22 | `test_n1zOV8uChT0j` | REVIEW TEST 2 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (226.9 KB) | ✓ (1170.2 KB) | 10 |
| 23 | `test_nLzMnANHtSXD` | UNIT TEST 4 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (226.7 KB) | ✓ (484.2 KB) | 7 |
| 24 | `test_Clqz2n10Brz7` | UNIT TEST 3 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (226.7 KB) | ✓ (489.9 KB) | 5 |
| 25 | `test_M8ueeVRZGIOs` | REVIEW TEST 01 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (227.1 KB) | ✓ (1094.5 KB) | 13 |
| 26 | `test_OpsukyexJtbZ` | UNIT TEST 2 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✓ (226.6 KB) | ✓ (1610.8 KB) | 7 |
| 27 | `test_xM51AiGP85c2` | UNIT TEST 1 | 11th • Nurture | Offline | FINAL_RESULT_GENERATED | ✗ 403 S3 Link | ✓ (413.6 KB) | 0 (No Syl) |

### 10.2 PDF Storage Audit (46 Files on Disk)
All files reside in `backend/storage_data/test_<external_test_id>/`:
- **Total Tests with Directories**: 27
- **Syllabus PDFs Downloaded**: **26 / 27** (Only `test_xM51AiGP85c2` missing due to unsigned S3 403).
- **Question Paper PDFs Downloaded**: **20 / 27**
  - Class 12th Leader: 6 QPs acquired; 2 pending exam conduct (`test_rKS8BbPwZFxe`, `test_jxnew5CjV9Lx`).
  - Class 11th Nurture: 14 QPs acquired; 5 pending exam conduct (`test_zxjVgTrujXp0`, `test_kIuhK6z4dcyW`, `test_FFC8nh7hgOLS`, `test_l21tMcri8Syb`, `test_oHi438EEMphH`).
- **Total Local PDF Files**: $26 + 20 = \mathbf{46\text{ files}}$.

### 10.3 Topic Catalog Breakdown (102 Canonical Topics)

- **Total Unique Topics**: **102 Topics**
- **Class Track Scopes**:
  - **Class 12th Track Catalog**: **50 Topics** (29 exclusive + 21 shared)
  - **Class 11th Track Catalog**: **73 Topics** (52 exclusive + 21 shared)
  - **Shared Core (11th & 12th Overlap)**: **21 Topics** ($50 + 73 - 21 = 102$)

#### The 21 Shared Core Topics (Appearing in both 11th & 12th Tests)
1. `physics:units-dimensions-and-measurements` (*Units, Dimensions and Measurements*)
2. `physics:basic-mathematics-used-in-physics-and-vectors` (*Basic Mathematics in Physics & Vectors*)
3. `physics:kinematics-and-current-electricity` (*Kinematics & Current Electricity*)
4. `physics:laws-of-motion-and-friction` (*Laws of Motion & Friction*)
5. `physics:exp-vernier-calipers` (*Experimental Skills: Vernier Calipers*)
6. `physics:exp-screw-gauge` (*Experimental Skills: Screw Gauge*)
7. `chemistry:some-basic-concepts-of-chemistry` (*Some Basic Concepts of Chemistry*)
8. `chemistry:structure-of-atom` (*Atomic Structure*)
9. `chemistry:classification-of-elements-and-periodicity-in-properties` (*Periodicity in Properties*)
10. `chemistry:chemical-bonding-and-molecular-structure` (*Chemical Bonding & Molecular Structure*)
11. `chemistry:thermodynamics` (*Thermodynamics*)
12. `chemistry:equilibrium` (*Equilibrium*)
13. `chemistry:redox-reactions` (*Redox Reactions*)
14. `biology:the-living-world` (*The Living World*)
15. `biology:biological-classification` (*Biological Classification*)
16. `biology:plant-kingdom` (*Plant Kingdom*)
17. `biology:animal-kingdom` (*Animal Kingdom*)
18. `biology:morphology-of-flowering-plants` (*Morphology of Flowering Plants*)
19. `biology:cell-the-unit-of-life` (*Cell: The Unit of Life*)
20. `biology:biomolecules` (*Biomolecules*)
21. `biology:cell-cycle-and-cell-division` (*Cell Cycle and Cell Division*)

#### Subject Distribution Across Courses
| Subject | Class 12th Total | Class 11th Total | Shared | Overall Unique |
| :--- | :---: | :---: | :---: | :---: |
| **Physics** | 23 | 34 | 6 | **51** |
| **Chemistry** | 13 | 16 | 7 | **22** |
| **Biology** | 14 | 23 | 8 | **29** |
| **Total** | **50** | **73** | **21** | **102** |

### 10.4 Data Integrity & Graph Purity Verification
- **Total Bidirectional Edges**: **562 Indexed Edges** in `test_topics`.
- **Zero Anomaly Guarantee**:
  - Leaked Subject Prefixes (`PHYSICS:`, `CHEMISTRY:`, `BIOLOGY:`): **0**
  - Leaked Footer Disclaimers (`+91-744-3510275`, `dlp@allen.in`, `Governing Body`): **0**
  - Fragmented Chapter Tokens (`"Unit"`, `"Dimensions and Measurement"`, `"Work"`): **0**
  - Corrupted OCR Font Ligatures (`classication`, `owering`, `deection`): **0**

---

## 11. Operational Runbook: Commands, Ingestion & Auditing

### 11.1 Launching the Full Stack
1. **Start Backend Server**:
   ```bash
   cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
   PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start Frontend Dev Server**:
   ```bash
   cd /Users/mast/Documents/VInayPrograming/ReferMe/frontend
   npm run dev
   ```
   Navigate to `http://localhost:3000`.

### 11.2 Running Live Ingestion CLI
To query Allen Live API and populate MongoDB Atlas:
```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend

# Ingest Class 11th (Nurture - 19 Tests)
PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/python -u -m app.cli ingest --live --course 11th

# Ingest Class 12th (Leader - 8 Tests)
PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/python -u -m app.cli ingest --live --course 12th

# Ingest Both Courses Sequentially
PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/python -u -m app.cli ingest --live --course all
```

### 11.3 Auditing Database & File Integrity
Run the audit script to verify live database state, check on-disk file sizes, and scan for string anomalies:
```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/python -u scripts/audit_database.py
```

### 11.4 Running Automated Test Suite
```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
PYTHONPATH=. /Users/mast/miniconda3/envs/all/bin/pytest
```
*Current test suite*: **23 passing unit tests** verifying deterministic normalization, ligature repairs, contextual headers, API routes, and repository upsert logic.

---

## 12. Known Quirks, Edge Cases & Failure Recovery Protocols

### 12.1 Python Stdout Buffering in Background Subprocesses
- **Symptom**: Running a background command via AI agent or script results in an empty log or appears frozen.
- **Root Cause**: When Python detects a non-interactive pipe, it buffers standard output by default.
- **Protocol**: Always include `-u` flag (`python -u ...`) or use `flush=True` in `print()` statements for CLI commands.

### 12.2 Next.js In-Memory Webpack Cache Desync
- **Symptom**: Frontend renders a 500 error page with `TypeError: __webpack_modules__[moduleId] is not a function`.
- **Root Cause**: Running `npm run build` while `next dev` is running overwrites `.next/server/` files on disk, making the in-memory webpack runtime references of the dev server stale.
- **Protocol**: Terminate the process on port 3000 and restart `npm run dev`:
  ```bash
  kill -9 $(lsof -ti :3000)
  npm run dev
  ```

### 12.3 Allen S3 Ephemeral Tokens & 403 Forbidden on Unsigned Links
- **Symptom**: `httpx.HTTPStatusError: 403 Forbidden` on `https://ap-south-1-prod-test-and-assessment-syllabus.s3.ap-south-1.amazonaws.com/...`
- **Root Cause**: Allen's signed S3 links have an expiration window of 900 seconds (15 minutes). Furthermore, one specific test (`test_xM51AiGP85c2` - UNIT TEST 1) returns a raw S3 link without signature parameters.
- **Protocol**: The `AllenClient.get_syllabus_pdf` method wraps the download inside a `try ... except Exception` block that logs a warning and returns `None`. The orchestrator treats missing syllabi as `PARTIAL` without crashing, preserving the question paper and existing relationships.

### 12.4 Atomicity of Re-Indexing
- **Risk**: Ingesting a test whose topics changed could leave stale edges in `test_topics`.
- **Protocol**: `TestTopicRepository.replace_for_test(test_id, relationships)` always deletes all records where `test_id == current_test_id` before inserting the newly parsed relationships. Following insertion, affected topic counts are recomputed from live document counts in `test_topics`.

---

## 13. Handoff Checklist for Resuming Engineers

When picking up this codebase:
- [ ] Confirm Python environment: `/Users/mast/miniconda3/envs/all/bin/python`
- [ ] Run `python -u scripts/audit_database.py` to confirm MongoDB Atlas connection and the 27-test / 102-topic baseline.
- [ ] Run `pytest` in `backend/` to verify all 23 unit tests pass.
- [ ] Verify `http://localhost:8000/api/v1/health` responds with `{"status": "ok"}`.
- [ ] Verify `http://localhost:3000` loads the Next.js Web Studio and that toggling between:
  - **12th • Leader**: shows exactly **8 tests** and **50 topics** across both the HUD counters, pill buttons, and 3D card stream.
  - **11th • Nurture**: shows exactly **19 tests** and **73 topics** across both the HUD counters, pill buttons, and 3D card stream.
  - **All Classes**: shows exactly **27 tests** and **102 topics**.
- [ ] Click on a test card (e.g. `MAJOR TEST`) $\rightarrow$ verify the inline PDF studio displays the syllabus and grouped subjects.
- [ ] Click on a topic card (e.g. `Equilibrium`) $\rightarrow$ verify the bidirectional radar drawer lists tests from both Class 11th and 12th with matched source excerpts.
