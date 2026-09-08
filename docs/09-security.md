# 09 — Security

## 1. Threat Model

Important risks:
- credential leakage;
- unauthorized ALLEN access;
- leaked signed URLs;
- PDF redistribution beyond authorization;
- accidental logging of private data;
- malicious user input;
- abuse of public search endpoints.

## 2. ALLEN Credentials

Credentials must be:
- environment/secret-manager based;
- absent from git;
- absent from frontend bundles;
- absent from logs;
- redacted in error messages.

If the integration requires session-derived headers, encapsulate them in the ALLEN client.

## 3. Signed URLs

Signed S3 URLs:
- are temporary;
- contain security-sensitive query parameters;
- should not be persisted as permanent records;
- should not appear in logs.

If proxying through our backend, ensure authorization rules are explicit.

## 4. Artifact Access

Decide whether artifacts are:
- public to application users;
- authenticated;
- owner-restricted.

Do not accidentally expose private ALLEN content through an unprotected object-storage bucket.

## 5. MongoDB

Use:
- least-privilege database credentials;
- network restrictions where supported;
- separate dev/prod credentials;
- indexes and bounded queries.

Never use unrestricted admin credentials in the application.

## 6. Input Validation

Validate:
- IDs;
- pagination;
- search strings;
- enum values.

Never interpolate user input into MongoDB operators without validation.

## 7. Logging

Safe to log:
- request ID;
- endpoint;
- status;
- latency;
- external test ID;
- job ID.

Do not log:
- Authorization headers;
- cookies;
- signed URLs;
- secret environment values.

## 8. Dependency Security

Pin/lock dependencies and update regularly.

## 9. Public Deployment

Before public deployment:
- review content rights;
- configure HTTPS;
- configure CORS narrowly;
- add application rate limits if needed;
- disable verbose debug errors;
- protect ingestion/admin endpoints.
