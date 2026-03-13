# Desktop App

## Current Status
- Vite + React + TypeScript app is running.
- Tauri v2 scaffold is present and runnable.
- Desktop UI calls sidecar `GET /health` and `GET /events`.
- Desktop UI calls sidecar `GET /index/status` for indexing visibility.
- UI shows a recent-events list from sidecar persistence.
- UI supports client-driven `/events` filters for source, app name, and UTC time range.
- UI calls `GET /search` with the same filters for query-time retrieval.
- UI shows which search mode produced the current results (`semantic` or `keyword_fallback`).
- Tailwind + shadcn-style foundation is configured.
- Final desktop behavior is intended to surface both:
  - fast local retrieval from the embedding/vector pipeline
  - heavier local query-time reasoning output when available

## Key Files
- `src/main.tsx` - frontend entry point
- `src/App.tsx` - health + recent-events MVP screen
- `src/styles.css` - Tailwind directives + token values
- `src/components/ui/button.tsx` - reusable Button primitive
- `src/lib/utils.ts` - `cn` utility
- `src-tauri/tauri.conf.json` - Tauri app config
- `src-tauri/src/main.rs` - Tauri runtime entry

## Local Run
1. `cd apps/desktop`
2. `npm install`
3. `npm run tauri dev`

Frontend-only:
1. `cd apps/desktop`
2. `npm install`
3. `npm run dev`
