# F4 보고된 준비 조건과 업무 사용 허가

2026-09-23 · **지원 범위: 작성자 조건과 구성요소 자기 보고의 대조. 운영 영역의 긍정 허가 provider는 미연결·미지원이며 호스트는 허가를 발급하지 않는다.**

후속 [F5](28_dependency_binding.md)는 이 자기 보고를 실제로 소비하는 별도 진단 작업과 구간별 의존 재판정을 추가한다. 아래 F4의 과거 관측 수치와 준비·허가의 의미는 그대로다.

후속 [F6](29_verified_external_decisions.md)은 검증된 외부 승인만 전달하는 긍정 경로를 추가한다. 기본 카탈로그는 여전히 앵커가 없으며 아래 F4의 과거 범위와 근거는 보존한다.

## 두 축을 판정으로 만든 범위

[F1](24_host_execution_requirements.md)의 수락, [F2](25_component_registration.md)의 등록, [F3](26_explicit_recovery_disposition.md)의 처분은 기능 준비나 업무 허가가 아니다. F4는 작성자가 선언한 용도별 조건을 실제 보고와 대조하고, 업무 판단을 별도 포트에 묻는다. `ProcessReady`를 준비 완료로 복사하지 않는다. 기존 `AliveOnly => Ok(true)`는 생존 probe로 그대로 둔다.

**여기서 `SATISFIED`는 해당 용도의 자기 보고 조건이 일치했다는 뜻이다. 기능의 실제 동작·보정·물리 조건·작업 적합성을 독립적으로 입증한 것이 아니다.** 등록·설치·서명·프로세스 생존·F1 Receipt·F3 처분에서 이 값을 만드는 자동 경로는 없다.

`Program.functional_readiness`는 작성자 catalog의 선택적 선언이다. 역할/용도 이름별 profile에는 관측 endpoint와 이름 붙은 조건이 있다. 조건은 인스턴스 상관, 보고 필드의 형식/값 대조, 명시적 미지원으로 표현한다. 빈 profile과 인스턴스 상관이 없는 선언은 거절한다. 현재 source는 소유한 비구동 `HttpStatus` 프로그램의 loopback HTTP 보고뿐이다. `AliveOnly`만 있는 프로그램과 관측 수단이 없는 조건은 미지원이다.

현장 `Process`에는 준비 조건을 쓰는 필드를 추가하지 않았다. 프로그램의 전체 catalog digest에 선언이 포함되므로 낮춘 선언으로 기존 등록/저장소를 다시 열면 거절된다. 신뢰된 작성자가 조건을 설계한다는 가정은 유지한다. 타입이 임의 작성자 조건의 업무적 충분성이나 자기 보고 내용의 진실성을 자동 인증하지 않는다.

## 관측과 출처

`assess_use(UseScope, WorkUsePort)`는 현재 등록·catalog·run·선택·instance·PID·역할·endpoint와 새 평가 요청 ID를 결속한다. OsProcesses는 자신의 실제 child가 살아 있는지 확인하고 요청한 보고를 읽는다. 인스턴스 응답이 다르면 다른 필드는 평가하지 않는다. 이전 요청의 응답을 새 요청에 재사용해도 거절한다. `StatusObservation`은 외부 생성자/필드 및 Deserialize를 제공하지 않는다.

평가는 시작·정지·수락·처분을 실행하지 않고 영속 실행 상태나 이력을 변경하지 않는다. 결과는 그 호출의 snapshot이다. 별도의 `query()`는 probe를 호출하지 않고 미평가 상태를 반환하며 이전의 준비 판정을 현재 상태나 권한으로 복원하지 않는다. child가 보고 직후 종료할 가능성까지 제거하는 지속 보장은 아니다.

기존 `rx/status-http`의 응답 출처를 다음처럼 구분한다.

| 필드 | 실제 출처 | F4가 주장하지 않는 것 |
|---|---|---|
| `supervisor_instance` | 시작 시 전달된 `RX_PROCESS_INSTANCE_ID` 환경변수 | 독립적 신원 인증이나 물리 권한 |
| `native_packages` | 시작 시 읽은 native audit의 파생값 | 패키지별 현장 자격 |
| `support_profiles`, `simulation_profiles` | 시작 시 읽은 catalog의 파생값 | 모든 장비가 현재 사용 가능하다는 판단 |
| `schema`, `operator_api_delegation` | 릴리스 코드의 정적 선언 | 현재 operator 연결을 실시간으로 시험한 결과 |

조건마다 `INSTANCE_ENVIRONMENT`, `STARTUP_AUDIT_DERIVED`, `STARTUP_CATALOG_DERIVED`, `RELEASE_DECLARATION` 등 출처를 표시한다. 보고를 받은 시각은 HTTP 관측 시각이며 시작 시 계산된 값의 재측정 시각이 아니다. payload digest는 받은 내용을 고정할 뿐 물리 진실성을 증명하지 않는다.

## 기존 서비스의 두 사용 조건

같은 `/api/v1/solution/support` 응답에 두 작성자 profile을 적용한다.

| 용도 | 선언된 조건 | 현재 관측 |
|---|---|---|
| `diagnostics/support-summary` | 현재 instance 일치, status schema 일치, native/support/simulation count 필드의 비음수 정수 형식 | 자기 보고 조건 `SATISFIED` |
| `diagnostics/operator-connected` | 위 조건 + `operator_api_delegation == CONNECTED` | `NOT_CONNECTED`여서 `NOT_MET` |

두 번째 불충족은 살아 있는 연결 점검이 실패해서가 아니라 **현재 릴리스가 `NOT_CONNECTED`라고 정적으로 선언하기 때문**이다. 첫 번째는 지원 요약을 보고하는 형식/값의 대조이며 실제 업무를 수행해 성공했다는 뜻이 아니다. 새 장비 기능이나 가짜 접속 시나리오를 만들지 않고 기존 응답의 두 사용 조건을 구분했다.

## 미평가·불충족·미지원·충족

| 준비 상태 | 해석 |
|---|---|
| `NOT_EVALUATED` | 아직 평가하지 않았거나 현재 소유/응답을 얻지 못해 조건을 평가하지 못함 |
| `NOT_MET` | 얻은 보고나 실행 결속이 선언된 조건과 다름 |
| `UNSUPPORTED` | 작성자 profile 또는 해당 관측 수단이 없음 |
| `SATISFIED` | 해당 요청에서 모든 선언된 자기 보고 조건이 충족됨 |

각 상태에 `conditions` 목록을 제공한다. 각 항목은 이름·상태·이유·출처·관측값을 구분한다. 예를 들어 `operator/api-delegation`, `report/current-instance`, `report/support-profile-count`, `report/transport`, `catalog/readiness-profile`이 어느 조건이 부족한지를 말한다. 보고 인스턴스가 다르거나 관측을 못 얻었을 때 다른 필드를 충족으로 처리하지 않는다. 둘 이상의 상태가 섞이면 실제 불충족을 먼저 표시하고, 상세 목록에서 미지원/미평가도 남긴다.

## 업무 판단은 운영 영역의 책임

`WorkUsePort`는 운영 영역의 작업 판단 결과를 받는 경계다. 호스트 안에는 `Granted` 변종·긍정 허가 생성자·허가 토큰 발급 경로가 없다. 현재 포트가 표현하는 것은 세 가지 비허가 결과다.

| 상태 | 해석 |
|---|---|
| `NOT_EVALUATED` | 범위가 지정된 업무 판단을 아직 요청하지 않았거나 판단자가 평가하지 않았다고 보고함 |
| `DENIED` | 연결된 운영 영역 adapter가 이름 붙은 조건과 decision reference로 거부를 보고함 |
| `UNSUPPORTED` | 판단자가 미연결이거나 응답을 해석할 지원이 없음 |

기본 `NoWorkUseProvider`는 `UNSUPPORTED`와 `work-use/operating-area-provider` 사유를 반환한다. 이것을 권한 있는 판단자가 실제로 평가해 거부했다는 뜻으로 표시하지 않는다. 미연결이어도 사용 허가는 생성되지 않는다. 빈 사유 목록이나 잘못된 provider 응답도 named `work-use/provider-response` 미지원으로 처리한다.

**운영 영역의 긍정 허가 provider 연결은 이번 범위에 없다. 현재 항상 비허가인 결과는 그 부재의 결과이며 이 구성요소를 영원히 사용할 수 없다는 설계 주장이 아니다.** 거부 응답의 진실성/인증은 adapter 통합의 책임이고, 시험의 거부 provider는 명시적인 모의 정책이다. 현재 snapshot은 자격 증명이나 업무 실행 명령이 아니다. diagnostic GET의 접근 제어나 실제 업무 dispatch를 이 포트가 집행한다고 주장하지 않는다.

## 조회·호환과 기존 경계

`Registry::query()`는 여전히 supervisor/plan/OS 없이 동작한다. `use_assessment`의 중립 데이터 타입을 사용하며 `Supervisor`, `Plan`, `State`에 의존하지 않는다. 실제 I/O와 평가 연결은 `RegisteredSupervisor` 및 Backend 쪽에 있다. 기본 Backend는 추가 관측 source를 지원하지 않으므로 기존 구현자에 새 필수 메서드를 강제하지 않는다.

`View.functional_readiness`와 `work_use_permission`은 문자열에서 typed 판정 객체로 바뀐다. 이는 **로컬 조회 API의 형식 변경**이며 무수정 문자열 소비자 호환성을 주장하지 않는다. 독립 registry와 새 owner는 준비·허가를 주장하지 않도록 `NOT_EVALUATED` 및 이름 붙은 미평가 조건을 반환한다. 기존 문자열 `starts_with("UNSUPPORTED")` 단언2개는 이 상태, 비어 있지 않은 조건, 각 조건의 미평가를 확인하는 단언으로 강화했다. 다른 기존 단언은 유지했다.

Program의 `functional_readiness: None`은 직렬화에서 생략하므로 기존 미선언 catalog/plan digest 입력을 유지한다. Rust struct literal에는 None 초기화가 필요하다. builtin status의 명시적 선언은 digest를 바꾸므로 이전 catalog에 결속된 등록/실행 store는 설명되는 거절을 유지한다. 자동 이관·미결 삭제·낮춘 catalog 재개는 없다.

F1 단일 수락과 작성자 소유, F2 등록/실행 신원, F3 비역직렬화 증거와 별도 처분·명시 재개는 유지한다. F3의 과거 처분 `work_use_permission=UNSUPPORTED`를 현재 허가로 승격하지 않는다. lifecycle의 마지막 관측은 기능 준비 판정이 아니며 새 평가 결과를 그 과거 기록에 덮어쓰지 않는다. 공유 규범 v1.0·wire/proto·SDK·manifest는 변경하지 않는다.

## 실제 Linux 절차와 음성 대조

기존 절차 하나를 그대로 확장했다.

```sh
python3 tools/registration_passage.py --image RX_RUNTIME_IMAGE --evidence /tmp/rx-f4-passage-new
```

기존 등록→수락→실행→종료→재시작 대조→처분→새 실행과 재생 거절을 유지한다. 실제 상태 서비스가 ProcessReady일 때 다음 두 장면을 추가한다.

- `process-ready-but-use-conditions-not-met`: operator 용도의 조건은 NOT_MET이며 정적 릴리스 선언이 원인임을 출력한다.
- `reported-conditions-met-but-work-use-unavailable`: readonly 조건은 SATISFIED, 업무 판단은 provider 미연결로 UNSUPPORTED다.

기존5 worker 안의 관측 단계가13개에서15개로 늘었다. 이를 독립 시험15개로 세지 않는다. 별도 시험은 AliveOnly/미선언, 이름별 미평가·불충족·미지원, 잘못된 instance, 이전 응답 재생, 명시적 거부와 미연결, catalog 약화 및 새 owner의 비복원을 대조한다. 외부 crate에서 등록·ProcessReady·F1 Receipt·F3 처분·catalog metadata를 준비/허가로 변환하는 시도, host Granted 생성, 관측 및 기존 증거 토큰 역직렬화를 실제 컴파일 오류로 거절한다.

실제 장비 동작, 물리 조건, 협업 자원 결합, 의존 결합(F5), Linux 자원 집행, 다중 호스트, F3 외부 조사 provider는 미지원이다. 긍정 업무 허가 provider도 미지원으로 query와 절차 limitations에 표시한다. 이 단위를 전체 프레임워크 또는 현장 자격의 완성으로 보고하지 않는다.

## 회귀에서 찾은 기존 비구동 종료 경계

F4 회귀 중 기존 `/usr/bin/true` 시험이 `owned process signal was not confirmed`로 실패했다. 시작 전 기준 `b05f247`을 별도 source/target으로 실행한50회 probe에서, 신호 오류 직후 같은 소유 Child의 정상 exit가50회 확인됐다. 새 준비 축이 만든 결함으로 분류하지 않았다.

기존 코드는 신호 전에는 이미 종료된 Child를 확인해 Ok로 처리했으나 신호 실패 후에는 그 동일한 종료 근거를 읽지 않았다. 보완은 **Effect::NonActuating**에만 제한한다. 실패한 신호가 성공했다고 바꾸지 않고, 동일 소유 Child의 실제 종료가 추가로 확인된 경우에만 이미 종료된 경우의 기존 의미를 적용한다. 살아 있거나 확인 불가하면 오류다. ProtocolGuardedService·RequiresPlatformAuthority·효과 불명에는 이 완화를 적용하지 않는다.

신호 성공은 요청 수락일 뿐 종료 완료가 아니다. 실제 exit 관측은 별개다. timeout·force·제어 종료 규칙과 AliveOnly 본문은 그대로다. 신호 성공/실패+실제exit/실패+생존·불명/제어 효과를 분리한 시험을 추가했다. OS가 EPERM을 반환한 일반적 원인까지 규명하거나 자손 프로세스·물리 중단을 증명했다고 주장하지 않는다. 제어 경로에서 같은 오류가 관측되면 별도 미결로 유지하며 이 보완으로 숨기지 않는다.

현재 소프트웨어 probe의 관측은 다음과 같다. 여기서 오류 수는 Backend 반환 오류이며 신호 전달 성공 횟수가 아니다.

| 50회 probe | Backend 오류 | 신호 명령 오류 출력 | 범위 |
|---|---:|---:|---|
| 기준 소스 NonActuating | 50 | 50 | 오류 직후 같은 Child의 exit0을50회 확인 |
| 보완 후 NonActuating | 0 | 47 | 오류 출력은 보존하며 실제 소유 exit로 종료 경계를 확인 |
| 기준 소스 ProtocolGuardedService 태그 | 0 | 0 | 이 PID-target fixture50회에서 같은 오류 미관측; 일반적 부재 증명 아님 |
| 기준 소스 RequiresPlatformAuthority 태그 | 50 | 50 | 같은 group-target 경계가 관측됨; 현재 보완 대상에서 제외 |

**남은 문제: 제어 효과의 group-target 신호 오류와 후속 child 종료 관측의 대조.** 이를 비구동 예외로 처리하지 않는다. 제어/guarded 태그 probe는 `/usr/bin/true` 소프트웨어 fixture로 분기를 관찰한 것이며, 실제 플랫폼 권한·장비 동작·guarded 정상 종료 자격을 검증한 것이 아니다. 제어 효과와 효과 불명에서 실패를 유지하는 별도 음성 시험이 있다.

## 구현과 관측한 검증

구현 기준은 [rx-solutions `4439442e`](https://github.com/jack0682/rx-solutions/commit/4439442e6a68c1b8c085771a4f0c8b2b37b7a55a)다. 재현 진입점은 [같은 Linux 절차](https://github.com/jack0682/rx-solutions/blob/4439442e6a68c1b8c085771a4f0c8b2b37b7a55a/tools/registration_passage.py)와 [준비·허가 시험](https://github.com/jack0682/rx-solutions/blob/4439442e6a68c1b8c085771a4f0c8b2b37b7a55a/runtime/rx-supervisor/tests/use_assessment.rs)이다.

- macOS 전체 Rust 시험: **309 통과, 0 실패, 17 ignored**. 실행 인수는 `cargo test --workspace --all-features --locked -- --test-threads=1`이며 전용 target을 사용했다. `cargo fmt --all -- --check`와 전체 target/features clippy `-D warnings`도 통과했다.
- 별도 준비·허가 시험9개와 신호 결과 시험4개가 통과했다. 위 전체 수에 포함되므로 합산하지 않는다.
- 외부 consumer의 승격/역직렬화 시도9종은 실제 `E0277` 또는 `E0599`로 거절됐다. 각 시도 직후 유효한 읽기 consumer로 복원해9번 모두 컴파일 성공을 확인했다.
- 동일한 실제 Linux 절차는 parent1개·worker5개·관측15단계로 완료했다. 같은 현재 instance에 대한 operator profile은 `NOT_MET`, support-summary profile은 `SATISFIED`이며 업무 provider는 `UNSUPPORTED`였다. 새 UUID를 사용하므로 재실행 시 식별자는 달라진다.
- 실행 runtime image는 `sha256:fcb56bfdfcc1f68bf8cfb6d28f7f24d5899f5e31030ee2a882f6e29e1e28b4a0`, builder는 `sha256:ff521445a372125ed4f76e1453a1f8098f2d05332d1601d30db1c1f62757e730`이다. 서비스 보고의 native675·support4·simulation4는 시작 시 audit/catalog 파생값이며 물리 자격 수가 아니다.

초기 검사 실패도 보존했다. clippy의 큰 enum 지적은 observation을 Box로 보유해 수정했고, 기존 비구동 정지 시험의 신호 오류는 위 기준 소스 대조 후 제한적으로 보완했다. 최종 통과를 초기 실패가 없었다는 뜻으로 쓰지 않는다. 실제 Linux 절차는 새 Rust probe를 빌드해 기존 상태 서비스와 실행한 결과이며, 전체 native 재빌드나 실제 장비 운전 검증은 아니다.
