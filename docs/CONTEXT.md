# Remnis Context Guide

## What This Project Is
Remnis is a local macOS memory engine for developers. It observes work context (initially app/window state), stores it as structured events, and makes it searchable using semantic embeddings.

## Why This Exists
Developer work context is fragmented across terminals, editors, browsers, and docs. Keyword search is often poor for memory recall. Remnis aims to let users search by intent, not exact text.

## High-Level System
There are three major parts:
- Desktop shell (Tauri + React): UI, hotkey, menu bar, and local orchestration.
- Sidecar service (Python FastAPI): observer, ingest pipeline, embedding, and search endpoints.
- Local vector storage (LanceDB): vector + metadata persistence for semantic retrieval.

## Mental Model
Think of Remnis as a pipeline:
1. Observe context changes.
2. Normalize event data.
3. Debounce and deduplicate.
4. Embed text into vectors.
5. Persist vectors + metadata.
6. Query semantically and render results quickly.

## Strategy Clarification
- The hardest part of this product is reliable, high-signal capture across sources.
- Embeddings and heavier models improve retrieval quality, but they cannot compensate for poor capture.
- Product strategy is now explicitly:
  - capture-first architecture
  - lightweight background processing
  - heavier query-time reasoning when the user explicitly invokes Remnis

## Data Flow (Initial)
1. Observer identifies active app/window.
2. Event is normalized to canonical schema.
3. Hash computed from normalized context.
4. If debounce/dedupe passes, event is stored and embedded.
5. Search endpoint returns ranked matches for query.
6. HUD displays results with app identity, snippet, relative time.

## Core Terms
- Observer: module that reads current macOS context.
- Debounce: delay/filter that prevents noisy event writes.
- Deduplication: hash-based skip logic for repeated context.
- Embedding: numeric vector representing semantic meaning of text.
- Vector search: nearest-neighbor retrieval by embedding similarity.
- Sidecar: local background service launched and supervised by desktop app.

## Constraints You Must Respect
- Local-only by default.
- Explicit OS permission handling.
- Low overhead on CPU/memory.
- Graceful failure modes when dependencies are unavailable.

## What "Good" Looks Like Early
- App and sidecar start reliably.
- `/health` is stable and visible from desktop app.
- Observer captures useful low-noise events.
- Search can return plausible prior events for natural language queries.

## Current Implemented Slice
- Desktop app can start and fetch sidecar health.
- Sidecar returns contract-shaped health response with readiness flags.
- UI stack already includes Tailwind + shadcn-compatible primitives for future screens.
- Observer/ingest/search logic is implemented at baseline level:
  - observer v1 active-window capture
  - ingest dedupe/debounce
  - JSONL persistence
  - keyword search fallback endpoint

## Planned Source Expansion
- Browser adapter is the next high-value source (URL/title/snippet).
- Clipboard and notification capture follow to improve cross-app recall robustness.

## Where Confusion Usually Happens
- IPC vs HTTP: Tauri commands call Rust functions; sidecar API is local HTTP. You can combine both.
- Raw events vs indexed events: raw capture may happen before embeddings are ready.
- Permissions vs bugs: missing macOS permissions can look like broken logic.
- Packaging later can surface assumptions hidden during dev runs.

## Practical Rule of Thumb
If unsure, simplify the pipeline and keep visibility high:
- log inputs
- log debounce/dedupe decisions
- log indexing outcomes
- expose readiness in `/health`
