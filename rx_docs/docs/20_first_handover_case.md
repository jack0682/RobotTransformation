# 20. 첫 비산업 인계 사례: 출입구에서 로봇 간 소포 인계

기준일: 2026-09-14 · **사례 정의. 구현·모의 검증·실물 검증·운영 준비를 뜻하지 않는다.**

실내 로봇이 건물 출입구의 인계 구획에서 소포 한 개를 실외 로봇의 적재함에 넘긴다.
이 문서는 [로드맵 N1](00_design_roadmap.md)의 일곱 항목과
[제품 정의 §4](01_product_definition.md)의 네 물음을 값으로 채운다.
기존 규범이 표현하는 의미와 이 사례에 필요한 미결을 드러내어 N2의 계약 대조와
N3의 반례 작성에 넘긴다. 규범·API·schema·실행 가능한 profile을 새로 선언하지 않는다.

## 1. 사례의 값과 경계

아래 식별자는 이 문서 안의 사례 값이며 신규 wire 필드나 구현된 인스턴스 이름이 아니다.
실제로 관측한 현장을 기술한 것이 아니라, 대조할 입력을 고정한 것이다.

| 항목 | 이 사례의 값 |
|---|---|
| 시작 | 건물 `SITE-01`의 출입구 `BAY-01`에서 실내 로봇 `IN-01`이 소포 `PKG-01`을 그리퍼로 지지한다. 실외 로봇 `OUT-01`은 비어 있는 적재함 `TRAY-01`을 가진 채 인계 위치에 도킹해 있다. 요청자 `CLIENT-01`이 이 소포의 로봇 간 인계 한 건을 요청하는 순간부터 기록한다. |
| 끝 | `PKG-01`이 `TRAY-01`에 지지·유지되고 `IN-01`의 그리퍼가 소포에서 분리되어 인계 구획 밖으로 물러난다. 수령 확인자 `RECIPIENT-01`의 인수 선언과 §4의 완료 근거가 기록된 지점에서 끝난다. 실외 운송 출발과 목적지 배송은 이 사례 뒤의 작업이다. |
| 참여자 | 보내는 역할은 `IN-01`과 그 장치 명령·관측을 맡는 `HOST-IN`, 받는 역할은 `OUT-01`과 `HOST-OUT`이다. 플랫폼 `RUNTIME-01` 한 개가 두 Host의 operation 의도·판정·권한 원장을 소유한다. `CLIENT-01`은 요청자이고 `RECIPIENT-01`은 사람인 수령 확인자 겸 현장 개입 담당자 한 명이다. |
| 물품 | 책 한 권이 들어 있는 봉인된 소포 `PKG-01` 한 개. 소포 표면의 식별 표지를 인계 전후에 대조한다. 표지 관측은 표지가 붙은 소포의 식별 주장이고 내용물·봉인 진위 보증은 아니다. 인계 중 소포 교체·재포장은 허용하지 않는 사례다. |
| 자원 | 실내 주행·그리퍼 제어 자원, 실외 주행·적재함 제어 자원, 적재 공간 `TRAY-01`, 공유 인계 공간 `BAY-01`, 같은 소포·인계 세대 `PKG-01/HG-01`의 지지 자원을 구별한다. 그리퍼와 적재함의 동시 지지는 허용하되 두 쪽의 동시 지지 해제는 허용하지 않는다. |
| 사람 개입 | 정상 경로에서 `RECIPIENT-01`은 물품 이동 구획 밖에서 인계를 확인하고 소포·받는 로봇·확인 시점·절차 revision을 특정한 인수 선언을 한다. 직접 물품을 받는 두 번째 물리 인계는 없다. 소포에 손을 대거나 구획에 진입하는 경우에는 정상 경로를 벗어나 개입·재확인·명시적 재시작 대상으로 기록한다. 사람 식별·수령 절차의 확정은 `OPEN-RECEIPT`다. |
| 최종 완료 조건 | §4의 접수, 실제 전달, 인수 확인, 전체 완료 근거가 같은 인계 건으로 연결된다. 필요한 operation 결과가 기록되고, 수령 선언이 그 근거와 모순되지 않으며, 보내는 제어 자원을 다음 작업에 넘길 별도의 해제 조건이 확인된다. `OUT-01`이 남아 있는 `BAY-01`과 소포 유지 자원은 점유를 계속 기록한다. 미해결 결과·모순·관련 개입이 남아 있으면 전체 완료를 주장하지 않는다. |

토폴로지는 **같은 사이트의 주 컴퓨터 한 대, authoritative Runtime 한 개, 두 Host,
하나의 `CellDefinition`에 등록하는 실내·실외 두 operating scope**로 고정한다.
두 scope는 인계 구획과 소포 지지 자원을 공유한다. 운영 영역은 실행 책임·정책의 범위이고
Runtime 수와 같은 개념이 아니다([제품 정의 §3](01_product_definition.md),
[공통 계약 Scope](contracts/v1.0/README.md), [셀 계약 §1·6](cell_operations/v1.0/01_scope_conditions_functions.md)).
건물 안팎이라는 위치만으로 독립된 두 Runtime을 가정하지 않는다.

출입문은 이번 동작의 참여자로 추가하지 않는다. 시작 시 인계 구획이 확보된 조건을
사례 입력으로 두며, 자동 문 제어·공공 통행로 운행·출입문 보호 기능이 확인됐다고
주장하지 않는다. 실제 설치 입력과 근거가 갖춰지기 전 상태는 셀 계약 §2의
`NOT_COMMISSIONED`다.

## 2. 근거를 읽는 법

- **cited**: 기존 규범에서 그 의미를 인용할 수 있다. 이 사례의 구현이나 실제 장비의
  적합성을 입증했다는 표시는 아니다. 모델·profile·설치별 근거는 별도로 필요하다.
- **open**: 이 사례에 필요한 구체 입력 또는 서비스 판단 규칙을 읽은 v1.0 본문에서
  찾을 수 없다. 미결 이름과 빠진 내용을 명시한다. 이를 새 공통 계약이 필요하다는
  판정으로 읽지 않는다. 기존 profile의 값으로 채울 수 있는지 여부는 N2의 일이다.

관측된 사실은 아래 인용 문서가 해당 규칙을 담고 있다는 것이다. §1의 로봇·물품·공간은
사례의 선언 값이고, 이동형 수신 장치에도 이 규칙을 충족시킬 수 있다는 주장은 검증할
가설이다. 공통 계약의 `resource_disposition`은 명령 자원을 다음 operation에 넘길 수
있는지를 나타낸다(공통 01 §5). 물품의 실제 위치·복수 지지는 `MaterialState`로 별도
기록한다(셀 01 §6). 명령 소유자 한 명이라는 I05를 물리 지지 주체 한 개라는 뜻으로
바꾸지 않는다. `RELEASED`에는 물리 인계 조건도 포함된다(공통 01 §7).

## 3. 인계 지점의 네 물음

각 행은 한 하위 항목이며 라벨은 하나다. 물음에 `open` 행이 하나라도 있으면 그 물음은
열린 것으로 센다. 번호가 같은 행들은 [제품 정의 §4](01_product_definition.md)의 같은
물음에 답한다.

| 물음·하위 항목 | 사례의 답 | 분류·근거 |
|---|---|---|
| Q1-a 무엇이 이동하는가 | `PKG-01`의 위치와 지지를 `IN-01` 그리퍼에서 `OUT-01/TRAY-01`로 바꾼다. 중간에는 두 쪽이 함께 지지할 수 있다. 소포 식별 근거·위치·각 지지 근거·변경 세대를 함께 남긴다. | **cited** — `MaterialState`, sender-release, receiver-support evidence. [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md). |
| Q1-b 어떤 작업이며 누가 기록·판정하는가 | 인계 한 건을 하나의 `Run`에 연결하고 내려놓기·받는 장치의 유지·보내는 그리퍼 해제·후퇴의 필요한 native 효과를 별개 `Activation`/`Operation`으로 구별한다. `RUNTIME-01`은 의도와 결론, 두 Host는 각 native 전달 사실과 원 관측을 맡는다. 물리 이동 전 지지자는 `IN-01`, 이동 후 지지자는 `OUT-01`이며 플랫폼 판정 책임은 이동하지 않는다. | **cited** — C02·C03·C04, `Run`, `Activation`, `Operation`, `NativeInvocation`. 임의의 다중 native 명령을 한 operation으로 숨기지 않는다. [공통 01 §1–2](contracts/v1.0/01_responsibility_and_semantics.md). |
| Q2-a 필요한 능력·권한·자원을 어떻게 확인하는가 | `HOST-OUT`은 적재·유지·도킹 관련 capability와 관측을 제공해야 한다. 플랫폼은 바인딩·현재 모드·교정·물품·증거원을 대조하고 충돌 자원을 예약한다. `RunMandate`와 별개로 해당 operation·Host·epoch·증거에 묶인 `DispatchPermit`을 쓰며 Host가 전송 직전에 다시 검사한다. | **cited** — `BindingProfile`, `resource_set`, admission, `RunMandate`, `DispatchPermit`. [공통 04 §1·5](contracts/v1.0/04_binding_and_admission.md), [셀 02 §2·4–5](cell_operations/v1.0/02_authorization_invalidation.md). |
| Q2-b 이 이동형 receiver는 실제로 그 자격이 있는가 | `TRAY-01`의 소포 유지와 도킹·제동, 인계 중 지지 상실에 대한 근거가 필요하다. 현재 문서는 그 근거를 제공하지 않는다. | **open — OPEN-MOBILE-SUPPORT**: v1.0 본문에는 이 사례의 장치·소포·공간 조합에 대한 관측 범위, 허용 하중·자세·위치 범위, 신선도 한계, 고장 반응과 검증 결과 값이 없다. §5에 입력 묶음을 명명한다. |
| Q3-a 접수와 실제 전달을 어떻게 구별하는가 | 인계 요청의 저장과 개별 operation의 접수는 구별한다. operation의 identity·intent·activation binding·pending dispatch가 영속 확정된 단계가 `ADMITTED`, Host 준비는 `HOST_PREPARED`, native 접수는 profile이 의미를 보장할 때의 `NATIVE_ACCEPTED`다. 실제 전달은 operation 종류에 맞는 완료 근거와 소포 식별·받는 쪽 지지·보내는 쪽 분리 관측이 필요하며 판정 입력과 결과를 함께 기록한다. | **cited** — acceptance stages, `completion_rule`, `RESULT_RECORDED`, I04·I07·I08. [공통 01 §1–8](contracts/v1.0/01_responsibility_and_semantics.md), [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md). |
| Q3-b 사람의 인수 확인과 이 인계 서비스의 완료는 무엇인가 | `RECIPIENT-01`이 이 소포를 이 받는 로봇으로 인수한다고 선언한 기록을 물리 근거와 구별해 요구한다. 그 선언을 유효하게 인정할 사람 식별·권한·절차와 물리 근거의 결합 규칙이 필요하다. §4는 요구할 관측을 적는다. | **open — OPEN-RECEIPT**: `HUMAN_ATTESTATION`의 actor·scope·observation time·procedure revision은 기존 필드지만, 이 서비스의 수령자 식별 수단, 위임 범위, 선언 유효기간과 최종 완료 결합 규칙은 v1.0에 주어져 있지 않다. [공통 01 §6](contracts/v1.0/01_responsibility_and_semantics.md). |
| Q4-a 유실·지연·경합·고장 때 무엇을 보존하는가 | 원 operation의 identity·전달 가능성·원 증거를 보존한다. 불명은 `RECONCILING/UNKNOWN`, 결론과 충돌하는 늦은 근거는 기존 outcome을 보존한 `integrity=DISPUTED`로 구별한다. 관련 자원의 `QUARANTINED`와 결과 판정을 분리하고 자동 재전송·자동 재시작으로 빈 근거를 덮지 않는다. | **cited** — I03·I05·I08·I09, SC02·SC03·SC06·SC14. [공통 01 §5–8](contracts/v1.0/01_responsibility_and_semantics.md), [공통 06 §2–3](contracts/v1.0/06_scenarios_and_validation.md). |
| Q4-b 누가 후속 조치를 맡는가 | `RUNTIME-01`이 기록 조회·결론·관련 dispatch 제한을 맡고 각 Host가 장치 관측·잔여 명령 확인·정의된 현지 반응을 맡는다. 조사·직접 개입은 `RECIPIENT-01`이 현장 개입 역할로 맡으며, 접근 자체의 허가와 물리 정지는 별도 확인한다. 개입 후 재시작에는 그 역할의 새 시작 의도가 필요하다. 구체 반례 질문은 §6이다. | **cited** — C03·C05, Site operations/intervention role, `TRANSIENT`/`LATCHED`, `RestartRun`. [공통 01 §1](contracts/v1.0/01_responsibility_and_semantics.md), [셀 01 §1](cell_operations/v1.0/01_scope_conditions_functions.md), [셀 02 §2–3](cell_operations/v1.0/02_authorization_invalidation.md). |

집계: 하위 항목 8개 = `cited` 6개 + `open` 2개. 열린 물음은 Q2·Q3 두 개다.
Q1·Q4가 닫혔다는 것은 인용 가능한 책임·표현 규칙이 있다는 뜻이며,
`OPEN-MOBILE-SUPPORT`가 해소되어 물리 동작이 허가됐다는 뜻은 아니다.

## 4. 접수부터 완료까지의 서로 다른 근거

다음은 이 사례가 요구하는 관측 기준이다. 아직 실행 trace나 실제 결과가 아니다.
네 행은 네 번의 단일 native 호출을 뜻하지 않으며, 한 버튼이나 한 enum으로 합치지 않는다.

| 단계 | 있어야 하는 기록·관측 | 이 근거가 없으면 |
|---|---|---|
| 접수 | `CLIENT-01`의 같은 인계 요청과 의도·`Run` 연결을 플랫폼이 영속 기록한 사실. 원 요청 재조회로 같은 건임을 확인한다. 이어서 각 operation의 identity·intent·activation binding·pending dispatch가 확정됐는지를 `ADMITTED`로 따로 기록한다. `ADMITTED`는 서비스 요청이나 Run 전체의 상태명이 아니다. | 접수를 주장할 수 없다. UI 성공 표시·통신 전송 성공만으로 플랫폼 저장을 대신하지 않는다. 접수됐어도 모든 operation의 admission·Host 준비·물리 전달·인수 확인을 주장할 수 없다. |
| 실제 전달 | 각 operation kind/profile이 요구하는 완료 근거와 동일 소포 식별, `TRAY-01`의 지지·유지, 보내는 그리퍼의 분리를 뒷받침하는 원 관측. `FINITE_ACTION`은 해당 native invocation과 상관된 terminal result + profile postconditions를 요구하고, `ENSURE_STATE`는 신선하고 유효한 목표 상태 관측을 요구한다(공통 01 §3). 플랫폼은 `completion_rule`에 쓴 evidence와 operation outcome을 함께 기록한다. | 실제 전달을 주장할 수 없다. 도킹 성공·관절 목표 도달·현재 idle·대기시간 만료만으로 소포 인계를 확정하지 않는다. 현재 적재 관측만으로 과거의 특정 내려놓기 호출 성공을 복원하지 않는다. |
| 인수 확인 | 실제 전달 근거와 별도로 `RECIPIENT-01`이 `PKG-01`, `OUT-01`, 이 인계 건, 본인이 관찰한 범위와 시각을 특정한 `HUMAN_ATTESTATION`. `OPEN-RECEIPT`의 절차 revision·권한·유효성 확인이 필요하다. | 인수 확인을 주장할 수 없다. 기계 관측이 사람의 수령 선언을 대신하지 않고, 사람의 선언도 native 성공·센서 지지 근거를 대신하지 않는다. 일반 UI 확인 클릭은 이 기록이 아니다. |
| 전체 완료 | 위 세 단계의 유효한 기록 연결, 필요한 operation 결과와 후퇴 근거, 인수 선언과 물리 근거 사이 모순 부재, 관련 미해결·개입 부재, 보내는 제어 자원을 해제할 별도 근거와 받는 쪽·공유 구획의 잔여 점유 기록을 함께 확인한다. 이 결합을 서비스 완료로 기록하는 규칙은 `OPEN-RECEIPT`에 남는다. | 전체 완료를 주장할 수 없다. 어느 한 operation의 `SUCCEEDED`나 `RESULT_RECORDED`, 또는 인수 선언 하나를 전체 완료로 승격하지 않는다. |

결과 확정과 자원 해제는 [공통 01 §7·I08](contracts/v1.0/01_responsibility_and_semantics.md)에
따라 분리한다. `RELEASED`에는 잔여 native 명령의 추가 실행 불가, 다음 owner가 사용할
제어 상태, 필요한 물품·중력 지지 인계 완료의 확인이 필요하다. terminal result·torque off·
lease 만료만으로 해제하지 않는다. 인계 완료 시 보내는 제어 자원은 해제 조건을 확인하지만,
받는 로봇의 소포 유지 책임과 `BAY-01` 점유는 남는다. `OUT-01`의 출발은 범위 밖이므로
`BAY-01`을 빈 공간으로 해제하지 않으며, 그 공간과 충돌하는 새 인계를 허가하지 않는다.
완료를 모든 자원·모든 지지의 해제로 읽지 않는다.

특히 [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md)에 따라
지지를 줄이는 operation은 같은 소포·인계 세대의 지지 자원을 예약한다. 수신 측 지지가
확인됐다는 사실만으로 양측이 동시에 해제할 수 없다. 해제 과정 내내 대체 지지가
유지되는 근거와 결과·새 지지 상태 확인은 `OPEN-MOBILE-SUPPORT`의 검증 범위다.

## 5. N2로 넘길 명명된 미결

| 이름 | 현재 규범에 있는 것 | 이 사례에 빠진 값·판정과 다음 산출물 |
|---|---|---|
| OPEN-MOBILE-SUPPORT | `BindingProfile`의 capability·resource_set·completion/cancel·timing·evidence, `OperatingEnvelope`의 조합 조건, `MaterialState`와 receiver-support 및 H03·H06 의무. [공통 04 §1·2·5](contracts/v1.0/04_binding_and_admission.md), [셀 01 §3·6–7](cell_operations/v1.0/01_scope_conditions_functions.md). | `IN-01/OUT-01` 실제 장치·버전, 소포/적재함 조합, 인계 구획·도킹·제동 범위, 식별·지지·분리 관측의 source와 신선도, 허용 하중·자세·위치, 전원·압력·통신 상실 시 유지/반응 근거를 가진 사례별 입력 카드. 지금 임의 수치나 PASS를 채우지 않는다. N2가 기존 profile 설정으로 충분한지 판정하고 N3가 지지 상실 반례를 구체화한다. |
| OPEN-RECEIPT | `HUMAN_ATTESTATION`의 출처 필드와 일반 확인 클릭의 한계, `completion_rule` 및 operator 역할. [공통 01 §6](contracts/v1.0/01_responsibility_and_semantics.md), [셀 01 §1·5](cell_operations/v1.0/01_scope_conditions_functions.md). | `RECIPIENT-01` 식별·수령 권한·위임 확인, 실제 관찰 범위와 시각·절차 revision·유효기간, 중복/늦은 선언·소포 불일치 처리, 물리 결과와 선언을 이 인계 서비스의 완료로 묶을 규칙. N2가 기존 기록·profile/업무 구성과 추가 의미의 경계를 판정한다. 법적 소유권 이전을 선언하는 문서가 아니다. |

위 두 의무의 [N2 경계 판정](22_open_items_boundary.md)은 기존 표현 수단과 남은 사례별 입력·검증·업무 의미를 구분했다. 사용한 단위와 라벨은 [77자리 측정](21_declaration_reuse_measurement.md)을 따른다. N2의 문서 판정이 끝나도 두 미결의 상태는 **open**이며, 물리 지지 자격이나 실제 수령 규칙이 확정된 것은 아니다.

**범위 밖 변형 `INDEPENDENT-RUNTIMES`**: `HOST-IN`과 `HOST-OUT`의 판정 주체를
각각 독립 Runtime으로 바꾸는 경우다. 이 문서의 `RUNTIME-01` 원장·자원 예약·epoch를
두 원장에 그대로 적용할 수 있다고 주장하지 않는다.
[공통 계약 Scope](contracts/v1.0/README.md)는 단일 authoritative Runtime을 전제하고,
[공통 04 §4](contracts/v1.0/04_binding_and_admission.md)는 fleet manager 연결만으로
독립 Runtime의 분산 권한을 검증했다고 주장하지 못하게 하며,
[셀 02 §7](cell_operations/v1.0/02_authorization_invalidation.md)은 동일 state DB의
transaction을 요구한다. 이 변형은 N2의 범위 질문으로만 남기며 정상 사례나 위 집계에
넣지 않는다. 영역 간 신뢰·권한 위임·분산 원장 구현은 N6의 별도 작업이다.

## 6. N3가 구체화할 반례 후보

아래는 유발 조건과 판정 질문이며, 실행한 장애 시험이나 해결된 반례가 아니다.

| 후보 | 유발 조건 | 그때 미결인 것 | 후속 책임 | 기존 제약·N3 질문 |
|---|---|---|---|---|
| 응답 유실 | `HOST-IN`이 그리퍼 해제의 `SEND_ENTERED`를 기록한 뒤 응답 경로가 끊긴다. | 해제가 실행됐는지, 어느 지지가 남았는지, 원 호출의 결과가 회수 가능한지. 현재 idle만으로 닫히지 않는다. | 플랫폼이 같은 identity의 기록을 조회하고 관련 후속 동작을 제한한다. 양쪽 Host는 잔여 명령·지지 관측을 제공한다. 현장 조사가 필요하면 `RECIPIENT-01`이 맡는다. | I03·I04·I08, SC02. 같은 호출 재전송 없이 결과 또는 `UNRESOLVED` 조사로 갈 근거가 있는가? 실제 유지 반응은 OPEN-MOBILE-SUPPORT에 의존한다. |
| 인계 지연 | 도킹은 끝났지만 적재함 유지 관측이 없거나 신선도를 잃는다. 보내는 그리퍼는 아직 소포를 지지한다. | 정상 `WAIT_TARGET`인지, 지지 유지 조건 상실/관측 연속성 불명인지. 단순 시간 초과는 전달 성공이 아니다. | 플랫폼이 다음 해제 dispatch를 보류한다. Host가 원 관측과 현지 조건을 확인한다. 연속성 불명·고장이면 현장 개입 역할이 조사한다. | I04·I09, SC06, 셀 02 §3. `TRANSIENT`로 해소할 연속성 근거가 있는가, `LATCHED`로 전환할 사건인가? |
| 지지 자원 경합 | 받는 장치가 소포를 지지하는 도중 두 Host가 같은 `PKG-01/HG-01`에 대해 각각 지지를 줄이려 한다. | 두 이름이 같은 실제 소포를 가리키는지, 예약의 승자와 현재 대체 지지가 무엇인지. | 플랫폼이 공통 자원 예약을 직렬화하고 각 Host가 dispatch gate를 적용한다. 물품 alias가 불명하면 관련 지지 감소를 허가하지 않는다. | I05·I08, 셀 01 §6, SC14. 서로 다른 제어기 이름이나 receiver PASS 하나만으로 동시 해제가 통과하는가? 물리 지지 연속성은 lock만으로 입증되지 않는다. |
| 받는 로봇 고장 | 적재함 지지 확인 뒤, 보내는 그리퍼 해제 전후에 `OUT-01`의 전원·제어기 세대·제동 상태가 변한다. | 기존 지지 관측의 유효성, 실제 소포 위치, 이미 진입한 native 효과와 해제 가능 여부. 과거 확정 결과와 현재 상태도 구별해야 한다. | Host가 선언된 현지 반응과 원 관측을 맡고 플랫폼은 관련 허가·근거를 무효화한다. `RECIPIENT-01`의 현장 조사·개입 뒤 명시적 새 시작이 필요하다. | I08·I09·I12, SC03-C·SC09, 셀 02 §3·6. fence가 이미 진입한 명령·물리 움직임을 없앤 것으로 오인되는가? 실제 고장 시 지지 유지 근거는 OPEN-MOBILE-SUPPORT다. |

위 후보의 [N3 문서 반례 검토](23_handover_counterexamples.md)는 원 질문을 유지한 채 유발 단계와 책임·권한·증거·격리·후속 조치, 규범상 금지 문장과 남는 현장 근거를 구체화한다. 후보 표와 두 open 상태는 그대로이며, 실행한 장애 시험이나 물리 자격의 승인이 아니다.

공통 invariant와 SC 인용의 원본은 [공통 01 §8](contracts/v1.0/01_responsibility_and_semantics.md)과
[공통 06 §2–3](contracts/v1.0/06_scenarios_and_validation.md)이며,
셀 조건·무효화 인용은 [셀 01 §4·6](cell_operations/v1.0/01_scope_conditions_functions.md)과
[셀 02 §3–6](cell_operations/v1.0/02_authorization_invalidation.md)이다.
이 규칙이 있다는 사실은 해당 모바일 장치의 보호 기능·반응 시간·현장 접근을 검증한
결과가 아니다. 필요한 실물 근거는 [핵심 미결 O01–O03·N01](implementation/critical_open_items.md)에
연결된다. N1 정의가 끝나도 N01의 정상·유실·거부·미결 검증 의무는 남는다.

후속 [선언·판정 지원도 측정](21_declaration_reuse_measurement.md#6-두-번째-기준선-조사-현재-결과)은 이 사례를 선언 기준선으로 쓸 수 있는지 점검했다. 77자리 중 값이 대응되는 것은 7자리였으며, 다른 저장소의 후보까지 조사한 뒤 inherited를 측정 불가로 남기고 규범 단독의 declared/free를 전수 판정했다. 이 결과가 위 미결이나 실제 장치 자격을 해소하지는 않는다.
