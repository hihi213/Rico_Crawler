from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CrawlCheckpoint:
    current_page: int


class CheckpointStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Optional[CrawlCheckpoint]:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        current_page = int(data.get("current_page", 0))
        if current_page <= 0:
            return None
        return CrawlCheckpoint(current_page=current_page)

    def save(self, checkpoint: CrawlCheckpoint) -> None:
        payload = {"current_page": checkpoint.current_page}
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(self._path)

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
