from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .retrieval_documents import RetrievalDocument


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
        self._indexed_document_ids: set[str] = set()
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
                if not self._has_expected_schema():
                    self._db.drop_table(VECTOR_TABLE_NAME)
                    self._table = None
                    table_exists = False
            else:
                self._table = None
            self._load_manifest(reset=not table_exists)
            if table_exists and not self._manifest_path.exists():
                self._rebuild_manifest_from_table()
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
        return self._status.ready and self._db is not None

    def last_error(self) -> str | None:
        return self._status.last_error

    def indexed_event_count(self) -> int:
        return len(self._indexed_document_ids)

    def retrieval_document_count(self) -> int:
        return len(self._indexed_document_ids)

    def has_document_id(self, document_id: str) -> bool:
        return document_id in self._indexed_document_ids

    def index_document(self, document: RetrievalDocument, embedding: list[float]) -> bool:
        if not self.is_ready():
            raise RuntimeError("vector_store_not_ready")
        if self.has_document_id(document.id):
            return False

        row = document.to_vector_row(embedding)
        self._add_row(row)
        self._indexed_document_ids.add(document.id)
        self._append_manifest_entry(document.id)
        return True

    def search_similar(self, embedding: list[float], limit: int) -> list[dict[str, Any]]:
        if not self.is_ready() or self._table is None:
            raise RuntimeError("vector_store_not_ready")

        rows = self._table.search(embedding).limit(limit).to_list()
        return [dict(row) for row in rows]

    def _add_row(self, row: dict[str, Any]) -> None:
        if self._db is None:
            raise RuntimeError("vector_store_not_ready")

        embedding = row["embedding"]
        if self._table is None:
            self._table = self._db.create_table(VECTOR_TABLE_NAME, data=[row])
            return

        expected_dimension = self._embedding_dimension()
        actual_dimension = len(embedding)
        if expected_dimension is not None and expected_dimension != actual_dimension:
            if self._table.count_rows() != 0:
                raise RuntimeError(
                    f"embedding_dimension_mismatch:{expected_dimension}:{actual_dimension}"
                )

            self._db.drop_table(VECTOR_TABLE_NAME)
            self._table = self._db.create_table(VECTOR_TABLE_NAME, data=[row])
            self._indexed_context_hashes = set()
            if self._manifest_path.exists():
                self._manifest_path.unlink()
            return

        self._table.add([row])

    def _embedding_dimension(self) -> int | None:
        if self._table is None:
            return None
        try:
            field = self._table.schema.field("embedding")
        except (KeyError, ValueError):
            return None
        return getattr(field.type, "list_size", None)

    def _load_manifest(self, reset: bool) -> None:
        if reset:
            self._indexed_document_ids = set()
            if self._manifest_path.exists():
                self._manifest_path.unlink()
            return

        if not self._manifest_path.exists():
            self._indexed_document_ids = set()
            return

        document_ids: set[str] = set()
        with self._manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                document_id = line.strip()
                if document_id:
                    document_ids.add(document_id)
        self._indexed_document_ids = document_ids

    def _rebuild_manifest_from_table(self) -> None:
        if self._table is None:
            self._indexed_document_ids = set()
            return

        arrow_table = self._table.to_arrow()
        document_ids = {
            str(value)
            for value in arrow_table.column("id").to_pylist()
            if value
        }
        self._indexed_document_ids = document_ids
        if not document_ids:
            return

        with self._manifest_path.open("w", encoding="utf-8") as handle:
            for document_id in sorted(document_ids):
                handle.write(document_id)
                handle.write("\n")

    def _append_manifest_entry(self, document_id: str) -> None:
        with self._manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(document_id)
            handle.write("\n")

    def _has_expected_schema(self) -> bool:
        if self._table is None:
            return False

        field_names = set(self._table.schema.names)
        required_fields = {
            "id",
            "time_start_utc",
            "time_end_utc",
            "app_name",
            "window_title",
            "summary_text",
            "file_path",
            "context_hash",
            "source",
            "source_version",
            "document_version",
            "raw_event_ids_json",
            "embedding",
        }
        return required_fields.issubset(field_names)
