from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import ObservedContextEvent


VECTOR_TABLE_NAME = "remnis_events"


@dataclass
class VectorStoreStatus:
    ready: bool
    last_error: str | None = None


class LocalVectorStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._db = None
        self._table = None
        self._status = VectorStoreStatus(ready=False, last_error=None)

    def initialize(self) -> None:
        try:
            import lancedb
        except Exception as exc:
            self._status = VectorStoreStatus(
                ready=False,
                last_error=f"dependency_unavailable:{type(exc).__name__}",
            )
            self._db = None
            self._table = None
            return

        try:
            db_path = self._data_dir / "lancedb"
            db_path.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(db_path))
            if VECTOR_TABLE_NAME in self._db.table_names():
                self._table = self._db.open_table(VECTOR_TABLE_NAME)
            else:
                self._table = self._db.create_table(
                    VECTOR_TABLE_NAME,
                    data=[
                        {
                            "id": "bootstrap",
                            "timestamp_utc": "1970-01-01T00:00:00Z",
                            "app_name": "bootstrap",
                            "window_title": "bootstrap",
                            "context_text": "bootstrap",
                            "context_hash": "bootstrap",
                            "source": "bootstrap",
                            "source_version": "event.v1",
                            "embedding": [0.0, 0.0],
                        }
                    ],
                )
                self._table.delete("id = 'bootstrap'")
        except Exception as exc:
            self._status = VectorStoreStatus(
                ready=False,
                last_error=f"initialization_failed:{type(exc).__name__}",
            )
            self._db = None
            self._table = None
            return

        self._status = VectorStoreStatus(ready=True, last_error=None)

    def is_ready(self) -> bool:
        return self._status.ready and self._table is not None

    def last_error(self) -> str | None:
        return self._status.last_error

    def index_event(self, event: ObservedContextEvent, embedding: list[float]) -> None:
        if not self.is_ready():
            raise RuntimeError("vector_store_not_ready")

        row: dict[str, Any] = {
            "id": str(event.id),
            "timestamp_utc": event.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "app_name": event.app_name,
            "window_title": event.window_title,
            "context_text": event.context_text,
            "context_hash": event.context_hash,
            "source": event.source.value,
            "source_version": event.source_version,
            "embedding": embedding,
        }
        self._table.add([row])

    def search_similar(self, embedding: list[float], limit: int) -> list[dict[str, Any]]:
        if not self.is_ready():
            raise RuntimeError("vector_store_not_ready")

        rows = self._table.search(embedding).limit(limit).to_list()
        return [dict(row) for row in rows]
