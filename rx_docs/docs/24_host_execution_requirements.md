# F1 호스트 실행 요구 선언과 단일 수락

2026-09-23 · **범위: Supervisor의 선언·거절·관측 계약. OS 자원 집행은 미구현.**

## 1. 결정과 첫 구현 범위

상주 프레임워크의 첫 조각으로 작성자가 호스트 실행 요구를 표현하고, 적용할 수 없으면 실행을 거절하는 경로를 추가한다. F1은 등록 신원(F2), 명시적 복구(F3), 준비와 업무 사용 허용의 연결(F4), 의존 기능의 결합·재판정(F5)을 완성하지 않는다. 시험 개수나 프로세스 생존은 프레임워크 완성의 근거가 아니다.

기존 [v1 자원 계약](contracts/v1.0/02_identity_durability_recovery.md#4-authority-and-resources)은 다음을 규정한다.

> v1 reserves every resource needed at operation start in one transaction and prohibits waiting while holding a partial allocation.

F1은 이 **부분 확보 대기 금지**를 호스트 실행 요구의 수락 경계에 계승한다. 기존 P의 작업 예약 트랜잭션에 호스트 자원을 추가하거나, 양쪽을 원자적으로 결합했다고 주장하지 않는다. 기존 규범 본문·wire/proto·SDK·manifest는 변경하지 않는다. 계산 자원 회수는 물품·공간·장비 제어권의 인계를 뜻하지 않는다.

## 2. 요구의 소유와 의미

`Program.execution_requirements`는 release catalog 작성자가 제공한다. 현장 `Process`의 필드와 JSON 입력 형식은 그대로다. 현장은 프로그램과 허용된 기존 인자를 선택할 뿐 요구 선언을 대체하지 못한다. F1에는 현장에서 수치·단위·접근 대상의 바인딩을 새로 입력하는 경로가 없다.

| 선언 | 의미 |
|---|---|
| `None` | 기존 프로그램의 미선언. F1에 참여하지 않는 호환 경로이며, 요구가 없다고 검증한 것이 아니다 |
| `Some(Requirements({}))` | 작성자가 명시적으로 빈 요구 집합을 제공함. 미선언과 다른 plan digest를 갖는다 |
| `NotRequired` | 이름 붙은 해당 조건을 요구하지 않음 |
| `Unknown` | 해당 조건을 아직 모름. 빈 요구나 NotRequired로 바꾸지 않고 거절 |
| `UpperBound` | 적용할 사용 상한. 다른 실행의 상한과 합산해 확보 용량으로 취급하지 않음 |
| `ReservedCapacity` | 반드시 확보해야 하는 용량. 부족하면 전체 실행 거절 |
| `ExclusiveAccess` | 이름 붙은 호스트 접근 대상의 독점 접근 요구 |
| `SharedAccess` | 이름 붙은 호스트 접근 대상의 공유 접근 요구 |

수량 자원은 CPU millicores와 memory bytes로 구분한다. CPU 1000단위는 논리 CPU 하나에 해당하는 양의 표현이며 성능·주기·최악 응답 시간 보장이 아니다. 단위와 의미는 작성자가 고정하고 현장 인자에서 가져오지 않는다. 0을 쓰는 것으로 요구를 비활성화할 수 없으며 명시적 NotRequired와 구분한다. 묶음은 이름으로 식별되는 요구 최대32개다.

실제 `Program`은 Serialize만 구현하고 site JSON에서 Deserialize하지 않는다. `Process`는 알 수 없는 필드를 거부하고 parameters는 catalog의 정확한 허용 집합과 대조한다. 선택된 catalog 전체가 저장된 plan digest에 포함되므로 같은 저장소를 낮춘 요구로 다시 열면 conflict다. 런타임 `Request`와 `Receipt`의 필드는 비공개이며 Request를 낮추거나 일부 요구만 담은 Receipt를 외부 코드에서 직접 만들 수 없다.

이 경계는 **현장 입력 경로**에 대한 것이다. 신뢰된 Rust 통합 코드가 최초 catalog map을 임의로 만드는 것, release image를 수정하는 관리자, 저장소를 지우는 공격까지 인증하는 서명된 범용 catalog 포맷을 이번에 추가하지 않았다. `Program`의 기존 trusted-release 가정을 유지한다. 작성자의 정당한 요구 변경은 새 catalog/plan의 검토 대상이며 과거 digest를 우회하지 않는다.

## 3. 수락·실행 포트와 순서

기존 `Backend`에 `spawn_with_requirements(launch, request, authorize)` 경계를 추가한다. 별도 서비스나 크레이트를 만들지 않는다. 수락된 자원 적용과 child 생성의 책임을 같은 backend가 소유한다. 자원만 적용한 뒤 supervisor가 별도 호출로 exec하는 두 단계 API를 만들지 않는다.

1. 기존 `LifecycleAuthority::may_start`를 먼저 확인한다. 실행 요구가 충족돼도 이 권한을 대신하지 않는다.
2. 기존 PREPARED/SPAWN_ENTERED 기록과 권한 재확인을 유지한다. 저장 실패 후 선언만 보고 child를 만들지 않는다.
3. 미확정 `Unknown` 요구는 backend를 부르기 전 거절한다.
4. backend는 전체 묶음을 하나로 판단하고, 적용·exec 직전에 authorize를 다시 확인해야 한다.
5. 알려진 결과는 `Admitted { pid, receipt }` 또는 `Rejected { unmet }`뿐이다. 수락 Receipt는 요청의 program/process/instance/plan digest와 **전체 요구**에 결속된다. 일부 적용 성공을 반환하는 형식은 없다.
6. 거절과 `SpawnFailure::NotStarted`는 정책·예약·child가 남지 않았음을 뜻해야 한다. 일부 외부 효과 또는 복구 여부가 불명이라면 기존 `SpawnFailure::Uncertain` 오류 채널을 사용한다. 이를 거절로 가장하지 않는다.
7. 부정확한 Receipt, 유효한 이름·사유가 없는 거절, 불명 실행은 UNKNOWN으로 보존하고 자동 재실행하지 않는다.

기본 backend는 어떤 플랫폼에서도 cgroup v2, rlimit, CPU/메모리 예약, 독점·공유 장치 접근을 구현하지 않는다. 필수 요구가 하나라도 있으면 **어떤 요구도 적용하지 않고 spawn하지 않는다**. 명시적 빈 선언 또는 NotRequired만 있는 선언은 요구를 적용했다고 가장하지 않고 NoRequirements 근거로 기존 spawn 경로를 사용한다.

수락 불가한 시작 시도는 START_FAILED와 이름별 blocked/error 사유를 남긴다. 기존 restart budget과 명시적 재활성화 규칙을 사용하며, 부분 자원을 보유한 대기 큐를 만들지 않는다. 미선언 프로그램은 기존 `Backend::spawn` 경로 그대로다. `Effect::RequiresPlatformAuthority`의 기존 권한·종료 의미는 변경하지 않는다.

향후 Linux backend는 실행 인스턴스와 집행 근거, 전부 적용 또는 확실한 원복, 권한 변화, 생성 실패, 실제 종료와 자원 수명, 불명 후 대조를 검증해야 한다. enum이 두 가지라는 사실만으로 외부 OS 동작의 원자성이 증명되지는 않는다. 이번의 실체는 기본 거절 경로이며, 긍정 적용은 명시된 모의 backend에서만 시험했다.

## 4. 조회 근거의 세 구분

Supervisor status의 `execution_admission[process]`는 다음을 별도 제공한다.

현재 소유자의 `Supervisor::execution_admission()`은 이 관측을 읽기만 하며 수락 판정·기동·준비 probe·권한 평가를 실행하지 않는다. 시작을 진행하는 `tick()`의 status에도 같은 map이 포함된다. 아직 시작을 시도하지 않은 Pending의 NotApplied와 빈 사유 목록은 적용 가능 여부를 평가했다는 뜻이 아니다.

| 필드 | 해석 |
|---|---|
| `requested` | catalog가 요청한 정확한 선언. null(미선언)과 빈 map(명시적 빈 선언)을 구분 |
| `application` | LegacyNotDeclared, NotApplied, ReportedAtStart 또는 Unconfirmed |
| `not_applied_reasons` | 현재 거절/미적용에서 확인한 요구 이름과 이유. 원래 `Record.error`에도 시작 실패 사유가 남음 |

ReportedAtStart의 Receipt는 **해당 시작 경계에서 backend가 보고한 근거**다. 현재 자원 정책을 지속 감시한 값이 아니다. `Evidence::Simulation`은 모의 결과, `HostReport`는 향후 신뢰된 집행기의 보고이며 그 내용의 물리적 진실성을 생성자가 검증해 주지 않는다. NoRequirements는 아무 자원도 집행할 필요가 없었다는 선언 범위에만 쓸 수 있다.

**자원 제한이 설정되었다는 사실은 최악 응답 시간을 입증한 것이 아니다.**

적용 관측은 현재 소유자의 메모리 상태다. 이전 Record와 오류는 기존 저장소에 남지만, 재시작 후 Receipt를 복원해 현재 적용으로 주장하지 않는다. 시작을 시도한 기록만 남은 경우 적용 관측은 Unconfirmed다. 기존 실행 소유 UNKNOWN도 유지한다. 복구·자원 인계의 새로운 자동 절차를 제공하지 않는다.

미선언 Program은 새 필드를 직렬화하지 않아 기존 plan digest를 유지한다. 기존 site Plan과 저장 State 형식은 그대로이며, status 조회에는 위 진단 map이 추가된다. Rust의 직접 Program literal 작성자는 `execution_requirements: None` 또는 작성자 선언을 명시한다. 이는 Rust 소스 수준의 필드 추가이며 기존 struct literal의 무수정 컴파일 호환성을 주장하지 않는다.

## 5. 시험과 미검증 범위

| 구분 | 확인 방법과 결과의 의미 |
|---|---|
| 문서·정적 대조 | 기존 v1의 한 트랜잭션 예약/부분 확보 대기 금지와 개념 검토 RR01을 연결. RR02 의존 갱신·RR03 코어 변경은 이번 구현 밖 |
| 모의 수락 | 전부 가능은 전체 적용/child1, 전부 불가 및 일부 불가는 적용0/child0. CPU용량4에서3+3의 상한과 확보 용량을 구분하고 공유/독점 충돌을 대조 |
| 실제 개발 호스트 | 필수 조건은 기본 backend가 거절. PID/owned child/exec log가 생기지 않음. 미선언·빈 선언·NotRequired 경로는 비구동 `/usr/bin/true` child로 대조 |
| 강등 공격 | site 선언 주입, 미허용 parameter로0요청, 낮춘 catalog 재개,0수량을 거절. 외부 Request 필드 변경/Receipt 직접 생성/Program 역직렬화는 컴파일 실패로 대조 |
| 연속성 | 권한 상실 직전 적용 금지, stale Receipt/응답 불명 및 재시작의 UNKNOWN과 자동 재실행 금지를 시험 |
| Linux CI | 일반 Rust/기존 OS 시험이 Linux runner에서 실행되는 것과 아래 자원 집행 검증은 별개다. CI 결과는 실제 PR/run 증거로 확인 |
| 미구현·미검증 | cgroup v2 quota/reservation, rlimit, 장치 권한/핸들 집행, scheduler/RT·최악 응답 시간, OOM/부분 적용 rollback, 실제 장비, 협업 자원 인계와의 원자 결합 |

양성 모의 시험을 실제 OS 집행·물리 자격으로 사용하지 않는다. 현재 builtin release recipes는 미선언 호환 경로를 유지한다. 이 문서는 F1의 책임과 한계를 기록하며 Linux 집행 provider나 패키지 등록/교체/복구의 완성을 선언하지 않는다.

경계는 Supervisor가 관리하는 Program의 시작 경로다. 별도 metadata-only `Initializer` 실행,
Supervisor를 거치지 않는 직접 backend/OS 호출, 권한 있는 호스트 통합 코드의 변경을 전역적으로
차단하는 sandbox를 추가하지 않았다. 이런 경로까지 자원 집행을 확장하려면 실행 단계별 작성자
요구와 집행 근거를 별도로 결속해야 한다.
