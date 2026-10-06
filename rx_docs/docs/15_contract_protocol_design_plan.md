# 15. 계약과 프로토콜 변경 방법

현재 원본은 [공통 계약 v1.0](contracts/v1.0/README.md)과 [셀 운영 v1.0](cell_operations/v1.0/README.md)이다. 선행 계획은 [이전 기록](../references/README.md)에 보존한다.

변경은 해결할 반례·책임 경계·wire 의미·과거 기록 해석·지원 profile에 미치는 영향을 적는다. 규범 byte가 바뀌면 manifest·무결성·platform 사본·solutions SDK를 함께 동기화한다.

문서 revision과 wire semantic version은 다르다. 이번 지원 정책 개정은 enum·메시지·상태전이를 바꾸지 않지만 exact manifest 협상 값은 달라진다. 구버전과 신버전 연결은 자동 허용하지 않고 [migration 영향](contracts/v1.0/revision_2026-09-14.md)을 따른다.

이 주제의 이전 산업 초안은 [고정 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/15_contract_protocol_design_plan.md)에 보존한다.
