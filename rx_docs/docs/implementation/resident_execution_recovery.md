# 상주 실행의 정산과 운영 복귀

2026-10-01. RF02·RF07·RF08을 이어가는 R7 작업 기록이다. 전체 목표는
[완료 원장](resident_framework_completion.md)과 [실행 모델](../45_resident_framework_execution_model.md)의 장애·복구 요구를 유지한다.
이 문서의 목표 흐름은 구현 완료 선언이 아니다.

## 현재 막히는 지점

R6는 종료한 원 프로세스와 미전송 종료 기록을 보존하지만 P/S가 새 세션으로 재시작하면
이전 grant.peer와 새 인증 peer가 다르므로 원 Observe를 재전달할 수 없다. 이 거절은 유지해야 한다.
과거 요청을 새 실행 보고로 바꾸면 원 요청의 결과와 새 관측의 출처가 섞인다.

기존 S의 `registration/recovery.rs`에는 scoped process identity 조사, 별도 처분,
새 run을 지정한 명시적 resume 및 소비 기록이 있다. 그러나 로컬 resume는 P로 이행한 원장에서
거절되며, P의 새 실행도 미해결 로컬 기록이 있으면 거절된다. 두 거절을 단순히 제거하지 않고
중앙의 승인과 원본의 실제 근거를 연결해야 한다.

## 필요한 전체 흐름

1. 현재 인증된 S가 원 assignment/grant/instance, 원 registry·이관 cut, 실제 내용과 로컬 기록을 대조한다.
2. source는 과거 결과와 현재 종료·잔여 의무 관측을 나눠 제시한다. 불명인 과거 업무 결과를 성공으로 고치지 않는다.
3. P 소유자는 원 요청·원 배정·현재 source 신원·정확한 근거 revision에 묶인 정산 후보를 검토한다.
4. 수용 시 현재 권한·근거·원 start 차단·모든 선택의 의무를 재확인하고 별도 처분을 원자적으로 기록한다.
5. source는 인증된 P의 수용을 원 요청으로 확인한다. 응답 유실은 원 결과 조회로 복구한다.
6. 새 run/instance의 명시적 배정과 실제 로컬 복구 조건을 함께 만족한 경우에만 새 실행을 시작한다.

정산은 시작·중지·프로세스 채택 명령이 아니다. 살아 있는 원 자식은 소유 가능한 기존 관리 경로의 책임이며,
PID로 새 관리자를 붙이지 않는다. 전체 DB 복원이나 다른 boot/namespace를 현재 근거로 오인하지 않는다.

## 첫 구현: 실제 source 조사

현재 작업 브랜치는 `platform-investigate` 명령을 연결한다. 기존 인증 Inspect로 P의 원 배정을 받고,
서명된 설치 카탈로그에서 원 plan을 다시 구성한다. 원 grant/preparation, catalog, registry 소유,
원 consumption/execution 쌍과 실제 supervisor journal을 대조한다. 두 실제 저장소의 잠금을 확보하고
관리자를 다시 열지 않아 원 Running 기록을 Unknown으로 덮어쓰지 않는다.

| 원본과 현재 근거 | 조사 결과 | 아직 확정하지 않는 것 |
|---|---|---|
| registry와 supervisor가 같은 자식 종료를 기록 | 원 direct-child 종료 기록 | 후손 프로세스·장비·자원 인계·업무 완료 |
| 두 기록이 같은 미시작을 기록 | 원 미시작 기록 | 새 실행 허가 |
| 실제 원 저장소의 미소비와 시작 전 journal, 원 start window 종료 | 미소비·시작 전 기록 | source rollback 탐지나 새 배정 허가 |
| 원 생성 신원과 현재 Linux 관측 일치 | 원 프로세스 존재 | 소유권 채택·임의 종료 |
| 기존 scoped 조사로 원 프로세스가 더 이상 실행 중이지 않음 | 별도 현재 조사 결과 | 과거 수행 결과의 재작성·잔여 의무 해제 |
| birth 누락·관측 불일치·지원 범위 밖 | 확인 불가 또는 요청 거절 | timeout/PID 부재에 의한 종료 추정 |

DHI/외부 supervisor의 잔여 정지 의무는 기존 판정 함수를 재사용한다. 프로세스의 외부 효과 등급과
guarded 종료 미확인도 결과에 보존한다. 새 JSON 출력은 진단 자료이며 다시 역직렬화해 권한으로 사용할 수 없다.
이번 단계는 wire·공유 DTO·저장 schema를 변경하지 않는다. 새 P 승인·수용 계약은 후속 개정에서 다룬다.

## 수락·반례 행렬과 미완

| 경우 | 요구되는 관찰 | 상태 |
|---|---|---|
| 종료 후 보고 응답 유실/통신 단절 | 원 기록 조회, outbox key/body·P 결과 보존 | 실제 Linux source 조사 통과 |
| 관리자 강제 종료, 원 자식은 생존 | 실제 birth 조사로 존재 표시, 채택/종료/새 실행 없음 | 실제 Linux 별도 장면 통과 |
| 원 내용·registry·instance·소비 신원 변경 | 거절, 원 이력 보존 | 대상 시험 통과 |
| birth가 없음 | 확인 불가 유지 | 대상 시험 통과 |
| P/S 재시작 뒤 원 정산 응답 유실 | 현재 권한으로 원 receipt 조회, 중복 처분 없음 | P/source 수용 연결 미완 |
| 원 결과 불명이나 현재 소프트웨어 종료가 확인됨 | 원 Unknown 보존, 별도 처분·새 승인·새 run 실제 실행 | 미완 |
| 다중 선택 일부만 종료·일부 residual/unknown | 전체 의무 보존, 확인된 부분과 미확인 부분 분리 | 전체 복귀 미완 |
| 생성 진입 직후 source 사망, birth 기록 없음 | 실행 미발생으로 추정하지 않고 조사/봉쇄 경로 제공 | 운영 복구 근거 미완 |
| boot/namespace 변경·저장 복원·권한 철회 | 기존 사실/허가 재사용 금지, 명시적 이행·재확인 | 전체 RF07/RF08 미완 |

source 조사만으로 R7·RF02·RF07을 완료하지 않는다. 다음 변경은 **원 근거를 P의 별도 정산 처분으로
연결하고 같은 설치에서 새 승인 실행이 실제로 가능한지 검증하는 것**이다. 다른 자원·기능 의존·업무·확장·
설치·현장 게이트도 완료 원장에 계속 남긴다.

[현재 실행 근거](../../references/resident_recovery_source_2026-10-01/README.md)는 깨끗한 소스에서 수행한
정상 종료·통신 단절·관리자 상실의 Linux 장면과 로컬 검사를 담는다. 관련 코드 PR은
[Platform #69](https://github.com/jack0682/rx-platform/pull/69),
[Solutions #78](https://github.com/jack0682/rx-solutions/pull/78)이다. 문서 #86 → P #69 → S #78 순서로
필수 CI·DCO를 확인해 develop에 통합했다. [통합 기록](../../references/resident_recovery_source_2026-10-01/integration.json)은
시험/병합 트리 동일성·서명·DCO·SDK 130개 일치를 담는다. Linux CI는 P 530/0/22, S 475/0/22
(passed/failed/ignored)이고 S amd64·arm64 설치 검사도 통과했다. 정산 승인·원 처분·새 실행의 연결은 여전히 미완이다.
