# 13 — Known Unknowns

This file is deliberately explicit. Unknowns are not permission to invent behavior.

## U-01 Pagination

Need to verify:
- exact termination semantics;
- total count availability;
- maximum page size;
- duplicate behavior across pages.

## U-02 Authentication for Automation

Need to determine the minimum stable credential/session mechanism for an authorized ingestion process.

Do not copy a browser session blindly into production.

## U-03 Complete ALLEN Test Coverage

Need to verify whether every relevant test type appears through the same test-list API.

## U-04 Syllabus Variants

Current evidence suggests a standardized syllabus format, but different years/test types may vary.

Parser must detect format failures.

## U-05 Heading Representation

Some syllabus headings may not be searchable as ordinary PDF text.

Need to inspect extraction/layout before deciding whether OCR is necessary.

## U-06 Question Paper Availability

Need to verify which test statuses/types expose the question-paper artifact and through which route.

## U-07 Artifact Storage

Final choice between:
- MongoDB GridFS;
- object storage;
- another authorized storage solution.

Decision must consider:
- PDF volume;
- free-tier limits;
- backup needs;
- egress;
- privacy/access control.

## U-08 Content Rights

Technical access does not establish redistribution rights. Verify authorization/terms before public hosting.

## U-09 Topic Taxonomy

Need to define how granular canonical topics should be.

Start from source syllabus wording and only normalize where deterministic evidence supports it.

## U-10 Historical Retention

Need a product decision on whether changed syllabi should retain all historical snapshots or only the current one.

Recommended default: retain immutable snapshots if storage allows.

## U-11 Frontend Visual Design

Technology direction is preferred, but exact UI/branding/layout remains open.

## U-12 User Authentication

Not required for core V1 unless deployment requirements demand it.

## U-13 Deployment

Final hosting choices are open.

## Verification Rule

When an implementation encounters an unknown:
1. check this file;
2. check reverse-engineering evidence;
3. verify with a safe experiment;
4. update the documentation;
5. only then encode the behavior.
