# Remnis Requirements (Initial)

## 1. Product Objective
Remnis is a local-first macOS developer productivity app that captures workflow context and enables semantic recall of past work.

## 2. Scope
### In Scope
- Passive capture of active macOS application/window context.
- Local-first capture of rich workflow context over time, beginning with active-window and browser signals and expanding to higher-value sources such as editor/workspace state, clipboard history, and local agent/chat context.
- Smart noise suppression and retrieval compaction without discarding useful accepted raw history.
- Local vector indexing and semantic search.
- Fast local API for querying indexed context.
- Spotlight-style HUD for quick retrieval.
- Menu bar presence and global hotkey trigger.

### Out of Scope (Initial)
- Cloud sync or remote processing.
- Multi-user collaboration.
- OCR-heavy capture pipelines as baseline requirement.

## 3. Core Principles
- Privacy-first: no user context leaves device by default.
- Local-first: all capture, indexing, and querying happen on-device.
- Low-friction UX: mostly invisible until hotkey summon.
- Resource-aware: bounded CPU/memory impact while observing.
- Final product requires two local model tiers:
  - a lightweight always-on embedding/indexing model
  - a heavier local query-time reasoning model

## 4. System Architecture Requirements
### 4.1 Desktop Shell (Tauri v2, Rust)
- Must provide native macOS integration for menu bar and hotkeys.
- Must launch and supervise a local Python sidecar process.
- Must expose secure IPC between frontend and backend commands.

### 4.2 Frontend HUD (Vite + React + TypeScript)
- Must render a centered, borderless Spotlight-style search surface.
- Must show result rows with app identity, context snippet, and relative time.
- Must support keyboard-first interaction (open, navigate, dismiss).

### 4.3 Python Sidecar (FastAPI)
- Must expose local HTTP API for health, ingest, and search.
- Must run observer + indexing logic on-device.
- Must remain functional without system Python preinstalled when packaged.

### 4.4 Vector Layer (LanceDB)
- Must persist vectors and metadata on local disk.
- Must support semantic top-k retrieval with low latency.

### 4.5 Background Embedding Model
- Baseline model: `all-MiniLM-L6-v2` (local execution).
- Embedding generation must be deterministic for same input text/version.
- This model is responsible for background indexing and semantic retrieval features.

### 4.6 Query-Time Reasoning Model
- A second local model must exist for on-demand reasoning when the user invokes Remnis.
- This model is responsible for reranking, synthesizing short answers, generating reminders, and connecting related events after retrieval.
- This model must not be required for background capture/indexing.
- Exact model choice is still open, but it must run locally and remain within acceptable interactive latency on target Macs.

## 5. Functional Requirements
### 5.1 Observation
- Capture active app name and window title.
- Capture file path/visible text where accessible and permitted.
- Timestamp all events with UTC ISO-8601.

### 5.2 Smart Debouncing
- Record only when user stays on context for >15 seconds OR context changes significantly.
- Significant change baseline: app/window title hash differs from previous event.

### 5.3 Deduplication
- Compute content hash over normalized context payload.
- Use source-aware duplicate suppression for clearly redundant emissions.
- Preserve accepted raw event history as an append-only local log whenever possible.
- Allow the retrieval/index layer to compact repeated raw events into cleaner search documents without deleting the underlying raw timeline.

### 5.4 Storage
- Store raw context, timestamps, and hash metadata in an append-only local event history.
- Support a derived retrieval/index layer that may merge or compact raw events for search quality while preserving the raw timeline for auditability and later enrichment.
- Store embeddings and retrieval metadata for indexed search documents derived from raw history.

### 5.5 Search API
- Provide semantic query endpoint over localhost.
- Return ranked results with score + metadata.
- Support limit/offset style pagination.
- Search should be able to answer developer-oriented lookup questions over prior local work context, not only exact keyword matches.
- Support a second query-time reasoning pass over retrieved results.

### 5.6 HUD Retrieval
- Query as user types with request throttling.
- Render best matches with app icon, snippet, and relative time.

## 6. Non-Functional Requirements
### 6.1 Privacy & Security
- No remote telemetry by default.
- Explicit user consent flow for macOS permissions.
- Local-only API binding (loopback interface only).

### 6.2 Performance
- Observer loop must remain lightweight during normal developer workflow.
- Search response target: interactive latency suitable for type-ahead UX.
- Background model work must stay low overhead.
- Query-time model work may use more CPU/RAM than background indexing, but must remain bounded and user-invoked.

### 6.3 Reliability
- Sidecar auto-restart policy on crash with bounded retries.
- Graceful degradation when permissions are missing.

### 6.4 Packaging
- Deliverable target: distributable `.app` and `.dmg` for macOS.
- Python sidecar bundled (PyInstaller) with no external Python dependency.

## 7. macOS Integration Requirements
- Accessibility permission handling is mandatory for observer capability.
- Optional future capture modes (e.g., screen text extraction) must require explicit user opt-in.
- Permission state must be inspectable in-app with clear remediation guidance.

## 8. API Contract (Initial Draft)
### `GET /health`
- Returns service status and model/db readiness flags.
- Final architecture should expose readiness separately for the embedding model and the query-time reasoning model.

### `POST /ingest`
- Accepts normalized context event payload.
- Performs dedupe + optional embed + persist.

### `GET /search?q=<query>&k=<n>`
- Returns top-k semantically ranked context items.

## 9. Data Model (Initial Draft)
Required fields per indexed item:
- `id` (UUID)
- `timestamp_utc` (ISO-8601)
- `app_name` (string)
- `window_title` (string)
- `context_text` (string)
- `context_hash` (string)
- `embedding` (vector<float>)
- `source_version` (schema/model version)

## 10. Milestone Gates (High-Level, Unordered)
- Observer captures and logs stable context events.
- Dedupe/debounce logic validated with repeated context switching.
- LanceDB persists vectors and metadata.
- Search endpoint returns relevant results for natural language queries.
- HUD invokes search and displays ranked results.
- Global hotkey opens/closes HUD reliably.
- End-to-end packaged app runs on clean macOS machine.

## 11. Open Decisions
- Exact IPC pattern between Tauri commands and sidecar HTTP.
- Initial persistence strategy for raw events before embedding completion.
- Fallback behavior when embedding model initialization fails.
- Final local query-time reasoning model choice and resource envelope.
- Final ranking blend (semantic score + recency weighting).
