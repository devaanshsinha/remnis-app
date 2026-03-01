from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventSource(str, Enum):
    ACTIVE_WINDOW = "observer.active_window"
    ACCESSIBILITY_TEXT = "observer.accessibility_text"


class ObservedContextEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    timestamp_utc: datetime
    app_name: str = Field(min_length=1)
    window_title: str = Field(min_length=1)
    file_path: str | None = None
    context_text: str = Field(min_length=1)
    source: EventSource
    capture_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_version: str = Field(pattern=r"^event\.v1$")

    @field_validator("timestamp_utc")
    @classmethod
    def _validate_timestamp_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp_utc must include timezone")
        return value.astimezone(timezone.utc)


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: ObservedContextEvent


class DedupeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_duplicate: bool
    reason: str | None = None


class DebounceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_debounced: bool
    reason: str | None = None


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    event_id: UUID
    dedupe: DedupeDecision
    debounce: DebounceDecision


class HealthReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observer_ready: bool
    db_ready: bool
    embedder_ready: bool


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    service: str
    version: str
    time_utc: str
    readiness: HealthReadiness


def normalize_for_hash(event: ObservedContextEvent) -> dict[str, Any]:
    return {
        "app_name": " ".join(event.app_name.strip().lower().split()),
        "window_title": " ".join(event.window_title.strip().split()),
        "file_path": (event.file_path or "").strip(),
        "context_text": " ".join(event.context_text.strip().split()),
    }
