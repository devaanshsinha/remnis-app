from __future__ import annotations

import json


def parse_raw_event_ids(raw_value: object) -> list[str]:
    if isinstance(raw_value, list):
        return [str(value) for value in raw_value if value]
    if not isinstance(raw_value, str) or not raw_value.strip():
        return []

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(value) for value in parsed if value]
