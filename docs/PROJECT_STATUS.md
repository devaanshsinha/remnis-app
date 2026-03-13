# Project Status

## Snapshot
- Date: 2026-03-13
- Repo state: runnable local observer + ingest + raw-event persistence + semantic search prototype, with local embedder/vector store verified on this machine

## Completed So Far
- Established repository structure (`apps/desktop`, `sidecar`, `docs`).
- Finalized foundational docs and contracts.
- Implemented sidecar runtime:
  - `GET /health`
  - `POST /ingest` with schema/hash validation and dedupe/debounce
  - observer v1 active-window polling loop
  - `GET /observer/stats` degraded-state diagnostics
  - `GET /index/status` embedder/vector-store readiness and indexed-count visibility
  - JSONL persistence (`sidecar/data/events.jsonl`)
  - `GET /events` filterable retrieval over persisted events
  - `GET /search` with vector-first retrieval, search-mode visibility, and keyword fallback
  - browser repeat-window suppression for rapid duplicate extension emissions
  - startup-time embedder and LanceDB vector-store initialization
  - startup backfill from JSONL into the vector index
  - vector index self-repair for older empty wrong-dimension tables and manifest rebuild for indexed-count recovery
- Implemented desktop runtime baseline and UI foundation.

## Current Intent
- Build a rich local developer-memory layer: preserve useful raw context, derive cleaner retrieval documents for search, and progress toward developer question answering over prior work.

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
- Define the raw-event to retrieval-document compaction model.
- Define clipboard + notification event schema extensions.
- Define editor/workspace and agent/chat schema extensions.
- Choose and integrate the local query-time reasoning model.
- Improve semantic retrieval quality and ranking over richer context.
- Integrate search results into the final Spotlight-style HUD.

## Risks to Manage Early
- macOS permission complexity (Accessibility/AX behavior).
- Performance overhead from observer loops.
- Packaging complexity for sidecar distribution.

## Next Gate
- Validate semantic retrieval quality on real developer-memory queries, then implement the separate local query-time reasoning pass.
