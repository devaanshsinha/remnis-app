# Next Actions (What, Why, Output)

## Status Update
- Step 1 (Freeze Contracts): completed in `docs/CONTRACTS.md`.
- Step 2 (Acceptance Criteria): completed in `docs/ACCEPTANCE_CRITERIA.md`.
- Step 3 (Permission and Failure Behavior): completed in `docs/FAILURE_BEHAVIOR.md`.
- Step 4 (Minimal Scaffolding + `/health`): completed with running desktop/sidecar health checks.

## 5. Build Observer v1 (No Embeddings Yet)
What to do:
- Capture active app/window title.
- Normalize events and compute `context_hash` per contract.
- Apply smart debounce and dedupe decisions.

Why:
- Data quality is the foundation of search quality.

What it produces:
- Reliable low-noise event stream and validated ingest behavior.

## 6. Add Storage and Semantic Search
What to do:
- Persist events.
- Add embedding generation and LanceDB-backed retrieval.
- Expose `/search` endpoint with contract-compliant response.

Why:
- Converts captured context into useful retrieval behavior.

What it produces:
- First product loop: capture -> index -> search -> display.

## 7. Connect HUD and Hotkey
What to do:
- Implement spotlight-style HUD and keyboard flows.
- Register and test global hotkey path in Tauri.

Why:
- User value is realized when recall is fast and frictionless.

What it produces:
- Usable desktop experience and demonstrable MVP.

