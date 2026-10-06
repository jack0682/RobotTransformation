# 현재 프로젝트의 핵심 미결

기준일: 2026-09-15. 이 목록은 이전 초안의 한계를 새 목표에 연결한 것이다. [당시 O01–O08 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/implementation/critical_open_items.md)은 보존하며 항목 이름 변경을 해결이나 새 검증으로 표현하지 않는다.

| ID | 미결 | 완료에 필요한 근거 |
|---|---|---|
| O01 | 실제 Authority Provider와 관측·제어권 연결 | 선택한 장비의 실제 source/time/generation/owner, 외부 goal·reload·reboot·종료 반례와 제품 factory 인수. 단순 READY/bool 대입 불가 |
| O02 | 실물 적용 범위·profile·현장 입력 | 장비·물품·공간·교정·신호·완료·지지·개입·보호 책임과 실제 시험. [OPEN-MOBILE-SUPPORT의 N2 판정](../22_open_items_boundary.md#4-open-mobile-support-판정)은 profile 규범만으로 불충분함과 설치 조합·검증 위치를 명시했다. 미결과 NOT_COMMISSIONED는 유지된다. |
| O03 | UNKNOWN 조사·처분과 절차 신뢰 | 원 evidence·actor·서명·CAS, 결과 미해결 처분과 검증된 자원 해제, 실제 procedure admission. [OPEN-RECEIPT의 N2 경계](../22_open_items_boundary.md#5-open-receipt의-기존-구성과-추가-의미)는 기존 기록과 수령 자격·위임·유효성·서비스 결합의 미정 의미를 구분하며 실제 규칙은 만들지 않았다. |
| O04 | 명시적 재개·새 운전 등록·전체 복원 | epoch·grant·원 요청·격리·stop 인계, 부분 실패·재시작·복원 뒤 명시적 새 시작 |
| O05 | 선택 장비의 지원·배포 조합 실증 | model/firmware/controller/SDK/OS/CPU별 source·license·교정·lifecycle·설치·정상 종료 근거. 특정 제조사 전체 지원 의무 없음 |
| O06 | 운영·편집·관리 흐름의 미연결 구간 | 필요한 역할별 end-to-end 경로, 오류·권한·버전 변경, 고주기 stream과 외부 UI의 별도 범위 |
| O07 | 장기 운영·저장·진단·부하·전체 종료 | 지원 기간·Host 수·보존량·장애 모델, 저장 실패·백업/복원·장시간 시험. WAL 및 rollback 검출 한계 포함 |
| N01 | [첫 비산업 인계 서비스](../20_first_handover_case.md) | N1 정의·[N2 경계 판정](../22_open_items_boundary.md)·[N3 문서 반례 검토](../23_handover_counterexamples.md)는 남겼으나 두 open 항목의 해소와 정상·유실·거부·미결의 실행 검증은 남는다. [선언 측정](../21_declaration_reuse_measurement.md)의 재사용 계수도 측정 불가다. N4의 작은 모의 경로는 후속 작업이다. |
| N02 | 여러 운영 영역과 규모 확장 | 신뢰·권한 위임·자원 소유·단절·재연결 계약 및 측정된 성능·장애 범위 |

O01에서 controller active 또는 API 가시성은 명령 소유권의 증거가 아니다. 장비 관측, 명령 배타성, 현지 상태·lifecycle, 물리 보호 책임을 각각 확인한다. qualification 서명 검증과 현지 command ownership도 다른 문제다.

이전 산업 사례의 고객 효과·납품 비용 항목 O08과 구체 현장 신호는 [당시 기록](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/implementation/critical_open_items.md)에 남긴다. 해당 사례를 다시 수행할 때 측정하며 개인 프로젝트 전체의 필수 선행 조건으로 삼지 않는다.

후속 순서는 선택한 사례가 실제로 요구하는 미결을 기준으로 정한다. [로드맵](../00_design_roadmap.md)의 작은 인계 경로가 출발 제안이며 이 표 전체를 한 번에 구현하라는 계획은 아니다.
