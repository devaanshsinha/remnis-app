from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .hash_utils import compute_context_hash, is_context_hash_valid
from .observer import ActiveWindowObserver
from .schemas import (
    BrowserIngestRequest,
    DebounceDecision,
    DedupeDecision,
    HealthReadiness,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ObserverStatsResponse,
    SearchResponse,
    SearchResult,
    ObservedContextEvent,
)

app = FastAPI(title="Remnis Sidecar", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^chrome-extension://.*$",
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
    last_error_code = _observer.last_error_code() if _observer else "observer_not_started"

    if observer_ready:
        observer_state = "healthy"
    elif last_error_code == "permission_denied":
        observer_state = "degraded_permission"
    elif last_error_code in {"capture_failed", "capture_empty"}:
        observer_state = "degraded_capture"
    elif last_error_code == "observer_not_started":
        observer_state = "starting"
    else:
        observer_state = "degraded_error"

    with _state_lock:
        return ObserverStatsResponse(
            observer_state=observer_state,
            observer_ready=observer_ready,
            last_error=last_error,
            last_error_code=last_error_code,
            stored_count=_stored_count,
            skipped_count=_skipped_count,
            last_stored_timestamp_utc=(
                _last_stored_timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                if _last_stored_timestamp_utc
                else None
            ),
        )


def _tokenize_query(query: str) -> list[str]:
    tokens = [part.strip().lower() for part in query.split() if part.strip()]
    # preserve order while dropping duplicates
    return list(dict.fromkeys(tokens))


def _search_score(event: dict[str, Any], query_tokens: list[str]) -> float:
    haystack = " ".join(
        [
            str(event.get("app_name", "")),
            str(event.get("window_title", "")),
            str(event.get("context_text", "")),
        ]
    ).lower()

    if not query_tokens:
        return 0.0

    matched = sum(1 for token in query_tokens if token in haystack)
    return matched / len(query_tokens)


def _load_persisted_events() -> list[dict[str, Any]]:
    if not EVENTS_JSONL.exists():
        return []

    rows: list[dict[str, Any]] = []
    with EVENTS_JSONL.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return rows


@app.get("/search", response_model=SearchResponse)
def search(q: str, k: int = 10, offset: int = 0) -> SearchResponse | JSONResponse:
    query = q.strip()
    if not query:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="q is required",
                details={"field": "q"},
            ),
        )
    if k < 1 or k > 50:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="k must be between 1 and 50",
                details={"field": "k"},
            ),
        )
    if offset < 0:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="offset must be >= 0",
                details={"field": "offset"},
            ),
        )

    query_tokens = _tokenize_query(query)
    events = _load_persisted_events()

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for event in events:
        score = _search_score(event, query_tokens)
        if score <= 0:
            continue
        scored.append((score, str(event.get("timestamp_utc", "")), event))

    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)

    total_estimate = len(scored)
    page = scored[offset : offset + k]

    results: list[SearchResult] = []
    for score, _, event in page:
        results.append(
            SearchResult(
                id=event["id"],
                timestamp_utc=str(event.get("timestamp_utc", "")),
                app_name=str(event.get("app_name", "")),
                window_title=str(event.get("window_title", "")),
                context_text=str(event.get("context_text", "")),
                score=round(float(score), 4),
                context_hash=str(event.get("context_hash", "")),
                source_version=str(event.get("source_version", "event.v1")),
            )
        )

    return SearchResponse(
        query=query,
        k=k,
        offset=offset,
        total_estimate=total_estimate,
        results=results,
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


@app.post("/ingest/browser", response_model=IngestResponse)
def ingest_browser(payload: BrowserIngestRequest) -> IngestResponse | JSONResponse:
    browser_event = payload.event
    snippet = (browser_event.snippet or "").strip()
    context_text_parts = [
        browser_event.app_name.strip(),
        browser_event.page_title.strip(),
        browser_event.url.strip(),
    ]
    if snippet:
        context_text_parts.append(snippet)
    context_text = " | ".join(part for part in context_text_parts if part)

    mapped = ObservedContextEvent(
        id=uuid4(),
        timestamp_utc=browser_event.timestamp_utc,
        app_name=browser_event.app_name.strip(),
        window_title=browser_event.window_title.strip(),
        file_path=browser_event.url.strip(),
        context_text=context_text,
        source="observer.accessibility_text",
        capture_confidence=0.98,
        context_hash="0" * 64,
        source_version=browser_event.source_version,
    )
    mapped.context_hash = compute_context_hash(mapped)
    return process_ingest_event(mapped)


def _persist_stored_event(event: ObservedContextEvent) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json())
        handle.write("\n")
