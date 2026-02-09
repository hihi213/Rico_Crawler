from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import json  # JSON 직렬화.
from pathlib import Path  # 경로 처리.
from typing import Any  # 범용 타입.


class SnapshotStore:  # 원본 응답 스냅샷 저장.
    def __init__(self, base_dir: str) -> None:  # 저장 디렉터리 주입.
        self._base_dir = Path(base_dir)  # 경로 객체화.
        self._base_dir.mkdir(parents=True, exist_ok=True)  # 디렉터리 생성.

    def save(self, name: str, key: str, payload: dict[str, Any]) -> None:  # 스냅샷 저장.
        safe_key = key.replace("/", "_")  # 파일명 안전 처리.
        path = self._base_dir / f"{name}_{safe_key}.json"  # 파일 경로 구성.
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")  # JSON 저장.
