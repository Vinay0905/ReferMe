# 06 — PDF and Topic Processing

## 1. Principle

The syllabus PDF is the source of truth for topic coverage.

Do not derive topic coverage by guessing from test names.

## 2. Extraction Strategy

Try in this order:

1. native PDF text extraction;
2. layout-aware extraction if needed;
3. targeted OCR only for pages/regions that genuinely lack text;
4. manual review/failure state for unresolved cases.

Do not OCR every PDF by default.

## 3. Why Searchability Is Not Enough

A PDF can have:
- selectable body text;
- vector/image headings;
- fragmented text blocks;
- reading-order problems.

Therefore parser quality must be evaluated on extracted layout/content, not only browser Ctrl+F behavior.

## 4. Structural Parsing

The observed format contains:
- exam/test metadata;
- Physics;
- Chemistry;
- Biology;
- topic/body text.

The parser should identify subject regions and topic lines.

Do not hard-code coordinates unless the format genuinely requires them.

## 5. Preserve Raw Evidence

For each parsed syllabus retain enough information to debug:
- extracted text;
- page number;
- subject;
- source line/block;
- parser version.

Full raw PDF storage is handled by the artifact layer.

## 6. Topic Normalization

Normalization should initially be deterministic.

Examples of safe operations:
- trim whitespace;
- normalize repeated spaces;
- normalize punctuation;
- normalize obvious casing;
- preserve meaningful scientific notation;
- normalize known formatting variants.

Avoid aggressive stemming or synonym merging without evidence.

## 7. Canonicalization

A canonical topic should represent a meaningful NEET study concept.

Example:

```text
Original: "Power"
Canonical: "Electric Power"
```

should NOT be automatically done unless context/section/rules justify it.

The subject is part of the disambiguation context.

## 8. Hierarchy

If a syllabus gives:

```text
Physics
  Electrostatics
    Electric Potential
```

preserve the hierarchy where detectable.

Suggested logical fields:
- subject;
- chapter/unit;
- topic;
- subtopic.

Do not invent hierarchy when the source does not provide it.

## 9. Subject Handling

Treat subjects as controlled values:

```text
Physics
Chemistry
Biology
```

Normalize case/whitespace.

## 10. Duplicate Topics Within a Test

If the same canonical topic appears multiple times:
- retain source occurrences if useful;
- create one active test↔topic relationship unless the product needs occurrence-level detail.

## 11. Parser Versioning

Store:
- parser version;
- normalization version.

When rules change, old syllabi can be reprocessed reproducibly.

## 12. OCR Policy

OCR is a fallback, not the first tool.

Trigger OCR only if:
- required content is absent from native extraction;
- layout inspection indicates image/scanned content;
- parser cannot produce a valid subject/topic structure.

## 13. Validation

A parsed syllabus should pass sanity checks:
- at least one recognized subject;
- nonempty content;
- expected metadata where available;
- plausible topic count;
- no obvious page garbage dominating the output.

If validation fails, mark the test for review/reprocessing rather than silently producing bad relationships.

## 14. Test Fixtures

Keep representative PDFs/text fixtures in a test-safe location with appropriate rights.

Tests should cover:
- normal syllabus;
- heading-not-searchable case;
- spacing variants;
- multiple topics;
- empty/malformed extraction;
- future format variant.
