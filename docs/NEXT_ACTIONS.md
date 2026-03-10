# Next Actions (What, Why, Output)

## Status Update
- Step 1 (Freeze Contracts): completed.
- Step 2 (Acceptance Criteria): completed.
- Step 3 (Permission and Failure Behavior): completed.
- Step 4 (Scaffold + `/health`): completed.
- Step 5 (Observer v1): completed with diagnostics and local JSONL persistence.
- Step 6 (Storage + Search): in progress with browser ingest + `/events` retrieval + keyword `/search` baseline.
- The two-local-model architecture is a required end-state, but neither model tier is integrated yet.

## 6. Improve MVP Retrieval and Data Quality
What to do:
- Deterministic filters to `/search` (time range, app/source filters): completed.
- Add browser ingest dedupe improvements for repeated rapid tab emissions: completed.
- Wire desktop UI to `/events` and `/search` instead of health-only rendering: completed.

Why:
- This completes the first end-to-end user loop before heavier model/vector work.

What it produces:
- Usable MVP query flow with better quality and lower noise.

## 7. Add Semantic Search
What to do:
- Integrate the local background embedding model (`all-MiniLM-L6-v2`).
- Introduce LanceDB for vector storage/query.
- Replace keyword ranking in `/search` with semantic ranking.

Why:
- Keyword fallback is useful but limited for intent-level recall.

What it produces:
- True semantic retrieval aligned with Remnis core value.

## 8. Add Two-Tier Query Pipeline
What to do:
- Keep fast path for immediate results from lightweight retrieval.
- Add the heavier local query-time reasoning model for rerank/summarize with strict timeout and cancel behavior.

Why:
- Delivers better answers without increasing background resource usage.

What it produces:
- Fast initial response plus enhanced answer quality from a second local model.

## 9. Connect HUD and Hotkey
What to do:
- Implement spotlight-style HUD query flow and keyboard interactions.
- Register global hotkey in Tauri.

Why:
- Product value appears when recall is instant and low-friction.

What it produces:
- Usable desktop experience with real retrieval loop.

## End-State Reminder
- Remnis is not considered complete until both local model tiers are implemented and documented:
  - embedding/indexing model
  - query-time reasoning model
