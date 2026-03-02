# Project Status

## Snapshot
- Date: 2026-03-01
- Repo state: runnable local observer + ingest + persistence + keyword search baseline

## Completed So Far
- Established repository structure (`apps/desktop`, `sidecar`, `docs`).
- Finalized foundational docs and contracts.
- Implemented sidecar runtime:
  - `GET /health`
  - `POST /ingest` with schema/hash validation and dedupe/debounce
  - observer v1 active-window polling loop
  - `GET /observer/stats` degraded-state diagnostics
  - JSONL persistence (`sidecar/data/events.jsonl`)
  - `GET /search` keyword fallback over persisted events
- Implemented desktop runtime baseline and UI foundation.

## Current Intent
- Build robustness through capture-source expansion while progressing semantic retrieval.

## Strategic Decisions (Locked)
- Capture quality is the primary product risk and priority.
- Browser adapter is the next high-value source integration.
- Runtime architecture will use two tiers:
  - lightweight always-on background processing
  - heavier query-time processing only on user invoke

## Open Items
- Implement browser adapter ingest path (URL/title/snippet).
- Define clipboard + notification event schema extensions.
- Replace keyword `/search` scoring with embedding + LanceDB retrieval.
- Add structured persistence/index schema for vector workflow.
- Integrate search results into the final Spotlight-style HUD.

## Risks to Manage Early
- macOS permission complexity (Accessibility/AX behavior).
- Performance overhead from observer loops.
- Packaging complexity for sidecar distribution.

## Next Gate
- Semantic `/search` returning embedding-ranked results from LanceDB.
