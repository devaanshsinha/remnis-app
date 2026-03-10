from __future__ import annotations

from dataclasses import dataclass


DEFAULT_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass
class EmbedderStatus:
    ready: bool
    model_name: str
    last_error: str | None = None


class LocalEmbedder:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None
        self._status = EmbedderStatus(ready=False, model_name=model_name, last_error=None)

    def initialize(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            self._status = EmbedderStatus(
                ready=False,
                model_name=self._model_name,
                last_error=f"dependency_unavailable:{type(exc).__name__}",
            )
            self._model = None
            return

        try:
            self._model = SentenceTransformer(self._model_name)
        except Exception as exc:
            self._status = EmbedderStatus(
                ready=False,
                model_name=self._model_name,
                last_error=f"initialization_failed:{type(exc).__name__}",
            )
            self._model = None
            return

        self._status = EmbedderStatus(ready=True, model_name=self._model_name, last_error=None)

    def is_ready(self) -> bool:
        return self._status.ready and self._model is not None

    def last_error(self) -> str | None:
        return self._status.last_error

    def model_name(self) -> str:
        return self._status.model_name

    def encode_text(self, text: str) -> list[float]:
        if not self.is_ready():
            raise RuntimeError("embedder_not_ready")

        vector = self._model.encode(text, normalize_embeddings=True)
        return [float(value) for value in vector.tolist()]
