from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SnapshotStore:
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, key: str, payload: dict[str, Any]) -> None:
        safe_key = key.replace("/", "_")
        path = self._base_dir / f"{name}_{safe_key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
