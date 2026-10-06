# Host 재수용과 연구 host-rejoin 비교 — 흡수·폐기 판정

기준일: 2026-09-29. [마스터 플랜](../42_framework_master_plan.md) Phase 0.4의 선행 문서다.

- **기준 설계**: develop에 들어간 Host 재수용이다. rx-platform `crates/rx-application/src/engine/host_readmission.rs`, `POST /api/v1/hosts/readmission`, [Host binding 재수용 기록](../host_binding_admission.md)이 여기에 해당한다.
- **비교 대상**: 저장소 밖 연구 worktree에서 커밋 없이 진행된 host-rejoin 후보 v1이다. 지금은 WIP 스냅샷 커밋과 로컬 bundle로 보존되어 있다.

이 문서는 코드와 명세를 읽고 비교한 결과다. 빌드나 시험을 실행해 확인한 판정이 아니다.

## 1. 의미별 비교

| 의미 | develop 재수용 | 연구 host-rejoin | 판정 |
|---|---|---|---|
| 진입 | 재수용 요청 한 번(**재시작한 Host**, 다른 boot만) | context → proposal → 승인 → 진행 → 조회 → 정산 → rebind 다단계 | 재시작한 Host는 이미 있음. 다단계 API 형태는 폐기 |
| **P만 재시작하고 Host는 유지된 경우의 운영 rebind** | **없음.** 같은 boot의 새 producer 세션을 link 준비가 거절하고(`engine/host_link.rs`), 재수용은 다른 boot만 다루며(`covers`), Host 복구 흐름은 recovery-only에서 끝난다 | 새 grant와 등록·baseline 교체로 운영 등록을 되찾는 rebind | **없음 → 흡수(재설계).** 2026-09-29 정정(§5) |
| 승인 주체 | 등록 terminal의 ReleaseManager가 Host의 모든 등록 셀을 포함해야 함 | 같은 역할이 cohort 전체를 포함해야 함 | 이미 있음 |
| 신원·세대·저널 연속성 | 같은 이전 boot·delivery journal·session. evidence journal 일치. 새 boot는 이전 boot와 달라야 함. link 준비 시 실제 snapshot 대조 | Runtime·인증 바인딩·구성·epoch·scope·baseline·transport pin 비교. 새 read로 fence 카운터·구성 적용 증명 확인 | 부분. 인증 바인딩 불변과 fence 카운터 대조는 후속 보강 후보 |
| 복원 범위 | 등록 교체만 함. grant·Arm·자격·permit·Run은 복원하지 않고 block 유지 | RECOVERY_ONLY fence 뒤 rebind에서 새 grant. 생산 허가 없음 | 이미 있음 |
| 무효화 origin 기록 | 없음. DeviceRestart block에 출처 기록 없음 | 변경 불가 origin 기록 | **없음 → 흡수.** 구현(2026-09-30, rx-platform #48, §2) |
| 제안 수명·TTL | TTL 없음. 모든 셀이 다시 연결될 때까지 유효. Host당 하나 | proposal 30초, 승인 실행 30초 | 설계 차이. 폐기. 오래 방치된 승인의 만료는 별도 과제 |
| 실행 중 작업 | 실행 중 Run·미해결 작업이 있으면 승인 거절 | 활성 Run·mandate·permit이 있으면 blocker | 이미 있음 |
| binding 변경과의 관계 | 재수용이 staged 변경의 binding intent를 받아 commit 전후 세대 규칙 적용 | 별도 rebind 구성 origin 체인(최대 64) | 다른 방식으로 있음. 체인은 폐기(구성 증명 이원화 방지) |
| grant 획득 | 정상 link commit이 새 grant 검증 | 정상 link 거절을 유지하고 별도 grant 래퍼 사용 | 재시작한 Host에서는 충돌. 유지된 Host의 rebind에서는 흡수 설계 시 하나의 link 경로로 통합 |
| 결과를 아는 작업의 정산 | 없음. 재수용이 Quarantined·RecoveryRequired를 정산하지 않음 | 작업별 receipt·native evidence 기준으로 교체된 boot에서 정산 | **없음 → 재설계해 흡수** |
| DeviceRestart 해제 | **해제 경로 없음**(아래 §2) | review에 묶인 해제 | **없음 → 재설계해 흡수.** 구현(2026-09-30, #48): 재link 뒤 재자격 선택으로 해제 |

## 2. 확인된 코어 공백 — DeviceRestart block

develop에서 DeviceRestart block은 두 곳에서 생긴다.
- producer 교체: rx-platform `engine/producer.rs`
- 관측 무효화: `engine/observation.rs`

그런데 이 block을 해제하는 경로가 없다. 재자격은 새로 생긴 block과 Runtime 재시작 제한만 해제하고, 기존 block은 유지한다(`engine/requalification.rs`의 block 필터). 따라서 Host가 재시작되면 재수용을 해도 해당 셀은 계속 사용할 수 없는 상태로 남는다.

rx-platform `crates/rx-api/HOST_READMISSION.md`에는 "별도 재개·재자격까지 사용 불가"라고 적혀 있다. 하지만 그 재개 경로가 실제로 있는 것처럼 읽힌다. 이 문장은 이 공백이 해소될 때 함께 고친다.

**해소(2026-09-30, rx-platform #48)** — 상세는 rx-platform `crates/rx-application/DEVICE_INVALIDATION_ORIGIN.md`.

무효화 트랜잭션이 셀마다 변경 불가 origin을 기록한다. origin에 담기는 것은 다음과 같다.
- 원인: producer 교체 또는 source generation 변경. 교체된 세대를 함께 적는다.
- 등록 셀과 무효화 직후 그 셀의 epoch. 공유 scope·자원으로 함께 막힌 이웃 셀은 Host의 등록 셀을 가리킨다.

해제는 재자격 요청이 block을 origin digest로 명시 선택할 때만 한다(요청 v3). 소유권은 Begin에서 묶고, block을 지우는 것은 활성화 시점뿐이다.

해제 전제조건은 **재link**다. Host의 현재 bound link가 기록된 epoch 이후에 확정되어야 하고, 등록이 그 link의 세대여야 한다. 여기에 원인별 진전 조건이 붙는다.

등록의 epoch는 비교하지 않는다. 같은 세대 안에서 fence 확인이 등록 epoch를 올리기 때문이다. 초안은 등록 epoch와 generation을 비교했는데, generation이 그대로인 손실에서는 fence 확인만으로 조건이 충족되는 허점이 있었다. 이 허점은 시험으로 막았다.

이 변경 이전에 생긴 block은 origin이 없으므로 여전히 해제 경로가 없다. `HOST_READMISSION.md`도 이에 맞춰 고쳤다. 실제 Host 이미지 실행과 이웃 셀의 끝까지 해제는 시험하지 않았다.

## 3. 판정과 배치

| 항목 | 판정 | 배치 |
|---|---|---|
| executor 교체 시 자격 batch를 같은 트랜잭션에서 중지하고 제한 소유권을 기록(버그 수정) | 흡수 | Phase 0.4 |
| program-inputs 정책 primitive. admission·Host 구성·자격 연결은 미구현으로 명시 | 흡수 | Phase 0.4 |
| settlement v1: 유지된 Host에서 결과를 아는 작업을 명시 승인으로 정산. host-rejoin 참조 필드 제거. 후보 계약: [settlement v1](../contracts/settlement/v1/README.md) | 흡수 | Phase 0.4 |
| Host 무효화 origin 기록. 재수용 기록과 교차 참조하도록 확장 | 흡수 | Phase 2 코어 보강 — **구현(#48)** |
| DeviceRestart 해제. origin·재수용 기록·link receipt 기준으로 재작성 | 흡수(재설계) | Phase 2 코어 보강 — **구현(#48)**, bound link 기준 |
| observation-only binding(P와 Host). commit 경로에도 제어 거절 가드 추가 | 흡수 | Phase 2 코어 보강 |
| settlement v2: 재기동 Host의 결과를 아는 작업. 재수용 뒤 fresh read와 receipt 기준 | 흡수(재설계) | Phase 2 코어 보강 |
| 유지된 Host의 운영 rebind(새 grant, 등록·baseline 교체). 기존 Host 복구 승인과 재수용 기록 모델에 맞춰 재설계 | 흡수(재설계) — **2026-09-29 정정** | Phase 2 코어 보강(우선) |
| host-rejoin의 별도 context·proposal·승인 엔드포인트 형태, rebind 구성 origin 체인, 전용 recovery transport | 폐기(rebind 의미는 위 행으로 흡수) | — |
| 계약 README 네 개 | 각 흡수 항목과 함께 현재 코드 기준으로 새로 작성 | 각 단계 |

**폐기 이유**
- 재수용과 host-rejoin이 권한·연속성 판단을 두 경로로 나누게 된다.
- 정상 link 거절 정책이 develop과 모순된다.
- 연결 계층과 link 준비 코드의 충돌 비용이 크다.

폐기한 원본은 로컬 bundle에 남아 있어 필요할 때 참고할 수 있다.

## 4. 계약 영향

observation-only binding은 Host 로컬 설치 입력의 형식과 Rust API를 바꾼다. 하지만 기본 계약 `rx.contract.v1`·`rx.cell.v1`의 wire와 manifest는 바꾸지 않는다. 유효한 기존 binding의 digest도 그대로다.

따라서 [마스터 플랜](../42_framework_master_plan.md)의 "호환성이 깨지는 계약 변경은 v1.1 revision"에는 해당하지 않는다. 대신 host-configuration 선택 binding 계열의 revision과 호환성 시험으로 다룬다. 구버전 Host·P는 새 형식을 모르는 필드로 거절한다(fail-closed).

## 5. 정정 — 유지된 Host의 운영 rebind (2026-09-29)

§1과 §3의 첫 판정은 host-rejoin의 rebind를 재수용과 같은 경우로 보고 폐기했다. 이는 틀렸다. 재수용은 **Host가 재시작한 경우**(다른 boot)만 다룬다. rebind는 **P만 재시작하고 Host는 그대로인 경우**를 다룬다.

develop에서 P만 재시작하면 다음과 같이 된다.
- Host는 새 producer 세션으로 증거 통신을 이어 간다. 그러나 운영 HostRegistration은 옛 세션에 묶인 채 남는다(rx-platform `PRODUCER_RUNTIME_RECONNECT.md`).
- link 준비는 같은 boot의 다른 세션을 `ContinuityUnproven`으로 거절한다.
- 결과적으로 셀은 운영 link를 되찾지 못한다.

실제 이미지 실행에서 확인했다. 재시작 인수 A안 뒤 인수는 수락됐지만, Host 운영 context가 `IDENTITY_UNAVAILABLE`에 머물렀다([기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/p_restart_adoption_2026-09-29/README.md)).

이 rebind는 Phase 2에서 기존 Host 복구 승인(context → proposal → approve)과 재수용 기록을 기준으로 재설계해 흡수한다. link 경로는 하나로 유지한다.

구현(2026-09-29): 별도 rebind API 대신 **재수용 승인이 세션이 만료된 같은 boot도 교체**하도록 넓혔다. 이전 runtime의 grant가 끝나야 link되며, 승인 소비 시 Run·work 조건을 다시 검사한다. 실제 이미지 3회 연속 통과([기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/p_restart_rebind_2026-09-29/README.md)).
