# F7 상주 데몬의 등록 소유

2026-09-24 · 기존 `rx-solutionsd`가 계획 전체의 실행 관리자 하나와 등록부 하나를 소유한다. 각 프로세스 선택에는 별도 등록 UUID를 결속한다. 이번 연결은 등록과 실행 수명 대조에 한정된다.

## 확인한 책임과 선택

기존 단일 상태 서비스 예시와 지원 범위는 다르다. `PROTOCOL_GUARDED_SERVICES.md` 9행은 기존 계획 상한 32 프로세스 안에서 다중 Host·Executor·cell을 지원한다고 명시한다. 39행의 Host 2개·Executor 2개는 시험 커버리지다. 따라서 단일 프로세스만 등록하고 나머지를 미등록 Supervisor 경로로 남기는 접근은 버렸다.

`RegisteredSupervisor::open_resident` 내부의 Supervisor 하나가 기존 계획 전체와 OS Child 핸들을 계속 소유한다. 등록부는 그 소유자가 만든 실행 배정과 관측을 기록한다. 별도 실행 관리자·데몬·서비스·네트워크 API는 없다. `src/bin`의 바이너리도 하나다.

등록은 실행보다 오래 살아야 하며 두 저장소의 SQLite writer lock은 배타적이다. 따라서 상태 디렉터리에 **등록 저장소 `registration.db` 하나와 그 writer lock**을 추가한다. 기존 `supervisor.db`와 필요 시 사용하는 `initialization.db`의 책임은 유지된다. 저장소 추가 금지라는 이전 검사 문안은 이 확인된 책임과 충돌했다. 이 변경은 책임 확인 후 추가한다는 순서 원칙에 따른다.

## 등록과 선택, 실행을 분리한다

기동 설정 형식은 늘리지 않았다. 처음 여는 빈 저장소 쌍에서 process selection마다 UUID를 발급하고, 등록 기록과 선택 인덱스를 같은 트랜잭션에 넣는다. `state_subdirectory`가 저장소 범위를 정한다. process 이름은 저장된 UUID를 찾는 선택 좌표일 뿐이며 plan ID·PID·port·label에서 등록 신원을 계산하지 않는다.

다음 기동은 인덱스를 읽고 작성자 Program의 catalog digest와 기존 등록을 비교한다. 매핑 누락, 두 선택의 같은 등록 참조, 같은 선택의 복수 매핑, retired 등록, catalog 변경은 구별되는 사유로 거절한다. 자동 등록·승계나 미등록 실행으로 이어가지 않는다. 선택 집합을 바꾸는 명시적 이행 API는 아직 없다.

`Launch.selection`은 저장되지 않는 Rust 실행 문맥에 추가했다. 기존 spawn 경로에서 등록 배정을 먼저 저장하고, 실제 OS 실행 직전에 기존 lifecycle authority와 등록 적격성을 다시 확인한다. 배정 저장 실패는 OS 호출에 도달하지 않는다. 작성자 Program의 역직렬화나 site 정책 loader는 추가하지 않았다.

## 기동 대조와 조회

기동 시 각 선택의 저장된 instance를 해당 등록의 배정과 대조한다. 배정 없음과 다른 run·selection·catalog·등록 신원은 거절한다. 한 선택의 배정은 다른 선택의 근거가 되지 않는다. 계획 전체의 결속을 확인한 뒤 관측을 기록한다. 과거 배정의 등록 revision은 그 배정 당시 값이며, 현재 revision으로 다시 써서 승계하지 않는다. 새 배정과 실행 직전 검사는 현재 등록 revision을 요구한다.

표준 출력 `rx.resident-reconciliation.v1`에는 선택별 등록 UUID, 실행 관측, Supervisor 상태와 실행 요구 수락 상태가 담긴다. 이후 수명 변화에는 `rx.resident-registration-observation.v1`을 출력한다. 저장된 PID는 소유 증거가 아니며, 관리자 재기동에서 소유 핸들이 없어진 실행은 `UNKNOWN`을 유지한다. `activate`가 이를 지우거나 미실행으로 바꾸지 않는다.

정상 종료한 비구동 소프트웨어의 명시적 재활성화는 유지된다. 기존 guarded 프로그램의 요구 미선언 `None / LegacyNotDeclared`를 명시적 빈 요구나 자원 집행 완료로 바꾸지 않는다. 의존 순서의 종료, 협조적 종료 확인과 guarded 강제 종료 금지는 기존 실행 관리자에 남는다.

## 호환성과 남는 경계

기존 `open`·`open_with_resume`은 단일 비구동 컴포넌트와 명시적 실행 요구라는 제한을 그대로 둔다. resident 모드는 계획이 한 프로세스여도 기존 단일 컴포넌트 준비·결정 API를 거절한다. 별도 조회만 제공하므로 F1–F6의 보증을 전제 없이 얻는 통로가 아니다.

이전 미등록 Supervisor DB는 새 등록부를 만들어 자동 인수할 수 없다. 과거 저장소와 기록을 보존하고 별도 이행 판단이 필요하다. 기존 기록 삭제를 복구로 제시하지 않는다. 새 인덱스는 로컬 저장 형식이며 공유 wire/proto·SDK·규범 본문은 바꾸지 않았다. 옛 writer로의 downgrade 호환성은 주장하지 않는다.

| 경계 | 이번 근거 |
|---|---|
| 실제 데몬에 연결됨 | 등록 소유, 프로세스별 실행 배정, 기동 대조, stdout 조회 |
| 실제 Linux 정상 경로 | 읽기 전용 상태 서비스 두 개, launcher 종료 후 등록 유지, 정상 종료 후 같은 UUID 대조, 명시적 재활성화 |
| 실제 Linux 장애 대조 | 시험 컨테이너 강제 종료 후 같은 UUID와 UNKNOWN 유지, 재활성화 거절 |
| 모델·모의 회귀 | 매핑 공격, 저장 원자성, 배정 실패 전 OS 차단, guarded 의존 종료 순서·협조적 종료·강제 종료 금지 |
| 아직 연결·검증하지 않음 | 실제 Host/Executor의 새 데몬 경로, Linux 자원 집행, 관리자 완전 상실 복구, 기능 준비와 업무 판단 집행, 의존 교체 적용, 실제 운영 영역 서명 서비스 |

기본 결정 앵커는 여전히 없다. 장비 운전·물리 자격·처리량·품질·안전, 인증된 불변 release root와 악성 OS/저장소 작성자 격리를 증명하지 않는다. 기존 제어 효과 신호 경쟁도 해결했다고 주장하지 않는다.

## 검증 근거

구현은 [rx-solutions `9fa53afe`](https://github.com/jack0682/rx-solutions/commit/9fa53afe308f0df89b09d2fa01e92a2e753181cb)에 고정된다. 데몬 소유와 실제 Linux 시험 절차를 포함하며 기존 SDK·계약·native 및 실행 관리자/OS 수명 본문은 보존했다.

재현 명령, 실제 출력, 최초 실패와 수정된 시험 배치는 [근거 묶음](../references/resident_registration_2026-09-24/README.md)에 기록한다. 개별 시험 수와 32단계 관측 통과선은 전체 상주 프레임워크 완성의 기준으로 확대하지 않는다.
