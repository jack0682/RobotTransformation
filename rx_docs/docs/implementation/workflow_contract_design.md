# W01 — Workflow 저작·실행 계약 설계

2026-10-01. [세부 개발 계획](framework_delivery_plan.md)의 W01 산출물이다. 아래 새 계약과 API는
**구현할 설계**이며 현재 서버의 지원 선언이나 frozen v1 규범의 대체가 아니다. 현재 소스와
[API 조사 자료](../../references/workflow_contract_design_2026-10-01/api_inventory.json)를 먼저 대조했다.
자료의 route 존재는 종단 간 사용 가능성이나 실행 권한을 입증하지 않는다.

## 1. 기존 경로의 재사용과 확장

| 사용자 기능 | 현재 경로 | 판정 / 다음 변경 |
|---|---|---|
| 초안 저장·목록·버전 | HTTP process-drafts/process-draft → runtime → process_draft writer | 저장 원자성·CAS·원 요청 복구 재사용; 현재 cell 소속/v1 소스 경계 보존 |
| 동작 연결·컴파일 입력 | process-draft-bindings, binding-options, process-draft-compile-input | 기존 ActionBinding/DeviceSource와 정확한 revision 묶음 재사용 |
| 패키지 검토·설치 변경 | package-intakes, process-reviews, process-changes | 새 게시 버전과 패키지의 provenance를 연결; 검토/설치/실행 상태를 합치지 않음 |
| 작업 준비·시작 | HTTP runs/start-context/start-attempt/runs/start, 셀 시작 계약 | 공개 base Workflow.StartRun의 stub을 무조건 채우지 않음; terminal/셀 권한 경로 유지 |
| 실행 추적 | checkpoint/artifact, executor snapshot/frontier | Node/Port/Edge/visit 참조 확장; UI에서 별도 실행 상태를 확정하지 않음 |
| 일반 구성요소 수명 | components, resident-executions, reporting/execution gRPC | 등록/배정/관측 재사용; Task 완료와 프로세스 종료 구별 |
| 복구·재시작 | Host recovery, settlement, case, R7 source 조사 | 현재 서로 다른 책임을 보존해 UI 연결; R7 승인/확인/새 실행 및 case restart 미완 |
| Task/Object/Resource/Property 정의 | 해당 범용 카탈로그 API 없음 | 버전 있는 정의 저장·resolver·편집 UI 추가 |
| 일반 영역 관리·영역 간 위임 | 독립 영역 writer/위임 API 없음 | 로컬 셀 권한을 자동 승격하지 않는 영역 범위 계약 추가 |
| Journal 구독 | 현 ingress 서비스 등록 없음, UI polling | cursor/snapshot/gap/보존 계약 완료 후 추가; 내부 control-journal의 순번을 곧바로 공개하지 않음 |

gRPC의 UNIMPLEMENTED는 조사 JSON에 실제 함수명/문구로 남겼다. 대체 HTTP가 존재하는 경우에도
caller 역할과 terminal/계약이 다르므로 같은 의미라고 단정하지 않는다. W07–W15에서 각각
구현/명시적 대체 경로/예약을 공개 문서와 SDK에 일치시킨다. 단순 삭제로 계약 공백을 숨기지 않는다.

## 2. 데이터 신원과 저작 경계

새 저작 자료는 WorkflowDraft, DefinitionRevision, ResolutionReport, PublishedWorkflow,
DeploymentReference로 나눈다. 자료는 P의 기존 repository/writer에서 기록하고 공정 실행기는 S에 둔다.

| 자료 | 최소 계약 | 생성/소비 |
|---|---|---|
| ScopedRef | domain ID, kind, 원 local ID, revision, content digest | 새 영역 간 참조에 사용; 기존 ID/기록은 재발급하지 않음 |
| WorkflowDraft | ID, owner scope, expected revision, metadata, source schema/document, presentation | Engineer 저장; writer가 내용/기록/원 요청 결과를 함께 commit |
| DefinitionRevision | 종류, ID/revision/digest, 타입 있는 body, 정확한 부모/의존 참조 | Engineer 정의; 순환·없는 참조·권한 없는 참조 거절 |
| ResolutionReport | Workflow/정의/입력 digests, 대상별 값·출처, constraints, 후보/제외 이유, issues | 순수 resolver 출력; 서버가 입력 일치/현재 접근을 확인 |
| PublishedWorkflow | 정확한 source/definition/resolution/compiler 버전, 검토/승인 참조 | Verifier 검토 뒤 ReleaseManager 게시; 운영 시작 권한 없음 |
| DeploymentReference | 게시 artifact, 설치/영역, 적용 configuration/revision, 상태 | 기존 package/change/qualification 경로에 연결 |
| ExecutionTrace | run/activation/operation, source node/port/edge, visit/call/iteration, 기록 출처 | 원장에 확정된 실행/판단 결과의 read projection |

기존 Principal.cells는 영역 권한 목록이 아니다. 새 영역 권한은 별도 명시적 scope로 부여하고
기존 계정의 셀 접근을 영역 전체 접근으로 변환하지 않는다. 이 이행이 끝나기 전 신규 영역 저작 API는
닫혀 있어야 한다. 기존 cell draft 경로는 기존 역할과 scope로 계속 동작한다.

새 저작 API는 `/api/v1/workflow-drafts`(목록/저장), `/api/v1/workflow-draft`(정확한 revision 조회),
`/api/v1/definitions`(목록/저장), `/api/v1/definition`(revision 조회),
`/api/v1/workflow-resolutions`(입력 고정 계산/검증), `/api/v1/workflow-publications`(검토한 버전 게시)
계열로 분리한다. 이는 추가할 경로다. 기존 process-drafts의 엄격한 v1 decoder를 묵시적으로 바꾸지 않는다.
전송 wrapper는 기존 request_key/command와 identity 생성 경계를 재사용한다. 읽기도 현재 역할/scope를 확인한다.
설치/운전 명령은 이 새 API가 직접 수행하지 않고 기존 package/change/run 경로에 연결한다.

모든 새 decoder는 schema/unknown field/크기·복잡도 상한을 검사한다. initial authoring 한도는 기존의
512KiB 문서, 128 flow, flow당 1024 node, 4096 expanded node, depth64를 넘겨 기본 허용하지 않는다.
새 실행 IR의 동적 Loop는 unroll 결과 대신 runtime visit 예산도 검사한다. 한도 초과는 명시적 진단이다.

## 3. 그래프와 실행 의미

새 소스 schema는 `rx.workflow-source.v1`로 별도 식별한다. 기존 `rx.process-source.v1`은 그대로
보존한다. 새 compiler/IR/trace는 정확한 지원 schema를 광고하고 지원하지 않는 버전을 거절한다.
이 source schema 추가가 기존 base/cell wire의 변경을 요구하면 해당 frozen 계약의 v1.1 영향 절차를 먼저 밟는다.

Graph는 entry, nodes, typed output ports, edges, 중첩 제어 scope를 갖는다. 단일 출력 포트에는
한 전이만 연결하고 fan-out은 Parallel로 표현한다. 순서는 edge이며 좌표나 배열 순서가 아니다.
각 scope는 하나의 entry와 명시적 완료 지점을 갖는다. 임의 back-edge는 거절하고 Loop만 반복한다.
공통 후속 노드로의 배타적 합류와 병렬 Join을 구분하며 서로 다른 loop/scope로 건너뛰는 연결을 거절한다.

| 종류 | 성공/선택 의미 | 실패·미결 의미 |
|---|---|---|
| Task | TaskDefinition/선택 Skill을 bound intent/operation으로 연결, 근거 있는 결과로 전이 | command 접수/idle은 성공 아님; UNKNOWN은 failure와 다르게 보류 |
| Branch | 조건 포트의 명시적 우선순위에서 첫 PASS; 이전 조건이 전부 FAIL일 때만 뒤 포트 선택 | 앞선 조건 UNKNOWN이면 뒤/default로 우회하지 않음; default는 모두 FAIL일 때만 |
| Condition | 기존 All/Any/Eq/Range/SetContains의 삼값 의미 재사용 | Any는 유효 PASS가 있으면 다른 UNKNOWN과 함께 PASS 가능; 이를 Branch 우선순위와 혼동하지 않음 |
| Parallel All | 같은 activation에서 자식별 신원으로 실행, 모두 성공/의무 정산 후 성공 | 한 실패 시 신규 자식 시작 중지, 실행 중 자식의 정지/종료·잔여 의무 추적 |
| Parallel Any | 최초 committed 성공이 승자; 동시 후보는 원장 commit 순서로 결정; 승자 확정 후 후속 경로 진행 가능 | 나머지 cancel/완료/정산 의무는 유지; 후속의 충돌 자원 사용과 전체 Run 종결은 정산 전 거절 |
| Wait | 시간/조건/이벤트/자원별 조건을 만족한 committed 판단으로 전이 | deadline 만료는 해당 scope timeout; 자원 관측 PASS는 실제 claim 취득을 대체하지 않음 |
| Loop | 횟수 또는 각 회차 시작의 조건, max_iterations와 deadline, 반복별 visit | UNKNOWN은 재판정/보류, 상한 도달은 명시적 제한 결과; 무한 반복 기본값 없음 |
| Call | 정확한 하위 Workflow revision, 명시적 입력/결과 매핑, 독립 call path | 재귀 거절; 오류 위치에 전체 call path 보존 |
| Handoff | 원 물체/작업/자원과 송신·수신 책임, 준비/수락/이전/확인 | timeout/응답 유실은 자동 완료/해제/재할당 아님 |
| End | scope 결과를 반환, root는 관련 수행/인계 의무까지 검사 | 미결 obligation을 건너뛰어 전체 성공으로 닫지 않음 |

Task의 Event 출력은 계약에 정의한 상관 event만 받는다. 이벤트 도착이 Task/operation 완료를
의미하지 않는다. 한 node visit의 전이 결정은 첫 유효 trigger의 commit으로 한 번만 소비한다.
Event가 선택되면 후속 경로는 진행할 수 있지만 원 operation은 계속 추적하는 의무로 남는다.
그 뒤 도착한 success/failure는 같은 visit의 두 번째 경로를 만들지 않고 원 결과/미결 의무를 갱신한다.
원 작업의 후발 실패는 정의된 실패정책/개입에 연결하고, 충돌 자원 사용과 전체 성공 종결을 재검사한다.
서로 독립적인 이벤트 감시 경로 여러 개는 Parallel 안의 Event Wait로 명시한다.
의무·자원 충돌로 대기하는 이유와 아직 실행 중인 원 Task를 Inspector/Preview에 함께 표시한다.

Failure/Timeout 출력은 오류 정책이 소비한 뒤의 명시적 분기다. 동일 실패에서 자동 retry와
failure edge를 동시에 시작하지 않는다. Retry/Rebind/Reassign은 유한 예산을 소모하며 원 시도와
후속 시도의 ID를 구분한다. 원 effect 불명이면 원 요청 조회/조사가 우선이다.

### 기존 소스 변환

변환은 기존 자료를 수정하지 않고 새 초안과 source map을 만든다. 기존 node ID는 map에 유지한다.
Sequence children은 번호 순 연결로, ParallelAll은 Fork/Join scope로, Branch는 true/false/default
선택 scope로, Repeat는 유한 Loop로, Call은 정확한 하위 flow 참조로 옮긴다. Operation은 기존
binding 참조를 보존하는 Task 형태이며 Wait/Intervention도 기존 조건/절차 참조를 보존한다.
변환 전후의 정상·실패·UNKNOWN·인계 대기 trace가 달라지는 입력은 자동 변환을 거절한다.
특히 기존 binary Branch의 FAIL을 default로 매핑할 때 UNKNOWN까지 default로 보내면 안 된다.
새 기능을 사용하는 그래프의 v1 역변환은 지원하지 않는다. 신규 IR과 BT plugin 지원이 없으면 실행을 거절한다.

## 4. 정의·resolver·로봇 선정

PropertyDefinition은 타입/단위/허용 범위/override 허용과 지원 연산을, TaskDefinition의 property
사용은 **순서 있는 source chain**을 가진다. HTML의 property별 chain 방식을 유지하고 전역 우선순위를
새로 강제하지 않는다. Object/Resource에서 파생된 값은 실제 rule revision을 참조해야 하며
UI에서 편집한 rule과 하드코딩 계산을 분리하지 않는다.

chain은 override/object/resource/property-set/default/runtime-input 등의 허용 source를 명시한다.
첫 사용 가능한 값을 택하되 잘못된 타입·단위·충돌은 '없음'으로 취급해 뒤 값으로 숨기지 않는다.
false/0/빈 허용 집합과 누락을 구분한다. required runtime 값은 설계 때 Deferred이며 실행 입력으로 재검증한다.
Resource 값은 instance→model→type의 정확한 부모 참조로 해석한다. 순환은 거절한다.

Object의 유형 범위는 후보 모델 범위/증거이며 실제 소재가 아니다. 범위의 중간값을 실행값으로 쓰지 않는다.
Target Group은 순서 있는 실제 대상 항목으로 확장하고 대상별 값을 보존한다. 합쳐진 min/max는 설명용이다.
한 대상의 값으로 다른 대상의 실행값을 채우지 않는다. 실행 입력은 게시된 허용 범위 안에서만 바인딩한다.

순수 resolver의 연산은 typed lookup/선택/유한 수치 연산/명시 단위 변환/범위 집계다. 스크립트·네트워크·
현재 시간 접근은 없다. 관측의 freshness/세대/품질 판정은 기존 condition 계약을 사용한다.
단위가 맞지 않거나 알 수 없는 연산은 오류이며 새 수식을 조용히 무시하지 않는다.

ConstraintReport는 대상/자원 자체의 적합성과 robot Capability/Skill 매핑·spec·현재 readiness를 나눈다.
후보 선정은 이유 있는 후보 집합일 뿐이다. 실제 allocation은 기존 P의 자원/권한 검사로 확정한다.
최초 자동 선택은 적합 후보 중 명시적 선호 순위와 stable ID tie-break를 사용하고 선택 근거를 기록한다.
성능/최적성은 이 결정적 기본 선택의 보장이 아니다. 경쟁으로 거절된 후보를 바꾸는 행위도 retry 예산에 포함한다.

## 5. 우리 공정에 적용하는 수락 예시

| 예시 | 저작 입력 → 해석 | 실행에서 확인할 것 |
|---|---|---|
| 듀얼 교환 | grasp_slots=2, incoming/finished 별도 ID, alignment-station 참조 | incoming 정렬 후 대기; finished는 다른 slot; 착좌 후 Clamp/Release |
| 싱글 교환 | grasp_slots=1 | finished 배출 전 incoming 파지 배정 거절; 이후 정렬/삽입 |
| 버퍼 싱글 | 명시 buffer instance·지지/점유 조건 | buffer 미선택이면 오류; 지지 확인 없는 Release 거절 |
| 회전 정렬 | 독립 station readiness/점유/detect/rotate/aligned/stopped | 손목 회전 대체 금지; unknown stopped는 regrip을 통과시키지 않음 |
| 품목/작업면 | ECC 계열→PART1, CVR_F front→PART2/back→PART3, FLANGE_L→PART4, FLANGE_R→PART2 | 장착 지그·툴링·교정 대조; 자료 색상을 실제 핑거 ID로 사용하지 않음 |
| Failure/Timeout | 알려진 정렬 실패는 개입 경로, 요청 유실은 원 operation 조사 | 오류 branch 이동과 물리 명령 replay를 구분 |
| Parallel Any | 대체 관측 두 경로 중 첫 성공 | 독립 후속 작업은 진행; 다른 수행이 점유한 공유 자원 작업과 전체 종결은 정산까지 보류 |
| 영역 간 공급/처리 | domain A 원 물체/작업 → domain B scoped 수락 | ACK 유실 후 원 인계 조회; 중복 소유·새 효과 금지 |

실제 파지/회전 지지 방법과 수치가 없으므로 물리 실행 profile은 incomplete다. software profile은
별도의 simulation 사실/값을 명시해 검증한다. 최초 투입/마지막 배출은 steady-state 교환과 별도 entry다.
공정 전용 필드를 Graph 코어 enum에 추가하지 않는다.

## 6. 복구·영역 간 연결의 추가 기록

R7의 원 assignment/observation과 별도 disposition을 유지한다. disposition은 범위가 확인된
claim만 정산하며 과거 UNKNOWN을 성공으로 바꾸지 않는다. source receipt와 새 실행 준비/허가를
분리하고 기존 Supervisor/Host/Executor gate를 우회하지 않는다. 무효한 old reader는 닫힌 상태로 거절한다.

영역 ID는 설치 ID와 별개다. 설치 복원/교체가 다른 영역을 자동 생성하거나 그 영역의 권한을 승계하지 않는다.
영역 관리 등록 시 신뢰 관계, signer, allowed scope, generation을 명시하고 관리자의 기존 셀 권한과 구분한다.
Delegation은 issuer/receiver 영역, 원 request, 허용 Task/자원/작업량/기한, 세대, 내용 digest를 묶는다.
Handoff는 prepare/accept/transfer/confirm과 각각의 원 receipt를 기록한다. 출발 영역이 책임 이전을
확정한 근거를 받기 전 대상 영역은 해당 인계 자원으로 새 작업을 시작하지 않는다.

각 영역은 자신의 writer만 갱신한다. 응답 유실 시 persistent pending을 유지하고 원 요청을 대조한다.
단절 중 원격 철회를 즉시 안다고 가정하지 않는다. 이미 받은 유한 권한의 조건만 사용하며, 만료 후 새
admission은 중지한다. 사용 중 작업의 종료/불명/보호는 해당 실행 계약을 따른다. 재연결은 상태 대조를
시작할 뿐 권한 갱신이 아니다. 위임 만료만으로 remote 자원/효과가 없었다고 판정하지 않는다.
시계 불확실성 안에서 유효 범위를 증명할 수 없으면 거절한다. 다른 clock_id의 tick을 직접 비교하지 않는다.

## 7. 후속 구현 게이트

### W03의 기존 cell draft library 확장

새 영역 저작 scope는 W04/W19의 명시적 권한 계약으로 남긴다. W03은 현재 cell에 속한 초안의
목록/분류/보관/이력을 기존 writer에 연결한다. site/service는 이 단계에서 **분류용 label**이며
새 영역/현장 등록, 존재 검증, 접근 권한 부여가 아니다. 후속 Definition/ScopedRef로의 연결은 별도다.

- Save/Version/Summary에 optional `library {site, service, archived}`를 더한다. 생략 시 기존 값을
  유지하고 오래된 기록은 분류 없음/활성 초안으로 읽는다. 보관도 같은 원 요청·CAS·불변 revision이다.
- 보관된 초안은 조회/이력/복제가 가능하다. 기존 client의 library 생략 저장은 보관을 풀거나 편집하지 못한다.
  `archived=false`를 명시한 복원 이후 편집한다. 복제는 새 ID의 활성 초안이며 원본을 바꾸지 않는다.
- 목록의 q/site/service/archived 조건은 권한을 확인한 cell 안에서 pagination 전에 적용한다.
  조건을 생략한 기존 API의 전체 목록 의미는 유지하고 UI는 활성/보관/전체를 명시적으로 선택한다.
- `/api/v1/process-draft-history`는 cell/id/before revision으로 최대 50개의 최신순 summary를 반환한다.
  원 document/layout은 기존 정확한 revision 조회로 읽는다. 과거 버전 편집은 새 초안 복제로 한다.
- 분류/보관은 source digest, 설치된 configuration, 실행/게시 상태를 바꾸지 않는다. Published 상태는
  W14의 실제 게시 계약 전에는 만들지 않는다. 새 optional 필드를 읽는 strict client는 함께 갱신한다.
- 수락 시험: 50개보다 뒤에 있는 검색 결과, cell/역할 격리, 같은 key 복구, stale revision,
  보관 뒤 old-client 편집 거절/명시적 복원, 변경 전 이력·좌표 보존, 실제 UI 검색/보관/복원/이력 복제.

- W02: 기존 v1 저작/좌표 저장을 검증·통합한다. 신규 그래프 의미의 지원으로 표시하지 않는다.
- W03/W04: 영역 authoring scope 및 새 draft/definition 저장 계열을 연결한다. 새 권한 scope가 닫힌
  상태를 UI에서 설명하고 기존 cell authoring은 보존한다.
- W05/W06: 같은 source chain/정의 revision이 실제 계산/후보 설명에 사용되는 계약 시험을 둔다.
- W07/W08: 확인된 기존 복구 결함과 이행/재시작을 해결한다. UI 진척과 별도 필수 게이트다.
- W09–W12: 새 source/IR/compiler/frontier/BT plugin을 함께 구현하고 v1 변환 비교 및 위 예시를 실행한다.
- W19–W21: 독립 영역/시계·유실·단절/재합류를 실제 분리 프로세스와 호스트로 검증한다.

W01은 소스 대응과 설계 명세다. 위 예시는 아직 새 형식으로 실행한 시험 결과가 아니다.
실제 구현 단계의 green unit test를 다른 층의 완료 증거로 올리지 않는다. 계약·데이터 이행과
사용자 결과를 같은 작업 묶음에서 검증하고 [세부 계획](framework_delivery_plan.md)의 상태를 갱신한다.
