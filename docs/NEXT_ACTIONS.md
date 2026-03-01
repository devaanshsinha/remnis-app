# Next Actions (What, Why, Output)

## Status Update
- Step 1 (Freeze Contracts): completed in `docs/CONTRACTS.md`.
- Step 2 (Acceptance Criteria): completed in `docs/ACCEPTANCE_CRITERIA.md`.
- Step 3 (Permission and Failure Behavior): completed in `docs/FAILURE_BEHAVIOR.md`.

## 1. Freeze Contracts
What to do:
- Define exact payloads for observer events and search results.
- Define API response/error shapes for `/health`, `/ingest`, `/search`.

Why:
- Prevents rewrites across Rust, Python, and React.

What it produces:
- A stable integration boundary for all components.

## 2. Add Acceptance Criteria Per Phase
What to do:
- For each phase, write 3-6 objective checks that prove it works.

Why:
- Keeps progress measurable and avoids "almost done" ambiguity.

What it produces:
- Clear build gates before moving to next phase.

## 3. Define Permission and Failure Behavior
What to do:
- Document behavior for missing Accessibility permission, sidecar crash, and model load failure.

Why:
- These are the most likely early blockers on macOS.

What it produces:
- Predictable UX and faster debugging.

## 4. Start Minimal Scaffolding
What to do:
- Scaffold Tauri desktop app and Python sidecar skeleton only.
- Implement only `/health` first.

Why:
- Verifies process orchestration before adding observer/index/search complexity.

What it produces:
- A working end-to-end backbone you can build on safely.

## 5. Build Observer v1 (No Embeddings Yet)
What to do:
- Capture app/window title and run debounce/dedupe logic.

Why:
- Data quality is the foundation of search quality.

What it produces:
- Reliable event stream and realistic test data.

## 6. Add Storage and Semantic Search
What to do:
- Persist events, add embedding generation, and expose search endpoint.

Why:
- Converts captured context into useful retrieval behavior.

What it produces:
- First true product loop: capture -> index -> search -> display.

## 7. Connect HUD and Hotkey
What to do:
- Implement spotlight-style HUD query flow and keyboard interactions.

Why:
- User value is realized only when recall is fast and frictionless.

What it produces:
- Usable product experience and demonstrable MVP.
