# Acceptance Criteria

This file defines objective pass/fail gates for implementation phases.

## Phase 1: Skeleton and Health Handshake
1. Desktop app launches locally without runtime crash.
2. Sidecar process starts from desktop startup path.
3. `GET /health` returns `200` with `status` and `readiness` fields.
4. Desktop can read and render sidecar readiness state.
5. Desktop shutdown cleanly terminates sidecar process.

## Phase 2: Observer v1 (No Embeddings)
1. Observer emits app/window events at runtime.
2. Smart debounce enforces the >15s stability rule or significant-change bypass.
3. Deduplication skips repeated `context_hash` entries.
4. Ingest API returns `stored` and `skipped` statuses correctly.
5. Event timestamps are UTC ISO-8601 and validated.

## Phase 3: Storage and Semantic Search
1. LanceDB table initializes on first run and reopens on restart.
2. Event metadata persists and is queryable after app restart.
3. Embeddings are generated for stored events when embedder is ready.
4. `GET /search` returns ranked results with `score`.
5. Query latency is acceptable for interactive typing on local machine.

## Phase 4: HUD Retrieval UX
1. Global hotkey opens and closes HUD reliably.
2. Query input triggers throttled search calls.
3. Results list shows app name, snippet, and relative time.
4. Keyboard navigation supports up/down/select/escape.
5. Empty/error states are visible and non-blocking.

## Phase 5: Packaging Baseline
1. Sidecar runs without requiring system Python installation.
2. Packaged app launches on a clean macOS environment.
3. Loopback-only sidecar API policy is preserved after packaging.
4. Permission prompts and denied-state UX are functional.
5. DMG installation path produces a runnable `.app`.

## Exit Rule
A phase is complete only when every criterion in that phase is demonstrably satisfied.

