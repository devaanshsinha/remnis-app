from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import ObservedContextEvent


VECTOR_TABLE_NAME = "remnis_events"
INDEX_MANIFEST_NAME = "vector_index_manifest.jsonl"


@dataclass
class VectorStoreStatus:
    ready: bool
    last_error: str | None = None


class LocalVectorStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._db = None
        self._table = None
        self._manifest_path = data_dir / INDEX_MANIFEST_NAME
        self._indexed_context_hashes: set[str] = set()
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
            table_exists = VECTOR_TABLE_NAME in self._db.table_names()
            if table_exists:
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
                            "file_path": None,
                            "context_text": "bootstrap",
                            "context_hash": "bootstrap",
                            "source": "bootstrap",
                            "source_version": "event.v1",
                            "embedding": [0.0, 0.0],
                        }
                    ],
                )
                self._table.delete("id = 'bootstrap'")
            self._load_manifest(reset=not table_exists)
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

    def indexed_event_count(self) -> int:
        return len(self._indexed_context_hashes)

    def has_context_hash(self, context_hash: str) -> bool:
        return context_hash in self._indexed_context_hashes

    def index_event(self, event: ObservedContextEvent, embedding: list[float]) -> bool:
        if not self.is_ready():
            raise RuntimeError("vector_store_not_ready")
        if self.has_context_hash(event.context_hash):
            return False

        row: dict[str, Any] = {
            "id": str(event.id),
            "timestamp_utc": event.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "app_name": event.app_name,
            "window_title": event.window_title,
            "file_path": event.file_path,
            "context_text": event.context_text,
            "context_hash": event.context_hash,
            "source": event.source.value,
            "source_version": event.source_version,
            "embedding": embedding,
        }
        self._table.add([row])
        self._indexed_context_hashes.add(event.context_hash)
        self._append_manifest_entry(event.context_hash)
        return True

    def search_similar(self, embedding: list[float], limit: int) -> list[dict[str, Any]]:
        if not self.is_ready():
            raise RuntimeError("vector_store_not_ready")

        rows = self._table.search(embedding).limit(limit).to_list()
        return [dict(row) for row in rows]

    def _load_manifest(self, reset: bool) -> None:
        if reset:
            self._indexed_context_hashes = set()
            if self._manifest_path.exists():
                self._manifest_path.unlink()
            return

        if not self._manifest_path.exists():
            self._indexed_context_hashes = set()
            return

        hashes: set[str] = set()
        with self._manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                context_hash = line.strip()
                if context_hash:
                    hashes.add(context_hash)
        self._indexed_context_hashes = hashes

    def _append_manifest_entry(self, context_hash: str) -> None:
        with self._manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(context_hash)
            handle.write("\n")
