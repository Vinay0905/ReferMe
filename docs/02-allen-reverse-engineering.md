# 02 — ALLEN Reverse Engineering

> This document records observed behavior. It is not a claim that ALLEN publishes these APIs as a stable public contract.

## 1. Test List API

Observed request:

```http
GET https://api.allen-live.in/api/v1/tests/student-tests:byCompletionStatus
    ?status=all
    &mode=all
    &page_number=1
    &page_size=25
```

Observed response shape:

```json
{
  "status": 200,
  "reason": "success",
  "data": {
    "title": "Your tests",
    "cards": [
      {
        "label": "UPCOMING TEST",
        "status": "UPCOMING",
        "title": "MINOR TEST (DLP)",
        "labels": [
          {"text": "13 Sep"},
          {"text": "180 Min"},
          {"text": "Offline"}
        ],
        "link_cta": {
          "label": "View Syllabus",
          "action": {
            "type": "FETCH",
            "data": {
              "uri": "/tests/{test_id}/syllabus",
              "method": "POST",
              "query": {
                "test_id": "{test_id}"
              }
            }
          }
        },
        "test_id": "{test_id}"
      }
    ]
  }
}
```

Observed page size was 25. Pagination beyond page 1 remains an implementation-time verification item.

## 2. Syllabus API

Observed request:

```http
POST https://api.allen-live.in/api/v1/tests/{test_id}/syllabus?test_id={test_id}
```

Observed status: `200 OK`.

The browser then retrieves a signed PDF.

Do not hard-code a particular test ID.

## 3. Syllabus S3

Observed stable bucket/object pattern:

```text
https://ap-south-1-prod-test-and-assessment-syllabus.s3.ap-south-1.amazonaws.com/test_{test_id}/syllabus.pdf
```

The actual browser URL contains temporary AWS SigV4 query parameters.

Important:
- the signed URL is temporary;
- observed expiration was 900 seconds;
- query parameters must not be stored as the permanent artifact identity.

The application should retain a stable object reference such as:

```text
bucket = ap-south-1-prod-test-and-assessment-syllabus
key = test_{test_id}/syllabus.pdf
```

only if that object identity is verified for the relevant test.

## 4. Result Insights API

Observed request:

```http
GET https://api.allen-live.in/api/v1/tests/{test_id}/result-insights?attempt=0
```

Observed response status: `200`.

The response for a missed test included:

```json
"missed_test_info": {
  "secondary_cta": {
    "label": "Answer key",
    "action": {
      "type": "SHOW_MODAL",
      "data": {
        "ctas": [
          {
            "label": "English",
            "action": {
              "type": "OPEN_PDF",
              "data": {
                "uri": "https://.../test_{test_id}/Solution.pdf?...signed..."
              }
            }
          },
          {
            "label": "Hindi",
            "action": {
              "type": "OPEN_PDF",
              "data": {
                "uri": "https://.../test_{test_id}/Solution_Hindi.pdf?...signed..."
              }
            }
          }
        ]
      }
    }
  }
}
```

The English PDF was observed to contain the question paper. For this project it is logically stored as `question_paper`.

## 5. Question-Paper S3

Observed bucket:

```text
ap-south-1-prod-test-and-assessment-question-papers
```

Observed stable object pattern:

```text
test_{test_id}/Solution.pdf
```

Hindi variant:

```text
test_{test_id}/Solution_Hindi.pdf
```

These are examples of observed behavior, not guarantees for every test.

## 6. Authentication

Observed browser requests included:
- `Authorization: Bearer <redacted>`
- origin/referer context;
- client/device headers;
- selected batch/course context.

Never copy live credentials into source code.

The exact minimum header set required for a standalone ingestion client must be verified during implementation.

## 7. PDF Viewer

ALLEN's `pdf_viewer.html` is presentation infrastructure. It is not the artifact source.

Do not scrape the PDF viewer HTML when the PDF itself is accessible.

## 8. Next.js RSC

A request resembling:

```text
/taj-ui/str?attempt=0&test_id={test_id}&_rsc=...
```

was observed. This is frontend/Next.js RSC plumbing, not the primary data API for our ingestion.

Do not build ingestion around RSC unless required as a fallback.

## 9. Syllabus Format

Observed syllabus:
- titled around topic-wise test syllabus and schedule;
- includes target/exam context;
- includes date/test name/test pattern;
- organizes content under Physics, Chemistry, Biology;
- body text is selectable/searchable in the PDF;
- some headings may not be represented as searchable text.

Do not assume headings being unsearchable means the whole PDF requires OCR.

## 10. Evidence Classification

### Confirmed
The observations above were directly captured from browser network behavior.

### Inferred
Stable S3 key patterns and the idea of persisting object identity rather than signed URLs.

### Unknown
Complete behavior for every test type, every historical test, every pagination page, and every authentication context.

## 11. Credentials Incident Rule

A live Bearer token/signed URL was previously exposed during investigation. It must never be copied into this repository. If still active, the session should be refreshed/revoked as appropriate.
