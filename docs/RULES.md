# Remnis Working Rules

## 1. Decision Rules
- Privacy-first is non-negotiable: no context leaves the device by default.
- Local-first architecture is the default: no external dependency is required for core search.
- Build smallest testable slice first before adding advanced capture/search features.
- Prefer reversible technical choices in early phases.
- Capture quality is the primary product bottleneck, not model size.
- Use a two-tier inference strategy:
  - lightweight always-on processing for background capture/indexing
  - heavier on-demand processing only when user invokes search/HUD

## 2. Scope Rules
- Do not add cloud sync, auth, or collaboration in early milestones.
- Do not add OCR/screenshot capture as baseline behavior.
- Do not expand capture sources until active-window capture is stable.
- After active-window capture is stable, expand sources in this order:
  - browser adapter (URL/title/snippet)
  - clipboard events
  - notifications metadata
  - app-specific adapters as needed

## 3. Repo and Change Rules
- Every meaningful code change must update at least one doc if behavior/architecture changes.
- Track assumptions and decisions explicitly (avoid hidden decisions in commit messages only).
- Keep contracts stable: schema/API changes must be documented before implementation.

## 4. Security and Privacy Rules
- Sidecar API binds to loopback only.
- No analytics/telemetry unless explicitly added with local-only defaults and user opt-in.
- Store minimal useful context needed for retrieval quality.
- Add explicit permission checks and user-facing permission states.

## 5. Quality Rules
- Start each phase with acceptance criteria.
- Add smoke tests for health/startup paths before feature expansion.
- Validate failure behavior (permissions denied, sidecar down, model unavailable).
- For any new capture source, define a minimum signal quality bar and fallback behavior.

## 6. Execution Rules for Early Development
- Order of work: contracts -> skeleton wiring -> minimal behavior -> validation -> iteration.
- Keep a running status log in `docs/PROJECT_STATUS.md`.
- Keep implementation intent in `docs/CONTEXT.md` updated as understanding evolves.

## 7. Definition of "Ready to Build"
A feature is ready when:
- Requirement is explicit.
- API/data contract is defined.
- Success criteria is testable.
- Known risks and fallback are written down.
