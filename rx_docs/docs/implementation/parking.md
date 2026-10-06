# 0F 모델·API·CLI 세로 경로의 제외 범위

2026-10-01 최신 사용자 목표에 따른 제외다. WF/RF 장기 목표는 유지한다.

- 듀얼 그리퍼 교환 순서: 단일 그리퍼 경로만 다룬다.
- 버퍼 교환 순서: 이번 경로에 포함하지 않는다.
- 회전 정렬 장비: 이번 경로에 포함하지 않는다.
- 다중 로봇 인계: 한 로봇 경로만 다룬다.
- 범용 규칙 표현 언어: 필요한 유한·타입 있는 계산만 제공한다.
- 캔버스/그래프 UX 개선: 기존 화면을 재사용하며 새 시각 디자인·스타일 작업을 하지 않는다.
- 다중 운영 영역: 이번 경로에 포함하지 않는다.
- 물리 장비: 명시된 SIMULATION profile과 모의 provider만 사용한다.
- BT 자동 생성: 이번 경로에 포함하지 않는다.
- 새 거버넌스 또는 릴리스 정책: 기존 절차를 사용한다.


## M3a–M3c 범위 통제 — 2026-10-03

신규 반례·측정·hardening 제안(사용자 제안 포함)은 M3a/b/c 수락을 현재 막는 근거가 없는 한
이 목록에 보류하고 구현하지 않는다. 기존 첫 관문 실패 수정과 필수 운전/설치 수락은 보류 대상이 아니다.

- 추가 병렬 부하/QoS·freshness 여유 측정: M3a의 handover 수정과 기존 관문을 넘는 측정은 M3c 이후 검토한다.
- dense 2400 반복 benchmark·다른 플랫폼 성능 비교: 이미 기록한 600s 상한 비교를 유지하고 이번 landing 전에 반복하지 않는다.
- 기존 승인 반례를 넘는 공격 변형·보안 강화: 실제 M3a/b/c 차단 근거가 생기기 전까지 보류한다.
- 큰 Run의 paging/index/capacity 일반화: 약속한 checkpoint 실행을 실제로 막는 경우만 최소 수정하고 나머지는 보류한다.


## F0 수락 후 재계획 — 2026-10-03

- dense/my-tray 슬롯 z=0.0 vs surface_height 900/850 불일치, 정합 제약 미적용. 사용자가 보류 기록을 요청했으며 이번 F1′ 계획 작성에서 데이터나 계산식을 수정하지 않는다.
- F1′에서 확인한 Cargo 캐시/복사 파일 mtime 불일치의 다른 Docker 빌드 경로 전수 점검: 체크포인트 1에 쓰는 RuntimeSkillValidation 경로만 수정하며, 그 밖의 빌드·캐시 강화는 별도 후속 작업으로 보류한다.
- amd64 에뮬레이션 111–114ms 관측

## F2′ CP1 범위 결정 — 2026-10-04

- held/UNKNOWN operation의 adapter hot replacement·migration: F2′에서는 선택된 package 교체를 거절하고 동일 digest의 passive restart만 기존 증거·custody 검증으로 다룬다.
- SIM unclamp의 fresh support observation 부재: 현재는 같은 Part acquire-support의 SETTLED/SUCCEEDED 순서만 사용한다. Registry가 동작한 뒤 gripper support를 registry-declared observation으로 제공하고 unclamp를 그 관측으로 gate한다. Python Host에 같은 관측 기능을 중복 구현하지 않는다.
- F3′ 저작 근거: 외부 package의 저수준 API/서명 policy/qualification 문서 조립과 심볼릭 링크 보존·CLI 호출 pacing에 수동 마찰이 있었다. CP2의 22파일/1296행과 기록된 725 leaf 호출(반복 설치 포함)을 개선 비교 대상으로 보존하며 지금 F3′ 도구를 시작하지 않는다.
