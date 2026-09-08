# 12 — Future AI and Scaling

## 1. AI Extension

AI can be introduced when deterministic rules show a real limitation.

Good future use cases:
- canonical topic mapping;
- synonym detection;
- ambiguous syllabus interpretation;
- topic hierarchy inference with confidence.

Bad first use:
- sending every user query to an LLM;
- replacing indexed lookup;
- creating RAG solely because PDFs exist.

## 2. AI Guardrails

Any AI-generated mapping should retain:
- original text;
- proposed canonical topic;
- model/version;
- confidence;
- timestamp;
- approval/status.

The system must remain usable if the AI provider is unavailable.

## 3. RAG

RAG becomes relevant only if the product later asks questions such as:
- "Find the exact question where this concept was tested."
- "Explain all questions involving this topic."
- "Compare how a topic appears across tests."

That is a different feature from the current topic↔test index.

## 4. Scaling

If the dataset grows:
- keep MongoDB indexes optimized;
- move PDFs to object storage;
- add background workers;
- introduce a queue only when workload requires it;
- add caching for hot reads;
- separate ingestion from API serving if necessary.

## 5. Service Extraction

Potential future split:

```text
API service
Ingestion worker
Processing worker
Artifact service
```

Do not do this in V1 without measured need.

## 6. Search Evolution

Possible progression:

```text
V1: exact/canonical MongoDB lookup
V2: aliases + controlled text search
V3: semantic/AI-assisted normalization
V4: vector search for question-level discovery
```

Do not jump directly to V4.
