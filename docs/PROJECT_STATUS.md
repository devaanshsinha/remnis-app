# Project Status

## Snapshot
- Date: 2026-03-10
- Repo state: runnable local observer + ingest + persistence + keyword search baseline, with embedder/vector-store startup scaffolding added

## Completed So Far
- Established repository structure (`apps/desktop`, `sidecar`, `docs`).
- Finalized foundational docs and contracts.
- Implemented sidecar runtime:
  - `GET /health`
  - `POST /ingest` with schema/hash validation and dedupe/debounce
  - observer v1 active-window polling loop
  - `GET /observer/stats` degraded-state diagnostics
  - JSONL persistence (`sidecar/data/events.jsonl`)
  - `GET /events` filterable retrieval over persisted events
  - `GET /search` with vector-first retrieval and keyword fallback
  - browser repeat-window suppression for rapid duplicate extension emissions
  - startup-time embedder and LanceDB vector-store initialization scaffolding
- Implemented desktop runtime baseline and UI foundation.

## Current Intent
- Build robustness through capture-source expansion while progressing semantic retrieval.

## Strategic Decisions (Locked)
- Capture quality is the primary product risk and priority.
- Browser adapter is the next high-value source integration.
- Runtime architecture will use two tiers:
  - lightweight always-on background processing
  - heavier query-time processing only on user invoke
- Finished product requires two separate local model roles:
  - local embedding/indexing model
  - local query-time reasoning model

## Open Items
- Define clipboard + notification event schema extensions.
- Replace keyword `/search` scoring with local embedding + LanceDB retrieval.
- Choose and integrate the local query-time reasoning model.
- Add structured persistence/index schema for vector workflow.
- Integrate search results into the final Spotlight-style HUD.

## Risks to Manage Early
- macOS permission complexity (Accessibility/AX behavior).
- Performance overhead from observer loops.
- Packaging complexity for sidecar distribution.

## Next Gate
- Semantic `/search` returning embedding-ranked results from LanceDB, followed by a separate local query-time reasoning pass.
