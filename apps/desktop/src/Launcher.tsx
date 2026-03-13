import { useEffect, useRef, useState } from "react";
import { invoke, isTauri } from "@tauri-apps/api/core";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { listen } from "@tauri-apps/api/event";
import { Search, Settings2 } from "lucide-react";

const SIDECAR_BASE_URL = "http://127.0.0.1:8765";
const FOCUS_INPUT_EVENT = "launcher:focus-input";
const SEARCH_DEBOUNCE_MS = 140;

function focusElement(input: HTMLInputElement | null) {
  if (!input) {
    return;
  }

  requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
}

async function fetchJson(url: string, signal: AbortSignal) {
  const response = await fetch(url, {
    method: "GET",
    signal
  });

  if (!response.ok) {
    throw new Error(`${url} HTTP ${response.status}`);
  }

  return response.json();
}

export default function Launcher() {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    focusElement(inputRef.current);
  }, []);

  useEffect(() => {
    if (!isTauri()) {
      return;
    }

    const focusInput = () => {
      focusElement(inputRef.current);
    };

    let cleanupFocusEvent: (() => void) | undefined;
    let cleanupWindowFocus: (() => void) | undefined;
    let disposed = false;

    void (async () => {
      cleanupFocusEvent = await listen(FOCUS_INPUT_EVENT, () => {
        focusInput();
      });
      cleanupWindowFocus = await getCurrentWindow().onFocusChanged(({ payload }) => {
        if (payload) {
          focusInput();
        }
      });

      if (disposed) {
        cleanupFocusEvent?.();
        cleanupWindowFocus?.();
      }
    })();

    return () => {
      disposed = true;
      cleanupFocusEvent?.();
      cleanupWindowFocus?.();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void fetchJson(`${SIDECAR_BASE_URL}/health`, controller.signal).catch(() => {
      // Launcher keeps sidecar health warm but does not surface status here.
    });

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      const params = new URLSearchParams({
        q: trimmedQuery,
        k: "20"
      });

      void fetchJson(
        `${SIDECAR_BASE_URL}/search?${params.toString()}`,
        controller.signal
      ).catch(() => {
        // Search requests stay active behind the launcher UI even without visible results.
      });
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [query]);

  const hideLauncher = async () => {
    if (!isTauri()) {
      return;
    }
    await invoke("hide_search");
  };

  const openSettings = async () => {
    if (!isTauri()) {
      return;
    }
    await invoke("open_settings");
  };

  return (
    <main className="launcher-shell">
      <div className="launcher-pill">
        <div className="launcher-icon" aria-hidden="true">
          <Search className="h-5 w-5" strokeWidth={2.1} />
        </div>
        <input
          ref={inputRef}
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              void hideLauncher();
            }
          }}
          className="launcher-input"
          placeholder="Search your context"
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          aria-label="Search your context"
        />
        <button
          type="button"
          className="launcher-settings-button"
          onClick={() => void openSettings()}
          aria-label="Open settings"
          title="Open settings"
        >
          <Settings2 className="h-[18px] w-[18px]" strokeWidth={1.9} />
        </button>
      </div>
    </main>
  );
}
