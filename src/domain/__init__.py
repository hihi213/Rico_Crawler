from __future__ import annotations  # 타입 힌트에서 전방 참조를 허용한다.

# 서비스/리포지토리 계층에서 도메인 모델을 일관되게 가져오도록 공개 목록을 유지한다.

from .models import (  # 도메인 모델을 한 곳에서 export하기 위해 모은다.
    AttachmentItem,  # 첨부 메타 모델.
    BidNoticeDetail,  # 상세 공고 모델.
    BidNoticeKey,  # 공통 식별자 모델.
    BidNoticeListItem,  # 목록 공고 모델.
    BidOpeningResult,  # 개찰결과 목록 모델.
    BidOpeningSummary,  # 개찰결과 요약 모델.
    CommCd,  # 코드 사전 모델.
)

__all__ = [  # 외부로 노출할 공개 심볼을 명시한다.
    "AttachmentItem",  # 첨부 메타 모델.
    "BidNoticeDetail",  # 상세 공고 모델.
    "BidNoticeKey",  # 공통 식별자 모델.
    "BidNoticeListItem",  # 목록 공고 모델.
    "BidOpeningResult",  # 개찰결과 목록 모델.
    "BidOpeningSummary",  # 개찰결과 요약 모델.
    "CommCd",  # 코드 사전 모델.
]
