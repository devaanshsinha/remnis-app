from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .hash_utils import is_context_hash_valid
from .observer import ActiveWindowObserver
from .schemas import (
    DebounceDecision,
    DedupeDecision,
    HealthReadiness,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ObserverStatsResponse,
    ObservedContextEvent,
)

app = FastAPI(title="Remnis Sidecar", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


DEBOUNCE_WINDOW_SECONDS = 15.0
_last_stored_hash: str | None = None
_last_stored_timestamp_utc: datetime | None = None
_stored_count = 0
_skipped_count = 0
_observer: ActiveWindowObserver | None = None
_state_lock = threading.Lock()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EVENTS_JSONL = DATA_DIR / "events.jsonl"


def _error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {"loc": (), "msg": "Invalid request"}
    field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    payload = _error_payload(
        code="INVALID_REQUEST",
        message=first.get("msg", "Invalid request"),
        details={"field": field or "body", "path": str(request.url.path)},
    )
    return JSONResponse(status_code=400, content=payload)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    observer_ready = _observer.is_ready() if _observer else False
    return HealthResponse(
        status="ok",
        service="remnis-sidecar",
        version="0.1.0",
        time_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        readiness=HealthReadiness(
            observer_ready=observer_ready,
            db_ready=False,
            embedder_ready=False,
        ),
    )


@app.get("/observer/stats", response_model=ObserverStatsResponse)
def observer_stats() -> ObserverStatsResponse:
    observer_ready = _observer.is_ready() if _observer else False
    last_error = _observer.last_error() if _observer else "observer not started"
    with _state_lock:
        return ObserverStatsResponse(
            observer_ready=observer_ready,
            last_error=last_error,
            stored_count=_stored_count,
            skipped_count=_skipped_count,
            last_stored_timestamp_utc=(
                _last_stored_timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                if _last_stored_timestamp_utc
                else None
            ),
        )


def process_ingest_event(event: ObservedContextEvent) -> IngestResponse | JSONResponse:
    global _last_stored_hash
    global _last_stored_timestamp_utc
    global _stored_count
    global _skipped_count

    if not is_context_hash_valid(event):
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="context_hash does not match normalized event payload",
                details={"field": "event.context_hash"},
            ),
        )

    is_duplicate = _last_stored_hash is not None and event.context_hash == _last_stored_hash
    dedupe = DedupeDecision(
        is_duplicate=is_duplicate,
        reason="same_context_hash" if is_duplicate else None,
    )

    is_debounced = False
    debounce_reason: str | None = None
    if _last_stored_timestamp_utc is not None:
        elapsed_seconds = (event.timestamp_utc - _last_stored_timestamp_utc).total_seconds()
        if elapsed_seconds < DEBOUNCE_WINDOW_SECONDS and is_duplicate:
            is_debounced = True
            debounce_reason = "below_stability_window"

    debounce = DebounceDecision(is_debounced=is_debounced, reason=debounce_reason)
    should_skip = dedupe.is_duplicate or debounce.is_debounced

    with _state_lock:
        if should_skip:
            _skipped_count += 1
        else:
            _stored_count += 1
            _last_stored_hash = event.context_hash
            _last_stored_timestamp_utc = event.timestamp_utc
            _persist_stored_event(event)

    return IngestResponse(
        status="skipped" if should_skip else "stored",
        event_id=event.id,
        dedupe=dedupe,
        debounce=debounce,
    )


def _on_observer_event(event: ObservedContextEvent) -> None:
    response = process_ingest_event(event)
    if isinstance(response, JSONResponse):
        return

    print(
        "[observer]",
        response.status,
        event.app_name,
        "|",
        event.window_title,
        f"(stored={_stored_count}, skipped={_skipped_count})",
    )


@app.on_event("startup")
async def on_startup() -> None:
    global _observer
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _observer = ActiveWindowObserver(on_event=_on_observer_event)
    _observer.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if _observer:
        _observer.stop()


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse | JSONResponse:
    return process_ingest_event(payload.event)


def _persist_stored_event(event: ObservedContextEvent) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json())
        handle.write("\n")
