from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .embedder import LocalEmbedder
from .hash_utils import compute_context_hash, is_context_hash_valid
from .observer import ActiveWindowObserver
from .schemas import (
    BrowserIngestRequest,
    DebounceDecision,
    DedupeDecision,
    EventSource,
    EventsResponse,
    HealthReadiness,
    HealthResponse,
    IndexStatusResponse,
    IngestRequest,
    IngestResponse,
    ObserverStatsResponse,
    SearchResponse,
    SearchResult,
    ObservedContextEvent,
)
from .vector_store import LocalVectorStore

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
BROWSER_REPEAT_WINDOW_SECONDS = 3.0
_last_stored_hash: str | None = None
_last_stored_timestamp_utc: datetime | None = None
_last_browser_store_by_key: dict[str, tuple[str, datetime]] = {}
_stored_count = 0
_skipped_count = 0
_observer: ActiveWindowObserver | None = None
_embedder: LocalEmbedder | None = None
_vector_store: LocalVectorStore | None = None
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
    db_ready = _vector_store.is_ready() if _vector_store else False
    embedder_ready = _embedder.is_ready() if _embedder else False
    return HealthResponse(
        status="ok",
        service="remnis-sidecar",
        version="0.1.0",
        time_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        readiness=HealthReadiness(
            observer_ready=observer_ready,
            db_ready=db_ready,
            embedder_ready=embedder_ready,
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


@app.get("/index/status", response_model=IndexStatusResponse)
def index_status() -> IndexStatusResponse:
    return IndexStatusResponse(
        embedder_ready=_embedder.is_ready() if _embedder else False,
        embedder_model_name=_embedder.model_name() if _embedder else "uninitialized",
        embedder_last_error=_embedder.last_error() if _embedder else "embedder_not_started",
        vector_store_ready=_vector_store.is_ready() if _vector_store else False,
        vector_store_last_error=(
            _vector_store.last_error() if _vector_store else "vector_store_not_started"
        ),
        indexed_event_count=_vector_store.indexed_event_count() if _vector_store else 0,
    )


def _tokenize_query(query: str) -> list[str]:
    tokens = [part.strip().lower() for part in query.split() if part.strip()]
    # preserve order while dropping duplicates
    return list(dict.fromkeys(tokens))


def _normalize_text_signature(raw_value: str | None) -> str:
    return " ".join((raw_value or "").strip().lower().split())


def _is_browser_app(app_name: str) -> bool:
    lowered = app_name.strip().lower()
    return any(
        token in lowered
        for token in [
            "chrome",
            "brave",
            "edge",
            "arc",
            "firefox",
            "safari",
        ]
    )


def _normalize_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if not parsed.scheme or not parsed.netloc:
        return raw_url.strip()

    blocked_query_prefixes = ("utm_",)
    blocked_query_keys = {
        "fbclid",
        "gclid",
        "dclid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "ref",
        "ref_src",
    }
    clean_items: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in blocked_query_keys:
            continue
        if any(lowered.startswith(prefix) for prefix in blocked_query_prefixes):
            continue
        clean_items.append((key, value))
    clean_query = urlencode(clean_items, doseq=True)

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            clean_query,
            parsed.fragment,
        )
    )


def _should_skip_observer_browser_event(event: ObservedContextEvent) -> bool:
    if event.source != EventSource.ACTIVE_WINDOW:
        return False
    return _is_browser_app(event.app_name)


def _browser_store_key(app_name: str, window_id: int | None, tab_id: int | None) -> str | None:
    if tab_id is None:
        return None
    return f"{_normalize_text_signature(app_name)}:{window_id or 0}:{tab_id}"


def _browser_store_signature(
    normalized_url: str,
    page_title: str,
    snippet: str | None,
) -> str:
    return "|".join(
        [
            normalized_url,
            _normalize_text_signature(page_title),
            _normalize_text_signature(snippet),
        ]
    )


def _should_skip_browser_repeat(
    app_name: str,
    window_id: int | None,
    tab_id: int | None,
    normalized_url: str,
    page_title: str,
    snippet: str | None,
    timestamp_utc: datetime,
) -> bool:
    key = _browser_store_key(app_name, window_id, tab_id)
    if key is None:
        return False

    with _state_lock:
        previous = _last_browser_store_by_key.get(key)
    if previous is None:
        return False

    signature = _browser_store_signature(normalized_url, page_title, snippet)
    previous_signature, previous_timestamp_utc = previous
    elapsed_seconds = (timestamp_utc - previous_timestamp_utc).total_seconds()
    return signature == previous_signature and elapsed_seconds < BROWSER_REPEAT_WINDOW_SECONDS


def _remember_browser_store(
    app_name: str,
    window_id: int | None,
    tab_id: int | None,
    normalized_url: str,
    page_title: str,
    snippet: str | None,
    timestamp_utc: datetime,
) -> None:
    key = _browser_store_key(app_name, window_id, tab_id)
    if key is None:
        return

    signature = _browser_store_signature(normalized_url, page_title, snippet)
    with _state_lock:
        _last_browser_store_by_key[key] = (signature, timestamp_utc)


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


def _semantic_score(raw_distance: Any) -> float:
    try:
        distance = float(raw_distance)
    except (TypeError, ValueError):
        return 0.0
    if distance < 0:
        distance = 0.0
    return 1.0 / (1.0 + distance)


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


def _load_persisted_observed_events() -> list[ObservedContextEvent]:
    events: list[ObservedContextEvent] = []
    for row in _load_persisted_events():
        try:
            events.append(ObservedContextEvent.model_validate(row))
        except Exception:
            continue
    return events


def _parse_event_timestamp(raw_value: Any) -> datetime | None:
    if not isinstance(raw_value, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@app.get("/events", response_model=EventsResponse)
def events(
    limit: int = 50,
    offset: int = 0,
    source: EventSource | None = None,
    app_name: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
) -> EventsResponse | JSONResponse:
    if limit < 1 or limit > 200:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="limit must be between 1 and 200",
                details={"field": "limit"},
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

    from_dt = _parse_event_timestamp(from_ts) if from_ts else None
    if from_ts and from_dt is None:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="from_ts must be ISO-8601 UTC time",
                details={"field": "from_ts"},
            ),
        )
    to_dt = _parse_event_timestamp(to_ts) if to_ts else None
    if to_ts and to_dt is None:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="to_ts must be ISO-8601 UTC time",
                details={"field": "to_ts"},
            ),
        )
    if from_dt and to_dt and from_dt > to_dt:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="from_ts must be <= to_ts",
                details={"field": "from_ts"},
            ),
        )

    app_name_normalized = app_name.strip().lower() if app_name else None
    filtered: list[ObservedContextEvent] = []
    for event in _load_persisted_observed_events():
        if source and event.source != source:
            continue
        if app_name_normalized and event.app_name.strip().lower() != app_name_normalized:
            continue
        if from_dt and event.timestamp_utc < from_dt:
            continue
        if to_dt and event.timestamp_utc > to_dt:
            continue
        filtered.append(event)

    filtered.sort(key=lambda item: item.timestamp_utc, reverse=True)
    total_estimate = len(filtered)
    page = filtered[offset : offset + limit]
    return EventsResponse(
        limit=limit,
        offset=offset,
        total_estimate=total_estimate,
        results=page,
    )


@app.get("/search", response_model=SearchResponse)
def search(
    q: str,
    k: int = 10,
    offset: int = 0,
    source: EventSource | None = None,
    app_name: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
) -> SearchResponse | JSONResponse:
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

    from_dt = _parse_event_timestamp(from_ts) if from_ts else None
    if from_ts and from_dt is None:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="from_ts must be ISO-8601 UTC time",
                details={"field": "from_ts"},
            ),
        )
    to_dt = _parse_event_timestamp(to_ts) if to_ts else None
    if to_ts and to_dt is None:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="to_ts must be ISO-8601 UTC time",
                details={"field": "to_ts"},
            ),
        )
    if from_dt and to_dt and from_dt > to_dt:
        return JSONResponse(
            status_code=400,
            content=_error_payload(
                code="INVALID_REQUEST",
                message="from_ts must be <= to_ts",
                details={"field": "from_ts"},
            ),
        )

    app_name_normalized = app_name.strip().lower() if app_name else None
    scored: list[tuple[float, str, dict[str, Any]]] = []
    search_mode = "keyword_fallback"

    if _embedder and _vector_store and _embedder.is_ready() and _vector_store.is_ready():
        try:
            query_embedding = _embedder.encode_text(query)
            candidate_limit = min(max(k + offset, 25), 200)
            for row in _vector_store.search_similar(query_embedding, candidate_limit):
                try:
                    event = ObservedContextEvent(
                        id=row["id"],
                        timestamp_utc=row["timestamp_utc"],
                        app_name=row["app_name"],
                        window_title=row["window_title"],
                        file_path=row.get("file_path"),
                        context_text=row["context_text"],
                        source=row["source"],
                        capture_confidence=None,
                        context_hash=row["context_hash"],
                        source_version=row["source_version"],
                    )
                except Exception:
                    continue

                if source and event.source != source:
                    continue
                if app_name_normalized and event.app_name.strip().lower() != app_name_normalized:
                    continue
                if from_dt and event.timestamp_utc < from_dt:
                    continue
                if to_dt and event.timestamp_utc > to_dt:
                    continue

                event_dump = event.model_dump(mode="json")
                score = _semantic_score(row.get("_distance"))
                if score <= 0:
                    continue
                scored.append((score, str(event.timestamp_utc), event_dump))
            if scored:
                search_mode = "semantic"
        except Exception:
            scored = []

    if not scored:
        query_tokens = _tokenize_query(query)
        for event in _load_persisted_observed_events():
            if source and event.source != source:
                continue
            if app_name_normalized and event.app_name.strip().lower() != app_name_normalized:
                continue
            if from_dt and event.timestamp_utc < from_dt:
                continue
            if to_dt and event.timestamp_utc > to_dt:
                continue

            event_dump = event.model_dump(mode="json")
            score = _search_score(event_dump, query_tokens)
            if score <= 0:
                continue
            scored.append((score, str(event.timestamp_utc), event_dump))

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
        mode=search_mode,
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

    if _should_skip_observer_browser_event(event):
        with _state_lock:
            _skipped_count += 1
        return IngestResponse(
            status="skipped",
            event_id=event.id,
            dedupe=DedupeDecision(is_duplicate=False, reason=None),
            debounce=DebounceDecision(
                is_debounced=True,
                reason="browser_capture_disabled_in_observer",
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
    global _embedder
    global _vector_store
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _embedder = LocalEmbedder()
    _embedder.initialize()
    _vector_store = LocalVectorStore(DATA_DIR)
    _vector_store.initialize()
    _backfill_vector_index()
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
    event_id = uuid4()
    snippet = (browser_event.snippet or "").strip()
    normalized_url = _normalize_url(browser_event.url)
    normalized_prev_url = _normalize_url(browser_event.prev_url) if browser_event.prev_url else None
    normalized_page_title = " ".join(browser_event.page_title.strip().split())

    if _should_skip_browser_repeat(
        app_name=browser_event.app_name,
        window_id=browser_event.window_id,
        tab_id=browser_event.tab_id,
        normalized_url=normalized_url,
        page_title=normalized_page_title,
        snippet=snippet,
        timestamp_utc=browser_event.timestamp_utc,
    ):
        global _skipped_count
        with _state_lock:
            _skipped_count += 1
        return IngestResponse(
            status="skipped",
            event_id=event_id,
            dedupe=DedupeDecision(is_duplicate=False, reason=None),
            debounce=DebounceDecision(
                is_debounced=True,
                reason="browser_repeat_window",
            ),
        )

    context_text_parts = [
        browser_event.app_name.strip(),
        normalized_page_title,
        normalized_url,
    ]
    if normalized_prev_url:
        context_text_parts.append(f"from:{normalized_prev_url}")
    if browser_event.tab_id is not None:
        context_text_parts.append(f"tab:{browser_event.tab_id}")
    if browser_event.window_id is not None:
        context_text_parts.append(f"window:{browser_event.window_id}")
    if snippet:
        context_text_parts.append(snippet)
    context_text = " | ".join(part for part in context_text_parts if part)

    mapped = ObservedContextEvent(
        id=event_id,
        timestamp_utc=browser_event.timestamp_utc,
        app_name=browser_event.app_name.strip(),
        window_title=normalized_page_title,
        file_path=normalized_url,
        context_text=context_text,
        source=EventSource.ACCESSIBILITY_TEXT,
        capture_confidence=0.98,
        context_hash="0" * 64,
        source_version=browser_event.source_version,
    )
    mapped.context_hash = compute_context_hash(mapped)
    response = process_ingest_event(mapped)
    if not isinstance(response, JSONResponse) and response.status == "stored":
        _remember_browser_store(
            app_name=browser_event.app_name,
            window_id=browser_event.window_id,
            tab_id=browser_event.tab_id,
            normalized_url=normalized_url,
            page_title=normalized_page_title,
            snippet=snippet,
            timestamp_utc=browser_event.timestamp_utc,
        )
    return response


def _persist_stored_event(event: ObservedContextEvent) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json())
        handle.write("\n")

    _index_stored_event(event)


def _index_stored_event(event: ObservedContextEvent) -> None:
    if not _embedder or not _vector_store:
        return
    if not _embedder.is_ready() or not _vector_store.is_ready():
        return
    if _vector_store.has_context_hash(event.context_hash):
        return

    try:
        embedding = _embedder.encode_text(event.context_text)
        _vector_store.index_event(event, embedding)
    except Exception:
        # Indexing failures should degrade search quality, not break ingest.
        return


def _backfill_vector_index() -> None:
    if not _embedder or not _vector_store:
        return
    if not _embedder.is_ready() or not _vector_store.is_ready():
        return

    for event in _load_persisted_observed_events():
        _index_stored_event(event)
