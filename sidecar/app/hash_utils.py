from __future__ import annotations

import hashlib
import json

from .schemas import ObservedContextEvent, normalize_for_hash


def compute_context_hash(event: ObservedContextEvent) -> str:
    normalized = normalize_for_hash(event)
    serialized = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def is_context_hash_valid(event: ObservedContextEvent) -> bool:
    return compute_context_hash(event) == event.context_hash
