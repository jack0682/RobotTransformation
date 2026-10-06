# 43 RX 코어 헌장 — 무엇이 코어이고 무엇이 패키지인가

기준일: 2026-09-29. [마스터 플랜](42_framework_master_plan.md) Phase 1의 산출물이다. [개념 명세](44_resident_framework_concept.md)가 의미와 책임을 정하고, 이 문서는 그 의미를 **코드 어디에 두는가**를 정한다. 현재 코어는 새로 만들지 않고 보강한다.

## 1. 코어 판정 기준

아래 중 하나라도 해당하면 코어다. 어느 것에도 해당하지 않고 코어의 포트(계약·API·어댑터 프로토콜)를 통해서만 영향을 주면 패키지다.

| ID | 기준 | 뜻 |
|---|---|---|
| K-a | 바꾸면 기존 증거의 의미가 무효가 된다 | receipt, evidence, 계약 hash, 작업 신원의 해석이 달라지는 코드 |
| K-b | 틀려도 밖에서 관측되지 않는다 | 권한·결과 불명·인계 판정처럼, 오류가 다른 구성요소의 관측으로 드러나지 않는 코드 |
| K-c | 단일 writer 직렬화나 저장 원자성에 참여한다 | 원장 트랜잭션 안에서 상태를 바꾸는 코드 |
| K-d | 규범 필드를 해석한다 | `rx.contract.v1`·`rx.cell.v1`과 선택 binding 계열의 필드 의미를 정하는 코드 |

근거: 사전 연구의 코어 기준("바꾸면 증거가 무효가 되거나, 틀려도 밖에서 관측되지 않는 것", 2026-09-08 제품 구조 방향)과 개념 명세 6절의 판정·기록·집행 책임 표.

**코어의 결과 의무.** 코어에 속하는 코드는 [개념 명세](44_resident_framework_concept.md) CN01–CN22를 지키고, 판단의 근거·규칙·범위를 남기며, 불변식 추적(rx-platform `docs/invariant-traceability.md`)에 연결된다. 패키지는 선언한 능력·조건·미지원 범위를 제공하고 코어의 판정을 우회하지 않는다.

## 2. 저장소와 crate 분류

| 분류 | 대상 | 근거 기준 |
|---|---|---|
| **코어** | rx-platform: `rx-domain`, `rx-ports`, `rx-storage`, `rx-protocol`, `rx-process-contract`, `rx-runtime`(단일 writer), `rx-application`의 generic·변경통제 층 | K-a, K-b, K-c, K-d |
| **코어(장비 관문)** | rx-solutions `runtime/rx-host`의 gate·journal·admission·binding 유지보수. 권한·결과 불명 판정은 여기서 끝난다 | K-b, K-c |
| **코어(호스트 실행 관리)** | rx-solutions `runtime/rx-supervisor`의 등록 원장·실행 요구 적용·실행 관측·복구 처분. 업무 권한을 만들지 않는다(CN17) | K-b, K-c |
| **코어 공개 API** | `rx-api`(HTTP·gRPC ingress), `rx-host-client`(P→Host 전송), `rx-protocol-adapter`, `rx-package`의 검증기·Store. 의미를 바꾸지 않고 코어를 밖에 드러낸다 | K-d(해석은 코어에 위임) |
| **패키지** | 장비 backend(`rx-host` FILE/MELSEC/JTC/DYNAMIXEL/Python), `native/*`, `rx-executor`와 C++ BT 엔진, `rx-process(-package)`의 공정 컴파일·저작, `rx-device-package` 저작 도구, `apps/operator`, `catalogs/`, `deployment/`, supervisor builtin recipe의 내용 | 코어 포트로만 영향 |
| **도구·검사** | 두 저장소의 `tools/`, CI 검사, 클라이언트 라이브러리 생성 | 코어 밖. 다만 규범 사본·SDK 사본 검사는 코어의 무결성 게이트 |

`rx-package`는 두 성격이 섞여 있다. 서명 검증·Store 소유·release manifest 해석은 코어(K-a)이고, 패키지 조립 CLI는 도구다. Phase 3에서 manifest v3를 만들 때 이 경계를 crate 안에서 모듈로 나눈다.

## 3. Engine 안의 세 그룹

`rx-application`의 Engine(약 20k LOC, 모듈 약 60개)은 모두 `impl Engine` 블록이고 `use super::*`를 공유한다. 파일을 옮기지 않고 그룹을 선언한다. 최종 배정은 rx-platform `docs/engine-boundaries.json`(경계 검사의 설정)이 원본이며, 아래는 초안이다.

| 그룹 | 모듈(초안) | 규칙 |
|---|---|---|
| **generic 코어** | admission, access, identity, lifecycle, evidence, delivery, dispatch, reconciliation, invalidation, observation, host_link, host_recovery, host_readmission, host_binding_transition, device_binding, producer, executor_peer, operator_peer, requests, queries, diagnostics, pause, runtime_restrictions, execution_read, settlement | cell·production 모듈을 참조하지 않는다 |
| **cell·production 도메인** | workflow, production, handover, operator_start, assignment, run_configuration, closure, intervention, procedure, checkpoint_change, executor_requests, runtime_skill, configuration, configuration_dispatch, process | generic을 참조할 수 있다. "코어 안의 표준 도메인"으로 두고 봉합선으로 분리한다 |
| **변경 통제·자격** | package_intake, process_review, device_review, process_change, process_apply, process_draft, process_transition, draft_bindings, requalification, qualification_activation | generic을 참조할 수 있다. cell 참조는 봉합선 목록에 올린다 |

**봉합선 작업 순서**(동작 변화 0, 각 단계마다 기존 시험 100%와 저장 스냅샷 바이트 동일)
1. `tools/check_engine_boundaries.py`: 그룹 배정과 현재 위반 목록(allowlist)을 두고 CI에서 검사한다. allowlist는 줄어들기만 한다.
2. `Engine::open`의 cell 무효화 등 generic이 cell로 새는 지점을 `trait CellDomain`으로 추상화한다. 기본 구현은 현재 코드다.
3. `Cell` 구조체(configuration·qualification·blocks·cases)를 serde flatten으로 나눈다. 저장 형식은 그대로다.

## 4. 개념 명세와 코드의 대응

| 개념 명세 책임(6절) | 현재 코드 | 상태 |
|---|---|---|
| 구성요소 등록과 지원 정보 | supervisor `registration.db`(F2·F7), platform 패키지 intake·검토 | [실행 모델 r1](45_resident_framework_execution_model.md): P는 등록·선언, supervisor는 실행 사실을 소유하는 구현 기준안. 등록 이행·통합은 미완 |
| 프로세스 생성·종료·실행 소유 | `rx-solutionsd` supervisor | 코어(호스트 실행 관리) |
| OS 정책 적용 상태 | supervisor F1·F8(RLIMIT_AS) | cgroup v2·장치 접근은 Phase 2 |
| 작업·담당·결과·미결 | Engine generic + cell 도메인 | 코어 |
| 협업 자원·행동 권한 | Engine(fence·grant·permit), `rx-host` gate | 코어 |
| 원본 관측·native 전달 사실 | `rx-host` journal, Engine evidence·observation | 코어 |
| 재시도·업무 재개 | Engine host_recovery·readmission·settlement, device_invalidation | 코어. DeviceRestart는 재link 뒤 재자격으로 해제(rx-platform #48). 재기동 Host의 작업 정산(settlement v2)은 미구현 |
| 변경 적용·절차 재개 | Engine process_change·apply·host_binding_transition | 코어(변경 통제) |
| 최소 관리 기반 기동·복구 | `rx-platformd`·`rx-solutionsd` 기동, 서명 정책 | 코어. 제품 서명 custody 미확립 |

## 5. 기여 문장과 코어의 대응

| 기여([42](42_framework_master_plan.md) §3) | 코어에서 담당하는 곳 |
|---|---|
| C1 반복 통합·운영 개발의 공통화 | 구성요소 선언·등록(Phase 3), 어댑터 프로토콜, gate |
| C2 여러 기능 수행을 하나의 업무 완료로 연결 | Engine 작업 신원·workflow·handover, receipt 구조 |
| C3 실행이 끊겨도 책임을 잇는다 | 단일 writer 원장, 재시작 연속성(H1·rebind), UNKNOWN 보존, settlement |
| C4 운영 중 확장·교체의 통제 | 변경 통제 그룹, Host binding 교체, 재자격 |
| C5 재사용 자산 축적 | 패키지 manifest·서명·Store, SDK 사본 |

## 6. 지키는 것

- 코어 변경은 계약 영향(revision·해시·SDK 사본)과 불변식 추적을 함께 다룬다.
- 패키지가 코어의 판정(권한·UNKNOWN·인계)을 대신하거나 우회하는 코드를 넣지 않는다. 필요하면 코어에 포트를 추가한다.
- "코어 위 패키지"의 실행 코드는 Phase 3의 어댑터 프로토콜(외부 프로세스)과 컴파일 플러그인 경로로만 들어온다. 판정은 Host 게이트에 남는다.
