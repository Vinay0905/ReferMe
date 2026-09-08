# 01 — Project Requirements

## 1. Problem

The user studies from ALLEN NEET test papers. ALLEN organizes tests around changing syllabi, while the desired application needs the inverse relationship:

- ALLEN gives: **test → syllabus/topics**
- Our application provides: **topic → tests** and **test → topics**

The application should make historical/practice-test discovery substantially faster.

## 2. Primary Product

A searchable catalogue of ALLEN NEET tests and their syllabus-derived topics.

## 3. Functional Requirements

### FR-01 Test catalogue
Store and display available tests.

### FR-02 Test metadata
At minimum retain:
- external test ID;
- test name;
- date if available;
- status if available;
- duration if available;
- mode if available.

### FR-03 Syllabus snapshot
Every test must have its own syllabus artifact/reference.

### FR-04 Topic extraction
Extract subject/topic information from the syllabus.

### FR-05 Canonical topic mapping
Allow multiple syllabus wordings to map to one canonical topic where justified.

### FR-06 Topic → tests
Return all tests linked to a selected canonical topic.

### FR-07 Test → topics
Return all topics linked to a test.

### FR-08 Artifact access
Allow the user to open/download/view the syllabus and question paper.

### FR-09 Incremental ingestion
New tests and changed artifacts should be ingestible without rebuilding everything.

### FR-10 Idempotency
Running the same ingestion job repeatedly must not create duplicate tests/topics/relationships.

## 4. Non-functional Requirements

### Speed
User queries should normally hit MongoDB indexes and return quickly.

### Reliability
A failed PDF download must not corrupt the test record.

### Traceability
Every normalized topic should be traceable back to source syllabus text.

### Maintainability
ALLEN-specific logic should be replaceable.

### Security
No credentials or signed URLs in source control/logs.

## 5. Product Boundaries

The application is a study-navigation tool.

It does not:
- replace ALLEN;
- generate official results;
- submit tests;
- solve questions;
- provide copyrighted content beyond the artifacts the deployment is authorized to store/serve.

## 6. Content/Compliance Boundary

Before public deployment, verify that the intended retrieval, storage, and redistribution of ALLEN PDFs is permitted by the relevant terms/licensing/access rights. Technical accessibility is not itself permission to redistribute content.
