# Next Actions (What, Why, Output)

## Status Update
- Step 1 (Freeze Contracts): completed.
- Step 2 (Acceptance Criteria): completed.
- Step 3 (Permission and Failure Behavior): completed.
- Step 4 (Scaffold + `/health`): completed.
- Step 5 (Observer v1): completed with diagnostics and local JSONL persistence.
- Step 6 (Storage + Search): started with keyword `/search` baseline.

## 6. Add Semantic Search
What to do:
- Integrate embedding generation.
- Introduce LanceDB for vector storage/query.
- Replace keyword ranking in `/search` with semantic ranking.

Why:
- Keyword fallback is useful but limited for intent-level recall.

What it produces:
- True semantic retrieval aligned with Remnis core value.

## 7. Connect HUD and Hotkey
What to do:
- Implement spotlight-style HUD query flow and keyboard interactions.
- Register global hotkey in Tauri.

Why:
- Product value appears when recall is instant and low-friction.

What it produces:
- Usable desktop experience with real retrieval loop.

