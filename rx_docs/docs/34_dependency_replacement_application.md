# F11 의존 교체의 명시적 적용

구현 고정: [rx-solutions 0591b6f0](https://github.com/jack0682/rx-solutions/commit/0591b6f0283423db7c220c797abc683096c4373b).

2026-09-24 · 비구동 진단 Consumer API의 적용 경로다. 운영 영역 판단 서비스, 물리 인계, 상시 감시나 새 상주 CLI를 만들지 않는다. 서명 검증·운영 판단·적용 효과·현재 권한을 구별한다.

## 선택을 바꾼 관측

advance와 inspect는 매번 load_binding으로 공유 결속 행을 다시 읽는다. Run에는 binding ID만 있고 제공자 스냅샷이 없다. 따라서 “새 배정만 변경하면 기존 작업은 전에 읽은 제공자를 유지한다”는 시간 경계는 존재하지 않았다. 격리된 이전 소스에서 실제 HTTP 제공자 A/B를 띄우고 공유 행을 제자리 수정하자, 이미 진행 중이던 result-generation 작업이 B를 소비했다. 이 반례 개입은 제품 교체 API가 아니다. [원시 반례](../references/dependency_replacement_2026-09-24/binding-read-probe.txt)를 보존한다.

선택한 D는 **불변 결속 판본과 관계별 하나의 활성 경로**다. 이전 작업은 v1 ID를 계속 읽고, 별도 명시적 적용이 활성 경로를 v2로 바꾼 뒤 새 배정은 v2를 받는다. v1의 내용이 불변이므로 고정은 호출 타이밍에 의존하지 않는다. 첫 적용 전에는 원 결속이 세대 0의 암묵적 경로이며, 첫 적용이 이전 판본도 봉인한다. 관측으로 generation이 이미 고정된 의존 결속만 교체할 수 있다. 관측하지 않은 원 제공자를 소급 확정하지 않는다.

## 승인은 적용이 아니다

`prepare_replacement(ReplacementIntent, BindingJudgment)`는 저장소를 변경하지 않는다. 승인 맥락에는 application ID, 기존 경로와 revision, 기존 결속과 revision, 새 결속 ID, 제안한 제공자 등록/revision과 generation이 들어간다. F6의 issuer, kind, owner, 운영 영역, profile, policy, context, receiver epoch, monotonic TTL과 철회 검사를 그대로 쓴다. 호스트는 긍정 판단을 발급하지 않는다.

별도 호출 `apply_replacement(&PreparedReplacement, Source)`만 경로를 바꾼다. 후보의 현재 보고를 다시 관측하고 작성된 의존 조건과 고정 신원을 검사한다. 같은 트랜잭션 안에서 등록 적격성과 경로/revision을 다시 검사한다. 기존 `assess_binding`의 “not work-use permission, physical truth or automatic replacement” 이유 문자열은 그대로 참이다. 이전 수용 assessment를 적용 proof로 바꾸지 않으며, Prepared의 비공개 필드 접근·역직렬화·assessment/receipt 변환은 컴파일 거절된다.

출하 카탈로그는 여전히 앵커가 없다. 기본값에서는 이름 붙은 사유로 교체를 거절하지만 진단 작업은 완료할 수 있다. 긍정 시험은 별도 작성된 시험 카탈로그와 외부 OpenSSL 시험 발급자다. 실제 운영 영역 정책의 승인이나 물리 적합성을 증명하지 않는다.

## 하나의 경로와 진행 중 작업

`assign_current(root, Source)`는 활성 판본을 선택한다. 관측 중 경로가 바뀌어도 새 작업 커밋 내부에서 다시 검사하여 오래된 배정을 거절한다. 진행 중 작업의 begin/poll/finish에는 활성 경로를 따라가라는 규칙을 붙이지 않는다. 각 작업은 원래 ID의 봉인된 판본을 읽는다. 과거 결과도 원 판본을 유지한다.

**drain barrier는 두지 않는다.** 이 범위의 관계는 비구동 진단 입력이다. 관계당 이후 배정 경로가 하나이고 작업당 결속이 하나이며, 진행 중 v1 작업과 새로운 v2 작업의 동시 존재는 같은 물리 자원에 대한 이중 소유가 아니다. 기존 A 프로세스를 중지하거나 B에 PID/장비 권한을 인계하지 않는다. 독점 물리 자원의 인계로 확장하려면 별도 책임과 검증이 필요하다. A로 복귀할 때도 새로운 승인·명시적 적용·새 판본 ID가 필요하다.

## 원자성과 장애

기존 등록 저장소의 단일 트랜잭션이 새 결속과 불변 membership, 하나의 경로 CAS, application 영수증, 유일한 결정 소비 및 control events를 함께 커밋한다. 추가 DB 파일·데몬·서비스는 없다. 동일 기준 revision의 동시 적용 두 개는 하나만 성공한다. 첫 적용 후 membership이 없는 다른 경로로 새 판본을 다시 열 수 없다. 판본 digest가 달라지면 무결성 오류다.

- 새 결속을 쓴 직후 주입한 부분 실패는 모든 쓰기를 되돌리고 이전 경로와 기록을 보존했다. 살아 있는 proof를 재시도할 때도 현재 검사를 다시 한다.
- 성공 commit 뒤 응답을 잃어도 `recorded_replacement(application)`으로 영수증을 찾는다. 재제출이 두 번째 경로나 소비를 만들지 않는다.
- 실제 별도 관리자 프로세스를 SQL commit 전 또는 commit 후 응답 전 SIGKILL했다. 외부 부모가 DB를 다시 열었을 때 전자는 원 경로, 후자는 새 경로 하나와 영수증을 남겼다. 원 run/binding은 두 경우 모두 보존됐다. 경로만으로 소스 소유권이나 현재 준비가 복원되지 않아, NoSource로 새 배정은 진행하지 못했다. 시험의 pidfd 기반 고아 정리는 fixture 소유 프로세스 정리이며 RX의 프로세스 인수가 아니다.

수신자 재시작은 이전 proof를 무효화한다. 영수증은 이전/새 결속, 결정 참조, 후보 관측의 시각·실행 신원과 provenance를 담는 이력이다. current_authority는 NONE, process_ownership은 UNCHANGED/NO_PID_ADOPTION, physical_handover는 NOT_ASSESSED, work_use는 Unsupported다. 등록 revision이 바뀌어도 옛 이력은 읽을 수 있지만 현재 카탈로그로 옛 결속을 재해석하여 교체할 수 없다. 64개 결속 보존 한도에 도달하면 명시적 archival 정책이 필요하다는 오류로 멈추며 자동 삭제하지 않는다.

## 적용 시점과 남는 시간 경계

논리적 cut은 **성공한 원자 트랜잭션의 마지막 live 결정 검사**다. SQLite Immediate 쓰기 락이 등록·경로·소비 변경을 직렬화하고 F6 원장 Mutex를 전체 transact 및 물리 commit 동안 보유하여 철회가 끼어들 수 없다. F10과 같은 두 시간 경계가 남는다. TTL은 cut 이후 commit IO 중 만료될 수 있고, HTTP 보고는 자기 관측 시각 기준이므로 SQL commit과 원자적이지 않다. 영수증을 지속 가용성이나 현재 허가로 읽지 않는다.

## 명시적 확인과 감시의 구분

Inspection, Routing, 영수증은 CheckpointPolicy를 출력한다. 정해진 주기나 최대 감지 지연은 없다. 호출자가 다음 확인을 하지 않으면 상실을 언제 감지할지 보장하지 않는다.

| 의존 의미 | 현재 관측 시점 | 상실의 영향 |
|---|---|---|
| preparation-only | ASSIGN에서 입력 확보, 이후 확보 입력 사용 | 확보 전 상실은 배정을 막음; 확보한 입력은 뒤의 소스 상실만으로 무효화하지 않음 |
| result-generation | FINISH에서 입력 확보 | 결과 생성 시 상실이면 완료를 보류 |
| continuous | 명시적 ASSIGN/BEGIN/POLL/FINISH마다 관측 | 다음 해당 호출에서 진행 또는 결과 소비를 보류; 호출 사이를 감시했다는 뜻 아님 |
| INSPECT / APPLY | INSPECT는 의존 제공자, APPLY는 교체 후보 관측 | 진단/적용 시점의 조건 판정 |

다음 필요한 관측에서 알려진 상실·신원/보고 변경은 NOT_MET, 증거 부재는 NOT_EVALUATED다. 영향 작업의 전이와 결과 소비를 보류하며 원 기록은 지우지 않는다. 실제 시험에서 A 상실 후 기존 continuous 작업과 결과 소비는 보류되고, B의 새 작업과 무관한 진단은 계속됐다. 자동 중지·재실행·재교체는 하지 않는다.

## 연결 수준과 호환 영향

구현은 기존 diagnostic Consumer **애플리케이션 API**에 연결됐다. 실제 Linux HTTP 프로세스로 정상 적용, 진행 중 고정, 부분 실패, 응답 유실, 관리자 상실을 실행했다. 새 resident routing CLI나 실제 운영 영역 provider는 연결하지 않았다. 상주 서비스 전체의 교체 완성, 물리 인계, 다중 호스트, 안전·품질·처리량 검증을 주장하지 않는다.

네 개의 등록 문서 schema와 로컬 Rust API, Inspection의 추가 출력이 생겼다. 기존 Catalog/TrackedBinding/Run의 저장 형식, Program 직렬화, 출하 카탈로그/digest, SDK·wire/proto·규범 원문은 바뀌지 않았다. 이전 writer는 새 경로 규칙을 모르므로 downgrade 쓰기 호환성을 주장하지 않는다. F7/F8/F9/F10 및 기존 library32/resident/resource/manager-loss/work 통과선은 별도 회귀 검증이다.

[원시 명령·출력과 검증 집계](../references/dependency_replacement_2026-09-24/README.md)는 반례와 개발 중 실패도 보존한다. 실행하지 않은 범위를 테스트 개수로 대체하지 않는다.
