# 현재 요구와 검증 경계

이전 산업 초안의 R01–R30은 [원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/implementation/requirements.md)에 보존한다. 당시 PARTIAL26·OPEN3·FIELD_BLOCKED1은 그 요구·commit 범위의 판정이다. 새 개인 프로젝트 요구에 같은 ID나 통과 판정을 재사용하지 않는다.

| 요구 | 원본 | 현재 상태 |
|---|---|---|
| PG01–PG06 개인 프로젝트·이기종·전체 작업·규모 확장 | [프로젝트 정의](../01_product_definition.md) | 사용자 목표 확정, 서비스·규모 구현/실증 미완료 |
| PG07 RX Client Libraries와 ROBOTIS 다섯 프로젝트의 기본 전체 개발 번들 | [프로젝트 정의](../01_product_definition.md), [strict wire와 클라이언트](../40_strict_wire_and_clients.md), [DYNAMIXEL Ping](../41_dynamixel_ping_adapter.md) | 사용자 요구 확정(2026-09-25), G5.1 클라이언트·G5.2 모의 Ping까지. 번들 완결·실물 연결 미완료 |
| 공통 작업 의미·권한·기록·인계 | [공통 계약](../contracts/v1.0/README.md) | v1.0 문서 개정, 기존 구현의 범위는 인계와 개별 검증 근거 참조 |
| 설치 범위·조건·허가·개입·복구 | [셀 운영 계약](../cell_operations/v1.0/README.md) | 문서 규범, 실물 설치 NOT_COMMISSIONED |
| 제조사 중립 지원·선택 의존성 | [지원 정책](../13_device_support_matrix.md) | 현재 요구, 새 구성 검증은 별도 결과 필요 |
| door-to-door 참조 인계 | [범위](../03_product_scope.md) | 제안, 실제 장비·최종 완료 조건 미정 |
| 분산 운영 영역·도시 규모 | [후속 방향](../00_design_roadmap.md) | 설계·성능 요구·실증 미완료 |

진행 완료를 문서 존재나 시험 개수로 판단하지 않는다. 현재 구현의 구체적 미결은 [미결 목록](critical_open_items.md)에 남긴다.
