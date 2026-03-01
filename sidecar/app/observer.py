from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from .hash_utils import compute_context_hash
from .schemas import EventSource, ObservedContextEvent


@dataclass(frozen=True)
class WindowContext:
    app_name: str
    window_title: str
    bundle_id: str | None = None


class ActiveWindowObserver:
    _GENERIC_ELECTRON_NAMES = {
        "Electron",
        "Electron Helper",
        "Electron Helper (Renderer)",
        "Electron Helper (GPU)",
    }

    def __init__(
        self,
        on_event: Callable[[ObservedContextEvent], None],
        *,
        poll_interval_seconds: float = 1.0,
        stability_window_seconds: float = 15.0,
    ) -> None:
        self._on_event = on_event
        self._poll_interval_seconds = poll_interval_seconds
        self._stability_window_seconds = stability_window_seconds

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._lock = threading.Lock()
        self._ready = False
        self._last_error: str | None = None

        self._current_context: WindowContext | None = None
        self._current_started_at: float | None = None
        self._current_emitted = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def is_ready(self) -> bool:
        with self._lock:
            return self._ready

    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def _set_ready(self, ready: bool) -> None:
        with self._lock:
            self._ready = ready

    def _set_error(self, err: str | None) -> None:
        with self._lock:
            self._last_error = err

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = self._capture_active_window()
                self._set_ready(True)
                self._set_error(None)
                self._process_snapshot(snapshot)
            except Exception as exc:  # noqa: BLE001
                self._set_ready(False)
                self._set_error(str(exc))
            finally:
                self._stop_event.wait(self._poll_interval_seconds)

    def _process_snapshot(self, snapshot: WindowContext) -> None:
        now_monotonic = time.monotonic()
        if self._current_context is None:
            self._current_context = snapshot
            self._current_started_at = now_monotonic
            self._current_emitted = False
            return

        if snapshot != self._current_context:
            previous_context = self._current_context
            previous_duration = now_monotonic - (self._current_started_at or now_monotonic)
            emitted_current = False
            if previous_duration >= self._stability_window_seconds:
                self._emit(previous_context)
            elif self._is_significant_change(previous_context, snapshot):
                self._emit(snapshot)
                emitted_current = True

            self._current_context = snapshot
            self._current_started_at = now_monotonic
            self._current_emitted = emitted_current
            return

        if self._current_emitted:
            return

        stable_seconds = now_monotonic - (self._current_started_at or now_monotonic)
        if stable_seconds >= self._stability_window_seconds:
            self._emit(snapshot)
            self._current_emitted = True

    @staticmethod
    def _is_significant_change(previous: WindowContext, current: WindowContext) -> bool:
        return previous.app_name != current.app_name or previous.window_title != current.window_title

    def _emit(self, context: WindowContext) -> None:
        now_utc = datetime.now(timezone.utc)
        event = ObservedContextEvent(
            id=uuid4(),
            timestamp_utc=now_utc,
            app_name=context.app_name,
            window_title=context.window_title,
            file_path=None,
            context_text=f"{context.app_name} | {context.window_title}",
            source=EventSource.ACTIVE_WINDOW,
            capture_confidence=0.95,
            context_hash="0" * 64,
            source_version="event.v1",
        )
        event.context_hash = compute_context_hash(event)
        self._on_event(event)

    @staticmethod
    def _capture_active_window() -> WindowContext:
        script = """
        tell application "System Events"
          set frontApp to first application process whose frontmost is true
          set appName to name of frontApp
          set bundleId to ""
          try
            set bundleId to bundle identifier of frontApp
          end try
          set windowTitle to ""
          try
            set windowTitle to name of front window of frontApp
          end try
          return appName & tab & windowTitle & tab & bundleId
        end tell
        """
        proc = subprocess.run(  # noqa: S603
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip() or "unknown osascript failure"
            raise RuntimeError(f"observer capture failed: {stderr}")

        stdout = proc.stdout.strip()
        if not stdout:
            raise RuntimeError("observer capture returned empty response")

        parts = stdout.split("\t")
        app_name = parts[0] if len(parts) > 0 else ""
        window_title = parts[1] if len(parts) > 1 else ""
        bundle_id = parts[2] if len(parts) > 2 else ""
        app_name = app_name.strip()
        window_title = window_title.strip() or "Untitled Window"
        bundle_id = bundle_id.strip() or None

        if not app_name:
            raise RuntimeError("observer capture returned empty app name")

        resolved_name = app_name
        if bundle_id and app_name in ActiveWindowObserver._GENERIC_ELECTRON_NAMES:
            # Fallback: use bundle id for readability when process name is generic Electron.
            resolved_name = bundle_id

        return WindowContext(
            app_name=resolved_name,
            window_title=window_title,
            bundle_id=bundle_id,
        )
