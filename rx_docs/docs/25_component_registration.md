# F2 등록 신원이 실행보다 오래 산다

2026-09-23 · **지원 범위: 단일 호스트의 비구동 구성요소 등록과 실행 대조. 명시적 복구 처분·업무 사용 허용은 미지원.**

이 문서는 F2의 구현·실행 범위를 기록한다. 후속 [F3 명시적 복구 처분](26_explicit_recovery_disposition.md)은 소유 Child 핸들이 남은 비구동 실행에 한해 별도 처분과 명시적 새 실행을 추가한다. 전체 핸들 상실 이후의 외부 조사와 업무 사용 허가는 여전히 미지원이다.

## 목적과 배치

[F1](24_host_execution_requirements.md)은 실행 요구를 선언하고 거절할 수 있게 했다. F2는 실행이 없을 때도 조회되는 등록을 만들고, 실행 종료·상실·관리 재시작 뒤에도 그 신원·선언·이력을 유지한다. 참조 기능은 기존 `rx/status-http`다. 등록→F1 수락→실행 관측→종료→재시작 뒤 대조를 연결한다. 명시적 복구까지 포함한 M1 전체가 완료됐다는 뜻은 아니다.

`rx-supervisor` 라이브러리의 `registration` 모듈은 공유 `Repository` 포트 위에서 독립 저장소를 소유한다. 등록 키는 `components/registration/<UUID>`이며 plan, 실행 인스턴스, PID, 포트를 포함하지 않는다. 등록 모듈은 `Supervisor`, `Plan`, `State`에 의존하지 않는다. `registered` 연결부가 등록부와 기존 Supervisor/Backend를 함께 사용한다. 현재 연결부는 supervisor 저장소 하나당 비구동 구성요소 하나를 지원한다. 기존 무등록 실행 경로와 물리 권한 경로는 그대로다.

**이 배치는 첫 통과선을 위한 것이며 구성요소 관리 책임의 최종 소유를 확정하지 않는다.** 소비자가 하나인 시점에 크레이트나 서비스를 늘리지 않았다. 이후 platform으로 이주할 때도 등록 신원·이력·호환 경계를 보존해야 한다.

기존 플랫폼에는 Cell·Host 세션·grant에 결속된 `HostRegistration`이 있다. 이를 없다고 주장하거나 일반 구성요소 등록과 같은 것으로 취급하지 않는다. F2의 대상은 실행·Cell이 없어도 지속되는 별도 구성요소 등록이다.

## 등록의 의미와 변경

| 항목 | 의미 |
|---|---|
| 등록 UUID | 지속되는 관리 신원. 같은 표시 이름으로 별도 등록을 만들어도 신원은 다름 |
| declaration.label | 사람이 구별할 표시 이름. 실행 소유 근거가 아님 |
| declaration.catalog.program / digest | 수용한 작성자 Program의 ID와 전체 직렬화 digest. F1 요구의 편집 가능한 사본을 저장하지 않음 |
| revision | 선언 변경·폐기의 CAS 기준. 실행 관측 갱신과 별도 |
| ACCEPTED | 등록 내용 수용. 실행 허가·기능 준비·업무 허가가 아님 |
| RETIRED | 새 실행 배정 제한. 과거 기록 삭제나 현재 실행의 강제 종료가 아님 |

`put(expected_revision)`과 `append_control`을 같은 트랜잭션에서 실행해 변경, 제어 이벤트, 현재 투영을 함께 커밋한다. 경쟁 갱신은 revision conflict로 거절한다. 폐기는 삭제 API가 아닌 상태 전이다. 폐기 후 재활성화·선언 덮어쓰기는 지원하지 않는다. 과거 실행·미결·이력은 계속 조회한다. 이력 조회는 128개짜리 공유 포트 페이지를 끝까지 읽는다.

등록 API는 신뢰된 로컬 통합 호출이다. 새로운 네트워크 인증·관리자 권한 체계를 제공하지 않는다. 처음부터 악의적인 catalog를 만들거나 저장소를 수정하는 관리자를 차단하는 sandbox도 아니다. 실행 시 실제 catalog digest가 등록에서 수용한 digest와 다르면 자동 해석하지 않고 명시적 선언 검토를 요구한다. 이미 배정된 실행에는 당시 등록 revision과 catalog 참조가 남는다.

## 실행 연결과 실패 경계

실행 연결은 독립 등록 저장소와 기존 supervisor 저장소를 사용한다. 두 SQLite 저장소와 OS를 하나의 트랜잭션이라고 주장하지 않는다.

1. 작성자 catalog, 등록의 수용 digest, 비구동 효과와 명시적 F1 선언을 대조한다.
2. 기존 supervisor가 권한을 확인하고 PREPARED/SPAWN_ENTERED를 기록한다.
3. 외부 효과 전에 등록 상태·revision·catalog를 확인하고 실행 배정을 원자적으로 기록한다. 이전 배정이 미결이면 다른 plan·이름·PID로도 재실행하지 않는다.
4. F1 backend가 적용·exec 직전에 기존 권한과 등록 조건을 다시 확인한다. 등록은 LifecycleAuthority를 대체하지 않는다.
5. 실행 관측은 별도 실행 키에 보존한다. 그 키에는 등록 UUID와 새 인스턴스 UUID가 연결되며, 실행별 run/selection은 등록의 키가 아니다.
6. 저장소 사이의 실패는 미결 배정을 남길 수 있다. 배정만 남았다고 실제 실행 또는 미실행을 단정하지 않는다. 자동 재생·미결 삭제·PID 인수를 제공하지 않는다.

정상 종료는 실제 소유한 child의 종료 관측을 보존한다. 비정상 종료를 직접 관측했다면 종료와 오류를 기록하고, 핸들을 잃었거나 manager가 재시작했다면 기존 supervisor의 UNKNOWN을 유지한다. 실행 파일이 사라져 시작에 실패해도 등록은 자동 폐기되지 않는다. 폐기는 기존 실행을 강제 종료하지 않으며, 기존 소유자가 권한에 따라 종료하는 경로를 유지한다.

## 조회 축과 미지원

`Registry::query`는 supervisor나 plan 없이 등록과 역사적 실행 관측을 읽는다. 저장된 관측을 현재 실행 소유로 승격하지 않는다.

| 조회 항목 | 출력의 해석 |
|---|---|
| registration | 현재 수용 선언·digest·revision·등록 상태 |
| executions | 각 인스턴스에 연결된 당시 선언과 마지막 실행 관측. 표시 이름·PID·포트 재사용은 동일 실행의 증거가 아님 |
| execution_ownership | `NOT_ESTABLISHED_BY_PERSISTENT_RECORDS` |
| functional_readiness | `UNSUPPORTED: F2 does not assess functional readiness` |
| work_use_permission | `UNSUPPORTED: registration and process liveness do not permit work use` |

기존 `PROCESS_READY`는 인스턴스가 일치하는 프로세스 probe 결과다. 기능의 업무 적합성이나 사용 허가를 판정한 것이 아니다. F1의 적용 상태는 현재 실행 소유자의 별도 조회에 남으며 재시작 후 `Unconfirmed`다. 통과선은 수락 경로를 실제로 지나지만 `NoRequirements`인 경우 **어떤 자원도 집행하지 않는다**. 자원 제한이 설정되었다는 사실은 최악 응답 시간을 입증한 것이 아니다.

준비 판정·업무 사용 허용(F4), 의존 결합·재판정(F5), UNKNOWN의 명시적 처분·재개(F3), 다중 호스트, Linux cgroup/rlimit/장치 접근 집행, 물리 장비 검증은 미지원이다. 등록부의 지속성과 이 한 통과선을 전체 상주 프레임워크 완성으로 보고하지 않는다.

## 기존 status recipe의 호환 경계

`rx/status-http`의 작성자 선언이 `None`에서 명시적인 `Some(empty Requirements)`로 바뀐다. 기존 미선언은 F1을 건너뛰었고, 새 선언은 요구가 없음을 명시하고 실제 F1 수락 영수증을 얻는다. 다른 기존 프로그램의 미선언 의미는 바뀌지 않는다.

이 변경은 Program 및 해당 plan digest를 바꾼다. 기존 catalog에 결속된 supervisor 저장소는 새 recipe로 자동 재개되지 않는다. 거절은 plan/catalog 선언이 달라졌다는 원인과 기존 기록 보존·검토 필요를 설명한다. 거절 트랜잭션은 옛 기록을 변경하지 않는다. 기존 schema로 저장된 문서·이력은 여전히 Repository 포트로 읽을 수 있다.

운영자는 이전 release와 기록을 보존하고 기존 실행·미결 여부를 대조해야 한다. 아직 존재하거나 불명인 실행을 우회하려고 새 저장소를 만들면 안 된다. 기존 실행이 안전하게 정리됐다는 별도 근거와 새 선언 검토가 있어야 새 계획의 전환을 결정할 수 있다. F2에는 자동 이관·불명 처분·기록 삭제 도구가 없다. 규범 v1.0, wire/proto/SDK 및 공유 manifest의 변경도 없다.

## 재현과 증거의 구분

solutions에서 독립 target을 지정해 등록 시험을 실행한다.

```sh
cargo test -p rx-supervisor --test registration --locked --target-dir /tmp/rx-f2-check -- --nocapture
```

검증된 RX runtime 이미지가 있는 호스트에서는 현재 코드를 별도 Linux target에 빌드하고 실제 설치된 `rx/status-http`를 다음 절차로 연결한다. 새 evidence 디렉터리가 필요하며 기존 기록을 덮어쓰지 않는다.

```sh
python3 tools/registration_passage.py --image RX_RUNTIME_IMAGE --evidence /tmp/rx-f2-passage-new
```

이 절차는 `registration_passage` 시험을 실행한다. runtime 이미지의 실제 자체 점검과 현재 상태 서비스 소스 hash의 일치를 먼저 확인한다. 등록만 하는 프로세스, 실제 기동·종료 프로세스, 저장소를 재개하는 새 manager 프로세스를 구분해 실행하며 단계마다 다음 단계로 넘어간 근거와 원시 JSON을 남긴다. 추가로 현재 소유한 비구동 child의 강제 상실과, 실제 child가 살아 있는 동안 manager 객체·저장소를 재개하는 경우를 대조한다. 후자의 manager 재개는 객체 재생성이라고 정확히 표시한다.

| 증거 종류 | 해석 |
|---|---|
| 문서·정적 분석 | 독립 키와 모듈 의존 방향, 공유 포트 재사용, 보호 파일 hash |
| 모의 Backend + 실제 SQLite | CAS 경쟁, 같은 PID 재사용, 선언 변화, 두 저장소 사이 실패와 재실행 거절 |
| 실제 OS 거절 | 실행 파일 상실 뒤 시작 거절과 등록 보존 |
| 실제 Linux 통과선 | 현재 Rust 코드, 검증된 이미지의 실제 HTTP 서비스, 인스턴스 응답·소유 child 종료·지속 기록 대조 |
| 미검증 | 실제 자원 정책 집행, 물리 장비, 다중 호스트, 복구 처분과 업무 사용 허가 |

Docker의 네트워크·권한 제한은 시험 환경의 격리이며 F1이 호스트 요구를 집행한 증거가 아니다. 단계별 원시 출력과 사용한 이미지 ID·명령은 절차의 evidence 디렉터리에 남는다. 자동 CI의 기본 시험에서는 이 환경 의존 통과선 시험을 실행하지 않으며, 별도로 실행한 결과와 제외 개수를 구분해 보고한다.

## 이번 실행에서 확인한 결과

2026-09-23에 [구현 811b7d5](https://github.com/jack0682/rx-solutions/tree/811b7d5faf9fcd2a24518f16f28d03be9867e881/runtime/rx-supervisor)의 현재 소스를 검증했다. 기본 macOS workspace는 287 passed / 0 failed / 17 ignored, 새 등록 시험은 10 passed / 0 failed다. 제외 17개에는 opt-in 통과선의 parent/worker 두 선언이 포함된다. 이를 성공 개수에 더하지 않았다. 별도 Linux 실행에서는 parent 시험 1개가 worker 5단계를 실제 실행했다.

- 실제 runtime 이미지: `sha256:fcb56bfdfcc1f68bf8cfb6d28f7f24d5899f5e31030ee2a882f6e29e1e28b4a0`. 빌드 이미지: `sha256:ff521445a372125ed4f76e1453a1f8098f2d05332d1601d30db1c1f62757e730`.
- 실제 설치된 상태 서비스와 현재 원본의 SHA-256이 `c1101a2675e03a15f71d4e236a01c9c43140fb53364b03c3d0c3af52809c6975`로 일치했다.
- 등록 `cb9f3f73-47ac-4be4-9045-3844597b5e50`은 실행 전부터 존재했고, 정상 종료·새 manager 프로세스의 재조회·비정상 child 종료·소유 상실 뒤 대조에서도 유지됐다.
- 수락 근거는 실제 `NoRequirements` 영수증, 실행 관측은 인스턴스 일치 HTTP 응답, 종료 근거는 소유 child의 exit와 회수였다. manager 객체 재개에서는 이전 child가 살아 있어도 새 소유를 주장하지 않고 UNKNOWN을 기록했다.
- [재현 절차](https://github.com/jack0682/rx-solutions/blob/811b7d5faf9fcd2a24518f16f28d03be9867e881/tools/registration_passage.py)와 [단계별 단언](https://github.com/jack0682/rx-solutions/blob/811b7d5faf9fcd2a24518f16f28d03be9867e881/runtime/rx-supervisor/tests/registration_passage.rs)을 함께 보존했다. 명령·출력·데이터베이스는 절차의 evidence 디렉터리에 남으며, 이 기록은 물리 장비·자원 집행·업무 허가의 증거가 아니다.
