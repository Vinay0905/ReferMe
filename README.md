# ReferMe — ALLEN NEET Test ↔ Topic Intelligence System

> **A fast, bidirectional knowledge graph and studio connecting ALLEN NEET test papers, syllabi, and topics.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg?style=flat&logo=next.js)](https://nextjs.org)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248.svg?style=flat&logo=mongodb)](https://www.mongodb.com/atlas)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Language-Python%203.10%2B-3776AB.svg?style=flat&logo=python)](https://www.python.org)

---

## 📌 Project Overview

NEET aspirants take dozens of minor, major, and revision tests over the academic year. Each test has a detailed multi-page syllabus, but students and educators struggle with two fundamental questions:

1. **Topic → Tests**: *"Which tests covered Current Electricity, Rotational Motion, or Genetics so I can practice targeted questions?"*
2. **Test → Topics**: *"What exact chapters and subtopics were tested in Minor Test 04?"*

**ReferMe** solves this by converting raw ALLEN student portal test syllabi and papers into a searchable **bidirectional knowledge graph** backed by an interactive modern web studio.

```text
                  ┌─────────────────────────────────┐
                  │      ALLEN Student Portal       │
                  │ (Live API or Realistic Fixtures)│
                  └────────────────┬────────────────┘
                                   │ (PDFs & Test Metadata)
                                   ▼
                   ┌───────────────────────────────┐
                   │  Ingestion & Parsing Pipeline │
                   │  - Deterministic PDF Parser   │
                   │  - Dynamic Topic Normalizer   │
                   │  - Idempotent Mongo Atlas DB  │
                   └───────────────┬───────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│       FastAPI REST Backend      │         │     Next.js 14 Web Studio       │
│  - /api/v1/tests                │◄───────►│  - Dark Cyber HUD & Controls    │
│  - /api/v1/topics               │         │  - Bidirectional Graph Explorer │
│  - /api/v1/artifacts            │         │  - Split-view Dual PDF Viewer   │
│  - /api/v1/ingest               │         │  - Physics / Chem / Bio Filter  │
└─────────────────────────────────┘         └─────────────────────────────────┘
```

---

## ✨ Key Features

- **Bidirectional Exploration**:
  - **Topic → Tests**: Select any topic in Physics, Chemistry, or Biology (including Botany/Zoology) and instantly view all relevant tests with match confidence and source snippets.
  - **Test → Topics**: Select any test to view its full syllabus decomposed by subject, chapter, and normalized subtopics.
- **Deterministic PDF Parsing Engine**:
  - Layout-aware PDF text extraction with `pdfplumber` and automatic fallback to `pypdf`.
  - Header/footer noise filtering, section detection, and delimited item extraction.
  - Dynamic discovery and canonical slug generation (e.g. `physics:simple-harmonic-motion`).
  - Pre-configured alias mappings (e.g. `SHM`, `EM Waves`, `GOC`).
- **Integrated Dual PDF Studio**:
  - Stream or open syllabus PDFs and question paper/solution PDFs side-by-side directly in the browser.
  - Local caching and fallback links for distraction-free offline studying.
- **Resilient Ingestion Adapter**:
  - Dual-mode client supporting both **Live Mode** (authenticated `api.allen-live.in` session) and **Mock Mode** (realistic offline fixtures).
  - Background asynchronous task runner and CLI runner with idempotent upserts.
- **Modern Glassmorphic UI**:
  - Built with Next.js 14 App Router, TypeScript, Tailwind CSS, and Lucide icons.
  - Fast client-side filtering, debounced search, responsive layouts, and interactive HUD.

---

## 🏗️ Repository Architecture

```text
ReferMe/
├── backend/                         # FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/                  # REST API Endpoints
│   │   │   ├── artifacts.py         # PDF streaming & metadata endpoints
│   │   │   ├── health.py            # Health & readiness checks
│   │   │   ├── ingest.py            # Ingestion trigger & job status
│   │   │   ├── tests.py             # Test catalog & test ↔ topic lookups
│   │   │   └── topics.py            # Topic catalog & topic ↔ tests lookups
│   │   ├── db/                      # MongoDB Atlas connection & indexing
│   │   ├── ingestion/               # Orchestrator & pipeline logic
│   │   ├── integrations/allen/      # External ALLEN HTTP client (Live/Mock)
│   │   ├── models/                  # Pydantic data models & ODM
│   │   ├── processing/              # PDF extractor, parser & topic normalizer
│   │   ├── repositories/            # Database query layers (Test, Topic, Ingest)
│   │   ├── schemas/                 # API request & response schemas
│   │   ├── storage/                 # Local filesystem & artifact storage
│   │   ├── cli.py                   # Management CLI tool
│   │   ├── config.py                # Environment configuration & settings
│   │   └── main.py                  # Application entrypoint & CORS setup
│   ├── requirements.txt             # Python dependencies
│   ├── tests/                       # Automated test suites (pytest)
│   └── storage_data/                # Locally stored PDF artifacts (gitignored)
│
├── frontend/                        # Next.js 14 Web Studio
│   ├── app/                         # App Router (page.tsx, layout.tsx, globals.css)
│   ├── components/                  # React UI Components
│   │   ├── CleanHud.tsx             # Studio navigation & status bar
│   │   ├── ControlCenter.tsx        # Search, filters & mode toggles
│   │   ├── PdfStudio.tsx            # Embedded dual PDF viewer
│   │   ├── TestCard.tsx             # Test catalog card item
│   │   ├── TopicCard.tsx            # Topic catalog card item
│   │   └── TopicDetailStudio.tsx    # Topic test breakdown modal/panel
│   ├── lib/
│   │   └── api.ts                   # Typed API client with memory cache
│   ├── package.json                 # Frontend dependencies & scripts
│   └── tailwind.config.ts           # Tailwind CSS theme styling
│
├── docs/                            # Deep Technical Design Specifications
│   ├── 01-project-requirements.md
│   ├── 02-allen-reverse-engineering.md
│   ├── 03-system-architecture.md
│   ├── 04-data-model.md
│   ├── 05-ingestion-pipeline.md
│   ├── 06-pdf-and-topic-processing.md
│   ├── 07-backend-api.md
│   ├── 08-frontend.md
│   ├── 09-security.md
│   ├── 10-testing-and-observability.md
│   ├── 11-failure-modes-and-edge-cases.md
│   ├── 12-future-ai-and-scaling.md
│   └── 13-known-unknowns.md
│
├── Agent.md                         # Master operating contract for AI assistants
├── PHASE_1_GUIDE.md                 # Phase 1: DB models, repos & storage
├── PHASE_2_GUIDE.md                 # Phase 2: PDF extraction & topic normalizer
└── PHASE_3_GUIDE.md                 # Phase 3: Ingestion pipeline & CLI
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10` or higher
- **Node.js**: `18.x` or `20.x` (with npm)
- **MongoDB Atlas** or a local MongoDB instance (v6.0+)

---

### 1. Backend Setup

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment** (or conda environment):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy the `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your settings:
   ```dotenv
   ENVIRONMENT=development
   PROJECT_NAME="ALLEN NEET Test ↔ Topic Intelligence System"
   API_V1_STR="/api/v1"

   # MongoDB Atlas Connection
   MONGODB_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
   MONGODB_DB_NAME="referme_neet_dev"

   # Storage
   STORAGE_PROVIDER="local"
   LOCAL_STORAGE_DIR="./storage_data"

   # Ingestion (Use Mock mode for offline development without credentials)
   ALLEN_BASE_URL="https://api.allen-live.in"
   ALLEN_AUTH_TOKEN=""
   ALLEN_MOCK_MODE=true
   ```

5. **Populate initial data using the Ingestion CLI**:
   Run the CLI in mock mode to seed your database with realistic NEET tests and syllabi:
   ```bash
   python -m app.cli ingest --mock --limit 10
   ```

6. **Start the FastAPI development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Interactive Swagger API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 2. Frontend Setup

1. **Navigate to the frontend folder**:
   ```bash
   cd ../frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **(Optional) Configure environment variable**:
   By default, the frontend connects to `http://127.0.0.1:8000/api/v1`. To customize:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1" > .env.local
   ```

4. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```

5. **Open the studio**:
   Visit [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 📡 REST API Reference

All endpoints are prefixed by `/api/v1` (except the root `/health` checks):

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` / `/api/v1/health` | Service health status and MongoDB connectivity |
| `GET` | `/api/v1/tests` | List all tests with filtering (`search`, `status`, `category`, pagination) |
| `GET` | `/api/v1/tests/{id}` | Retrieve metadata and artifact availability for a test |
| `GET` | `/api/v1/tests/{id}/topics` | Get all extracted topics for a test grouped by subject |
| `GET` | `/api/v1/topics` | List canonical topics with `subject`, `search`, and sorting by test count |
| `GET` | `/api/v1/topics/{id}` | Get topic details by ID or canonical slug |
| `GET` | `/api/v1/topics/{id}/tests` | Find all tests containing a given topic |
| `GET` | `/api/v1/artifacts/tests/{id}/{type}` | Stream PDF (`syllabus` or `question_paper`) or get metadata |
| `POST`| `/api/v1/ingest/run` | Trigger a background ingestion pipeline run |
| `GET` | `/api/v1/ingest/jobs/{id}` | Check status, progress, and audit logs of an ingestion job |

---

## 🛠️ CLI Management

The backend includes a command-line interface for maintenance and ingestion tasks:

```bash
# Run ingestion in mock mode (offline)
python -m app.cli ingest --mock --limit 10

# Run ingestion in live mode (requires ALLEN_AUTH_TOKEN in .env)
python -m app.cli ingest --live

# Filter by test status
python -m app.cli ingest --mock --status COMPLETED --limit 5

# Inspect current database metrics
python -m app.cli inspect
```

---

## 🧪 Testing & Verification

Automated test suites verify database operations, PDF text extraction, parsing patterns, normalization rules, and ingestion pipeline idempotency:

```bash
cd backend

# Run the complete test suite
pytest

# Run tests with verbose output
pytest tests/ -v

# Run only the syllabus parser & normalizer test suite
pytest tests/test_parser.py -v

# Run the ingestion & client integration tests
pytest tests/test_ingestion.py -v
```

---

## 📚 Technical Specifications & Documentation

Comprehensive architectural design records and implementation notes are maintained in the repository:

- [`DEPLOYMENT.md`](DEPLOYMENT.md) — One-command Docker replication, database migration, and cloud storage (S3/R2) guide.
- [`Agent.md`](Agent.md) — Master operating context, invariants, and product requirements.
- [`PHASE_1_GUIDE.md`](PHASE_1_GUIDE.md) — MongoDB schemas, repositories, and local storage provider.
- [`PHASE_2_GUIDE.md`](PHASE_2_GUIDE.md) — Deterministic PDF parsing and canonical topic normalization.
- [`PHASE_3_GUIDE.md`](PHASE_3_GUIDE.md) — Adapter layer, live/mock client, and ingestion orchestrator.
- [`docs/`](docs/) — Full engineering documentation covering reverse-engineering observations, security boundaries, failure modes, and data contracts.

---

## 🔒 Security & Compliance

- **Zero Credential Storage**: No Bearer tokens, cookies, or signed URLs are stored in source code or logged.
- **Isolated Adapter**: The external ALLEN portal API is strictly isolated within `app/integrations/allen/`; domain code does not touch raw external URLs.
- **Safe Extraction**: PDF extraction validates magic bytes (`%PDF-`) and rejects HTML error redirects or non-PDF payloads before processing.
