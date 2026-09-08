# Phase 2: PDF Parsing & Topic Processing Engine

This guide details the architecture, components, and verification steps for **Phase 2: PDF Parsing & Topic Processing Engine**.

---

## 1. Overview of Components Created in Phase 2

All files are located in `backend/app/processing/` and `backend/tests/`:

```text
backend/
├── app/
│   └── processing/
│       ├── __init__.py
│       ├── extractor.py    # Deterministic PDF text & metadata extractor (pdfplumber + pypdf)
│       ├── parser.py       # Structural NEET syllabus parser (Subjects, Chapters, Topics)
│       └── normalizer.py   # Canonical topic generator (Pure dynamic discovery + slugify + aliases)
└── tests/
    ├── fixtures/
    │   ├── __init__.py
    │   └── sample_syllabus.py # Realistic NEET syllabus fixture & programmatic PDF builder
    └── test_parser.py      # Comprehensive unit tests for extraction, parsing & normalization
```

---

## 2. Component Details

### 2.1 PDF Text Extractor (`app/processing/extractor.py`)
- **Safety Validation**: Verifies `%PDF-` magic header, ensures minimum size (> 128 bytes), and detects/rejects HTML error pages (e.g. 403 Forbidden or login redirects) before feeding bytes to parsers.
- **Extraction Strategy**: Uses `pdfplumber` for layout-aware page extraction, with automatic fallback to `pypdf`.
- **Output**: Returns an `ExtractionResult` containing page-by-page character counts, page numbers, full text, and SHA-256 hash.

### 2.2 Structural Syllabus Parser (`app/processing/parser.py`)
- **Subject Tracking**: Accurately recognizes `Physics`, `Chemistry`, and `Biology` (including `Botany` and `Zoology`).
- **Metadata Extraction**: Discovers test pattern, test title (e.g., `MINOR TEST (DLP)`), and test dates if present.
- **Noise Filtering**: Automatically ignores header/footer boilerplate ("Page X of Y", "Confidential", etc.).
- **Delimited Item Splitting**: Extracts chapter/section names (e.g. `Current Electricity: ...`) and splits candidate topic items by commas, semicolons, and bullets while preserving scientific notation and compound terms.

### 2.3 Topic Normalizer (`app/processing/normalizer.py`)
- **Pure Dynamic Discovery**: Converts topic names into standardized slugs prefixed by subject:
  ```text
  "Electric Power" -> "physics:electric-power"
  "d- and f-Block Elements" -> "chemistry:d-and-f-block-elements"
  "Cell Cycle & Cell Division" -> "biology:cell-cycle-and-cell-division"
  ```
- **Display Name Formatting**: Strips trailing punctuation, cleans outer whitespace, and produces neat title capitalization.
- **Alias Mapping**: Pre-configured dictionary mapping abbreviations or synonyms:
  - `"SHM"` → `"physics:simple-harmonic-motion"`
  - `"EM Waves"` → `"physics:electromagnetic-waves"`
  - `"GOC"` → `"chemistry:general-organic-chemistry"`
- **Deduplication**: `normalize_all()` ensures a single test syllabus does not produce duplicate canonical relationships.

---

## 3. How to Run and Verify Phase 2

In your terminal (with your `all` conda environment activated):

```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
pytest
```

Or test the parser suite specifically:
```bash
pytest tests/test_parser.py -v
```

### Expected Output:
```text
tests/test_parser.py::test_pdf_validation PASSED
tests/test_parser.py::test_pdf_extraction_from_bytes PASSED
tests/test_parser.py::test_syllabus_parser_with_sample_text PASSED
tests/test_parser.py::test_topic_normalizer_slugify_and_clean PASSED
tests/test_parser.py::test_topic_normalizer_dynamic_and_alias PASSED
tests/test_parser.py::test_syllabus_parser_empty_or_malformed PASSED
tests/test_models_and_repos.py::test_test_repo_upsert PASSED
tests/test_models_and_repos.py::test_topic_and_relationship PASSED
tests/test_models_and_repos.py::test_local_storage PASSED

======================== 9 passed in 0.45s ========================
```

---

## Next Step: Phase 3
Once you have run `pytest` and verified the parser and normalizer, we will begin:
**Phase 3: Ingestion Pipeline & Adapter Layer** (orchestrating Discovery → Snapshot → Parsing → Topic Upserting → Artifact Storage, with idempotency and CLI/API triggers).
