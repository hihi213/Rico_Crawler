from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import json  # 체크포인트 직렬화.
from dataclasses import dataclass  # 간단한 데이터 컨테이너.
from pathlib import Path  # 경로 처리.
from typing import Optional  # 선택적 타입 표현.


@dataclass
class CrawlCheckpoint:  # 체크포인트 모델.
    current_page: int  # 마지막 저장 페이지(1-based).


class CheckpointStore:  # 체크포인트 저장/로드.
    def __init__(self, path: str) -> None:  # 경로 주입.
        self._path = Path(path)  # 경로 객체화.
        self._path.parent.mkdir(parents=True, exist_ok=True)  # 디렉터리 생성.

    def load(self) -> Optional[CrawlCheckpoint]:  # 체크포인트 로드.
        if not self._path.exists():  # 파일 없으면.
            return None  # 미존재 처리.
        data = json.loads(self._path.read_text(encoding="utf-8"))  # JSON 로드.
        current_page = int(data.get("current_page", 0))  # 페이지 추출.
        if current_page <= 0:  # 유효하지 않으면.
            return None  # 무시.
        return CrawlCheckpoint(current_page=current_page)  # 체크포인트 반환.

    def save(self, checkpoint: CrawlCheckpoint) -> None:  # 체크포인트 저장.
        payload = {"current_page": checkpoint.current_page}  # 저장 페이로드.
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")  # 임시 파일.
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")  # 임시 저장.
        tmp_path.replace(self._path)  # 원자적 교체.
