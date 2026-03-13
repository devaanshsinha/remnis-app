# Desktop App

## Current Status
- Vite + React + TypeScript app is running.
- Tauri v2 scaffold is present and runnable.
- Desktop runtime now uses two Tauri windows:
  - `search` - transparent Spotlight-style launcher window
  - `settings` - normal app window for inspector/settings details, created only when opened explicitly
- On macOS, the app now runs in accessory mode so it behaves like a launcher instead of a normal Dock app.
- Global shortcut `Option+Space` toggles the launcher window.
- Launcher autofocuses its input when shown and hides on `Escape`.
- Launcher includes a settings action that opens the normal app window.
- Desktop UI calls sidecar `GET /health` and `GET /events`.
- Desktop UI calls sidecar `GET /index/status` for indexing visibility.
- UI shows a recent-events list from sidecar persistence.
- UI shows raw-event count and retrieval-document count from sidecar index status.
- UI supports client-driven `/events` filters for source, app name, and UTC time range.
- UI calls `GET /search` with the same filters for query-time retrieval.
- UI shows which search mode produced the current results (`semantic` or `keyword_fallback`).
- The launcher window is now the primary interaction surface, while the settings window still hosts the prototype inspector over raw events and retrieval state.
- Tailwind + shadcn-style foundation is configured.
- Final desktop behavior is intended to surface both:
  - fast local retrieval from the embedding/vector pipeline
  - heavier local query-time reasoning output when available

## Key Files
- `src/main.tsx` - frontend entry point
- `src/App.tsx` - settings/details window UI
- `src/Launcher.tsx` - transparent Spotlight-style launcher UI
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
