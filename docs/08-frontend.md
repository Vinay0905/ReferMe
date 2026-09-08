# 08 — Frontend

## 1. Direction

Preferred:
- Next.js;
- TypeScript;
- responsive UI.

The exact visual design is not yet locked.

## 2. Primary Screens

### Home / Search

Two obvious entry paths:

- Browse/Search by Topic
- Browse/Search by Test

### Topic Detail

Display:
- canonical topic name;
- subject;
- matching tests;
- test date/name/mode;
- links to test detail.

### Test Detail

Display:
- test name;
- date;
- duration;
- mode/status;
- topics grouped by subject;
- syllabus button;
- question paper button.

## 3. UX Principle

The app is a navigation/search tool.

Keep interaction fast:
- search should query our API;
- no waiting for PDF parsing;
- no waiting for ALLEN.

## 4. Loading/Error States

Every data-fetching screen must handle:
- loading;
- empty;
- error;
- partial artifact availability.

Example:
A test may have topics and syllabus but no question paper yet.

Do not hide this state.

## 5. PDF Viewing

Use browser/native PDF viewing or an appropriate viewer.

Artifact URLs should be produced by the backend/storage layer.

The frontend should not know:
- S3 signing logic;
- ALLEN bucket names;
- ALLEN bearer tokens.

## 6. Accessibility

Provide:
- keyboard navigation;
- clear button labels;
- semantic headings;
- usable contrast;
- mobile-friendly layouts.

## 7. Frontend State

Avoid unnecessary global state.

Server state can be fetched through a small data-access layer.

Do not reproduce backend business logic in the frontend.
