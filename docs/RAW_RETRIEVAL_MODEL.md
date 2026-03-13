# Raw History and Retrieval Model

This document defines the intended split between:
- append-only raw local history
- derived retrieval/index documents

The goal is to preserve rich local developer context over time while still producing clean, high-signal search results.

## 1. Why This Split Exists

Remnis should not treat every current search heuristic as a storage rule.

Examples:
- repeated window-focus events may still be useful for dwell time, task switching, and later multi-source correlation
- browser navigation events may be noisy in raw form but still matter for reconstructing how a problem was solved
- future editor, clipboard, and agent/chat signals will be more valuable when linked back to the original local timeline

So Remnis needs two layers:
- raw events: what happened
- retrieval documents: what should be indexed and ranked for recall

## 2. Design Rules

- Raw accepted events are append-only by default.
- Retrieval/index documents are derived artifacts and may be recomputed.
- Source-specific suppression is allowed for clearly redundant emissions, but accepted raw history should be preserved whenever practical.
- Search quality should improve by compaction, grouping, ranking, and synthesis before deleting accepted raw history.
- Query-time reasoning should consume retrieval results plus linked raw context, not only a flat list of isolated events.

## 3. Core Entities

### 3.1 Raw Event

A raw event is the smallest accepted local fact written to history.

Examples:
- active window changed to a file in VS Code
- browser tab changed to a documentation page
- clipboard content changed
- agent chat answer was shown locally
- terminal command produced an error

Properties:
- append-only
- timestamped
- source-specific
- locally stored
- may be noisy or repetitive

Current raw storage:
- `sidecar/data/events.jsonl`

Current initial sources:
- `observer.active_window`
- browser extension mapped into `observer.accessibility_text`

Future sources:
- editor/workspace integrations
- clipboard
- notifications
- agent/chat sessions
- terminal integrations

### 3.2 Retrieval Document

A retrieval document is the unit that should be embedded, indexed, and ranked for search.

It may represent:
- one raw event
- a compacted cluster of repeated raw events
- a short activity episode
- a cross-source grouped unit of work

Properties:
- derived from raw events
- optimized for search quality
- versioned so it can be rebuilt as logic improves
- may contain summary text, merged metadata, and links back to raw event IDs

Current state:
- the vector index is still close to one-document-per-event

Target state:
- the vector index should gradually move toward cleaner retrieval documents rather than mirroring every raw event 1:1

### 3.3 Work Episode

A work episode is a higher-level grouping concept used to connect related raw events across time and sources.

Examples:
- editing `vector_store.py`, reading LanceDB docs, and asking an agent about schema mismatch
- debugging a Docker failure across terminal, browser, and code editor

An episode may later become:
- a retrieval document itself
- a reasoning-time bundle of context
- a timeline shown in the HUD

Episodes do not need to be fully implemented before retrieval documents, but the retrieval model should leave room for them.

## 4. Proposed Data Flow

1. Capture source emits a candidate event.
2. Sidecar normalizes and validates it.
3. If the event is accepted, it is appended to raw history.
4. A derivation step converts one or more raw events into one retrieval document.
5. The retrieval document is embedded and written to the vector index.
6. Search retrieves candidate retrieval documents.
7. Query-time reasoning reads those retrieval documents and can follow links back to raw events for richer answers.

## 5. What Should Stay Raw

These belong in raw history even if they are not indexed 1:1 forever:
- repeated returns to the same file or tab
- closely spaced focus switches
- clipboard changes
- intermediate agent prompts and responses
- repeated visits to the same error or doc page

Why:
- they help reconstruct intent and task flow
- they make later correlation possible
- they may matter for reasoning even when they are too noisy for direct retrieval

## 6. What Should Be Compacted for Retrieval

These are good candidates for derived retrieval documents:
- repeated identical active-window events within a short window
- multiple browser page events for the same page/session
- short bursts of related work on the same file
- a terminal error plus nearby file edits and doc reads

Compaction outputs should preserve:
- representative text
- first and last timestamp
- source mix
- app names
- referenced files/URLs
- linked raw event IDs
- a derivation version

## 7. Proposed Retrieval Document Shape

This is a target model, not yet the live contract.

```json
{
  "id": "retrieval-doc-uuid",
  "document_version": "retrieval_doc.v1",
  "time_start_utc": "2026-03-13T04:40:00Z",
  "time_end_utc": "2026-03-13T04:46:00Z",
  "title": "Editing vector_store.py while verifying LanceDB index repair",
  "summary_text": "Worked in VS Code on vector_store.py, viewed Remnis desktop state, and verified vector indexing recovery.",
  "source_kinds": ["editor.vscode", "observer.active_window", "desktop.remnis"],
  "app_names": ["Code", "remnis-desktop"],
  "file_paths": ["/Users/devaansh/dev/remnis-app/sidecar/app/vector_store.py"],
  "urls": [],
  "raw_event_ids": [
    "event-1",
    "event-2",
    "event-3"
  ],
  "context_hashes": [
    "hash-1",
    "hash-2"
  ],
  "embedding": [0.0],
  "index_version": "embedder.all-MiniLM-L6-v2.v1"
}
```

## 8. Linkage Rules

Retrieval documents should keep links back to raw history.

Minimum linkage:
- `raw_event_ids`
- time window
- source list

Why:
- allows drill-down in the UI
- lets reasoning inspect original evidence
- keeps derivation reversible

## 9. Source-Aware Compaction Rules

Different sources need different treatment.

### Active Window
- good for timeline and dwell
- often noisy when used directly for retrieval
- should likely compact repeated identical contexts into one retrieval unit

### Browser
- keep raw navigations locally
- compact repeated same-page emissions
- prefer title + normalized URL + snippet for retrieval text

### Editor/Workspace
- likely one of the highest-value future sources
- should produce richer retrieval text than generic window titles
- may include repo, file path, symbol, branch, diagnostics, and task context

### Clipboard
- raw history can be highly valuable later
- retrieval should be selective and permission-aware
- likely best used as supporting context rather than dominant retrieval text

### Agent/Chat
- preserve prompts/responses locally when enabled
- derive retrieval documents around task/question boundaries rather than every single message

## 10. Query-Time Reasoning Inputs

The second local model should not consume only plain search rows.

It should receive:
- top retrieval documents
- linked raw event excerpts
- source metadata
- timestamps and relative ordering
- files/URLs/apps involved

This makes it possible to answer questions like:
- "How did I fix that build error last week?"
- "What file and docs did I use when I changed vector indexing?"
- "What was I working on before I copied that command?"

## 11. Immediate Implementation Consequences

The next implementation phase should avoid over-optimizing raw ingest around current search behavior.

Priority order:
1. keep raw history append-only where practical
2. define a first retrieval-document builder over current raw events
3. embed/index retrieval documents instead of assuming raw event == indexed document forever
4. add richer sources using the same raw-to-derived pattern
5. feed linked retrieval + raw context into the later reasoning model

## 12. Short-Term Build Target

For the next concrete milestone, Remnis should implement:
- a first explicit retrieval document schema
- a raw-event-to-retrieval-document builder for current sources
- index status that can report both raw event count and retrieval document count
- search results that can link back to supporting raw history

That will make future VS Code, clipboard, browser, and agent/chat integrations much easier to add without rethinking the storage model each time.
