# F10 업무 판단의 실제 집행 — support-gap report

2026-09-24 · 호스트가 판단을 발급하는 기능을 추가하지 않는다. 외부 결정이 실제 비구동 업무 결과의 커밋을 허용하거나 거절하도록 수신 관문을 연결한다. 출하 상태의 운영 영역 provider와 앵커는 계속 없으며, 긍정 시험을 실제 운영 승인으로 표시하지 않는다.

## 먼저 반증된 경계와 선택

기존 비시험 `assess_use` 호출은 F5의 진단 제공자 관측 경로 하나였고, `NoWorkUseProvider`의 결과 중 functional_readiness만 꺼냈다. F5는 Purpose를 `DiagnosticOnly`로 제한하고 결과의 work_use를 Unsupported로 기록한다. 실제 설치 runtime의 상태 서비스도 읽기 전용 GET만 제공하며 POST는 503 CONTROL_NOT_EXPOSED였다. 그 소비를 업무 관문으로 바꾸면 기존 진단을 업무로 재정의하거나 진단 접근을 얻을 수 없는 권한에 종속시키므로 후보 A를 버렸다.

선택한 B2는 **기존 등록 저장소에 파생 산출물을 원자적으로 커밋**하는 별도 업무다. Repository에는 revision CAS와 atomic append_control이 있고, 실제 SQLite 구현은 Immediate 트랜잭션을 쓴다. 결과와 결정 소비를 같은 트랜잭션에 둘 수 있으며 추가 쓰기 마운트·저장소 파일·서비스가 필요 없다. 지역 파일 방출 B1보다 완료 조건도 선명하다. 해당 작업 ID의 결과와 소비 기록이 함께 커밋되어야 완료다. 기동 자체에 관문을 붙이는 후보 C도 택하지 않아, 앵커가 없는 출하 데몬의 정상 기동을 유지한다.

## 산출물은 허가 영수증이 아니다

작업은 **support-gap report 생성·커밋**이다. 요청은 operation UUID, selection, operating area, 필요한 native package 수와 support profile 수다. 실제 현재 상태 보고에서 관측한 두 수치와 요청 기준을 비교해 각각 observed, required, `shortfall = max(required - observed, 0)`을 계산한다. 관측 profile 4에 요구 6이면 부족분 2, 같은 관측에 요구 4이면 부족분 0이다. 실제 설치된 status 서비스의 count와 별도 관찰자 출력으로 입력을 대조했다.

이 결과는 자기보고 데이터에 대한 계산 결과다. 부족분이 0이라는 계산이 기능 적격·작업 승인·물리 안전을 뜻하지 않는다. 운영 영역 정책을 계산하는 주체를 호스트에 추가하지 않았으며, 정책의 진실성도 인증하지 않는다. 원래 F5의 진단 결과 생성·소비는 바뀌지 않고 계속 DIAGNOSTIC_ONLY / work_use Unsupported다.

## 판단부터 사용까지의 창

`prepare_work(Task, WorkUsePort)`는 현재 소유한 비구동 ProcessReady 실행과 작성자가 선언한 readiness를 관측한다. 고정한 업무 역할은 `work/support-gap-report`, 관측 profile은 `diagnostics/support-summary`다. 작업 입력이 역할·카탈로그·issuer 정책을 대체하지 못한다. 외부 검증을 받은 F6 `VerifiedDecision`만 비공개·역직렬화 불가인 `Prepared`에 들어간다.

F6 위에 결속하는 것은 작업 ID, 요구치, 입력 digest, 현재 등록/revision, program/catalog, run/instance, 설정, 작성된 준비 의미다. 새 관측의 nonce와 시각까지 같아야 한다고 요구하지는 않는다. 대신 보고 payload와 준비 의미가 같아야 하며, 새 관측 시각은 결과에 남긴다. F6의 issuer·kind·context·policy·epoch·monotonic TTL·철회 검사를 약화하지 않았다.

`commit_work(&Prepared)`는 실제 사용 전 다시 관측하고, 판단 이후 바뀐 입력·준비 상태·맥락을 거절한다. 등록·실행은 같은 저장 트랜잭션 안에서도 다시 확인한다. 시험에서 외부 판단 뒤 실제 HTTP 보고 수치나 준비 필드가 바뀐 경우, 등록이 퇴역한 경우 각각 결과와 소비 기록이 생기지 않았다. 오래된 VERIFIED 표시나 저장 참조는 이 경로의 입력 타입이 아니다.

## 논리적 cut과 정확히 두 개의 시간 경계

사용과 완료의 기준은 **성공한 단일 원자 트랜잭션의 마지막 live 결정 검사, 즉 논리적 commit cut**이다. 나중의 물리적 commit IO 완료 시각을 같은 것으로 주장하지 않는다. 트랜잭션이 실패하면 완성된 업무 결과나 소비된 허가는 없다.

등록 revision과 소비 키는 SQLite `TransactionBehavior::Immediate`가 트랜잭션 시작부터 잡는 쓰기 락 아래에서 확인한다. 따라서 그 아래에서 바뀔 수 없다. 추가한 내부 receiving helper는 F6 철회 원장의 인프로세스 Mutex를 **전체 transact 호출 동안**, 실제 commit IO까지 포함해 보유한다. 그 사이에 들어온 철회는 락을 기다린다. 커밋된 결과를 소급해서 지우지 않고 이후의 수신 검사에 적용된다. 시험은 성공 커밋 중 도착한 철회뿐 아니라 rollback 중 대기한 철회가 다음 재시도를 `revoked`로 막는 경우도 확인한다.

남는 시간 경계는 정확히 둘이다.

1. **논리적 cut 이후 commit IO 중 TTL이 만료될 수 있다.** 어떤 락도 monotonic 시계의 흐름을 멈추지 않는다. 이때 성공적으로 커밋된 산출물은 남는다. 산출물이 말하는 유효성은 cut 시점이지 IO 완료 시점이 아니다. 지연 주입 시험에서 커밋 반환 시 proof가 Expired여도 결과와 소비 기록은 함께 보존됨을 확인한다.
2. **HTTP 자기보고와 SQL commit은 물리적으로 원자적이지 않다.** 관측값은 자기 관측 시각 기준이다. 결과는 F4의 observed_at, 실행 instance, 실제 작성자 ReportOrigin, source digest를 보존하며 commit 시각의 외부 세계나 지속 불변을 함의하지 않는다.

이 둘을 이유로 등록·소비·철회의 이미 닫힌 창까지 미확정이라고 쓰지 않는다. 반대로 이 두 경계를 닫았다고 과장하지 않는다.

## 중복, 응답 유실, 저장 실패

결과 키는 작업 ID로 유일하고, 결정 소비 키는 등록과 결정 ID로 유일하다. 같은 트랜잭션이 결과·소비·control event를 CAS로 기록한다. 중복 제출은 revision conflict이며 두 번째 결과나 두 번째 소비를 만들지 않는다.

결과 응답을 잃은 호출자는 `recorded_work(selection, operation)`으로 이력을 조회한다. 성공 commit 뒤 응답 오류를 주입해도 그 작업 ID로 결과를 찾고 재제출은 중복 거절로 간다. 외부 판단 응답 자체가 없으면 Prepared를 만들지 못하므로 업무는 시작되지 않는다.

두 레코드를 쓴 뒤 rollback을 주입한 시험에서는 둘 다 없었다. 메모리에서 허가를 먼저 소비하지 않았으므로 rollback이 허가를 되살리는 과정도 없다. 아직 살아 있는 Prepared로 재시도해도 모든 현재 검사를 다시 거친다. 그 사이 만료·철회·맥락 변경이 생기면 거절된다. 수신자가 재시작하면 epoch가 달라져 보유한 proof는 무효이고, 과거 결과 조회만 가능하다.

## 현재 허가가 될 수 없는 이력

`work_use::Report`는 Deserialize 가능한 별도의 이력 DTO다. 그 안의 결정 참조는 현재 lease가 아니다. 산출물은 다음을 이름으로 분리한다.

- signature_verification: EXTERNAL_SIGNATURE_AND_CONTEXT_VERIFIED_AT_LOGICAL_CUT
- operating_area_policy: NOT_EVALUATED_BY_HOST; PRODUCTION_PROVIDER_NOT_CONNECTED
- current_permission: NONE; HISTORICAL_WORK_RESULT_ONLY
- physical_qualification: NOT_PERFORMED

Report나 과거 WorkUseAssessment에서 Prepared를 만들 수 없고, Prepared의 외부 필드 생성과 역직렬화도 막힌다. 별도 OpenSSL 프로세스의 시험 키가 서명한 긍정은 시험 발급자의 키 소유와 정확한 맥락만 입증한다. 실제 운영 영역 서비스가 정책을 판단했다는 뜻이 아니다.

## 실제 상주 연결과 보존 범위

구현은 [rx-solutions 2b0c4a35](https://github.com/jack0682/rx-solutions/commit/2b0c4a35631e55817a2f1a75e30eb396b448bfa4)와 [PR 32](https://github.com/jack0682/rx-solutions/pull/32)에 고정한다.

기존 한 바이너리의 `rx-solutionsd run CONFIG WORK_TASK`가 선택적인 업무 요청을 받는다. 선택된 status 프로세스의 시작 단계가 끝난 뒤 한 번 평가하고 `rx.work-use-result.v1`을 출력한다. 출하 Program·카탈로그·앵커·digest는 그대로이며 긍정 provider도 추가하지 않았다. 실제 출하 데몬 장면에서는 업무가 이름 붙은 이유로 거절되고 데몬과 health GET은 정상 유지됐다. supervisor 밖의 관찰자가 등록 DB의 업무 결과·소비 행이 0개임도 확인했다.

긍정은 실제 설치된 release count를 읽는 동일 수신 코드에 **별도로 작성한 시험 카탈로그와 외부 시험 발급자**를 연결해 검증했다. 제품 데몬의 운영 승인 양성 경로를 제공했다고 주장하지 않는다. 기존 library 32단계, resident, resource, manager-loss 통과선은 별도로 유지한다.

새 네트워크 API·daemon·서비스·DB 파일은 없다. `registration.db` 안의 결과·소비 문서 schema와 로컬 Rust API가 추가됐다. Program의 Deserialize 부재, F5 진단 의미, F6 기본 앵커 부재, F7 등록 소유/digest 거절, F8 자원 집행, F9 관리자 상실 경계는 보존한다. 공유 SDK·wire/proto·규범 본문·rx-platform·rx_ws/linux는 변경하지 않는다. 예전 writer가 새 업무 schema를 집행한다는 downgrade 호환성은 주장하지 않는다.

원시 명령·성공과 실패·이미지 및 바이너리 해시·검사 집계는 [검증 근거](../references/work_judgment_2026-09-24/README.md)에 남긴다. 이 칸은 비구동 업무의 수신 관문이다. 실제 운영 영역 정책 서비스, 물리 동작, 다중 호스트 및 전체 프레임워크 적격은 별도 범위다.
