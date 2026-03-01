from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .hash_utils import is_context_hash_valid
from .schemas import (
    DebounceDecision,
    DedupeDecision,
    HealthReadiness,
    HealthResponse,
    IngestRequest,
    IngestResponse,
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
    return HealthResponse(
        status="ok",
        service="remnis-sidecar",
        version="0.1.0",
        time_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        readiness=HealthReadiness(
            observer_ready=False,
            db_ready=False,
            embedder_ready=False,
        ),
    )


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse | JSONResponse:
    global _last_stored_hash
    global _last_stored_timestamp_utc

    event = payload.event

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

    if not should_skip:
        _last_stored_hash = event.context_hash
        _last_stored_timestamp_utc = event.timestamp_utc

    return IngestResponse(
        status="skipped" if should_skip else "stored",
        event_id=event.id,
        dedupe=dedupe,
        debounce=debounce,
    )
