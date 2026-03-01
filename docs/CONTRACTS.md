# Contracts (v0.1)

This file freezes integration contracts across observer, sidecar API, and desktop HUD.

## 1. Conventions
- Timestamp format: UTC ISO-8601, example `2026-02-28T22:15:10Z`
- IDs: UUID v4 strings
- Hashing: SHA-256 hex string
- API base URL (local only): `http://127.0.0.1:8765`
- Content type: `application/json`

## 2. Canonical Event Schema

### 2.1 `ObservedContextEvent`
```json
{
  "id": "2fd4c6c7-fbe4-4a44-b1e6-69b8c2ad9f0b",
  "timestamp_utc": "2026-02-28T22:15:10Z",
  "app_name": "Cursor",
  "window_title": "observer.py - remnis-app",
  "file_path": "/Users/devaanshsinha/dev/remnis-app/sidecar/observer.py",
  "context_text": "Editing observer debounce logic",
  "source": "observer.active_window",
  "capture_confidence": 0.98,
  "context_hash": "f7f6d5e6d4a...",
  "source_version": "event.v1"
}
```

### 2.2 Field Rules
- `id`: required, UUID v4.
- `timestamp_utc`: required, UTC ISO-8601.
- `app_name`: required, non-empty.
- `window_title`: required, can be short but not null.
- `file_path`: optional, nullable string.
- `context_text`: required; fallback to `"<app_name> | <window_title>"` when richer text is unavailable.
- `source`: required enum for capture origin.
  - Allowed initial values: `observer.active_window`, `observer.accessibility_text`.
- `capture_confidence`: optional float `0.0..1.0`.
- `context_hash`: required SHA-256 of normalized payload.
- `source_version`: required; fixed `event.v1` for initial implementation.

### 2.3 Normalization Rules (for `context_hash`)
Normalize this payload before hashing:
```json
{
  "app_name": "<trimmed-lowercase>",
  "window_title": "<trimmed-single-spaced>",
  "file_path": "<trimmed-or-empty>",
  "context_text": "<trimmed-single-spaced>"
}
```
- Lowercase only `app_name`.
- Collapse repeated spaces in text fields.
- Trim leading/trailing whitespace.
- Convert missing optional fields to empty string during hash input.

## 3. API Contracts

## 3.1 `GET /health`
Purpose: readiness and dependency visibility.

### Response 200
```json
{
  "status": "ok",
  "service": "remnis-sidecar",
  "version": "0.1.0",
  "time_utc": "2026-02-28T22:20:10Z",
  "readiness": {
    "observer_ready": true,
    "db_ready": true,
    "embedder_ready": false
  }
}
```

## 3.2 `POST /ingest`
Purpose: ingest one normalized event; dedupe/debounce decision done server-side.

### Request Body
```json
{
  "event": {
    "id": "2fd4c6c7-fbe4-4a44-b1e6-69b8c2ad9f0b",
    "timestamp_utc": "2026-02-28T22:15:10Z",
    "app_name": "Cursor",
    "window_title": "observer.py - remnis-app",
    "file_path": "/Users/devaanshsinha/dev/remnis-app/sidecar/observer.py",
    "context_text": "Editing observer debounce logic",
    "source": "observer.active_window",
    "capture_confidence": 0.98,
    "context_hash": "f7f6d5e6d4a...",
    "source_version": "event.v1"
  }
}
```

### Response 200 (stored)
```json
{
  "status": "stored",
  "event_id": "2fd4c6c7-fbe4-4a44-b1e6-69b8c2ad9f0b",
  "dedupe": {
    "is_duplicate": false,
    "reason": null
  },
  "debounce": {
    "is_debounced": false,
    "reason": null
  }
}
```

### Response 200 (skipped)
```json
{
  "status": "skipped",
  "event_id": "2fd4c6c7-fbe4-4a44-b1e6-69b8c2ad9f0b",
  "dedupe": {
    "is_duplicate": true,
    "reason": "same_context_hash"
  },
  "debounce": {
    "is_debounced": true,
    "reason": "below_stability_window"
  }
}
```

## 3.3 `GET /search`
Purpose: semantic retrieval.

### Query Params
- `q` (required): query string
- `k` (optional): integer `1..50`, default `10`
- `offset` (optional): integer `>=0`, default `0`

### Response 200
```json
{
  "query": "docker build error from yesterday",
  "k": 10,
  "offset": 0,
  "total_estimate": 34,
  "results": [
    {
      "id": "31f87340-12a9-49f7-a7c0-e4fd6fcb0866",
      "timestamp_utc": "2026-02-27T19:30:00Z",
      "app_name": "Terminal",
      "window_title": "docker compose build",
      "context_text": "failed to solve: process '/bin/sh -c npm ci'",
      "score": 0.86,
      "context_hash": "0f6c5...",
      "source_version": "event.v1"
    }
  ]
}
```

## 3.4 Error Shape (all endpoints)
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "k must be between 1 and 50",
    "details": {
      "field": "k"
    }
  }
}
```

Initial error codes:
- `INVALID_REQUEST`
- `DEPENDENCY_NOT_READY`
- `PERMISSION_DENIED`
- `INTERNAL_ERROR`

## 4. Desktop-to-Sidecar Contract
- Desktop assumes sidecar reachable at loopback host and configured port.
- Startup sequence:
  - Start sidecar process.
  - Poll `GET /health` until ready or timeout.
  - Surface user-visible state if timeout occurs.
- Desktop must handle `DEPENDENCY_NOT_READY` gracefully and keep UI responsive.

## 5. Search Result Contract for HUD
Each result row requires:
- `id`
- `app_name`
- `context_text`
- `timestamp_utc`
- `score`

Derived in UI:
- Relative time string from `timestamp_utc`.
- Optional icon key from `app_name`.

## 6. Contract Versioning Rule
- Contract version marker for this stage: `v0.1`.
- Any breaking shape change requires:
  - update to this file,
  - bump version marker,
  - note in `docs/PROJECT_STATUS.md`.


## 7. Failure Mode References
Failure semantics and retry policy are defined in `docs/FAILURE_BEHAVIOR.md`.
Any API-level change there must remain compatible with the error shape in section 3.4.
