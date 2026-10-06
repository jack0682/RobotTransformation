# 21. 두 번째 사례의 선언 계수: 기준선 대응 점검

기준일: 2026-09-14 · **라벨링 전의 열거·기준선 대응 점검. 재사용 계수의 완성본이 아니다.**

[20번 인계 사례](20_first_handover_case.md)를 사례 1로 삼고 받는 장치를 고정 적재
스테이션으로 바꿀 때의 재선언을 세려면, 먼저 사례 1에 비교할 선언 값이 있는지
확인해야 한다. 이 문서는 그 선행 점검의 단위와 원자료를 보존한다. 대응이 충분한지
판정하기 전 사례 2의 값이나 inherited·declared·free 수를 만들지 않는다.

20번은 가상 사례의 정의이며 executable profile, 현장 설치 기록 또는 적합성 시험
결과가 아니다. 그 문서의 독립 검토 통과는 이 한계를 없애지 않는다.
[11번](11_first_cell_contract.md)은 첫 적용 사례의 장비·장소·최종 수령 조건이
고정되지 않았고 이전 산업 셀은 `NOT_COMMISSIONED`라고 명시한다.
[18번](18_cell_operations_contract.md)과 [보존 기록 안내](../references/README.md)도
새 설치의 필수 입력·검증을 대신하지 않는다. 현재 지정된 문서들에는 실행 허가 입력이
채워진 첫 셀 기록이 없으므로, 이 점검을 실제 현장 이력의 측정으로 부르지 않는다.

## 1. 라벨링 전 고정한 단위와 출처

슬롯은 아래 원문이 확정을 요구한 **입력 항목의 자리**다. 한 자리의 입력값, 그 값이
현장에 맞는지 판단하는 노동, 동일 정보가 다른 기록에 다시 쓰이는 노동은 서로 같지
않다. 이 표의 행 수를 사람의 독립 판단 횟수나 시간으로 환산하지 않는다.

- **S2** = [cell_operations/v1.0/01_scope_conditions_functions.md §2](cell_operations/v1.0/01_scope_conditions_functions.md), `Per-installation operating-scope record`의 `Inputs required for execution admission`. 원문 Item 6개를 입력 주제 21개로 분해한다.
- **B1** = [contracts/v1.0/04_binding_and_admission.md §1](contracts/v1.0/04_binding_and_admission.md), `BindingProfile`의 `Required item` / `Details`. 원문 그룹 13개를 입력 주제 56개로 분해한다.

모든 표 행의 출처 셀은 위 파일·절과 원문 행 이름을 함께 지정한다. 원문의 `such as`
뒤 예시를 필수 슬롯으로 늘리지 않는다. 슬래시로 연결된 종류·조합 목록은 한 입력 주제로
보존한다. 반면 실제로 다른 입력인 단위와 채널 순서, 소프트웨어 버전과 source commit은
나눈다. 각 부모 그룹에서 만든 자리는 §2에 전부 적으며, 사례 2를 보고 새 자리를 추가하거나
사례 1에 값이 없다는 이유로 제거하지 않는다.

설치에 선택된 값(S2)과 지원 profile이 허용하는 값(B1)은 다른 자리다. 예컨대 설치의
교정과 profile의 교정 ID·범위·유효 조건은 같은 자료를 참조할 수 있지만, 자동으로 같은
조건을 만족하는 것은 아니다. 이 중복 기록 가능성 때문에 77이라는 수는 고유 지식이나
순수 추가 작업량의 수가 아니다. 완성 계수를 산출한다면 다른 단위의 결과는 민감도 분석으로
별도 제시하고 이 열거를 바꾸지 않는다.

값과 별도 증거를 나눈 혼합 부모는 **B1의 timing 1개**다. 원문이 명시한
`with supporting evidence`에 따라 값·basis 자리 P36–P41과 근거 자리 P42를 구별한다.
P36–P42의 7개 중 근거 분리로 생긴 자리는 1개이고, 이미 원문에서 별도로 열거한 evidence와
validation 그룹을 다시 이중 분할하지 않는다. 나머지 항목에 숫자를 적을 형식이 있다는
이유만으로 타당성 판단이 자동화됐다고 간주하지 않는다.

재사용 가능성은 형식·문자열·digest 동일성과 다르다.
[셀 프로토콜 §3](cell_operations/v1.0/04_protocol_integration_ui.md)은 artifact digest가
맞아도 schema 의미를 이해하지 못하면 업무 판정에 사용할 수 없으며 ID나 자유 서술이
machine decision rule을 대체할 수 없다고 규정한다. 미확정 입력을 default true나
`not applicable`로 채우지 않는 S2의 제한도 적용한다.

## 2. 고정 슬롯 목록

아래는 원문 입력 주제의 열거다. 사례 1의 대응 여부와 세 라벨은 아직 이 표의 값이 아니다.

| ID | 입력 주제 | 파일·절 별칭 / 원문 그룹 |
|---|---|---|
| S01 | 실제 demonstration/operation/teaching 범위 | S2 / Use |
| S02 | 운영 절차 | S2 / Use |
| S03 | 시설 제어 프로그램 | S2 / Facility controllers |
| S04 | 통신 설정 | S2 / Facility controllers |
| S05 | 신호 의미 | S2 / Facility controllers |
| S06 | 고장·재부팅 동작 | S2 / Facility controllers |
| S07 | 설치 인스턴스 | S2 / Equipment and goods |
| S08 | 설치 모델 | S2 / Equipment and goods |
| S09 | 설치 버전 | S2 / Equipment and goods |
| S10 | 설치 교정 | S2 / Equipment and goods |
| S11 | 좌표 | S2 / Equipment and goods |
| S12 | 하중 조합 | S2 / Equipment and goods |
| S13 | 실제 순서·병행 범위 | S2 / Work |
| S14 | 각 참여자의 책임 | S2 / Work |
| S15 | 개입 목적·위치 | S2 / People |
| S16 | 정비 절차 | S2 / People |
| S17 | 인계 절차 | S2 / People |
| S18 | 재시작 절차 | S2 / People |
| S19 | 환경별 검증 결과 | S2 / Validation |
| S20 | 미결 항목 | S2 / Validation |
| S21 | 제약 | S2 / Validation |
| P01 | support_id | B1 / identity |
| P02 | manufacturer/model/hardware_revision | B1 / identity |
| P03 | firmware 허용 범위 | B1 / identity |
| P04 | driver/controller 버전 | B1 / identity |
| P05 | source commits | B1 / identity |
| P06 | endpoint 역할 | B1 / native interface |
| P07 | native API/action/message 종류 | B1 / native interface |
| P08 | 단위 | B1 / native interface |
| P09 | joint/channel 순서 | B1 / native interface |
| P10 | return-value 의미 | B1 / native interface |
| P11 | native-ID/result-lookup 제공 여부 | B1 / native interface |
| P12 | 필수 패키지 | B1 / dependencies |
| P13 | 전이 의존성 | B1 / dependencies |
| P14 | image variants | B1 / dependencies |
| P15 | kernel/device/GPU 제약 | B1 / dependencies |
| P16 | 제공 kinds/bodies | B1 / capability |
| P17 | observation schemas | B1 / capability |
| P18 | completion/failure/cancel evidence | B1 / capability |
| P19 | 현재 상태와 과거 결과 lookup의 구별 | B1 / capability |
| P20 | 충돌 자원 단위 집합 | B1 / resource_set |
| P21 | prepare/activate/destructor의 torque·position·mode 효과 | B1 / startup/shutdown |
| P22 | 실제 init flags | B1 / startup/shutdown |
| P23 | base/tool/fixture/gripper/zero calibration IDs | B1 / calibration |
| P24 | 교정 범위 | B1 / calibration |
| P25 | 교정 유효 조건 | B1 / calibration |
| P26 | 필요한 mode | B1 / mode/authority |
| P27 | remote/auto/manual 전환 확인 | B1 / mode/authority |
| P28 | direct native client 배제 조건 | B1 / mode/authority |
| P29 | predicates | B1 / completion/cancel |
| P30 | correlation | B1 / completion/cancel |
| P31 | tolerances | B1 / completion/cancel |
| P32 | settling | B1 / completion/cancel |
| P33 | timeouts | B1 / completion/cancel |
| P34 | stop results | B1 / completion/cancel |
| P35 | release conditions | B1 / completion/cancel |
| P36 | observation age의 basis | B1 / timing |
| P37 | grant TTL 값 | B1 / timing |
| P38 | ticket/deadman 값 | B1 / timing |
| P39 | prepare validity 값 | B1 / timing |
| P40 | execution 시간 값 | B1 / timing |
| P41 | shutdown 시간 값 | B1 / timing |
| P42 | timing 값의 supporting evidence | B1 / timing |
| P43 | boot detection | B1 / restart |
| P44 | native-history retention | B1 / restart |
| P45 | residual commands | B1 / restart |
| P46 | resynchronization | B1 / restart |
| P47 | unobservable-reboot limitations | B1 / restart |
| P48 | required evidence schemas | B1 / evidence |
| P49 | permitted human-attestation scope | B1 / evidence |
| P50 | contradiction decisions | B1 / evidence |
| P51 | literature/laboratory/site findings | B1 / validation |
| P52 | actual test artifacts | B1 / validation |
| P53 | 검증 dates | B1 / validation |
| P54 | 검증 versions | B1 / validation |
| P55 | 검증 conditions | B1 / validation |
| P56 | 검증 limitations | B1 / validation |

분해 전 출처는 S2의 6개 Item과 B1의 13개 그룹, 합계 19개다. 열거된 입력 자리는
S01–S21 21개와 P01–P56 56개, 합계 77개다. 단일 자리를 유지한 B1 resource_set을
제외한 18개 출처 행에서 여러 자리가 나왔다. 따라서 일반 주제 분해에 의한 증가와
timing의 값/근거 분리 1건을 혼동하지 않는다.

## 3. 대응 판정 방법

대응은 **사례 1의 값이 있는지**의 축이며 inherited/declared/free와 독립이다.
20번의 §1·3·4·5에 그 입력 주제의 구체 선언이 있으면 대응으로 표시한다. 현장 적합성의
입증까지 요구하지는 않지만, 규범을 적용해야 한다는 말, 증거가 필요하다는 요구,
반례 질문 또는 OPEN 항목의 이름만으로 그 입력값이 있는 것으로 세지 않는다.

예를 들어 `BAY-01`은 장소 식별자이지 교정된 좌표값이 아니다. 문서에
`FINITE_ACTION`과 `ENSURE_STATE`의 차이가 설명돼 있어도 실제 장치가 어떤 kind/body를
제공하는지를 확정한 값은 아니다. `HOST-IN`과 `HOST-OUT`의 역할도 native API endpoint의
실제 역할 정의를 자동으로 채우지 않는다. 일부 설명만 있는 자리는 대응 불가로 표시하되
어떤 설명이 존재하는지는 매핑 근거에 남긴다.

대응 불가가 전체 77자리의 과반이면 사례 1을 이 측정의 기준선으로 쓰는 접근을
유지하지 않는다. 0인 라벨 수를 양수로 만들기 위해 단위를 고치는 기준은 사용하지 않는다.
대응의 관측값이 나오면 이 고정 목록과 관측을 보존한 채 다음 접근을 비교한다.

## 4. 사례 1의 대응 원자료

근거의 `20 §n`은 [20번 사례](20_first_handover_case.md)의 해당 절이다. `부분:`으로
시작하는 근거는 관련 설명은 있지만 그 입력 자리를 채울 값까지 제공하지 않는 경우다.
이를 별도로 표시하여 더 느슨한 대응 기준에서 결론이 달라지는지도 점검할 수 있게 한다.
대응 불가는 장비 자체가 그 기능이 없다는 뜻이 아니라, 이 기준 문서에 값이 없다는 뜻이다.

| ID | 대응 축 | 사례 1의 값 또는 대응 불가의 근거 |
|---|---|---|
| S01 | 대응 불가 | 부분: 20 §1은 소포 인계 한 건의 범위와 끝을 정하지만 실제 demonstration/operation/teaching 중 어떤 설치 사용 범위인지는 확정하지 않는다. |
| S02 | 대응 불가 | 부분: 20 §3·4에 동작 분해와 완료 근거는 있지만 설치의 구체 운영 절차·revision은 없다. |
| S03 | 대응 불가 | 제어 프로그램이나 그 artifact가 없다. 20 §1은 자동 출입문 제어를 이번 동작에 추가하지 않는다. |
| S04 | 대응 불가 | Host의 통신 endpoint·전송 설정 값이 없다. |
| S05 | 대응 불가 | 부분: 20 §4는 소포 식별·지지·분리 관측을 요구하지만 어떤 실제 신호가 그 의미를 보장하는지는 OPEN-MOBILE-SUPPORT다. |
| S06 | 대응 불가 | 부분: 20 §6의 고장·재부팅은 반례 후보이며 해당 장치의 실제 고장·재부팅 동작 선언이 아니다. |
| S07 | 대응 | 20 §1: SITE-01, IN-01/HOST-IN, OUT-01/HOST-OUT, TRAY-01, RUNTIME-01이라는 사례 인스턴스와 토폴로지. 실제 설치 확인은 아니다. |
| S08 | 대응 불가 | 실제 장치 모델을 선택하지 않았다. |
| S09 | 대응 불가 | 설치할 장치·controller·driver의 버전 값이 없다. |
| S10 | 대응 불가 | 설치 교정값·교정 기록이 없다. |
| S11 | 대응 불가 | BAY-01은 장소의 이름이며 좌표계·좌표값·변환이 아니다. |
| S12 | 대응 불가 | 부분: 20 §1에 책 한 권이 든 봉인 소포가 있지만 질량·자세와 장치/적재함의 허용 하중 조합은 OPEN-MOBILE-SUPPORT다. |
| S13 | 대응 | 20 §3 Q1-b의 내려놓기·받는 장치 유지·그리퍼 해제·후퇴 순서, §1·4의 복수 지지 허용과 동시 지지 해제 금지. 실행 그래프를 만들었다는 뜻은 아니다. |
| S14 | 대응 | 20 §1·3: 플랫폼의 의도·판정, 각 Host의 native 사실·관측, 보내는/받는 물리 역할, RECIPIENT-01의 현장 개입 책임. |
| S15 | 대응 | 20 §1: 구획 밖에서 인수를 선언하고 물품 접촉·구획 진입은 정상 경로 밖의 직접 개입으로 다룬다. |
| S16 | 대응 불가 | 장비 정비 절차가 없다. |
| S17 | 대응 불가 | 부분: 20 §4는 인계에서 요구할 관측을 정하지만 장치별 기계적 인계 순서·확정 절차는 OPEN-MOBILE-SUPPORT와 OPEN-RECEIPT다. |
| S18 | 대응 불가 | 부분: 20 §1·3 Q4-b는 개입 후 명시적 새 시작을 요구하지만 실제 재시작 절차·revision은 없다. |
| S19 | 대응 불가 | 20번은 현장 시험 결과를 제공하지 않는다. |
| S20 | 대응 | 20 §5: OPEN-MOBILE-SUPPORT, OPEN-RECEIPT의 이름과 빠진 입력 내역. 미결을 해소한 것으로 세지 않는다. |
| S21 | 대응 | 20 §1·5: 단일 사이트·Runtime, 두 Host, 인계 한 지점, 실외 운송 출발 제외, 독립 Runtime 변형 제외와 NOT_COMMISSIONED 제한. |
| P01 | 대응 불가 | 장치별 support_id를 선언하지 않았다. 로봇 별칭은 support_id가 아니다. |
| P02 | 대응 불가 | manufacturer/model/hardware_revision 값이 없다. |
| P03 | 대응 불가 | firmware 허용 범위가 없다. |
| P04 | 대응 불가 | driver/controller 버전 값이 없다. |
| P05 | 대응 불가 | 장치 바인딩 구현의 source commits가 없다. 문서의 Git commit과 다른 입력이다. |
| P06 | 대응 불가 | 부분: 20 §1의 HOST-IN/HOST-OUT은 소프트웨어 책임 경계다. B1이 요구하는 native endpoint별 역할은 없다. |
| P07 | 대응 불가 | 실제 native API/action/message 종류를 고정하지 않았다. |
| P08 | 대응 불가 | native 입력·관측 단위가 없다. |
| P09 | 대응 불가 | joint/channel 순서가 없다. |
| P10 | 대응 불가 | 실제 native return code의 의미가 없다. |
| P11 | 대응 불가 | 해당 장치의 native ID·과거 결과 조회 제공 여부가 없다. |
| P12 | 대응 불가 | 장치의 필수 패키지 목록이 없다. |
| P13 | 대응 불가 | 전이 의존성 목록이 없다. |
| P14 | 대응 불가 | 사용할 image variant가 없다. |
| P15 | 대응 불가 | kernel/device/GPU 제약 값이 없다. |
| P16 | 대응 불가 | 부분: 20 §4는 FINITE_ACTION·ENSURE_STATE의 의미 차이를 설명하지만 장치가 실제로 제공하는 kind/body 집합은 확정하지 않는다. |
| P17 | 대응 불가 | 장치 observation schema의 실제 선택과 revision이 없다. |
| P18 | 대응 불가 | 부분: 20 §4는 완료 관측의 종류를 요구하지만 실제 native 결과·실패·취소 근거를 갖춘 profile은 없다. |
| P19 | 대응 불가 | 부분: 20 §4는 현재 상태로 과거 성공을 복원하지 말라고 한다. 이 장치가 제공하는 두 lookup의 방법·차이는 선언하지 않는다. |
| P20 | 대응 불가 | 부분: 20 §1에 논리 자원 분류는 있지만 실제 controller/bus의 공유 여부와 native 충돌 단위 집합은 없다. |
| P21 | 대응 불가 | prepare/activate/destructor의 실제 torque·position·mode 효과가 없다. |
| P22 | 대응 불가 | 실제 init flags가 없다. |
| P23 | 대응 불가 | calibration ID 묶음이 없다. |
| P24 | 대응 불가 | profile 교정 범위가 없다. |
| P25 | 대응 불가 | profile 교정 유효 조건이 없다. |
| P26 | 대응 불가 | 장치의 필요한 native mode가 없다. |
| P27 | 대응 불가 | remote/auto/manual 전환 확인 방법이 없다. |
| P28 | 대응 불가 | direct native client를 배제할 조건이 없다. |
| P29 | 대응 불가 | 부분: 20 §4에 지지·분리라는 목표는 있지만 profile이 사용할 predicate와 typed 평가 규칙을 확정하지 않았다. |
| P30 | 대응 불가 | 부분: 20 §4는 같은 호출·소포·인계 건의 연결을 요구하지만 장치에서 확보되는 correlation 값·제약이 없다. |
| P31 | 대응 불가 | 허용오차 값이 없다. |
| P32 | 대응 불가 | settling 값과 조건이 없다. |
| P33 | 대응 불가 | profile timeout 값이 없다. |
| P34 | 대응 불가 | 해당 장치의 stop result 정의가 없다. |
| P35 | 대응 불가 | 부분: 20 §4의 RELEASED 일반 조건과 BAY 잔여 점유는 있지만 실제 장치에서 그 조건을 확인할 release rule은 확정하지 않았다. |
| P36 | 대응 불가 | 실제 observation age를 보장할 basis가 없다. |
| P37 | 대응 불가 | grant TTL 값이 없다. |
| P38 | 대응 불가 | ticket/deadman 값이 없다. |
| P39 | 대응 불가 | prepare validity 값이 없다. |
| P40 | 대응 불가 | execution 시간 값이 없다. |
| P41 | 대응 불가 | shutdown 시간 값이 없다. |
| P42 | 대응 불가 | timing 값의 supporting evidence가 없다. |
| P43 | 대응 불가 | 해당 장치의 boot detection 방법이 없다. |
| P44 | 대응 불가 | native-history retention 범위가 없다. |
| P45 | 대응 불가 | 부분: 20 §4·6은 잔여 명령 확인을 요구하지만 실제 queue·잔여 호출을 확인하는 방법이 없다. |
| P46 | 대응 불가 | 장치 resynchronization 방법이 없다. |
| P47 | 대응 불가 | 해당 장치에서 관측할 수 없는 재부팅의 한계가 없다. |
| P48 | 대응 불가 | 선택한 evidence schema와 revision이 없다. |
| P49 | 대응 | 20 §1·4: RECIPIENT-01의 특정 소포·받는 로봇·인계 건에 관한 인수 선언이며 native 성공·센서 지지의 대체를 허용하지 않는다. 선언 범위의 값은 있으나 신원·권한·유효성 근거는 OPEN-RECEIPT다. |
| P50 | 대응 불가 | 부분: 20 §3·4는 DISPUTED 일반 처리와 모순 배제를 요구한다. 실제 evidence 쌍의 양립/모순 판정은 profile에서 고정하지 않았다. |
| P51 | 대응 불가 | 장치별 literature/laboratory/site findings가 없다. |
| P52 | 대응 불가 | actual test artifacts가 없다. |
| P53 | 대응 불가 | 해당 장치 검증의 dates가 없다. 문서 기준일과 다르다. |
| P54 | 대응 불가 | 해당 장치 검증의 versions가 없다. 문서 revision과 다르다. |
| P55 | 대응 불가 | 해당 장치 검증의 conditions가 없다. |
| P56 | 대응 불가 | 부분: 20번은 미검증·미구현 범위를 밝히지만 특정 시험의 적용 한계를 기록한 validation 결과는 없다. |

## 5. 선행 점검 결과와 접근 전환

표를 재계산한 결과는 다음과 같다. 분모와 매핑 원자료를 결과에 맞춰 바꾸지 않았다.

| 지표 | 수 |
|---|---:|
| 고정 슬롯 총수 | 77 |
| 사례 1 값에 대응 | 7 |
| 사례 1 값에 대응 불가 | 70 |
| 대응 불가 중 관련 설명만 있는 자리 | 18 |
| 대응 불가 중 관련 값 자체가 없는 자리 | 52 |
| S2 원문 Item 중 하위 슬롯을 만들지 못한 Item | 0 / 6 |
| B1 원문 그룹 중 하위 슬롯을 만들지 못한 그룹 | 0 / 13 |

주결과는 **대응 불가 70/77 = 90.91%**다. 관련 설명을 선언값으로 넓게 인정하는
민감도 점검에서도 18개를 모두 대응으로 승격했을 때 대응 불가는 **52/77 = 67.53%**다.
엄격한 판정과 이 의도적으로 느슨한 판정 모두 과반이다. 두 번째 비율은 다른 기준의
결과이며 70이라는 주결과를 대체하지 않는다.

따라서 실패한 것은 규범에서 항목을 열거하는 부분이 아니라 **20번을 채워진 선언
기준선으로 사용한 선택**이다. 20번은 작업 의미와 미결을 정의하기 위한 문서였고,
profile과 실제 설치 입력을 채우는 문서가 아니었다. 이 결과는 장치가 인계할 수 없다거나
RX의 재사용 가치가 없다는 판정이 아니다.

계획의 과반 기준에 따라 여기서 접근을 전환한다. 사례 2를 유리하게 선언하거나
슬롯을 제거하여 이어가지 않는다. inherited·declared·free와 RX 고유 부담의 네 숫자는
**산출하지 않았다**. 이 칸들을 0이라고 읽지 않는다. 대응 불가 70개를 free 70개로
대체하는 것도 하지 않는다. 기준선의 값 부재와 새로운 사례에 필요한 인간 판단은
서로 다른 측정 대상이다.

이후 접근은 채워진 구성·profile·근거 묶음을 가진, commit이 고정된 모의 사례를 실제로
찾을 수 있는지부터 확인해야 한다. 발견되더라도 물리 현장 실측과 구별해야 한다.
그런 기준선이 없으면 규범의 선언·검사 지원도를 조사할 수는 있으나 그것을 다음 현장의
재사용 계수로 부를 수 없다. 이 선택은 다음 계획에서 결정한다.

RX 고유 부담은 이후에도 RX 전용 artifact/schema/식별·검증 포장의 하한으로만 셀 수
있으며, 그 방식은 RX 부담을 과소평가하는 방향으로 치우친다. 현재 점검에는 그 네 번째
숫자조차 없으므로 RX의 추가 부담을 빼고 재사용 효과를 주장할 근거가 없다. 슬롯 수를
사람의 시간·비용 절감으로 환산하지 않는다.

이 결론을 뒤집을 수 있는 관측은 20번에 이미 존재하지만 이 매핑이 놓친 구체 값이
충분히 발견되거나, 고정 슬롯의 중복·오독을 출처별로 지적하여 정정한 뒤 대응 불가가
과반 이하가 되는 경우다. 다른 설정 파일을 찾아 기준선으로 채택하는 것은 새 접근이지
20번의 빈 값을 사후 보충한 기존 측정으로 기록하지 않는다.


## 6. 두 번째 기준선 조사: 현재 결과

후속 측정일: 2026-09-15. **현재 결과는 declared 4, free 73, RX 전용 선언 포장 부담
하한 4다. inherited는 측정 불가이며 재판정 대상의 상한은 77이다.** §§1–5는 첫 시도의
보존 기록이고, 그 절의 “산출하지 않았다”는 당시 상태다. 이번 결과는 재사용 효과가
입증됐다는 뜻이 아니다. [가치와 평가](02_value_and_business.md)의 연결 비용 질문을
검사하기 위해, 지금 규범만으로 입력과 판정을 어디까지 지원하는지 좁혀 측정했다.

### 6.1 후보와 조사 범위

규범·20번 기준 revision은 rx_docs `44414c739e5f5c95594d29e514212b5ed60ba0d7`,
구성 후보는 rx-solutions `b6481ed4ad3de195db7dbadd50e0be29265956cf`와
rx-platform `ba49c59699110f54c91a3b9725873b61071c3e2e`의 추적 파일이다.
아래 링크는 모두 그 commit에 고정했다. 현재 checkout의 문서·구성 파일 경로를
`rg --files`와 `git ls-files`로 조사하고 관련 후보 및 README를 읽었다.
이것은 로컬 세 저장소의 조사이며 외부 현장, 다른 branch·과거 archive·개인 기록의
부재까지 증명하지 않는다. 코드 테스트 안의 즉석 fixture를 설치 선언 원장으로 승격하지 않는다.

| 별칭 | 읽은 후보 | 실제 내용과 한계 |
|---|---|---|
| A | [device-support.v1.json](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/catalogs/device-support.v1.json) | 4 profile. repositories와 profiles[].sources는 빈 배열, evidence_level은 SIMULATION_FIXTURE다. |
| B | [controllers.v1.json](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/catalogs/fixtures/controllers.v1.json) | controller 이름·plugin·joint_order 등의 합성 입력. A의 fixture_sources가 이 파일을 가리킨다. |
| C | [material-supply.bindings.json](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/process/material-supply.bindings.json) | 5 action의 host/target/resource/time 값. program/parameter_set의 schema_id는 rx.development.placeholder.v1이다. profile/site digest도 반복 바이트의 예시 값이며 실제 profile/site artifact 내용이 연결되지 않는다. |
| D | [host-configuration binding.json](https://github.com/jack0682/rx-platform/blob/ba49c59699110f54c91a3b9725873b61071c3e2e/spec/host-configuration/v1/binding.json) | process-configuration API의 schema와 source-file hash. 장치별 BindingProfile이나 설치 자격이 아니다. [README](https://github.com/jack0682/rx-platform/blob/ba49c59699110f54c91a3b9725873b61071c3e2e/spec/host-configuration/v1/README.md)는 process context 등록과 물리 적용을 구별한다. |
| E | [JTC README](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/jtc-simulation/README.md), [template](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/jtc-simulation/template.json), [site](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/jtc-simulation/site.json), [recipe](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/jtc-simulation/recipe.json) | 추가 발견한 SIMULATION 저작 입력. joint 목표·오차·endpoint 값은 있으나 교정/tool은 TEST ONLY 문자열이고 운영 자격·trust가 포함되지 않는다. |
| F | [시설 제어기 README](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/melsec-simulation/README.md), [template](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/melsec-simulation/template.json), [site](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/melsec-simulation/site.json), [recipe](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/device/melsec-simulation/recipe.json) | 모의 model/통신 주소·bit·settle 값. 프로그램과 publication 자료는 TEST ONLY이며 site_config를 실제 현장 근거로 쓰지 말라고 명시한다. 특정 제조사 지원 의무로 사용하지 않는다. |
| G | [process source](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/process/material-supply.source.json), [README](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/process/README.md) | C와 연결되는 실제 SEQUENCE 구조. 물리 순서/interlock 검증 결과는 아니다. |
| H | [cell-demo.json](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/development/cell-demo.json), [README](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/examples/development/README.md) | UI/API용 미검증 셀. definition/envelope/profile은 placeholder, completion은 UNOBSERVABLE이며 장치 driver·완료 근거·운영 자격이 없다. |

추가 탐색의 [restored-v1 fixture 안내](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/runtime/rx-executor/tests/fixtures/restored-v1/README.md)는
합성 clock/context/projection regression용이라고 명시한다. platform의 다른 binding 파일도
API schema와 source hash의 등록이다. 이들 및 rx_docs의 [11번](11_first_cell_contract.md)·
[18번](18_cell_operations_contract.md)에서 채워진 설치 선언과 자격 근거의 묶음을 확인하지 못했다.

### 6.2 고정 77자리의 대응 원자료

§3의 규칙을 그대로 적용한다. 주제의 실제 값이 있으면 대응이지만 일부 명칭·간접 함축·
placeholder만 있으면 대응 불가다. 대응은 현장 타당성의 입증을 요구하지 않는다.
A–D 합집합은 서로 다른 장치·API의 값을 모은 **후보 가용성 점검**이며 하나의 설치가 아니다.
E–H의 추가값도 동일하다. 이 합집합조차 미완성이라는 관측과 단일 유효 기준선 부재라는
판단을 구별한다. P17처럼 Host software 관측만 있는 대응은 그 한계를 셀에 적었다.

`관대` 열은 앞서 수행한 A–D 상한 probe의 대응 여부다. 그 probe는 부분 값·placeholder·
간접 함축까지 인정한 27자리였으며, 엄격 결과를 대신하지 않는다. `추가` 열은 E–H에서
새로 대응된 자리와 근거다. 원래 네 후보와의 비교를 유지하기 위해 원래 열에 합치지 않았다.

| ID | 관대 A–D | 엄격 A–D | 값 또는 대응 불가 이유 | 추가 E–H |
|---|---|---|---|---|
| S01 | 대응 불가 | 대응 불가 | 실제 demonstration/operation/teaching 사용 범위가 없다. | 추가 대응 없음 |
| S02 | 대응 불가 | 대응 불가 | C의 action별 binding은 운영 절차를 정하지 않는다. | 추가 대응 없음 |
| S03 | 대응 불가 | 대응 불가 | C의 program/parameter_set은 rx.development.placeholder.v1이고 실행 프로그램 내용이 없다. | 추가 대응 없음 |
| S04 | 대응 불가 | 대응 불가 | native endpoint·통신 설정 값이 없다. | E/F site: controller_manager/namespace/domain_id와 loopback 통신 route·timeout 설정. 모의 endpoint다. |
| S05 | 대응 불가 | 대응 불가 | 실제 입력 신호와 기계적 의미의 선언이 없다. | 추가 대응 없음 |
| S06 | 대응 불가 | 대응 불가 | 실제 fault/reboot 동작 선언이 없다. | 추가 대응 없음 |
| S07 | 대응 | 대응 | C: host/machine-sim, host/robot-sim과 target machine/sim, robot/sim을 지정한다. | 추가 대응 없음 |
| S08 | 대응 | 대응 불가 | A/B의 sim model 목록은 C의 설치 인스턴스에 연결된 모델 선택값이 아니다. | F template.controller_model이 해당 site/template 묶음의 controller 모델을 선택한다. 실제 설치 확인은 아니다. |
| S09 | 대응 불가 | 대응 불가 | 실제 설치 버전 묶음이 없다. | 추가 대응 없음 |
| S10 | 대응 불가 | 대응 불가 | C의 calibration_digests=[]; 교정값·기록이 없다. | 추가 대응 없음 |
| S11 | 대응 불가 | 대응 불가 | 실제 좌표계·변환·좌표값이 없다. | 추가 대응 없음 |
| S12 | 대응 불가 | 대응 불가 | 실제 하중·자세·도구 조합이 없다. | 추가 대응 없음 |
| S13 | 대응 | 대응 불가 | C의 JSON key 순서는 실행 순서·병행 선언이 아니다. | G: SEQUENCE.children이 door-open→place→clamp→withdraw→door-close 순서를 명시한다. |
| S14 | 대응 불가 | 대응 불가 | host/target 연결은 각 참여자의 전체 책임 선언이 아니다. | 추가 대응 없음 |
| S15 | 대응 불가 | 대응 불가 | 사람 개입 목적·위치가 없다. | 추가 대응 없음 |
| S16 | 대응 불가 | 대응 불가 | 정비 절차가 없다. | 추가 대응 없음 |
| S17 | 대응 불가 | 대응 불가 | 기계적 인계 절차가 없다. | 추가 대응 없음 |
| S18 | 대응 불가 | 대응 불가 | 재시작 절차가 없다. | 추가 대응 없음 |
| S19 | 대응 | 대응 불가 | SIMULATION_FIXTURE는 환경별 시험 결과가 아니다. | 추가 대응 없음 |
| S20 | 대응 | 대응 불가 | commissioning_inputs는 필요한 입력 종류 목록이며 실제 미충족 항목의 상태 기록이 아니다. | 추가 대응 없음 |
| S21 | 대응 | 대응 | A/B: SIMULATION_FIXTURE와 software simulation only 제한을 명시한다. 실제 설치 제약의 완성은 아니다. | 추가 대응 없음 |
| P01 | 대응 | 대응 | A/B: SIM-JTC-6DOF, SIM-JTC-7DOF, SIM-LEADER, SIM-IMPEDANCE. | 추가 대응 없음 |
| P02 | 대응 | 대응 불가 | model만 있고 manufacturer/hardware_revision이 없다. | 추가 대응 없음 |
| P03 | 대응 불가 | 대응 불가 | firmware 허용 범위가 없다. | 추가 대응 없음 |
| P04 | 대응 불가 | 대응 불가 | controller plugin 이름은 driver/controller 버전 값이 아니다. | 추가 대응 없음 |
| P05 | 대응 | 대응 불가 | repositories=[]와 sources=[]; fixture SHA와 D의 source_sha256은 source commit이 아니다. | 추가 대응 없음 |
| P06 | 대응 | 대응 불가 | MANIPULATOR 등의 role은 native endpoint 역할 선언이 아니다. | E site: controller_manager=/robot/controller_manager, namespace=/robot로 관리 endpoint 역할을 구체 지정한다. |
| P07 | 대응 | 대응 불가 | controller plugin 이름은 native API/action/message signature가 아니다. | 추가 대응 없음 |
| P08 | 대응 | 대응 불가 | position/velocity는 interface 이름이고 단위 선언이 아니다. | 추가 대응 없음 |
| P09 | 대응 | 대응 | A/B: controllers[].joint_order에 joint1…joint6/7 등의 순서가 채워져 있다. | 추가 대응 없음 |
| P10 | 대응 불가 | 대응 불가 | native return-value 의미가 없다. | 추가 대응 없음 |
| P11 | 대응 불가 | 대응 불가 | native ID/result lookup 제공 범위가 없다. | 추가 대응 없음 |
| P12 | 대응 | 대응 불가 | plugin namespace로 필수 패키지 전체를 확정할 수 없다. | 추가 대응 없음 |
| P13 | 대응 불가 | 대응 불가 | 전이 의존성 목록이 없다. | 추가 대응 없음 |
| P14 | 대응 불가 | 대응 불가 | image variant 선택이 없다. | 추가 대응 없음 |
| P15 | 대응 불가 | 대응 불가 | kernel/device/GPU 제약 값이 없다. | 추가 대응 없음 |
| P16 | 대응 | 대응 불가 | C의 FINITE_ACTION/program은 있지만 body의 실제 program/parameter artifact는 placeholder뿐이다. | 추가 대응 없음 |
| P17 | 대응 | 대응 | D: observation_schema=rx.host-process-configuration-observation.v1. Host process 관측 한 종류의 값이며 물리 장치 관측의 완성은 아니다. | 추가 대응 없음 |
| P18 | 대응 | 대응 불가 | simulation/completed, simulation/cancel은 규칙 이름이며 completion/failure/cancel evidence 정의가 아니다. | 추가 대응 없음 |
| P19 | 대응 불가 | 대응 불가 | 해당 장치의 현재/과거 lookup 방법을 구분한 선언이 없다. | 추가 대응 없음 |
| P20 | 대응 | 대응 | C: controller/machine-sim 또는 controller/robot-sim의 resource_set. 충돌 검증 결과는 아니다. | 추가 대응 없음 |
| P21 | 대응 불가 | 대응 불가 | 실제 lifecycle의 torque·position·mode 효과가 없다. | 추가 대응 없음 |
| P22 | 대응 불가 | 대응 불가 | 실제 init flags가 없다. | 추가 대응 없음 |
| P23 | 대응 불가 | 대응 불가 | C의 calibration_digests=[]; 대상별 교정 ID가 없다. | 추가 대응 없음 |
| P24 | 대응 불가 | 대응 불가 | 교정 범위가 없다. | 추가 대응 없음 |
| P25 | 대응 불가 | 대응 불가 | 교정 유효 조건이 없다. | 추가 대응 없음 |
| P26 | 대응 | 대응 불가 | IMPEDANCE_CONTROL 역할과 position interface로 native mode를 확정할 수 없다. | 추가 대응 없음 |
| P27 | 대응 불가 | 대응 불가 | remote/auto/manual 전환 확인이 없다. | 추가 대응 없음 |
| P28 | 대응 불가 | 대응 불가 | native client 배제 조건이 없다. | 추가 대응 없음 |
| P29 | 대응 | 대응 불가 | completion_rule 이름만 있고 predicate의 평가 내용은 없다. | 추가 대응 없음 |
| P30 | 대응 불가 | 대응 불가 | 장치 호출/결과의 correlation 값·제약이 없다. | 추가 대응 없음 |
| P31 | 대응 불가 | 대응 불가 | tolerance 값이 없다. | E site: goal_tolerance/path_tolerance의 joint별 position/velocity/acceleration=0.1. |
| P32 | 대응 불가 | 대응 불가 | settling 값·조건이 없다. | F template: predicates[].settle_ms=100. |
| P33 | 대응 | 대응 | C: execution_timeout_ms=5000이라는 timeout 값이 있다. 취소 전략 전체 검증은 아니다. | 추가 대응 없음 |
| P34 | 대응 불가 | 대응 불가 | stop result 의미가 없다. | 추가 대응 없음 |
| P35 | 대응 불가 | 대응 불가 | release 조건이 없다. | 추가 대응 없음 |
| P36 | 대응 | 대응 불가 | declared_update_hz=100은 source/cache 나이·취득 오차의 basis가 아니다. | 추가 대응 없음 |
| P37 | 대응 불가 | 대응 불가 | grant TTL 값이 없다. | 추가 대응 없음 |
| P38 | 대응 불가 | 대응 불가 | ticket/deadman 값이 없다. | 추가 대응 없음 |
| P39 | 대응 | 대응 | C: prepare_validity_ms=1000. | 추가 대응 없음 |
| P40 | 대응 | 대응 | C: execution_timeout_ms=5000. | 추가 대응 없음 |
| P41 | 대응 불가 | 대응 불가 | shutdown 시간 값이 없다. | 추가 대응 없음 |
| P42 | 대응 불가 | 대응 불가 | timing supporting evidence가 없다. | 추가 대응 없음 |
| P43 | 대응 불가 | 대응 불가 | boot detection 방법이 없다. | 추가 대응 없음 |
| P44 | 대응 불가 | 대응 불가 | native-history retention 범위가 없다. | 추가 대응 없음 |
| P45 | 대응 불가 | 대응 불가 | 잔여 native command 처리 선언이 없다. | 추가 대응 없음 |
| P46 | 대응 불가 | 대응 불가 | resynchronization 방법이 없다. | 추가 대응 없음 |
| P47 | 대응 불가 | 대응 불가 | unobservable reboot의 한계 선언이 없다. | 추가 대응 없음 |
| P48 | 대응 | 대응 불가 | D의 request/observation schema와 C의 program placeholder는 operation evidence schema의 선택값이 아니다. | 추가 대응 없음 |
| P49 | 대응 불가 | 대응 불가 | human-attestation 허용 범위가 없다. | 추가 대응 없음 |
| P50 | 대응 불가 | 대응 불가 | 실제 evidence 사이 contradiction 판정이 없다. | 추가 대응 없음 |
| P51 | 대응 불가 | 대응 불가 | 장치별 literature/laboratory/site findings가 없다. | 추가 대응 없음 |
| P52 | 대응 | 대응 불가 | fixture_sources는 입력 fixture의 hash이며 actual test artifact가 아니다. | 추가 대응 없음 |
| P53 | 대응 불가 | 대응 불가 | 검증 dates가 없다. | 추가 대응 없음 |
| P54 | 대응 불가 | 대응 불가 | 검증 versions가 없다. | 추가 대응 없음 |
| P55 | 대응 불가 | 대응 불가 | 검증 conditions가 없다. | 추가 대응 없음 |
| P56 | 대응 | 대응 불가 | synthetic scope 제한은 특정 시험 findings에 붙은 validation limitation 기록이 아니다. | 추가 대응 없음 |

E–H를 읽어도 TEST ONLY 교정·프로그램 bytes를 유효한 교정/프로그램 값으로 바꾸지 않는다.
F의 bit 이름은 센서 의미·native 완료/실패/cancel 계약을 완성하지 않고, H의 EQ ready 조건은
operation의 completion_rule 정의가 아니다. H의 observation unit·최대 age도 해당 장치의
native 단위·source age basis를 채우지 않는다. 그 이유로 S03/S05/S10/P08/P18/P29/P36은
추가 대응으로 승격하지 않았다.

| 측정 범위와 기준 | 대응 | 대응 불가 | 대응 불가 비율 |
|---|---:|---:|---:|
| 첫 측정: 20번, §3 엄격 | 7 | 70 | 90.91% |
| 두 번째: A–D, 관대한 상한 | 27 | 50 | 64.94% |
| 두 번째: A–D, §3 엄격 | 9 | 68 | 88.31% |
| 두 번째: A–H 추가 조사 포함, §3 엄격 | 15 | 62 | 80.52% |

A–D의 차이 18자리는 부분·간접·placeholder를 값으로 세지 않아서 생겼다.
E–H는 S04/S08/S13/P06/P31/P32의 6자리를 추가했다. 엄격 합집합은 39에 못 미친다.
이 점검에서 **채워진 선언 기준선은 확인되지 않았다.** 이것은 RX 전체 가치의 실패나
어떤 장치의 수행 불가능을 뜻하지 않는다.

## 7. inherited의 측정 불가와 사례 2의 경계

**inherited = 측정 불가.** 재사용된 것이 없다는 수치 결과가 아니다. 20번 기준의
대응 불가 70/77, 원래 네 후보의 68/77, 추가 조사까지의 62/77은 비교할 입력값이
충분하지 않다는 관측이다. 위 저장소/후보 범위에서 값·적용 조건·근거가 연결된 첫 셀
선언 묶음을 확인하지 못했으므로 어떤 슬롯에도 inherited 라벨을 부여하지 않는다.

사례 2는 [20번 §1](20_first_handover_case.md)의 소포 인계를 유지하면서 받는 이동형 로봇을
고정 적재 스테이션 `STATION-02`로 교체하는 **가상 비교 범위**다. 보내는 측, 소포 인계,
사람의 인수 확인, 단일 Runtime은 유지한다. 실제 장치 모델·버전·교정·하중·지지 기능·
profile 값은 만들어 넣지 않는다. 고정 설비라고 receiver support 증거나 OPEN-RECEIPT가
자동 해소되지 않는다(S2·S3·S6). 이 범위는 향후 비교할 변화의 정의이며 이번 라벨 수의
입력이 아니다. 결과는 사례 2의 재사용 계수 대신 규범 단독의 선언·판정 지원도다.

따라서 다시 판정할 대상은 **상한 77자리**로 보고한다. 반드시 77번 판단한다거나 모두
새로 개발한다는 뜻이 아니다. 값이 채워진 사례쌍과 명시된 재사용 조건이 있어야 실제
재판정 수를 줄여 셀 수 있다. 이번에 설치·기기 적합성 검사를 실행하지 않았다.
첫 산업 셀의 NOT_COMMISSIONED 상태를 이 문서로 변경하지 않는다.

## 8. 77자리의 declared/free 전수 판정

### 8.1 적용 정의와 인용

- **declared**: 슬롯의 표현·평가·검증 규칙이 고정돼 입력자에게 그 슬롯 자체의 별도
  타당성 판단을 남기지 않는다. 수치의 물리 근거를 규범이 별도 요구하여 이미 분리한
  경우에는 해당 근거 슬롯에서 센다.
- **free**: 무엇을 선언할지 또는 현장 타당성을 사람이 판단해야 한다. typed schema나
  validator가 있어도 그 판단이 남으면 free다. `침묵`은 필요한 형식/판정법이 아래 규범에
  완결돼 있지 않은 경우, `이관`은 규범이 실제 장치·설치·검증 역할의 판단에 넘긴 경우다.
  전자는 모든 기술 체계에 해결법이 없다는 주장이 아니다.
- P36–P42의 기존 분해를 유지한다. P37/P39/P40의 수치 표현·평가는 declared,
  그 수치를 선택한 물리 타당성 근거는 P42 free다. P38/P41은 그 분리를 적용해도
  슬롯 전체의 평가 표현이 닫혀 있지 않아 free다. P33은 completion/cancel 그룹의
  timeout 전략 자리여서 별도 timing 숫자 P40과 합치지 않는다.

시간값의 표현이 고정돼 있어도 검증 의무가 사라지는 것은 아니다.
[공통 03 §8](contracts/v1.0/03_data_and_protocol.md)은 시간값이 없거나 서로 양립하지
않으면 admission을 거부하도록 요구하고, [공통 05 §1 D09](contracts/v1.0/05_decisions.md)는
operation별 expiry 값 검증과 일부 binding의 timing 시험을 요구한다. 그 양립성·현장
적정성 의무는 **P42에서 한 번만 센다.** B1 timing 문장은 observation age의 basis 뒤
세미콜론 다음에 다섯 종류의 `values with supporting evidence`를 묶는다. §1에서 고정한
값/근거 분리는 이 묶음에 적용했고 basis P36에는 적용하지 않았다. 따라서 P37/P39/P40의
declared는 검증을 면제한다는 뜻이 아니라 별도 P42가 검증 판단을 보유한다는 독법이다.
이 독법에 대한 경쟁 해석의 민감도는 §9에 함께 보고한다.

인용 별칭은 원문의 파일과 절을 가리킨다. S2/B1은 §1과 같다.

| 별칭 | 규범 파일·절 |
|---|---|
| S1/S3/S4/S5/S6 | [셀 01](cell_operations/v1.0/01_scope_conditions_functions.md)의 각각 §§1/3/4/5/6 |
| B2/B3/B4/B5/B6 | [공통 04](contracts/v1.0/04_binding_and_admission.md)의 각각 §§2/3/4/5/6 |
| M1 | [공통 01](contracts/v1.0/01_responsibility_and_semantics.md), 표 안에서 절 지정 |
| T2 | [공통 02](contracts/v1.0/02_identity_durability_recovery.md), 표 안에서 절 지정 |
| D3 | [공통 03](contracts/v1.0/03_data_and_protocol.md), 표 안에서 절 지정 |
| C4 | [셀 04](cell_operations/v1.0/04_protocol_integration_ui.md), 표 안에서 절 지정 |
| V7 | [공통 06 §7](contracts/v1.0/06_scenarios_and_validation.md), slash 뒤는 validation ID |

### 8.2 라벨 원자료

RX 열의 `예`는 §9의 하한에 포함한다. `제외`는 부담이 없다는 뜻이 아니다.
규범 문장의 요구는 관측이고, 그 요구에 위 정의를 적용한 라벨은 문서 분석 판단이다.
기계가 계산한 값과 검토자의 의미 판단을 혼동하지 않는다.

| ID | 라벨 | free 사유 종류 | RX 하한 | 규범 인용 | 판정 근거 / 남은 인간 판단 |
|---|---|---|---|---|---|
| S01 | free | 이관 | 제외 | S2 Use; S3 | 사용 목적 enum만으로 실제 시연·운영·teaching 허용 조합을 정할 수 없다. |
| S02 | free | 이관 | 제외 | S2 Use; S3 | 현장의 운영 절차를 설치자가 정해야 한다. |
| S03 | free | 이관 | 제외 | S2 Facility controllers; B4 | 어떤 시설 프로그램이 해당 제어·완료 의미를 구현하는지 확인해야 한다. |
| S04 | free | 이관 | 제외 | S2 Facility controllers; B4 | 통신 설정이 실제 controller와 맞는지 현장에서 확인해야 한다. |
| S05 | free | 이관 | 제외 | S2 Facility controllers; S1; B4 | 신호 이름으로 센서 범위·기계적 의미를 추정할 수 없다. |
| S06 | free | 이관 | 제외 | S2 Facility controllers; B4; V7/V06 | 고장과 재부팅 때 장치에 실제로 남는 효과를 검증해야 한다. |
| S07 | free | 이관 | 제외 | S2 Equipment and goods; S1; B5 | 등록 ID가 실제 설치 장치·Host·자원과 일치하는지 확인해야 한다. |
| S08 | free | 이관 | 제외 | S2 Equipment and goods; B5 | 현장 모델이 선택 profile에 맞는지를 확인해야 한다. |
| S09 | free | 이관 | 제외 | S2 Equipment and goods; B1 identity; B5 | 설치 firmware/controller/driver 조합의 적합성을 확인해야 한다. |
| S10 | free | 이관 | 제외 | S2 Equipment and goods; S3; B5 | 교정값의 실제 도구·설치 적합성을 검증해야 한다. |
| S11 | free | 이관 | 제외 | S2 Equipment and goods; S3 | 좌표계·변환이 설치 기하를 올바르게 나타내는지 확인해야 한다. |
| S12 | free | 이관 | 제외 | S2 Equipment and goods; S3 | 개별 최대 하중의 곱은 실제 하중·자세 조합의 허가가 아니다. |
| S13 | free | 이관 | 제외 | S2 Work; S3; S6 | 순서와 병행이 실제 지지·공간·제어 독립성을 만족하는지 판단해야 한다. |
| S14 | free | 이관 | 제외 | S2 Work; S1 | 공통 역할표가 실제 참여자의 책임 배정을 확정하지 않는다. |
| S15 | free | 이관 | 제외 | S2 People; S3 | 사람의 개입 목적과 위치가 허용 운영 범위에 맞는지 판단해야 한다. |
| S16 | free | 이관 | 제외 | S2 People; S3 | 현장 정비 절차와 필요한 격리·인원 확인을 정해야 한다. |
| S17 | free | 이관 | 제외 | S2 People; S6 | 정확한 release 순서는 site mechanical/process specification에 맡겨져 있다. |
| S18 | free | 이관 | 제외 | S2 People; C4 §§3,6 | 재시작 절차가 해당 잔여 명령·인원·물품 상태에 맞는지 판단해야 한다. |
| S19 | free | 이관 | 제외 | S2 Validation; S3; V7 | 환경별 시험 방법·기간·임계치를 현장 요구에 맞게 정해야 한다. |
| S20 | free | 이관 | 제외 | S2 Validation; S3 | 미결 목록이 실제 미충족 요구를 빠짐없이 담는지 검토해야 한다. |
| S21 | free | 이관 | 제외 | S2 Validation; S3 | 검증 한계가 어떤 운영 제약을 만들어야 하는지 검토해야 한다. |
| P01 | declared | 해당 없음 | 예 | B1 identity; D3 §4 ProfileFinding; D3 §2 Name | RX support_id는 Name 표현 및 profile finding의 식별자로 고정된다. 실제 모델·버전 적합성은 P02–P05와 B5에서 별도로 다룬다. |
| P02 | free | 이관 | 제외 | B1 identity; B5; V7/V04 | 모델·hardware 조합의 허용 여부는 별도 profile 검증을 요구한다. |
| P03 | free | 침묵 | 제외 | B1 identity; B5 | firmware range의 비교 문법·버전 순서·예외 의미가 고정돼 있지 않다. |
| P04 | free | 침묵 | 제외 | B1 identity; B5 | native driver/controller version의 표현과 호환 조합 판정이 고정돼 있지 않다. |
| P05 | free | 침묵 | 제외 | B1 identity; B2 | source commits를 요구하지만 공급 소스·빌드·배포 코드와의 완전한 연결 검사는 주어지지 않는다. |
| P06 | free | 이관 | 제외 | B1 native interface; B4 | 각 native endpoint의 실제 역할을 profile 작성자가 확인해야 한다. |
| P07 | free | 이관 | 제외 | B1 native interface; B3; V7/V04 | 대표 mapping 예시는 해당 장치 API/action/message 선택을 확정하지 않는다. |
| P08 | free | 이관 | 제외 | B1 native interface; D3 §§2–3 | 공통 SI/typed unit 규칙으로 특정 native 값의 실제 단위를 알아낼 수 없다. |
| P09 | free | 이관 | 제외 | B1 native interface; B2; D3 §3 | 배열 순서 보존 규칙이 실제 joint/channel의 올바른 대응 순서를 정하지 않는다. |
| P10 | free | 이관 | 제외 | B1 native interface; B3–4 | return code가 접수인지 완료인지 장치 문서와 실제 경로로 확인해야 한다. |
| P11 | free | 이관 | 제외 | B1 native interface; B4 | native ID와 과거 결과 조회가 실제 제공되는 범위를 확인해야 한다. |
| P12 | free | 침묵 | 제외 | B1 dependencies | 필수 패키지 목록의 완전성과 적합성을 판정할 규범 형식이 없다. |
| P13 | free | 침묵 | 제외 | B1 dependencies | transitive dependency closure를 계산할 규범 규칙이 없다. |
| P14 | free | 이관 | 제외 | B1 dependencies; B5–6 | image variant가 실제 profile·장치 권한과 맞는지 검증해야 한다. |
| P15 | free | 이관 | 제외 | B1 dependencies; B6 | kernel/device/GPU 조건의 실제 성립과 성능 영향을 시험해야 한다. |
| P16 | free | 이관 | 예 | B1 capability; B2–3; D3 §3 | kind/body enum을 파싱해도 native 동작과 완료 의미의 올바른 mapping은 남는다. |
| P17 | free | 이관 | 예 | B1 capability; D3 §3 Observation; C4 §3 | observation schema 이름은 실제 값·단위·범위의 의미를 보장하지 않는다. |
| P18 | free | 이관 | 제외 | B1 capability; B5; M1 §6 | 완료·실패·취소에 어떤 native evidence가 충분한지는 profile 검증 대상이다. |
| P19 | free | 이관 | 제외 | B1 capability; M1 §6; B3–4 | 현재 상태와 과거 결과를 구분하라는 규칙만으로 장치별 두 조회 경로를 정할 수 없다. |
| P20 | free | 이관 | 제외 | B1 resource_set; S6; V7/V05 | 자원 집합의 정렬·CAS는 실제 controller/bus/공간 충돌 단위를 찾아주지 않는다. |
| P21 | free | 이관 | 제외 | B1 startup/shutdown; B2–3; V7/V04 | activate/destructor의 torque·pose 효과는 실제 driver별 조사·시험 대상이다. |
| P22 | free | 이관 | 제외 | B1 startup/shutdown; B2 | launch/init flag의 실제 확장값과 그 효과를 확인해야 한다. |
| P23 | free | 이관 | 제외 | B1 calibration; B5; S3 | calibration ID가 실제 base/tool/fixture/gripper/zero에 맞는지 확인해야 한다. |
| P24 | free | 이관 | 제외 | B1 calibration; S3 | 교정의 공간·하중·도구 적용 범위를 현장 근거로 정해야 한다. |
| P25 | free | 이관 | 제외 | B1 calibration; S6 | 교정이 계속 유효한 조건과 상실 원인을 실제 장치에 맞게 정해야 한다. |
| P26 | free | 이관 | 제외 | B1 mode/authority; B3; B5 | mode 이름만으로 작업에 필요한 실제 상태를 정할 수 없다. |
| P27 | free | 이관 | 제외 | B1 mode/authority; B3; V7/V04 | remote/auto/manual 전환 확인이 실제 권한·상태를 증명하는지 시험해야 한다. |
| P28 | free | 이관 | 제외 | B1 mode/authority; C4 §9; V7/V03 | RX 바깥 native client의 쓰기를 배제하는 방법·효과가 profile에 남는다. |
| P29 | free | 이관 | 제외 | B1 completion/cancel; S4; M1 §6 | 제한 문법의 계산은 고정됐지만 올바른 완료 predicate의 선택은 남는다. |
| P30 | free | 이관 | 제외 | B1 completion/cancel; D3 §3 Correlation; B4 | Correlation 필드를 채워도 native invocation과 실제 결과의 연결을 장치가 보장하는지 확인해야 한다. |
| P31 | free | 이관 | 제외 | B1 completion/cancel; S4; B3 | RANGE 형식은 허용오차의 현장 적정치를 결정하지 않는다. 이 슬롯은 P42로 근거를 분리한 timing 값이 아니다. |
| P32 | free | 이관 | 제외 | B1 completion/cancel; D3 §3 PredicateGoal; M1 §6 | settle_ms 형식만으로 안정화 기간이 물리 완료를 보장하는지 판정하지 못한다. |
| P33 | free | 이관 | 제외 | B1 completion/cancel; T2 §5; V7 | 이 그룹의 timeout은 완료·취소 전략 선택까지 포함하며 숫자 입력으로 분리되지 않았다. |
| P34 | free | 이관 | 제외 | B1 completion/cancel; M1 §6–7; B3 | stop 응답이 실제 정지·지지·잔여 명령 해소를 뜻하는지 확인해야 한다. |
| P35 | free | 이관 | 제외 | B1 completion/cancel; M1 §7; S6 | 일반 RELEASED 조건이 실제 장치의 release 절차·관측을 정하지 않는다. |
| P36 | free | 이관 | 제외 | B1 timing; T2 §5; D3 §3 Observation | age 계산식이 있어도 source/cache 시간의 정확성·acquisition uncertainty 근거는 골라야 한다. |
| P37 | declared | 해당 없음 | 제외 | B1 timing; D3 §§2–3 Grant; T2 §5 | P42로 근거를 분리한 TTL 값 자리다. uint64 ms와 Host monotonic expiry, 갱신/replay/만료 거부 규칙이 고정돼 있다. |
| P38 | free | 침묵 | 제외 | B1 timing; T2 §6; D3 §4 StreamTicket | ticket valid_for_ms는 고정됐지만 함께 묶인 deadman 값의 기산 사건·갱신·만료 비교를 완결한 규칙이 없다. |
| P39 | declared | 해당 없음 | 제외 | B1 timing; D3 §§2–3 Intent; T2 §5 | P42로 근거를 분리한 prepare_validity_ms 값 자리다. PREPARED에서 Host monotonic 기산, 갱신으로 연장 금지, 재부팅 후 복원 금지가 고정돼 있다. |
| P40 | declared | 해당 없음 | 제외 | B1 timing; D3 §§2–3 Intent; T2 §5 | P42로 근거를 분리한 execution_timeout_ms 값 자리다. ms 표현, 실행 시간 만료의 observation/recovery 의미와 clock 복원 불가 시 UNKNOWN 처리가 고정돼 있다. |
| P41 | free | 침묵 | 제외 | B1 timing; T2 §8; D3 §8 | shutdown 순서와 timeout으로 강제 종료하지 말라는 규칙은 있지만 시간 값의 필드·단위·기산/비교 규칙은 완결돼 있지 않다. |
| P42 | free | 이관 | 제외 | B1 timing; V7/V07 | timing 값이 CPU/GPU 부하·단절·지지 반응에 타당하다는 실제 근거를 심사해야 한다. |
| P43 | free | 이관 | 제외 | B1 restart; T2 §7; V7/V04 | 장치 reboot 신호가 실제 boot 연속성을 검출하는 범위를 확인해야 한다. |
| P44 | free | 이관 | 제외 | B1 restart; T2 §7; V7/V04 | native 결과 이력이 재부팅·보존기간 뒤에도 조회되는지 확인해야 한다. |
| P45 | free | 이관 | 제외 | B1 restart; B4; V7/V06 | 어떤 queue/내부 명령이 남아 실행될 수 있는지 실제 controller별 확인이 필요하다. |
| P46 | free | 이관 | 제외 | B1 restart; T2 §7; V7/V08 | 원장과 native 상태를 다시 맞추는 실제 장치 절차가 필요하다. |
| P47 | free | 이관 | 제외 | B1 restart; T2 §7 | silent reboot를 검출하지 못할 때 어떤 상태·결과 주장을 포기할지 경계를 정해야 한다. |
| P48 | free | 이관 | 예 | B1 evidence; D3 §3 Evidence; C4 §3 | schema 이름·digest만으로 증거가 작업 판정에 적합한 의미를 갖는지 알 수 없다. |
| P49 | free | 이관 | 제외 | B1 evidence; M1 §6; S5; C4 §3 | 사람 확인의 허용 범위·권한·관찰 한계를 절차별로 정해야 한다. |
| P50 | free | 이관 | 제외 | B1 evidence; M1 §6; S4 | UNKNOWN/DISPUTED 일반 규칙만으로 두 실제 evidence의 모순 관계를 정하지 못한다. |
| P51 | free | 이관 | 제외 | B1 validation; S3; V7 | 문헌·실험실·현장 findings의 해당 구성 적용 가능성을 검토해야 한다. |
| P52 | free | 이관 | 제외 | B1 validation; C4 §4 RegisterQualification | artifact hash 확인은 시험 진위·권한·범위 심사를 대신하지 않는다. |
| P53 | free | 침묵 | 제외 | B1 validation; D3 §2 UtcTime | 기록용 UTC 형식은 있지만 validation date가 어떤 시험 사건·artifact와 대응하는지 정한 필드·검사는 없다. |
| P54 | free | 침묵 | 제외 | B1 validation; S3 | 검증 versions가 시험 소프트웨어·장치·profile 중 무엇을 어떻게 고정하는지 완결된 기록 schema가 없다. |
| P55 | free | 이관 | 제외 | B1 validation; S3; V7 | 시험 조건이 허가하려는 환경·조합을 포괄하는지 검토해야 한다. |
| P56 | free | 이관 | 제외 | B1 validation; S3; C4 §4 | 시험의 한계를 운영 제약과 재검증 조건으로 옮기는 판단이 남는다. |

고정 목록을 분해·병합·삭제한 자리는 **0개**다. 기존 timing 부모의 근거 분리 1건 외에
추가 분해를 하지 않았다. ticket/deadman처럼 일부만 형식화된 슬롯은 전체를 free로
보존했다. 이 선택은 슬롯 수를 좋게 만들기 위한 재분할을 막는다.

## 9. 세 숫자와 부담 하한

| 지표 | 값 | 해석 |
|---|---:|---|
| declared | 4 | P01, P37, P39, P40 |
| free | 73 | §8의 나머지 전부. 침묵 9, 이관 64 |
| RX 전용 선언 포장 부담 하한 | 4 | P01, P16, P17, P48. 라벨과 별도 축 |
| inherited | 측정 불가 | §7. 재사용 부재의 수치로 대체하지 않음 |
| 재판정 대상의 상한 | 77 | 실제 재판정 횟수의 점추정이 아님 |

**경쟁 독법의 민감도:** 공통 03 §8과 공통 05 D09의 시간 양립성·operation별 검증
의무가 P42뿐 아니라 각 값 자리에도 남는다고 읽으면 P37/P39/P40을 free로 판정하게 되어
**declared 1, free 76**이 된다. RX 포장 하한 4와 분모 77은 같다. 이것은 같은 목록에
다른 귀속 규칙을 적용한 결과다. 주결과는 규범이 명시한 값/별도 근거 분리에 따른 4/73으로
유지하며, 경쟁 독법을 숨기거나 결과에 맞춰 슬롯을 다시 나누지 않는다.

라벨 합은 **4 + 73 = 77**이다. RX 하한의 교차 집계는 declared 1(P01)과
free 3(P16/P17/P48), 합 4다. 이것을 라벨 합에 더해 81로 세지 않는다.

하한에 넣은 이유는 다음과 같다.

| ID | RX가 요구하는 추가 표현 | 근거 |
|---|---|---|
| P01 | RX profile을 식별하고 admission finding에 연결할 support_id | B1 identity, D3 §4 ProfileFinding |
| P16 | native 능력을 RX의 Kind/Body 조합으로 명시하는 표현 | B1 capability, D3 §3 Intent/Body |
| P17 | native 관측을 RX Observation의 value_schema/typed value에 연결하는 표현 | B1 capability, D3 §3 Observation |
| P48 | 근거를 RX Evidence의 evidence_schema와 해석 가능한 내용에 연결하는 표현 | B1 evidence, D3 §3 Evidence, C4 §3 |

이 네 개는 **기존 SI에 전혀 없는 지식 4개**라는 주장이 아니다. 기존 자산이 같은
내용을 갖더라도 RX가 받아들일 식별·의미 포장에 맞춰 선언해야 하는 자리의 수다.
재사용 가능한 변환기가 있으면 실제 작업이 줄 수 있으며 그 공수는 측정하지 않았다.
혼합된 일반 공학 판단(교정·지지·복구), provenance, 중복 기록, time/resource 설정,
전체 77 목록 밖의 자격 관리·유지보수 부담은 추가 부담의 인과관계나 순수 포장 부분을
확정하지 못해 이 하한에서 제외했다. 따라서 **RX 부담을 과소평가하는 방향의 하한**이다.
기존 SI와 동등 작업을 수행한 비교자료가 없으므로 실제 추가 노동의 하한으로 환산할 수 없다.

## 10. free 항목별 다음 작업

각 항목의 **왜 사람이 판단해야 하는가**는 §8 같은 ID의 마지막 열에 적었다.
아래는 그 각각을 **declared로 내리려면 규범에 무엇이 더 있어야 하는가**에 대한 답이다.
추가 규범을 이 문서에서 승인·구현한 것은 아니다. 물리 근거가 필요한 항목은 schema만
추가해도 free가 해소되지 않는다. 검증된 적용 범위와 그 범위의 검사까지 필요하다.

| ID | declared로 내리기 위해 필요한 규범·검증 |
|---|---|
| S01 | 사용 목적별 허용 envelope와 검증된 조합 선택 규칙. |
| S02 | 절차의 typed 단계·전제·종료 조건과 적용 범위를 확인할 검사. |
| S03 | 프로그램 revision과 I/O 의미를 연결한 공급자 근거 및 적합성 검사. |
| S04 | 통신 파라미터 schema와 controller 식별·연결 적합성 검사. |
| S05 | 신호별 source·진리 조건·진단 범위와 물리 검증 근거의 대응 규칙. |
| S06 | 고장·재부팅 상태 전이 모델과 주입 시험별 합격 조건. |
| S07 | 인스턴스와 실물/Host 신원을 연결하고 누락·중복을 검출하는 등록 증거. |
| S08 | 장치가 제공하는 모델 증명과 profile 모델의 검증 가능한 대응표. |
| S09 | 실제 버전 수집·허용 조합 비교 및 변경 영향 검사. |
| S10 | 교정 방법·오차·범위·유효성의 측정 증거와 승인 조건. |
| S11 | 좌표계/변환 schema와 잔차·교정·적용 범위 검사. |
| S12 | 허용 하중·자세·도구 조합별 근거와 envelope 포함 여부 검사. |
| S13 | typed 작업 그래프와 병행/인계 전제, 독립성 증거 검사. |
| S14 | 참여자·권한·책임·인계의 완전성 및 충돌 검사. |
| S15 | 개입 목적·구역·역할별 허용 조건과 접근 검증 근거. |
| S16 | 정비 단계·격리·확인 조건 및 적용 범위의 검증 규칙. |
| S17 | 지지 이전 단계별 전제·관측·실패 반응과 물리 인계 검증. |
| S18 | 재시작 plan의 적용 조건과 잔여 명령·인원·지지 검사 경로. |
| S19 | 시험 환경·조건·합격 기준과 결과의 기계 판독 가능한 연결. |
| S20 | 필수 요구와 증거의 추적표 및 누락 시 자동 open 생성 규칙. |
| S21 | 근거의 제한 조건을 실행 envelope 제한으로 전파하는 규칙. |
| P02 | 제조사/모델/hardware revision 조합과 검증된 지원 범위의 대응 규칙. |
| P03 | firmware range 문법, 비교/제외 규칙과 검증된 허용 집합. |
| P04 | 버전 식별 형식과 지원 조합·불일치의 기계 판정 규칙. |
| P05 | 저장소·commit·빌드 provenance의 필수 schema와 배포 소스 일치 검사. |
| P06 | endpoint별 명령/관측/결과 역할과 공급자 계약의 검증 가능한 매핑. |
| P07 | 버전별 native API signature·동작 의미·RX kind의 적합성 표. |
| P08 | native 필드별 단위·변환·오차와 schema 일치 검사. |
| P09 | native 채널 식별과 RX 배열 위치의 명시적 일대일 대응 및 검증. |
| P10 | 상태 code별 의미·postcondition·실패/불명 전이의 검증된 표. |
| P11 | 조회 능력·보존 조건·identity 상관관계를 검증하는 capability probe. |
| P12 | 버전 고정 dependency manifest와 필수 패키지 해석·검사 규칙. |
| P13 | 의존성 그래프·resolver 의미와 전이 누락/충돌 검사. |
| P14 | variant별 dependency·권한·profile 적용 범위와 검사 결과. |
| P15 | 호스트 조건 schema와 장치 권한·부하·시간 제약별 적합성 검사. |
| P16 | 장치별 kind/body 의미와 native 결과·postcondition의 검증된 연결. |
| P17 | source별 typed observation 의미·범위·신선도와 schema 적합성 검사. |
| P18 | 결과 종류별 필요한 evidence 조합과 상관·유효성·모순 판정 표. |
| P19 | 현재 관측과 역사 조회의 source·ID·보존 범위를 구분한 adapter 계약. |
| P20 | 충돌·독립성·물품 alias 근거에서 자원 집합을 유도하는 검사. |
| P21 | lifecycle 단계별 native 효과와 잔여 결과·지지 조건의 검증 표. |
| P22 | 확장된 flag schema·기본값·부작용과 startup 승인 조건의 검사. |
| P23 | 교정 ID와 대상 구성·측정 기록을 연결하고 잘못된 대상 참조를 거부하는 검사. |
| P24 | 교정 허용 영역과 실제 조합의 포함 여부를 확인할 typed 범위 및 증거. |
| P25 | 유효기간·변경·고장별 무효화 predicate와 진단 검증 근거. |
| P26 | native mode와 작업 전제·postcondition의 검증된 mapping. |
| P27 | 전환 요청·fresh feedback·postcondition과 실패/경합 검사의 연결. |
| P28 | native 권한·격리·외부 쓰기 검출과 배제 검증의 필수 규칙. |
| P29 | 작업 의미·source·검증된 성공 조건에서 predicate를 도출/검사하는 규칙. |
| P30 | native ID/handshake/재시작별 결과 연결 가능성을 확인하는 검사. |
| P31 | 오차 산정·측정 방법과 작업별 검증된 허용 범위 및 비교 규칙. |
| P32 | 안정화의 관측 조건·시간 창·재시작 규칙과 물리 검증 근거. |
| P33 | 각 timeout의 목적·시작점·만료 후 reconciliation 및 장치별 시간 검증. |
| P34 | native stop result와 실제 정지/지지/잔여 효과의 evidence 판정 표. |
| P35 | 잔여 명령 불가·다음 owner 상태·물품 지지의 검증된 release predicate. |
| P36 | freshness_basis별 취득 경로·clock 증명·오차 상한의 검사. |
| P38 | deadman 기간의 단위·기산 사건·재기산/만료 식을 ticket 규칙과 함께 명세. |
| P41 | shutdown duration의 표현·시작/정지 사건·clock·만료 판정식. 강제 종료 허가와 구분 유지. |
| P42 | 시간 측정 환경·오차·부하·반응별 합격 조건과 값/증거 연결 검사. |
| P43 | boot 관측·연결 갱신·silent reboot별 검출 보장과 시험. |
| P44 | retention 조건·소실 사건·결과 조회 범위의 검증된 표. |
| P45 | 잔여 명령 조회·무효화·배제의 근거와 실패 시 UNKNOWN 규칙. |
| P46 | 장치별 resynchronization 단계·identity·잔여 효과 검사의 계약. |
| P47 | 관측 한계의 typed 선언과 연속성 불명 시 제한을 유도하는 규칙. |
| P48 | evidence schema별 의미·source·권한·correlation과 사용 가능 조건의 검사. |
| P49 | attestation별 역할·실제 관찰 범위·유효기간·대체 불가 근거의 typed 정책. |
| P50 | evidence 쌍의 양립/모순·우선 처리와 적용 범위의 기계 판정 규칙. |
| P51 | finding의 조건·대상·주장과 envelope의 연결 및 적용 범위 검사. |
| P52 | 시험 artifact schema와 scope/authenticity/authority/version 검증 절차. |
| P53 | 검증 날짜의 사건 정의, UTC 필드, 원 시험 기록과의 일치 검사. |
| P54 | 검증 대상·도구·구성 버전 필수 필드와 시험 artifact의 일치 검사. |
| P55 | 시험 조건과 envelope 범위의 포함 관계 및 미시험 조합 거부 규칙. |
| P56 | 검증 한계·미결의 typed 표현과 허가 축소·무효화로 이어지는 규칙. |

### 10.1 제품이 명시한 commissioning_inputs와의 대조

[A의 commissioning_inputs와 catalog 설명](https://github.com/jack0682/rx-solutions/blob/b6481ed4ad3de195db7dbadd50e0be29265956cf/catalogs/README.md)은
규범에서 얻은 free 내역의 외부 교차 근거다. 라벨을 이 구현 목록에서 역으로 만들지 않았다.

| 제품 항목 | 직접 겹치는 free 슬롯 | 일치점과 남는 차이 |
|---|---|---|
| native-authority | P26/P27/P28, S14 | 실제 mode·전환·외부 쓰기 배제 판단과 겹친다. 전체 참여자의 현장 책임 범위는 더 넓다. |
| calibration | S10/S11/S12, P23/P24/P25 | 대상·범위·유효 조건이 겹친다. 설치 좌표와 하중 조합은 교정 ID 하나보다 넓다. |
| startup-effects | S06/P21/P22/P41 | 실제 lifecycle 효과와 겹친다. P41은 그 외에 시간 평가 표현의 침묵도 남는다. |
| handover | S13/S17/P20/P34/P35 | 순서·동시 지지 해제·stop/release 판단과 겹친다. 인원 개입·재시작 절차 전체를 대신하지 않는다. |
| completion-evidence | S05/P10/P11/P18/P19/P29/P30/P31/P32/P33/P36/P48/P49/P50 | 실제 결과 의미·상관·유효성·모순이 겹친다. 사람 인수 선언의 권한·범위도 별도다. |

반대로 dependency(P12–P15), firmware/source 표현(P03–P05), 검증 기록(P51–P56),
정비·재시작(S16/S18), 환경별 검증(S19–S21) 등은 다섯 이름만으로 모두 드러나지 않는다.
이 목록은 일대일 분류가 아니며 같은 슬롯이 여러 현장 검증과 연결될 수 있다.
따라서 다섯 이름의 수를 free 수나 사람의 판단 횟수로 사용하지 않는다.

## 11. 한계와 이 측정을 반증하는 관측

이 문서는 현장 시간이 아니라 **규범의 입력 자리와 남은 판단 표면**을 센다.
77개의 입력 주제는 중복 지식을 가질 수 있고, 한 free 항목이 많은 시험을 요구하거나
여러 항목을 한 조사로 해결할 수도 있다. declared 4를 자동화율·절감률로 읽거나 free 73을
사람의 작업시간으로 환산하지 않는다. RX 고유 부담 하한을 빼지 않은 재사용 이익도
주장하지 않는다. 실제 순효과에는 RX 구성·통합·검증·유지보수 비용이 함께 들어가야 한다.

declared도 검사기가 구현됐거나 해당 장치의 검사를 실행했다는 뜻이 아니다. 이번 작업은
규범 읽기, 구성 후보 대조, 표 재계산, 문서/링크·불변 검사만 수행했다. 실행 적합성 시험,
실물 운전·커미셔닝, RX-TAM 학습 실험은 수행하지 않았다. 공통/셀 규범과 manifest·SDK를
수정하지 않았다. free 목록은 후속 범위/과녁 후보이며 학습 모델이 이를 해결한다는 증거가 아니다.

결과를 바꿀 수 있는 관측을 구체적으로 남긴다.

1. **기준선**: 현재 commit의 누락된 선언 묶음에서 실제 값·적용 조건·검증 근거가 연결돼
   있음이 발견되면 §6의 부재 판단과 대응표를 고친다. 미래에 만든 사례는 새 측정으로
   기록한다. 슬롯 대응이 많아지는 것만으로 물리 자격이 생기는 것은 아니다.
2. **라벨**: 침묵으로 적은 9자리의 누락된 규범 형식·평가·검사 경로, 또는 이관 64자리의
   인간 판단을 제거하는 검증된 선택 규칙을 제시하면 해당 free를 다시 판정한다.
   반대로 P01/P37/P39/P40에 다른 슬롯으로 분리되지 않은 타당성 판단이 남음을 보이면
   declared를 free로 바꾼다. 구현 코드만의 관행은 규범 단독 판정을 바로 뒤집지 않는다.
3. **부담**: 네 자리가 RX 전용 의미 포장 요구가 아니거나 다른 자리와 같은 포장임을
   규범으로 보이면 하한을 낮춘다. 추가로 RX가 요구하는 분리 가능한 포장이 확인되면
   높인다. 인시 비교자료가 나오기 전에는 어느 쪽도 실제 추가 공수로 바꾸지 않는다.
4. **단위**: §2가 원문을 중복/오독해 만든 자리를 지적하면 버전을 붙여 재열거하고 기존
   수치와 구분한다. 이번 라벨링 중 목록 수정 필요는 0자리였다. 결과에 맞춘 분모 변경은
   허용하지 않는다.

### 11.1 표에서 재계산하는 방법

문서 원자료만으로 숫자와 ID 누락·중복을 검사할 수 있다. 아래는 저장소 루트에서 실행한다.
표의 의미·인용 타당성은 별도의 원문 검토가 필요하며 이 계산이 대신하지 않는다.

```python
from pathlib import Path
from collections import Counter
import re
text = Path("docs/21_declaration_reuse_measurement.md").read_text()
def section(start, end):
    return text.split(start, 1)[1].split(end, 1)[0]
def rows(part):
    return [[c.strip() for c in line.strip("|").split("|")]
            for line in part.splitlines() if re.match(r"^\| [SP]\d\d \|", line)]
slots = rows(section("## 2. ", "## 3. "))
first = rows(section("## 4. ", "## 5. "))
second = rows(section("### 6.2 ", "## 7. "))
labels = rows(section("### 8.2 ", "## 9. "))
followups = rows(section("## 10. ", "### 10.1 "))
ids = [r[0] for r in slots]
assert len(ids) == len(set(ids)) == 77
for table in (first, second, labels):
    assert [r[0] for r in table] == ids
assert all(r[1] in {"declared", "free"} for r in labels)
counts = Counter(r[1] for r in labels)
assert counts == {"declared": 4, "free": 73}
free_ids = [r[0] for r in labels if r[1] == "free"]
assert [r[0] for r in followups] == free_ids
assert all(r[1] for r in followups)
print("labels", dict(counts), "free_types", dict(Counter(r[2] for r in labels if r[1] == "free")))
sensitive = Counter("free" if r[0] in {"P37", "P39", "P40"} else r[1] for r in labels)
assert sensitive == {"declared": 1, "free": 76}
print("sensitivity", dict(sensitive))
print("RX_lower_bound", sum(r[3] == "예" for r in labels))
print("first_matched", sum(r[1] == "대응" for r in first))
print("second_generous", sum(r[1] == "대응" for r in second))
print("second_strict", sum(r[2] == "대응" for r in second))
print("expanded_strict", sum(r[2] == "대응" or r[4] != "추가 대응 없음" for r in second))
```
