from __future__ import annotations

import json
from dataclasses import dataclass

from .schemas import ObservedContextEvent


RETRIEVAL_DOCUMENT_VERSION = "retrieval_doc.v1"


@dataclass(frozen=True)
class RetrievalDocument:
    id: str
    time_start_utc: str
    time_end_utc: str
    app_name: str
    window_title: str
    summary_text: str
    file_path: str | None
    context_hash: str
    source: str
    source_version: str
    document_version: str
    raw_event_ids: list[str]

    def embedding_text(self) -> str:
        return self.summary_text

    def to_vector_row(self, embedding: list[float]) -> dict[str, object]:
        return {
            "id": self.id,
            "time_start_utc": self.time_start_utc,
            "time_end_utc": self.time_end_utc,
            "app_name": self.app_name,
            "window_title": self.window_title,
            "summary_text": self.summary_text,
            "file_path": self.file_path,
            "context_hash": self.context_hash,
            "source": self.source,
            "source_version": self.source_version,
            "document_version": self.document_version,
            "raw_event_ids_json": json.dumps(self.raw_event_ids),
            "embedding": embedding,
        }


def build_retrieval_document(event: ObservedContextEvent) -> RetrievalDocument:
    timestamp_utc = event.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    return RetrievalDocument(
        id=str(event.id),
        time_start_utc=timestamp_utc,
        time_end_utc=timestamp_utc,
        app_name=event.app_name,
        window_title=event.window_title,
        summary_text=event.context_text,
        file_path=event.file_path,
        context_hash=event.context_hash,
        source=event.source.value,
        source_version=event.source_version,
        document_version=RETRIEVAL_DOCUMENT_VERSION,
        raw_event_ids=[str(event.id)],
    )
