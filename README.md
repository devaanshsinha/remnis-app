# Remnis

Privacy-first, local-first work-memory engine for macOS.

## Repository Initialization (v0)

This repo is intentionally initialized with structure and documentation first, before framework scaffolding.

## Current Structure

- `apps/desktop` - Tauri v2 + Vite + React + TypeScript app (to be scaffolded)
- `sidecar` - Python FastAPI observer/embedding/search engine (to be scaffolded)
- `docs` - project documentation, operating rules, and status tracking
- `requirements.md` - product + engineering requirements baseline

## Documentation Index

- `requirements.md` - canonical requirements and constraints
- `docs/RULES.md` - working rules and guardrails
- `docs/PROJECT_STATUS.md` - what has been done and current state
- `docs/CONTEXT.md` - system-level project context and mental model
- `docs/NEXT_ACTIONS.md` - immediate next actions with purpose and output
- `docs/CONTRACTS.md` - frozen event and API contracts (`v0.1`)
- `docs/ACCEPTANCE_CRITERIA.md` - objective pass/fail gates per phase

## Scaffolding Status

- Desktop app: not scaffolded yet
- Python sidecar: not scaffolded yet

## Recommended Next Step

Contracts and acceptance criteria are now documented.
Next move: scaffold desktop and sidecar skeletons, then wire a minimal `/health` handshake.
