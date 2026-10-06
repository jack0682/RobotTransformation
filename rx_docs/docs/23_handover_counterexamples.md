# 23. N3: 네 인계 반례 후보의 규범 검토

기준일: 2026-09-15 · **조건부 문서 시퀀스다. 장애 주입·시뮬레이션·장치 시험을 실행하지 않았다.**

[문서 20 §6](20_first_handover_case.md)의 네 후보를 구체화했다. 각 후보의 오독에 대한
판정은 모두 **막는다 — 규범상**이다. 자동 native 재전송, 연속성 없는 재개, 공통 지지
자원을 빠뜨린 동시 해제, fence를 물리 소거로 읽는 전이는 각각 명시된 규칙에 어긋난다.
각 반례의 다섯 축 **책임·권한·증거·격리·후속 조치**를 채우고 실제 근거의 결손도 분리했다.
이 결과는 규범 준수 구현이나 물리 안전을 입증하는 실행 결과가 아니다.

OPEN-MOBILE-SUPPORT와 OPEN-RECEIPT는 계속 **open**이며, 현재 사례는 **NOT_COMMISSIONED**다.
[문서 21의 측정](21_declaration_reuse_measurement.md)과 [문서 22의 N2 판정](22_open_items_boundary.md)은
그대로 보존한다. 같은 사이트의 RUNTIME-01과 두 Host라는 N1 경계에서만 검토하며
독립 Runtime 변형을 이번 반례에 섞지 않는다.

## 1. 읽는 법과 판정 기준

### 1.1 무엇에 대한 반례인가

여기서 반례는 “이렇게 읽어도 된다”는 **오독에 대한 부당 전이 후보**다. 준수 모델이
그 전이를 허용하는지 원문에 대조한다. 규범 자체의 결함을 실행으로 재현했다거나 모든
사건 순서를 증명했다는 뜻이 아니다. 규범 문장을 확인한 것은 관측이고, 그 문장을 특정
오독에 적용한 판정은 추론이다. 각 시퀀스는 규범으로 감사할 수 있게 쓴 가상 사건 순서다.

문서 20이 가정한 SEND_ENTERED나 도킹/지지 확인 시점에서 조건부로 시작한다.
이는 현재 미정인 설치 입력을 true/PASS로 채워 운전을 승인한다는 뜻이 아니다.
필수 입력이 없는 지금은 S2의 NOT_COMMISSIONED 제한을 유지한다. 새 장치 사양·시간·하중
수치를 넣지 않고 원문에 있던 사례 이름과 규범 개념만 사용한다.

- **막는다 — 규범상:** 원 질문의 오독을 금지하는 문장과 그 문장이 적용될 판단/gate 위치가 있다.
- **막지 못한다 — 규범상:** 해당 오독을 금지하는 근거를 읽은 규범에서 찾지 못한다.
- **부분적으로 막는다 — 규범상:** 원 질문 안의 일부 오독에만 금지·판정 근거가 있다.
  적용 범위와 남는 오독을 분리해야 한다.

이번 네 오독에는 금지와 판단 위치가 모두 있어 첫 값을 사용한다. 원 결과 lookup,
연속성, 실제 지지, 고장 검출의 **현장 근거가 비어 있다는 이유만으로 금지 문장을 없다고
판정하지 않는다.** 반대로 금지 문장이 있다는 이유로 그 현장 근거가 확보됐다고도 하지 않는다.
원 질문의 “근거가 있는가”에는 규범 경로의 존재와 사례 근거의 구비 여부를 각각 답한다.
세 번째 값은 이번 주판정에 사용하지 않았으며 그 수를 늘리려고 질문을 바꾸지 않았다.

`RECONCILING/UNKNOWN`은 operation의 phase/실행 지식, `SETTLED/UNRESOLVED`는 phase/outcome의
결합 표기다. `QUARANTINED`는 명령 자원의 disposition이고 `TRANSIENT/LATCHED`는 cell block
종류다. 이 상태들을 서로 대신 쓰지 않는다. 물리 지지와 명령 자원 해제도 구별한다.
같은 규범 문장을 여러 축에 인용할 수 있지만, 각 축에서 그 문장이 뒷받침하는 내용을 따로 적었다. 인용과 설명의 P는 platform인 RUNTIME-01, H는 해당 Host를 뜻한다.

### 1.2 기준 원문

기준 revision은 rx_docs `b7d3639fcdca565e044f1893f4f52852bd1b587b`다. 아래 파일 이름과 절을
각 표에 붙였다. I 식별자의 원본은 공통 01 §8, SC 식별자의 원본은 공통 06의 표다.

- [공통 01](contracts/v1.0/01_responsibility_and_semantics.md)
- [공통 02](contracts/v1.0/02_identity_durability_recovery.md)
- [공통 03](contracts/v1.0/03_data_and_protocol.md)
- [공통 04](contracts/v1.0/04_binding_and_admission.md)
- [공통 06](contracts/v1.0/06_scenarios_and_validation.md)
- [셀 01](cell_operations/v1.0/01_scope_conditions_functions.md)
- [셀 02](cell_operations/v1.0/02_authorization_invalidation.md)
- [셀 04](cell_operations/v1.0/04_protocol_integration_ui.md)

S2는 [셀 01 §2](cell_operations/v1.0/01_scope_conditions_functions.md)의 설치별 입력 의무를 뜻한다.

## 2. 응답 유실

### 2.1 원 질문과 규범 용어로 옮긴 질문

문서 20 §6의 마지막 칸 원문:

> I03·I04·I08, SC02. 같은 호출 재전송 없이 결과 또는 `UNRESOLVED` 조사로 갈 근거가 있는가? 실제 유지 반응은 OPEN-MOBILE-SUPPORT에 의존한다.

**옮긴 질문:** HOST-IN의 원 invocation이 SEND_ENTERED 뒤 UNKNOWN일 때, native 호출을 다시 보내지 않고 원 결과를 조회·상관하거나 조사 후 UNRESOLVED로 남길 규범 경로가 있는가? 이 사례에 그 경로를 채울 실제 결과/지지 근거도 있는가?

**반박할 오독:** 응답이 없으니 원 native 호출을 다시 보내거나 현재 idle을 과거 해제 성공으로 기록하고 다음 인계 단계로 진행한다.

### 2.2 조건부 유발 시퀀스

1. 문서 20의 조건처럼 HOST-IN이 IN-01 그리퍼 해제의 SEND_ENTERED를 영속 기록했다고 가정한다. 이 기록은 native 효과가 시작됐을 가능성의 경계이며 실제 해제 성공의 증거가 아니다.
2. 그 뒤 응답 경로가 끊긴다. HOST-IN이 이미 갖고 있을 수 있는 원 결과와 RUNTIME-01이 받은 결과를 구별한다. RUNTIME-01은 응답 부재만으로 실행/미실행 어느 쪽도 확정하지 못한다.
3. RUNTIME-01은 원 operation/invocation의 identity를 보존하고 RECONCILING/UNKNOWN으로 다룬다. 재연결이나 같은 요청의 조회가 새 native 호출을 만들지 않아야 한다.
4. 같은 identity로 Host receipt/evidence outbox와 제공 가능한 native 결과를 조회한다. 실제 전달 확인에는 해당 invocation의 결과와 profile postconditions가 필요하다. 현재 TRAY-01의 지지만으로 과거 해제 호출의 성공을 복원하지 않는다.
5. 상관된 terminal evidence를 회수하면 그 rule에 따라 결과를 판정한다. 회수하지 못하면 UNKNOWN을 유지하며, 조사로 더 결정할 수 없고 책임 있는 operator가 포기를 기록하는 조건에서만 SETTLED/UNRESOLVED로 갈 수 있다. timeout 자체가 이 처분을 만들지 않는다.
6. 결과가 정해져도 잔여 native 명령과 지지 인계의 별도 해제 조건을 확인한다. 원 호출 결과, 제어 자원 해제, RECIPIENT-01의 인수 및 서비스 전체 완료를 한 결론으로 합치지 않는다.

### 2.3 다섯 축

| 축 | 해당 순간의 규범상 판단 | 근거 |
|---|---|---|
| 책임 | RUNTIME-01은 원 identity·evidence·결론을 소유하고, HOST-IN은 native 전달/원 결과를, HOST-OUT은 받는 쪽 관측을 제공한다. 현장 조사가 필요하면 N1의 RECIPIENT-01이 개입 역할을 맡되 기록 버튼이 물리 사실을 대신하지 않는다. | [공통 01 §1·6](contracts/v1.0/01_responsibility_and_semantics.md) · [셀 01 §1](cell_operations/v1.0/01_scope_conditions_functions.md) |
| 권한 | 조회는 접근 권한을 확인하며 motion permit을 요구하지 않는다. 이미 SEND_ENTERED인 원 호출은 새 grant/permit이나 새 key로 자동 재전송하지 않는다. 취소가 필요하면 원 operation에 묶인 별도 cancel 경로의 조건을 따른다. | [공통 02 §1·3](contracts/v1.0/02_identity_durability_recovery.md) · [셀 02 §4·8](cell_operations/v1.0/02_authorization_invalidation.md) · I01·I03 |
| 증거 | delivery receipt와 evidence outbox의 journal identity를 구별한다. 조회한 receipt도 결론에 사용하기 전에 immutable evidence로 T2에 남긴다. 원 invocation correlation, 실제 결과, 현재 지지·잔여 명령 근거를 보존한다. | [공통 02 §1–2](contracts/v1.0/02_identity_durability_recovery.md) · [공통 01 §6](contracts/v1.0/01_responsibility_and_semantics.md) · I04·I07 |
| 격리 | SC02의 원 자원 quarantine과 관련 후속 dispatch 보류를 유지한다. native 응답 유실을 단순 결과조회 RPC 유실과 같게 취급해 자동 TRANSIENT로 두지 않는다. 조회만의 유실로 좁혀지고 연속성이 입증되는 경우와, 물리 변화/연속성이 불명하여 revocation/LATCHED가 필요한 경우를 구별한다. | [공통 06 §2 SC02](contracts/v1.0/06_scenarios_and_validation.md) · [셀 02 §3](cell_operations/v1.0/02_authorization_invalidation.md) · I08 |
| 후속 조치 | 원 결과 회수 또는 조사·근거 있는 UNRESOLVED 처분으로 간다. UNRESOLVED 뒤에도 success branch와 자동 자원 해제는 불가하다. 자원을 풀려면 검증된 RecoveryDisposition의 별도 조건이 필요하며, 이전 outcome을 성공으로 바꾸지 않는다. | [공통 01 §5·7](contracts/v1.0/01_responsibility_and_semantics.md) · [공통 02 §2 T5](contracts/v1.0/02_identity_durability_recovery.md) |

### 2.4 답과 남는 결손

**판정: 막는다 — 규범상.** 자동 native 재전송과 idle/timeout의 성공 승격은 금지되고, 원 결과 조회/상관 및 근거 있는 UNRESOLVED 조사·처분 경로는 규정돼 있다. 그러나 “이 장치가 실제 원 결과를 회수할 수 있는가”에는 현재 문서로 그렇다고 답할 수 없다. 그 실물 근거는 아래 결손에 남는다. native 장치가 deduplication을 제공하더라도 공통 v1.0의 불명 뒤 재전송 금지를 임의로 완화하지 않는다.

금지 문장과 그 근거:

> An unknown outcome after SEND_ENTERED does not justify automatic native retransmission.

[공통 01 §8 I03](contracts/v1.0/01_responsibility_and_semantics.md)

> At SEND_ENTERED or later, only lookup/reconciliation is allowed.

[공통 02 §3](contracts/v1.0/02_identity_durability_recovery.md)

**미확정: 과거 호출 결과 회수와 지지/잔여 명령 근거.** 결과 lookup 제공·보존 범위, 실제 correlation 및 release 근거가 없다. [문서 22 §4의 관측/완료 근거·상실 반응](22_open_items_boundary.md#4-open-mobile-support-판정), 문서 21의 P18/P19/P30/P35/P44/P45로 연결한다. 규범 경로가 있다는 것만으로 이 입력들을 생성하지 못한다.

## 3. 인계 지연

### 3.1 원 질문과 규범 용어로 옮긴 질문

문서 20 §6의 마지막 칸 원문:

> I04·I09, SC06, 셀 02 §3. `TRANSIENT`로 해소할 연속성 근거가 있는가, `LATCHED`로 전환할 사건인가?

**옮긴 질문:** 받는 쪽 유지 관측이 없거나 신선도를 잃은 동안, 정상 WAIT_TARGET/아직 native 효과와 관련 없는 admission hold인가? 아니면 유지 조건 상실·개입·보호 반응·generation/authority 변화 또는 연속성 불명으로 revocation/LATCHED가 필요한가?

**반박할 오독:** receiver 관측이 다시 PASS로 보이거나 대기시간이 끝났으니 연속성 확인 없이 block을 지우고 그리퍼 해제 또는 전달 성공을 허용한다.

### 3.2 조건부 유발 시퀀스

1. OUT-01의 도킹이 끝났고 IN-01의 그리퍼가 PKG-01을 지지하는 N1 조건에서 시작한다. 이 후보에서는 다음 그리퍼 해제의 native 진입 전, receiver-support 조건을 기다리는 분기를 검토한다.
2. TRAY-01 유지 관측이 아직 없거나 원 표본의 신선도를 잃는다. RUNTIME-01은 필요한 다음 해제 dispatch를 보류한다. 도킹 완료와 소포 지지 완료는 다른 조건이다.
3. 조건이 ADMISSION/WAIT_TARGET인지, 진행 중 동작의 MAINTAINED 조건인지 원 정의와 증거로 구별한다. “지연”이라는 사용자 표시만으로 block 종류나 mandate 상태를 결정하지 않는다.
4. 정상 WAIT_TARGET 또는 native 효과와 아직 연결되지 않은 admission 관측 보류이고, 개입·보호 반응·권한/장치 세대 변화·미확인 외부 변화가 없다는 연속성 근거까지 회복되면 기존 범위에서 계속할 수 있다. P의 TRANSIENT block이 있었다면 명시적으로 ClearTransientBlock을 기록하고 필요한 permit을 새로 평가한다.
5. 반대로 유지 조건 상실, 상충 evidence, 개입/보호 반응 또는 연속성 불명이면 revocation/LATCHED 경로다. 값이 다시 PASS가 됐다는 사실만으로 이를 지우거나 옛 mandate를 복원하지 않는다.
6. Host는 dispatch 직전에 현재 조건을 다시 확인한다. 실제 지지·분리 근거가 없으면 시간 경과나 기다림의 종료를 전달 성공으로 기록하지 않는다. 개입 경로였다면 조사·재확인 뒤 명시적 RestartRun이 필요하다.

### 3.3 다섯 축

| 축 | 해당 순간의 규범상 판단 | 근거 |
|---|---|---|
| 책임 | RUNTIME-01은 ConditionDefinition과 연속성 근거에 따라 대기/무효화 경로를 고른다. Host는 원 표본과 현재 native 조건을 제공하고 국소 반응을 맡는다. 개입 사건의 조사는 현장 역할에 속한다. | [셀 01 §1·4](cell_operations/v1.0/01_scope_conditions_functions.md) · [셀 02 §3](cell_operations/v1.0/02_authorization_invalidation.md) |
| 권한 | RunMandate가 ACTIVE인 것만으로 해제 호출 권한이 생기지 않는다. 정상 대기/보류와 revocation을 구별하고, 현재 조건을 만족하는 개별 DispatchPermit 및 최종 Host gate가 필요하다. LATCHED 뒤에는 새 시작 경로를 거친다. | [셀 02 §2–5](cell_operations/v1.0/02_authorization_invalidation.md) |
| 증거 | 원 취득 age·source/boot/quality·오차와 연속성 근거를 요구한다. cache를 다시 읽거나 PASS가 재출현한 사실만으로 신선도/연속성을 갱신하지 않는다. 이전 native 성공 이력과 현재 지지 증거도 구별한다. | [공통 01 §6](contracts/v1.0/01_responsibility_and_semantics.md) · [공통 02 §5](contracts/v1.0/02_identity_durability_recovery.md) · [공통 06 §3 SC06](contracts/v1.0/06_scenarios_and_validation.md) · I04·I09 |
| 격리 | 정상 대기는 관련 다음 동작을 보류하며 그 자체로 전체 셀을 중단시키지 않는다. P가 TRANSIENT를 소유하고, Host의 별도 LATCHED 이상은 P의 transient 해제로 지워지지 않는다. revocation 사건이면 검증된 dependency 영향 범위를 막는다. | [셀 02 §1·3·6](cell_operations/v1.0/02_authorization_invalidation.md) · [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md) |
| 후속 조치 | 연속성 입증 경로이면 새 evidence를 평가하고 명시적 transient 해제 후 진행한다. 입증 못 하면 원인 조사·필요한 intervention/qualification/epoch 확인을 거쳐 operator의 새 RestartRun으로 간다. 구체 복구 절차·인원/지지 검증을 이 문서에서 채우지 않는다. | [셀 02 §2–3](cell_operations/v1.0/02_authorization_invalidation.md) · [셀 04 §6](cell_operations/v1.0/04_protocol_integration_ui.md) |

### 3.4 답과 남는 결손

**판정: 막는다 — 규범상.** 원 질문에는 조건부 분기로 답한다. 정상 대기/보류와 입증된 연속성은 TRANSIENT 해소 가능 경로이고, 개입·보호 반응·상충·세대/권한 변화 또는 연속성 불명은 revocation/LATCHED 경로다. 후자의 경로를 PASS 재출현으로 우회하지 못한다. “이 사례가 어느 쪽인가”를 결정할 실제 연속성 근거는 아직 없다. 따라서 모든 지연을 LATCHED로 만들거나, 모든 관측 복구를 자동 재개로 만드는 어느 쪽도 이 답이 아니다.

금지 문장과 그 근거:

> If that continuity is unknown, take the revocation path.

[셀 02 §3](cell_operations/v1.0/02_authorization_invalidation.md)

> Reappearance of PASS alone does not establish lost continuity.

[셀 02 §3](cell_operations/v1.0/02_authorization_invalidation.md)

> SUCCEEDED satisfies the specified evidence rule and is not created from timeout/idle/BT success alone.

[공통 01 §8 I04](contracts/v1.0/01_responsibility_and_semantics.md)

**미확정: 관측 신선도와 연속성의 실제 입증.** 원 취득 경로·시간 오차·boot 관측·silent change 검출 한계가 없다. [문서 22의 M-05/M-06 및 §4 관측 근거](22_open_items_boundary.md#4-open-mobile-support-판정), 문서 21의 P17/P36/P42/P43/P47로 연결한다. 이 값이 없으면 문서상 PASS를 지어내지 않고 정해진 불명/무효화 경로를 적용해야 한다.

## 4. 지지 자원 경합

### 4.1 원 질문과 규범 용어로 옮긴 질문

문서 20 §6의 마지막 칸 원문:

> I05·I08, 셀 01 §6, SC14. 서로 다른 제어기 이름이나 receiver PASS 하나만으로 동시 해제가 통과하는가? 물리 지지 연속성은 lock만으로 입증되지 않는다.

**옮긴 질문:** 서로 다른 Host/controller를 대상으로 하더라도 같은 PKG-01/HG-01의 지지를 줄이는 요청들이 동일 support resource를 예약하는가? 물품 alias가 불명이거나 receiver-support PASS만 있을 때 두 요청을 함께 통과시킬 수 있는가?

**반박할 오독:** HOST-IN과 HOST-OUT의 제어기 이름이 다르고 receiver가 PASS이므로 두 지지 감소 요청을 독립 동작으로 예약·전송한다.

### 4.2 조건부 유발 시퀀스

1. TRAY-01이 PKG-01을 지지하는 N1 조건에서, HOST-IN과 HOST-OUT을 각각 대상으로 하는 지지 감소 의도가 겹친다고 가정한다. 두 의도의 platform 판정자는 같은 RUNTIME-01이다.
2. 먼저 두 물품 이름/slot이 같은 실물을 가리키는지 검증된 정의를 확인한다. 그 동일성이 불명이면 지지 감소를 허용하지 않는다. 같은 문자열이라는 이유로 검증됐다고 가정하지 않는다.
3. 동일 물품/인계 세대가 확인된 경우 각 resource_set은 해당 support resource를 포함해야 한다. 서로 다른 controller 이름만으로 이 공통 자원을 빼는 단계가 첫 번째 금지 전이에 해당한다.
4. RUNTIME-01의 T1은 필요한 자원 전부를 한 transaction에서 예약한다. 먼저 예약에 성공한 쪽만 그 조건 아래 다음 단계로 갈 수 있고, 충돌 자원을 얻지 못한 다른 새 요청은 BUSY다. 어느 Host가 이기는지는 고정하지 않는다.
5. 승자도 native 진입 전 Host gate에서 현재 permit·조건·지지 범위를 다시 확인해야 한다. release 과정 전체의 대체 지지와 결과/새 지지 상태를 확인하기 전 공통 support resource를 놓지 않는다.
6. BUSY는 예약을 얻지 못한 새 요청의 거부이며, 다른 원 operation의 FAILED/CANCELED를 만들지 않는다. 승자의 terminal result 하나나 lease 만료만으로 다음 owner에게 넘기지 않는다. 이미 진입한 결과가 불명이면 별도 quarantine/reconciliation을 유지한다.

### 4.3 다섯 축

| 축 | 해당 순간의 규범상 판단 | 근거 |
|---|---|---|
| 책임 | RUNTIME-01이 두 Host에 걸친 같은 자원의 예약을 직렬화한다. 각 Host는 자기 native 진입과 현재 조건을 확인한다. 물품 동일성·충돌 단위·지지 범위를 정하는 책임은 설치/장치/검증 역할에 남는다. | [공통 02 §2 T1·§4](contracts/v1.0/02_identity_durability_recovery.md) · [셀 01 §1·6](cell_operations/v1.0/01_scope_conditions_functions.md) |
| 권한 | 서로 다른 제어기 이름은 서로 다른 물리 지지 권한의 근거가 아니다. 공통 support resource를 포함해 T1 예약을 얻고 현재 permit을 만족해야 한다. 자원이 없으면 BUSY이며 partial allocation을 쥔 채 추가 자원을 기다리지 않는다. | [공통 02 §4](contracts/v1.0/02_identity_durability_recovery.md) · [셀 02 §4–5](cell_operations/v1.0/02_authorization_invalidation.md) · I05 |
| 증거 | 같은 PKG-01/HG-01을 가리키는 alias/slot 근거, receiver-support의 물품·도구·하중·자세·진단·신선도 범위, 실제 stop/release 결과와 대체 지지를 확인한다. CAS가 그 물리 근거를 만들어 주지는 않는다. | [셀 01 §3·6](cell_operations/v1.0/01_scope_conditions_functions.md) · [공통 04 §1·5](contracts/v1.0/04_binding_and_admission.md) · [공통 06 §3 SC14](contracts/v1.0/06_scenarios_and_validation.md) |
| 격리 | 정상 경합이면 승자가 자원을 HELD로 유지하고 패자는 예약되지 않는다. BUSY만으로 전체 셀을 LATCHED 처리하지 않는다. 물품 동일성이 불명이면 해당 지지 감소는 금지하고, 영향 범위 정의 자체가 불명이면 셀 범위를 넓혀 제한한다. 원 native 효과 불명은 별도 quarantine 사유다. | [공통 02 §3–4](contracts/v1.0/02_identity_durability_recovery.md) · [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md) · I08 |
| 후속 조치 | 선행 동작의 실제 결과와 지지/자원 해제 조건을 확인한 뒤 다음 요청을 다시 평가한다. 단순 시간 대기나 제어기 이름 변경으로 우회하지 않는다. N1의 종료에서도 OUT-01의 소포 유지와 BAY-01 점유가 남으므로 모든 자원을 해제했다고 기록하지 않는다. | [공통 01 §7](contracts/v1.0/01_responsibility_and_semantics.md) · [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md) · [문서 20 §4](20_first_handover_case.md) |

### 4.4 답과 남는 결손

**판정: 막는다 — 규범상.** 동일 물품/인계 세대의 공통 support resource와 T1 CAS를 요구하며, receiver PASS만으로 상호 해제를 허가하지 않는다. alias가 불명이면 지지 감소를 허용하지 않는 분기도 명시돼 있다. 따라서 제어기 이름만 나눈 동시 허가는 규범에 맞지 않는다. 하지만 올바른 alias/충돌 집합과 release 중 물리 지지 연속성이 실제로 검증됐다는 뜻은 아니다.

금지 문장과 그 근거:

> Current receiver PASS alone does not authorize mutual release.

[셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md)

> If it is unknown whether object aliases/slots reference the same physical material, do not allow support reduction.

[셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md)

> If resources are unavailable, return BUSY with a retry hint.

[공통 02 §4](contracts/v1.0/02_identity_durability_recovery.md)

**미확정: 동일 물품의 지지 자원 정의와 실제 지지 연속성.** alias, 실제 충돌 집합, 지지 predicate 및 stop/release 근거가 없다. [문서 22의 M-03/M-04/M-07/M-08과 §4 조합·인계 결손](22_open_items_boundary.md#4-open-mobile-support-판정), 문서 21의 P20/P29/P34/P35로 연결한다. resource_set을 문법상 채우는 것만으로 이 결손을 해소하지 못한다.

## 5. 받는 로봇 고장

### 5.1 원 질문과 규범 용어로 옮긴 질문

문서 20 §6의 마지막 칸 원문:

> I08·I09·I12, SC03-C·SC09, 셀 02 §3·6. fence가 이미 진입한 명령·물리 움직임을 없앤 것으로 오인되는가? 실제 고장 시 지지 유지 근거는 OPEN-MOBILE-SUPPORT다.

**옮긴 질문:** OUT-01의 실제 상태 변화와 RUNTIME-01의 인지/epoch 갱신, Host의 fence 설치는 어떤 경계인가? fence ack가 원 SEND_ENTERED 호출·native queue·움직임·물품 지지를 소거했다는 증거가 될 수 있는가?

**반박할 오독:** RUNTIME-01이 epoch를 바꾸거나 fence ack를 받았으니 진입한 해제 호출과 물리 움직임이 사라졌다고 보고 자원 인계·접근·재시작을 허용한다.

### 5.2 조건부 유발 시퀀스

1. N1처럼 적재함 지지 확인 뒤 IN-01의 그리퍼 해제 전후에 OUT-01의 전원·제어기 세대·제동 상태가 변하는 상황을 놓는다. 원 해제 호출이 아직 미진입인지 이미 SEND_ENTERED인지 구별한다.
2. 실제 장치 변화와 RUNTIME-01이 이를 아는 시점은 같다고 가정하지 않는다. 검출해 전달된 변화가 있는 분기를 검토하며, 검출할 수 없는 silent change는 별도의 지원 한계로 남긴다.
3. RUNTIME-01이 latched invalidation을 인지하면 영향 범위의 block·새 epoch·mandate revocation·permit invalidation·events/outbox를 원자적으로 기록하고 관련 Host로 FenceCell을 보낸다. 이미 필요한 현지 보호 반응은 이 DB 기록을 기다리는 정상 command 경로가 아니다.
4. P의 갱신과 Host의 fence 설치 사이에는 전달 지연이 있다. 그 사이 이전에 발급된 permit이 도착할 가능성을 지워서는 안 된다. Host의 현재 grant·epoch·관측·interlock 검사와 검증된 local protection이 별도로 필요하다.
5. Host가 fence를 설치한 뒤에는 이전 epoch의 미진입 명령을 막는다. 그러나 이미 SEND_ENTERED인 호출, native queue, 움직임과 지지 상태는 별도로 조사해야 한다. FENCE_INSTALLED는 물리 정지/접근 허가나 torque 해제의 증거가 아니다.
6. 현재 지지 claim과 미결 native 효과를 다시 확인한다. 이전에 영속 확정된 outcome이 있다면 장치가 뒤에 재부팅했다는 이유만으로 그 과거 결과를 실패로 덮지 않는다. 개입·재검증·현재 epoch 동기화 뒤 operator의 명시적 RestartRun을 거치며 옛 mandate를 되살리지 않는다.

### 5.3 다섯 축

| 축 | 해당 순간의 규범상 판단 | 근거 |
|---|---|---|
| 책임 | Host는 실제 local 반응·관측·native 전달 사실을 제공하고 RUNTIME-01은 영향을 받은 권한·근거를 무효화한다. RECIPIENT-01의 현장 조사는 절차·접근 조건을 따르며, UI/fence 기록이 물리 보호 책임을 대신하지 않는다. | [셀 01 §1·5–7](cell_operations/v1.0/01_scope_conditions_functions.md) · [공통 02 §8](contracts/v1.0/02_identity_durability_recovery.md) · I12 |
| 권한 | revocation/epoch 갱신은 이전 권한을 그대로 재사용할 수 없게 한다. 다만 P의 DB 갱신 순간을 모든 Host의 미진입 차단 시점으로 보지 않는다. Host fence 설치 후의 거부와 이미 진입한 호출의 별도 조사를 구별한다. | [셀 02 §4–6](cell_operations/v1.0/02_authorization_invalidation.md) |
| 증거 | 장치 boot/관측 generation과 Host process boot를 구별하고 원 결과·현재 지지·잔여 native 명령을 확인한다. 실제 고장 반응/정지 성능은 profile·현장 증거가 필요하다. 과거 성공 이력과 현재 상태 무효화는 다른 주장이다. | [공통 01 §5–7](contracts/v1.0/01_responsibility_and_semantics.md) · [공통 02 §7–8](contracts/v1.0/02_identity_durability_recovery.md) · [공통 06 §2 SC03-C·§3 SC09](contracts/v1.0/06_scenarios_and_validation.md) · I08·I09 |
| 격리 | 영향 closure의 LATCHED block과 관련 mandate/permit 무효화를 유지한다. 범위가 모호하면 전체 셀 경계로 넓힌다. 미확인 native 효과가 남은 자원을 새 owner나 접근 근거로 넘기지 않는다. fence ack와 물리 격리는 구별한다. | [셀 01 §6](cell_operations/v1.0/01_scope_conditions_functions.md) · [셀 02 §5–6](cell_operations/v1.0/02_authorization_invalidation.md) · [셀 04 §8](cell_operations/v1.0/04_protocol_integration_ui.md) |
| 후속 조치 | 정해진 local stop/hold 반응의 결과와 잔여 명령·지지를 조사하고, 필요 시 qualification/절차를 재검증한다. PrepareRestart의 새 epoch와 같은 세대의 clearance/Arm 확인 및 operator RestartRun으로 진행한다. 일반적인 torque-off, 자동 재시작 또는 정상 production을 I12 예외에 넣지 않는다. | [공통 02 §8](contracts/v1.0/02_identity_durability_recovery.md) · [셀 02 §2·8](cell_operations/v1.0/02_authorization_invalidation.md) · [셀 04 §6](cell_operations/v1.0/04_protocol_integration_ui.md) |

### 5.4 답과 남는 결손

**판정: 막는다 — 규범상.** fence의 의미를 미진입 명령의 gate 경계로 제한하고, 이미 진입한 호출·queue·움직임·지지는 별도 reconciliation 대상이라고 명시한다. P의 DB 갱신만으로 즉시 모든 물리 효과가 사라진다는 주장도 직접 부정한다. 따라서 원 질문의 fence 소거 오독은 규범에 맞지 않는다. 실제 fault 검출이나 지연 구간의 보호 성능을 이 금지 문장이 만들어 주지는 않는다.

금지 문장과 그 근거:

> Already-SEND_ENTERED calls, native queues, movement, and support require separate reconciliation; fence acknowledgement does not mean they have ended or that access is allowed.

[셀 02 §6](cell_operations/v1.0/02_authorization_invalidation.md)

> RX does not guarantee that all physical actions disappear immediately at P's DB update.

[셀 02 §6](cell_operations/v1.0/02_authorization_invalidation.md)

**미확정: 고장 검출, 지연 구간의 local 반응, 잔여 효과의 실제 근거.** 검출 범위·silent reboot 한계, 실제 stop/hold·지지 성능과 잔여 command 확인이 없다. [문서 22의 M-08 및 §4 상실 반응 결손](22_open_items_boundary.md#4-open-mobile-support-판정), 문서 21의 P34/P35/P42/P43/P45/P47로 연결한다. profile/현장 검증 없이 보호 성능을 보증할 수 없다.

## 6. 규범만으로 확정할 수 없는 부분의 연결

앞의 “막는다”는 규범상 부당 전이의 금지다. 아래는 그 규범이 **실제 값을 만들어 주거나
현장 사실을 입증하지 못하는 부분**이다. 금지 문장과 실물 증거의 부재를 한 축으로 합치지 않는다.
결손 이름은 이 문서의 설명용 표제이며 새 슬롯/새 wire ID가 아니다.

| 결손 | 영향을 받는 반례 | 문서 22의 기존 결손 | 문서 21의 기존 슬롯 | 남아 있는 후속 판단 |
|---|---|---|---|---|
| 과거 호출 결과 회수·지지/잔여 명령 근거 | 응답 유실 | M-05 및 §4 관측/완료 근거·상실 반응 | P18, P19, P30, P35, P44, P45 | 원 결과 제공/보존·상관 및 지지/해제 근거를 실제 profile과 조사에서 확보해야 한다. |
| 관측 신선도·연속성 입증 | 인계 지연 | M-05, M-06 및 §4 관측 근거 | P17, P36, P42, P43, P47 | cache/원 표본 나이·boot/authority 연속성·silent change 한계를 확인해야 한다. |
| 동일 물품의 지지 자원 정의·지지 연속성 | 지지 자원 경합 | M-03, M-04, M-07, M-08 및 §4 조합/인계 | P20, P29, P34, P35 | alias·충돌 집합과 release 중 실제 대체 지지를 검증해야 한다. |
| 고장 검출·local 반응·진입한 잔여 효과 | 받는 로봇 고장 | M-08 및 §4 상실 반응 | P34, P35, P42, P43, P45, P47 | 검출 범위와 fence 전달 지연 구간의 보호 성능, queue/지지 상태를 검증해야 한다. |
| 사람 인수와 서비스 전체 완료의 결합 | 네 반례 이후 공통 경계 | R-11의 부분매핑, §5 OPEN-RECEIPT 경계 | S13, P49, P50은 관련 입력만 연결 | 각 물리 결과를 수령 자격·유효한 선언과 어떤 관계로 묶어 서비스 완료로 기록할지는 여전히 미정이다. 관계 자체의 전용77슬롯은 없다. |

원본은 [문서 22 §§4–6](22_open_items_boundary.md)과 [문서 21 §§2·10](21_declaration_reuse_measurement.md)이다.
P43/P44/P45/P47은 이번 반례에서 문서 21의 고정77 목록을 직접 참조한 자리다. 문서 22의
선택33 목록을 늘리거나 기존 라벨을 수정하지 않았다. 마지막 행은 N2의 부분매핑 한계를
유지한다. 전용 관계 슬롯을 새로 만들지 않았으며 이를 “연결 완료”로 감추지 않는다.

이 네 반례의 결손은 위 기존 주제/슬롯에 연결됐다. 추가로 연결할 대상을 찾지 못한 새
결손은 없다. 단, R-11의 전용 자리 부재는 기존에 명명된 결손으로 그대로 남는다.
실제 지지 자격이 미결이므로 OPEN-MOBILE-SUPPORT를 닫지 않으며, 개별 operation 결과를
얻더라도 OPEN-RECEIPT의 유효 규칙과 전체 완료 결합이 자동 완성되는 것은 아니다.

## 7. 로드맵 네 낱말의 귀속

| 로드맵 낱말 | 반례 | 귀속 근거와 한계 |
|---|---|---|
| 유실 | 응답 유실 | SEND_ENTERED 뒤 native 응답을 잃고 원 identity의 결과를 조회/보존한다. |
| 경합 | 지지 자원 경합 | 같은 물품/인계 세대 support resource를 T1에서 함께 예약하려는 충돌이다. |
| 거부 | 지지 자원 경합, 받는 로봇 고장 | 공통 02 §4의 자원 미확보 BUSY와 셀 02 §§5–6의 오래된 permit/epoch 거부가 실제 규범 경로다. 여기서는 RX 예약/dispatch gate의 거부를 다룬다. |
| 인계 불명 | 응답 유실, 인계 지연, 받는 로봇 고장 | 원 native 효과 또는 현재 지지/관측 연속성을 확정하지 못하는 분기다. 정상 WAIT_TARGET 미달만을 원 호출의 UNKNOWN으로 바꾸지는 않는다. |

**다섯 번째 반례는 추가하지 않았다.** “거부”는 기존 경합/고장 후보 안에서
예약 실패 및 stale permit 차단으로 드러난다. 이는 [공통 02 §4](contracts/v1.0/02_identity_durability_recovery.md)와
[셀 02 §§5–6](cell_operations/v1.0/02_authorization_invalidation.md)의 직접 근거가 있다.
native 장치가 이미 받은 명령을 거절하는 모든 경우까지 검사했다는 뜻은 아니다.
그 유형을 후속 범위에 넣으려면 별도로 구체화해야 하며 이번 귀속 수에 끼워 넣지 않는다.

## 8. 인용 식별자와 검토의 한계

| 반례 | I 식별자 | SC 식별자 |
|---|---|---|
| 응답 유실 | I01, I03, I04, I07, I08 | SC02 |
| 인계 지연 | I04, I09 | SC06 |
| 지지 자원 경합 | I05, I08 | SC14 |
| 받는 로봇 고장 | I08, I09, I12 | SC03-C, SC09 |

직접 파싱한 규범 목록은 I 12개, SC 19개다. 위 참조의 고유 집합은 I 8개와 SC 5개이며
모두 실제 목록에 있다. 이 표는 사용한 인용의 목록이지 나머지 불변식/시나리오를 검증했다는
커버리지 주장이나 실행된 테스트 수가 아니다.

이 검토에서 N3가 낸 것은 **네 질문의 문서상 답과 부당 전이를 차단하는 규범 위치**다.
오독별 판정은 막는다 4, 부분적으로 막는다 0, 막지 못한다 0이다. 문서 21의 free 수나
문서 22의 불충분 판정으로 이 분포를 예측하지 않았다. 그 수들은 현장 타당성 입력의
잔존을 재며, 여기서는 특정 부당 전이의 명시적 금지를 묻기 때문이다.

판정을 뒤집을 수 있는 근거는 다음과 같다.

- 인용 문장이 실제로 다른 전이나 층위에 적용되거나, 같은 버전의 다른 규범이 해당 부당
  전이를 허용함을 보이면 해당 “막는다” 판정을 재검토한다.
- 원 질문을 옮긴 문장이 원래 질문의 근거/연속성/동시 해제/fence 경계를 바꿨음을 보이면
  질문과 답을 다시 대조한다. 질문을 더 쉬운 질문으로 바꾸어 결과를 유지하지 않는다.
- 요구되는 alias·관측·검사 경로를 실제 구현이 생략한다는 실행 증거가 나오면 그 구현의
  준수 주장은 깨진다. 이 문서는 그러한 실행을 수행하거나 구현 준수를 인증하지 않았다.
- local 보호 경로·시간 근거·수령 규칙이 이후 확보되면 결손 상태를 별도로 갱신한다.
  현재 NOT_COMMISSIONED나 두 open 상태를 이 문서로 변경하지 않는다.

N4 이후에는 이 문서의 조건부 시퀀스와 결손을 검증 범위로 삼을 수 있다. 이번에는
장애 시험·시뮬레이션·실물 운전·TLC 모델 검사를 실행하지 않았고, 새 장치/시간/하중 수치나
새 규범·schema·SDK를 만들지 않았다. CI와 아래 파서는 문서의 구조·인용·불변을 확인하는
도구이며 네 반례의 실행 증거가 아니다.

관련 문서: [로드맵 N3](00_design_roadmap.md) · [N1 후보](20_first_handover_case.md)
· [N2 경계](22_open_items_boundary.md) · [선언 측정](21_declaration_reuse_measurement.md)
· [실제 근거가 필요한 미결](implementation/critical_open_items.md).

### 8.1 문서 원자료 확인

저장소 루트에서 아래를 실행한다. 인용의 의미가 그 질문에 맞는지는 원문을 별도로 읽어야 한다.

```python
from pathlib import Path
import re
root = Path("docs")
source = (root / "20_first_handover_case.md").read_text()
text = (root / "23_handover_counterexamples.md").read_text()
names = ["응답 유실", "인계 지연", "지지 자원 경합", "받는 로봇 고장"]
original = {}
for line in source.split("## 6. ", 1)[1].splitlines():
    if line.startswith("| "):
        row = [c.strip() for c in line.strip("|").split("|")]
        if row[0] in names:
            original[row[0]] = row[4]
axes = {"책임", "권한", "증거", "격리", "후속 조치"}
axis_count = 0
for index, name in enumerate(names, 2):
    section = text.split(f"## {index}. {name}", 1)[1].split(f"## {index + 1}. ", 1)[0]
    assert original[name] in section
    assert "**옮긴 질문:**" in section and "**반박할 오독:**" in section
    steps = section.split(f"### {index}.2 ", 1)[1].split(f"### {index}.3 ", 1)[0]
    assert len(re.findall(r"^\d+\. ", steps, re.M)) == 6
    rows = [[c.strip() for c in line.strip("|").split("|")]
            for line in section.splitlines() if line.startswith("| ")]
    rows = [row for row in rows if row[0] in axes]
    assert len(rows) == 5 and {row[0] for row in rows} == axes
    assert all(row[1] and re.search(r"\]\((?:contracts|cell_operations)/", row[2]) for row in rows)
    assert "**판정: 막는다 — 규범상.**" in section and "**미확정:" in section
    axis_count += len(rows)
i_ids = set(re.findall(r"^- (I\d{2}):", (root / "contracts/v1.0/01_responsibility_and_semantics.md").read_text(), re.M))
sc_ids = set(re.findall(r"^\| (SC\d{2}(?:-[A-D])?)\b", (root / "contracts/v1.0/06_scenarios_and_validation.md").read_text(), re.M))
used_i = set(re.findall(r"(?<![A-Za-z0-9_])I\d{2}(?![A-Za-z0-9_])", text))
used_sc = set(re.findall(r"(?<![A-Za-z0-9_])SC\d{2}(?:-[A-D])?(?![A-Za-z0-9_-])", text))
assert len(i_ids) == 12 and len(sc_ids) == 19
assert used_i <= i_ids and used_sc <= sc_ids
fixed_text = (root / "21_declaration_reuse_measurement.md").read_text().split("## 2. ", 1)[1].split("## 3. ", 1)[0]
slots = set(re.findall(r"^\| ([SP]\d{2}) \|", fixed_text, re.M))
used_slots = set(re.findall(r"(?<![A-Za-z0-9_])[SP]\d{2}(?![A-Za-z0-9_])", text))
assert len(slots) == 77 and used_slots <= slots
def symbols(value):
    return set(re.findall(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+(?![A-Za-z0-9_-])", value))
open_names = {"OPEN-MOBILE-SUPPORT", "OPEN-RECEIPT"}
case_source = source.split("## 1. ", 1)[1].split("## 2. ", 1)[0]
case_ids = symbols(case_source) - open_names
n2 = (root / "22_open_items_boundary.md").read_text()
requirements = set(re.findall(r"^\| ([MR]-\d{2}) \|", n2, re.M))
prose = re.sub(r"(?ms)^```.*?^```\s*", "", text)
used_cases = symbols(prose) - open_names - sc_ids - requirements
assert used_cases <= case_ids
terms = text.split("## 7. ", 1)[1].split("## 8. ", 1)[0]
for term in ["유실", "경합", "거부", "인계 불명"]:
    row = next(line for line in terms.splitlines() if line.startswith(f"| {term} |"))
    assert any(name in row for name in names)
print("cases", len(names), "steps", 24, "axes", axis_count, "original questions preserved", len(original))
print("norm I", len(i_ids), "SC", len(sc_ids), "used I", len(used_i), "SC", len(used_sc))
print("linked slots", len(used_slots), "case names", len(used_cases), "unknown I/SC/slot/case", 0, "roadmap terms covered", 4)
```
