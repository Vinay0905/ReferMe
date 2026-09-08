# Phase 3: Ingestion Pipeline & Adapter Layer

This guide details the architecture, components, and verification steps for **Phase 3: Ingestion Pipeline & Adapter Layer**.

---

## 1. Overview of Components Created in Phase 3

```text
backend/
├── app/
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── allen/
│   │       ├── __init__.py
│   │       ├── client.py        # External HTTP adapter for api.allen-live.in (supports mock & live)
│   │       └── mock_data.py     # Realistic test cards & PDF fixtures for offline development
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── orchestrator.py      # End-to-end ingestion orchestrator (Discovery → Storage → Indexing)
│   ├── repositories/
│   │   └── ingestion_repo.py    # Audit repository tracking IngestionJobModel records
│   ├── api/
│   │   └── v1/
│   │       └── ingest.py        # Admin endpoints: POST /api/v1/ingest/run & GET /api/v1/ingest/jobs/{id}
│   ├── cli.py                   # Management CLI: python -m app.cli ingest
│   └── config.py                # Added ALLEN_BASE_URL, ALLEN_AUTH_TOKEN, ALLEN_MOCK_MODE
└── tests/
    └── test_ingestion.py        # Automated tests for AllenClient, Orchestration & Idempotency
```

---

## 2. Component Details

### 2.1 ALLEN Client Adapter (`app/integrations/allen/client.py`)
- **Isolation**: Encapsulates all interactions with `https://api.allen-live.in`. The rest of the application never touches raw ALLEN URLs.
- **Dual Mode (Mock vs Live)**:
  - **Mock Mode**: When `ALLEN_MOCK_MODE=true` or when no token is present, it returns sample test cards and mock PDF bytes.
  - **Live Mode**: When `ALLEN_AUTH_TOKEN` is set, makes authenticated async requests using `httpx`:
    - `list_tests()`: Calls `GET /api/v1/tests/student-tests:byCompletionStatus`.
    - `get_syllabus_pdf()`: Calls `POST /api/v1/tests/{test_id}/syllabus` and downloads the signed S3 PDF.
    - `get_question_paper_pdf()`: Calls `GET /api/v1/tests/{test_id}/result-insights` to extract and download the English Solution PDF.
- **Security**: No secrets or Bearer tokens are logged or included in error traces.

### 2.2 Ingestion Orchestrator (`app/ingestion/orchestrator.py`)
Executes the full pipeline:
1. **Discovery**: Queries `AllenClient.list_tests()`.
2. **Metadata Upsert**: Saves/updates `TestModel` with date, duration, mode, category, and status.
3. **Artifact Acquisition**: Downloads syllabus PDF bytes and saves to `storage_data/test_{id}/syllabus.pdf`.
4. **Content Hashing**: Hashes PDF using SHA-256 for change detection.
5. **Topic Parsing & Normalization**: Uses Phase 2 `SyllabusParser` and `TopicNormalizer`.
6. **Canonical Upsert & Relationship Replacement**:
   - Upserts each unique topic into `topics` collection.
   - Replaces `test_topics` for this test with exact source text, section context, and confidence.
   - Updates denormalized `test_count` for each topic.
7. **Question Paper Acquisition**: Attempts to acquire solution PDF. If available, records `question_paper` artifact; if not yet released, marks test as `PARTIAL` without failing.
8. **Idempotency**: Running repeatedly will safely update data without creating duplicate tests or relationships.

### 2.3 CLI & Admin API Triggers
- **CLI Runner**: `python -m app.cli ingest` with optional `--limit`, `--status`, `--mock`, or `--live`.
- **Admin API**: `POST /api/v1/ingest/run` launches ingestion in a background task and returns the `job_id`.

---

## 3. How to Run and Verify Phase 3

In your terminal (with conda environment `all` activated):

### Step 1: Run Automated Ingestion Tests
```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
pytest tests/test_ingestion.py -v
```

Expected output:
```text
tests/test_ingestion.py::test_allen_client_parse_card PASSED
tests/test_ingestion.py::test_allen_client_mock_mode PASSED
tests/test_ingestion.py::test_ingestion_orchestrator_mock_run PASSED
tests/test_ingestion.py::test_ingestion_idempotency PASSED

======================== 4 passed in 0.40s ========================
```

---

### Step 2: Run CLI Ingestion into your MongoDB Atlas

Run a test ingestion run in **Mock Mode** to see your Atlas database populate with realistic tests, topics, and relationships:

```bash
python -m app.cli ingest --mock --limit 3
```

You will see:
```text
=================================================================
ALLEN NEET Test ↔ Topic Intelligence System: Ingestion Runner
=================================================================
Mode: MOCK (Offline Fixtures)
Status Filter: all
Mode Filter: all
Test Limit: 3
-----------------------------------------------------------------
...
-----------------------------------------------------------------
Ingestion Job Completed!
Job ID: 66dd8f12...
Final Status: COMPLETED
Tests Discovered: 3
Tests Succeeded: 3
Tests Partial: 0
Tests Failed: 0
=================================================================
```

---

### Step 3: Running Live Ingestion (When You Have Your Session Token)

When you want to fetch your **real live tests** from `https://api.allen-live.in`:

1. In your browser, log in to `allen.in`.
2. Open DevTools (`F12` or `Cmd+Option+I`) ➔ **Network** tab.
3. Click on the "Tests" tab in the ALLEN portal.
4. Look for the request to `student-tests:byCompletionStatus`.
5. Copy the Bearer token from the `Authorization` request header: `Bearer eyJ...`
6. Put it in your `backend/.env`:
   ```ini
   ALLEN_AUTH_TOKEN="eyJhbGci..."
   ALLEN_MOCK_MODE=false
   ```
7. Run live ingestion:
   ```bash
   python -m app.cli ingest --live --limit 5
   ```

---

## Next Step: Phase 4
Once Phase 3 is verified, we move to **Phase 4: Backend REST API & Query Optimization** (`GET /api/v1/tests`, `GET /api/v1/topics`, `GET /api/v1/topics/{id}/tests`, `GET /api/v1/tests/{id}/topics`, and artifact streaming).
