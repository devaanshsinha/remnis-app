# Desktop App

## Current Status
- Vite + React + TypeScript app is running.
- Tauri v2 scaffold is present and runnable.
- Health-check UI calls sidecar `GET /health`.
- Tailwind + shadcn-style foundation is configured.

## Key Files
- `src/main.tsx` - frontend entry point
- `src/App.tsx` - current health-check screen
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

