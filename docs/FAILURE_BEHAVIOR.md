# Failure Behavior and Recovery (v0.1)

This file defines expected behavior for known failure modes.

## 1. Principles
- Fail closed on privacy boundaries.
- Keep app responsive even when sidecar/dependencies are degraded.
- Prefer degraded functionality over full outage when safe.
- Always surface actionable state to the user.

## 2. Runtime Modes
- `healthy`: observer + db + embedder are ready.
- `degraded_observer`: sidecar up, observer unavailable (often permissions).
- `degraded_embedder`: sidecar up, embedding model unavailable.
- `degraded_reasoner`: sidecar up, query-time reasoning model unavailable.
- `degraded_db`: sidecar up, persistence unavailable.
- `unavailable`: sidecar not reachable.

## 3. Health Contract Extension
`GET /health` should report runtime mode via readiness flags:
- `observer_ready`
- `db_ready`
- `embedder_ready`
- `reasoner_ready` once the second local model is integrated

Mode mapping:
- all true -> `healthy`
- observer false -> `degraded_observer`
- db false -> `degraded_db`
- embedder false -> `degraded_embedder`
- reasoner false -> `degraded_reasoner`
- request fails -> `unavailable`

## 4. Failure Modes

## 4.1 Accessibility Permission Denied
Trigger:
- macOS Accessibility permission is not granted to Remnis.

Expected sidecar behavior:
- Do not attempt privileged capture loops continuously.
- Return `observer_ready=false` on `/health`.
- Return error for observer-dependent ingest paths:
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Accessibility permission is required for observer capture",
    "details": { "permission": "accessibility" }
  }
}
```

Expected desktop behavior:
- Show non-blocking warning state.
- Keep HUD/search available for already indexed data.
- Provide one-click guidance to System Settings path in UI copy.

Recovery condition:
- After permission grant, sidecar re-check updates `/health` to `observer_ready=true`.

## 4.2 Sidecar Start Failure
Trigger:
- Sidecar process cannot be launched by desktop (missing binary/config/runtime error).

Expected desktop behavior:
- Retry sidecar launch up to 3 times with short backoff.
- If still failing, enter `unavailable` state.
- Show explicit startup failure status with retry action.

Expected API behavior:
- No API reachable; desktop treats as transport failure.

Recovery condition:
- User-triggered retry or app restart successfully launches sidecar.

## 4.3 Sidecar Crash During Runtime
Trigger:
- Sidecar exits unexpectedly after startup.

Expected desktop behavior:
- Detect process exit.
- Attempt bounded auto-restart (max 3 retries per 60 seconds).
- During restart window, UI shows temporary degraded banner.
- If retries exhausted, set `unavailable` until manual retry.

Recovery condition:
- Sidecar restarts and `/health` succeeds.

## 4.4 Embedder Initialization Failure
Trigger:
- Model files unavailable/corrupt, out-of-memory, or runtime import failure.

Expected sidecar behavior:
- Keep API running.
- Set `embedder_ready=false` in `/health`.
- `POST /ingest` may store raw event metadata without embedding.
- `GET /search` returns:
  - `DEPENDENCY_NOT_READY` if semantic search is impossible, or
  - degraded keyword/metadata fallback if implemented.

Error example when no fallback:
```json
{
  "error": {
    "code": "DEPENDENCY_NOT_READY",
    "message": "Embedding model is not ready",
    "details": { "dependency": "embedder" }
  }
}
```

Expected desktop behavior:
- Show "indexing degraded" message.
- Keep observer and historical browsing available.

Recovery condition:
- Embedder loads successfully and readiness flips to true.

## 4.5 Query-Time Reasoning Model Failure
Trigger:
- Query-time local model files unavailable/corrupt, out-of-memory, or runtime load failure.

Expected sidecar behavior:
- Keep API running.
- Keep retrieval-only search working if embeddings and DB are healthy.
- Mark the reasoning layer unavailable via readiness/degraded state once that contract is added.
- Skip answer synthesis/reranking instead of failing the whole query.

Expected desktop behavior:
- Show a non-blocking degraded reasoning state.
- Continue showing raw retrieval results and metadata.

Recovery condition:
- Query-time model loads successfully and reasoning path becomes available again.

## 4.6 Database Unavailable
Trigger:
- LanceDB path inaccessible/corrupted/init failure.

Expected sidecar behavior:
- Set `db_ready=false`.
- Reject ingest/search writes requiring DB with `DEPENDENCY_NOT_READY`.
- Continue serving `/health`.

Expected desktop behavior:
- Show "storage unavailable" state and disable write-dependent actions.

Recovery condition:
- DB path/permissions fixed and table initializes.

## 4.7 Invalid Request Payload
Trigger:
- Contract mismatch (missing required fields, invalid types, invalid `k`).

Expected sidecar behavior:
- Return `400` with `INVALID_REQUEST` and field-level details.

Expected desktop behavior:
- Do not crash.
- Log contract error with request ID and endpoint.

## 5. Timeouts and Retry Policy (Initial)
- Health poll timeout: 2 seconds.
- Startup readiness wait window: 20 seconds.
- Sidecar launch retries: 3 attempts.
- Health polling cadence: every 500 ms during startup, every 10 seconds in steady state.

## 6. Logging and Diagnostics
Required log events:
- sidecar launch attempt/result
- sidecar exit code/signal
- health check failure/success transitions
- permission check result
- dependency readiness transitions
- ingest skip reasons (dedupe/debounce)

Log hygiene:
- Do not log sensitive full context text by default in production mode.
- Include event IDs and hashes for traceability.

## 7. UX Copy Guidelines (Initial)
- Permission denied: "Remnis needs Accessibility access to capture active window context."
- Sidecar unavailable: "Remnis background service is unavailable. Retry to restore capture and search."
- Embedder degraded: "Semantic search is temporarily unavailable while model dependencies recover."
- Reasoner degraded: "Enhanced local answers are temporarily unavailable. Remnis will show retrieval-only results."
- DB degraded: "Local storage is unavailable. New context may not be saved until recovery."

## 8. Ownership and Change Rule
Any change to retry policy, failure codes, or degraded mode behavior must update:
- `docs/FAILURE_BEHAVIOR.md`
- `docs/CONTRACTS.md` (if API shape changes)
- `docs/PROJECT_STATUS.md`
