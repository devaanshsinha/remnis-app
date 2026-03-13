# Next Actions (What, Why, Output)

## Status Update
- Step 1 (Freeze Contracts): completed.
- Step 2 (Acceptance Criteria): completed.
- Step 3 (Permission and Failure Behavior): completed.
- Step 4 (Scaffold + `/health`): completed.
- Step 5 (Observer v1): completed with diagnostics and local JSONL persistence.
- Step 6 (Storage + Search): completed at prototype level with browser ingest + `/events` retrieval + semantic `/search` plus keyword fallback.
- Local model 1 (embedding/indexing) is now active on machines with dependencies installed.
- The two-local-model architecture is still incomplete because the query-time reasoning model is not integrated yet.

## 6. Improve MVP Retrieval and Data Quality
What to do:
- Deterministic filters to `/search` (time range, app/source filters): completed.
- Add browser ingest dedupe improvements for repeated rapid tab emissions: completed.
- Wire desktop UI to `/events` and `/search` instead of health-only rendering: completed.
- Verify semantic retrieval quality with real developer-memory queries: next.
- Define the split between append-only raw events and derived retrieval/index documents: completed in `docs/RAW_RETRIEVAL_MODEL.md`.
- Implement the first explicit retrieval-document builder over current sources: completed.
- Add compaction/grouping heuristics so retrieval documents stop mirroring raw events 1:1: next.
- Surface drill-down from search results back to supporting raw history: next.

Why:
- This turns the current prototype into a better local memory layer instead of a thin event viewer.

What it produces:
- Usable local recall with better quality and a clearer architecture for richer future sources.

## 7. Add Semantic Search
What to do:
- Integrate the local background embedding model (`all-MiniLM-L6-v2`): completed for local runtime with startup/backfill wiring.
- Introduce LanceDB for vector storage/query: completed for local runtime with index/status visibility and self-repair for older bad-schema tables.
- Replace keyword ranking in `/search` with semantic ranking: completed as semantic-first retrieval with keyword fallback when dependencies are unavailable.
- Index/status visibility for runtime verification: completed.

Why:
- Keyword fallback is useful but limited for intent-level recall.

What it produces:
- True semantic retrieval aligned with Remnis core value.

## 8. Add Two-Tier Query Pipeline
What to do:
- Keep fast path for immediate results from lightweight retrieval.
- Add the heavier local query-time reasoning model for rerank/summarize with strict timeout and cancel behavior.
- Design this reasoning layer around developer questions over rich prior context, not just reworded search results.

Why:
- Delivers better answers without increasing background resource usage.

What it produces:
- Fast initial response plus enhanced answer quality from a second local model.

## 9. Connect HUD and Hotkey
What to do:
- Implement spotlight-style HUD query flow and keyboard interactions.
- Register global hotkey in Tauri.
- Make the HUD able to present both raw recall results and later synthesized answers.

Why:
- Product value appears when recall is instant and low-friction.

What it produces:
- Usable desktop experience with real retrieval loop.

## End-State Reminder
- Remnis is not considered complete until both local model tiers are implemented and documented:
  - embedding/indexing model
  - query-time reasoning model
