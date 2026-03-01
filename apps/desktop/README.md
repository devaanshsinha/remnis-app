# Desktop App

Current status:
- Vite + React + TypeScript skeleton created.
- Health-check UI wired to `http://127.0.0.1:8765/health`.
- `src-tauri` placeholder config added for Tauri v2.

Prerequisites to run full desktop stack:
- Node.js + npm
- Rust toolchain (`cargo`) for Tauri runtime

Current limitation in this environment:
- `cargo` is not installed, so Tauri runtime is not runnable yet.

Frontend-only local run:
1. `cd apps/desktop`
2. `npm install`
3. `npm run dev`
