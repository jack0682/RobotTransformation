# 22. N2 판정: 이동형 지지와 사람 인수의 미결 경계

기준일: 2026-09-15 · **문서상 경계 판정. 두 미결은 open이며 실행·물리 자격을 승인하지 않는다.**

[문서 20 §5](20_first_handover_case.md)가 N2에 넘긴 두 질문에 답한다.
**OPEN-MOBILE-SUPPORT는 기존 profile 규범만으로 형식·평가·검증을 완결하기에 불충분하다.**
기존 표현 수단을 바탕으로 실제 장치 입력과 설치 조합·지지 검증을 채워야 한다.
**OPEN-RECEIPT는 기존 Attestation/Evidence에 기록할 수 있는 부분과 아직 정해야 할
수령 자격·위임·유효성·서비스 완료 결합 의미를 구분한다.** 부족한 사례 의미를 곧바로
새 공통 wire 계약의 필수 변경으로 승격하지 않는다.

요구 19개는 **완전매핑 18 / 부분매핑 1 / 매핑불가 0**이다. 부분매핑 R-11에는
서비스 전체 완료 결합 관계의 전용 자리가 없다는 결손이 남는다. 연결된 입력 주제만
33개 슬롯으로 모았으며, 그것으로 이 관계까지 표현됐다고 세지 않는다.
[문서 21](21_declaration_reuse_measurement.md)의 77개 목록과 §§1–11.1은 수정하지 않았다.
재사용 계수 inherited는 계속 **측정 불가**다.

## 1. 판정의 단위와 범위

### 1.1 서로 다른 세 질문

1. **표현 수단이 있는가:** 규범의 필드, artifact 내용 요구, 입력 주제가 있는지 확인한다.
   입력 주제만 이름 붙어 있고 정밀 schema/문법이 미완결인 경우도 그 차이를 적는다.
2. **이 사례의 입력값이 있는가:** N1의 가상 명칭/순서/역할과 실제 설치·검증 값을 구별한다.
3. **그 값의 타당성을 규범만으로 판정할 수 있는가:** 문서 21의 declared/free 라벨을
   그대로 사용한다. free는 표현 수단의 부재가 아니며, 값이 없는 경우와 값을 정한 뒤에도
   site validation/qualification이 필요한 경우를 구별한다.

§4의 충분/불충분은 세 번째 질문의 축이다. 첫 번째 질문에 대한 “기존 표현 수단 있음”은
그 값이 채워졌거나 검사기가 구현됐다는 뜻이 아니다. 표현 자체가 없는 부분은 새 규칙/
형식의 후보지만, 새 서비스 구성과 공통 계약 변경 중 어디에 둘지는 별도 판정이 필요하다.
여기서는 실제 수령 규칙·수치·허용 상태를 만들어 넣지 않는다.

관측된 것은 인용한 규범 문장과 기존 필드다. 요구 분해·매핑·경계 판정은 그 문장에
대한 분석이다. 아래 담당 표기는 필요한 책임 역할이며 실제 담당자가 배정됐다는 뜻은 아니다.

### 1.2 출처와 매핑 규칙

규범과 문서 20/21의 기준은 rx_docs `be5bfcb196f02601ed515de6275ebbba79d62cb4`다.
아래 별칭 뒤의 절 번호는 해당 파일의 절이다.

| 별칭 | 파일·절 |
|---|---|
| S1–S7 / S2 | [셀 01](cell_operations/v1.0/01_scope_conditions_functions.md)의 §§1–7. S2는 §2 Per-installation operating-scope record |
| B1–B6 | [공통 04](contracts/v1.0/04_binding_and_admission.md)의 §§1–6. B1은 BindingProfile의 Required item 표 |
| M1 | [공통 01](contracts/v1.0/01_responsibility_and_semantics.md) |
| D3 | [공통 03](contracts/v1.0/03_data_and_protocol.md) |
| C4 | [셀 04](cell_operations/v1.0/04_protocol_integration_ui.md) |

좌변은 문서 20 §5 마지막 열의 입력 문장을 분리한 요구다. M-01–M-08은
OPEN-MOBILE-SUPPORT, R-01–R-11은 OPEN-RECEIPT다. N2의 판정 의무와 N3의 후속 의무,
“임의 수치/PASS 금지”, “법적 소유권 이전이 아님”은 입력 슬롯으로 세지 않고 이 문서의
제약으로 보존한다. “사례별 입력 카드”는 M 요구와 근거를 모을 산출물 형태다.

- **완전매핑:** 요구의 입력 주제를 고정 슬롯들의 합으로 지목할 수 있다. 값·검증·구현의
  완비를 뜻하지 않는다. 슬롯에 적힌 여러 필수 하위 기록은 B1 원문에 따라 연결한다.
- **부분매핑:** 관련 입력 주제는 지목되지만 요구의 관계/층위 전체를 담는 전용 자리가 없다.
  이유와 남는 관계를 해당 행에 기록한다.
- **매핑불가:** 관련 입력 주제도 고정 목록에서 지목할 수 없다.

관계는 다대다다. 같은 슬롯이 서로 다른 요구에 쓰이는 것은 중복 오류가 아니다.
요구 번호는 유일하고 각 요구 안의 슬롯 ID 및 (요구, 슬롯) 연결은 중복되지 않는다.
§3의 슬롯 목록은 합집합을 한 번씩만 열거한다. 같은 규범 그룹이라는 이유만으로 그 그룹
전체를 자동 포함하지 않는다. 예컨대 신선도 요구를 grant TTL이나 사람의 UTC 시각으로
바꾸지 않고, 절차 revision을 검증 version(P54)으로 바꾸지 않는다.

## 2. 요구별 매핑

각 인용 문구는 문서 20 §5의 입력 요구를 분리한 것이다. 같은 행의 원문 규범 근거가
어떤 입력 주제를 연결하는지 설명한다. R-11의 ID들은 부분매핑된 **구성 입력**이다.

| 요구 | 원문의 입력 요구 | 상태 | 슬롯 ID | 규범 근거와 매핑 이유 |
|---|---|---|---|---|
| M-01 | 실제 장치 | 완전매핑 | S07, S08, P01, P02 | S2 Equipment and goods, B1 identity, B5. 설치 인스턴스·모델과 지원 profile 식별을 구별한다. |
| M-02 | 버전 | 완전매핑 | S09, P03, P04, P05 | S2 Equipment and goods, B1 identity. 설치 버전과 profile의 허용 firmware/driver/controller/source revision을 대조한다. |
| M-03 | 소포/적재함 조합 | 완전매핑 | S12 | S2 Equipment and goods, S3·S6. 이 인계에서 허용할 물품·적재함의 하중/지지 조합이므로 load combinations에 대응한다. |
| M-04 | 인계 구획·도킹·제동 범위 | 완전매핑 | S11, P16, P20, P34 | S3·S6·S7 H03/H06, B2 Mobile robot. 좌표/구역, docking 능력, 공유 공간/제어 자원, 실제 braking/stop 결과를 함께 요구한다. |
| M-05 | 식별·지지·분리 관측의 source | 완전매핑 | P17, P18, P19, P29, P30, P48 | B1 capability/evidence, M1 §3·6, S6. 관측 schema와 결과 evidence·현재/과거 구별·predicate·호출 상관을 통해 어떤 지지/분리 주장을 할 수 있는지 특정한다. |
| M-06 | 관측의 신선도 | 완전매핑 | P36, P42 | B1 timing, M1 §6, S4·S6. 원 취득 age의 basis와 그 경계가 타당하다는 timing evidence를 구별한다. |
| M-07 | 허용 하중·자세·위치 | 완전매핑 | S11, S12 | S2 Equipment and goods, S3·S6. 좌표와 하중/자세/지지 조합의 허용 범위다. 각각의 최대치를 곱해 허가하지 않는다. |
| M-08 | 전원·압력·통신 상실 시 유지/반응 근거 | 완전매핑 | S19, P34, P35, P51, P52, P53, P54, P55, P56 | S3·S6·S7 H03/H06, B1 completion/cancel/validation. 실제 정지/지지·release 조건과 환경별 시험, findings·artifact·date·version·condition·limitation의 근거 묶음에 대응한다. |
| R-01 | RECIPIENT-01 식별 | 완전매핑 | P48, P49 | M1 §6, D3 §3 Attestation, S1·S5. actor를 기록하는 형식과 그 사람이 해당 수령자인지 판정하는 근거를 구별한다. |
| R-02 | 수령 권한 | 완전매핑 | S14, P49 | S1·S2 Work/People, M1 §6. 참여자의 책임과 human-attestation 허용 범위다. 일반 operator 권한이 수령 자격의 확정은 아니다. |
| R-03 | 위임 확인 | 완전매핑 | S14, P49 | S1·S2 Work/People, C4 §3 procedure-assertions의 sources/authority/validity. 권한의 출처·허용 범위를 선언할 자리이며 실제 위임 정책은 미정이다. |
| R-04 | 실제 관찰 범위 | 완전매핑 | P48, P49 | M1 §6, S5, D3 §3 Attestation. scope/value/assertion의 의미와 사람이 실제 관찰한 범위를 연결해야 한다. |
| R-05 | 시각 | 완전매핑 | P49 | M1 §6, D3 §2·3. observed_at은 UtcTime 기록이다. 이 시각을 physical-command validity나 device freshness_basis로 바꾸지 않는다. |
| R-06 | 절차 revision | 완전매핑 | P49 | M1 §6, D3 §3 Attestation.procedure_digest, C4 §3. 내용 주소로 고정한 절차와 그 선언의 허용 범위를 연결한다. |
| R-07 | 유효기간 | 완전매핑 | P49 | B1 evidence, M1 §6, C4 §3 sources/authority/validity. 이 선언을 언제까지 어떤 용도로 인정할지는 typed 인간 절차 정책에 남는다. |
| R-08 | 중복 선언 처리 | 완전매핑 | P49 | B1 permitted human-attestation scope, C4 §3. 같은 업무 선언을 다시 인정할 조건/제한이라는 허용 정책의 구체화다. RPC key 재전송과 업무 중복을 같게 보지 않는다. |
| R-09 | 늦은 선언 처리 | 완전매핑 | P49, P50 | M1 §5·6, B1 evidence. 시각·권한·관찰 범위의 유효성과 기존 evidence와의 양립 여부를 따로 판정한다. 늦었다는 이유만으로 모순은 아니다. |
| R-10 | 소포 불일치 처리 | 완전매핑 | P49, P50 | M1 §6, S4·S6. 인간 선언 scope의 물품 주장과 물리 식별 evidence의 양립/모순을 대조한다. 불명한 물품 alias를 일치로 채우지 않는다. |
| R-11 | 물리 결과와 선언을 이 인계 서비스의 완료로 묶을 규칙 | 부분매핑 | S13, P18, P30, P35, P48, P49, P50 | 부분 이유: S2 Work의 Scope 열에는 final completion conditions가 있으나 77슬롯은 Inputs 열에서 열거됐다. S13은 순서/병행, 나머지는 결합할 입력 주제다. 서비스 전체 완료 결합 관계 자체의 전용 슬롯은 없다. M1 §2·6의 단일 operation completion_rule로 완전대응시키지 않는다. |

| 미결 | 요구 수 | 완전매핑 | 부분매핑 | 매핑불가 | 연결 슬롯 합집합 |
|---|---:|---:|---:|---:|---:|
| OPEN-MOBILE-SUPPORT | 8 | 8 | 0 | 0 | 29 |
| OPEN-RECEIPT | 11 | 10 | 1 | 0 | 8 |
| 전체 | 19 | 18 | 1 | 0 | 33 |

두 미결의 공유 슬롯은 P18, P30, P35, P48이다. 집합 수를 단순 합산하지
않는다. 이 수들은 분석에 쓰인 입력 주제의 범위이며 노동량·자동화율·재사용 수가 아니다.

**부분매핑의 남는 관계:** R-11은 물리 operation 결과와 인수 선언을 같은 인계 서비스의
최종 완료로 인정하는 결합이다. 문서 21 §1은 S2의 **Inputs** 열에서 슬롯을 열거했는데,
이 주제는 S2 Work의 **Scope** 열에 final completion conditions로 있다. 그러므로
서비스 결합 전용 슬롯이 없는 것은 선택한 열거의 해상도 한계다. 규범이 전혀 다루지 않는
새 주제는 아니므로 기존 목록 접근을 폐기할 이유로 쓰지 않는다. 새 슬롯을 추가하지 않고,
관련 입력의 부분매핑과 관계 자체의 결손을 함께 남긴다.

## 3. 연결된 슬롯의 기존 표현과 남은 판단

라벨과 free 유형은 문서 21 §8.2를 그대로 가져왔다. 표현 수단 칸의 “있음”은 요구항목/
기록/확장 지점의 존재를 뜻한다. 형식이 완결되지 않은 자리도 명시했으며 이를 declared로
바꾸지 않았다. N1의 가상 선언으로 실제 설치 값을 채우지 않는다.

| 슬롯 | 라벨 | free 유형 | 기존 표현 수단과 인용 | 이 사례에 남는 입력·판정과 담당 |
|---|---|---|---|---|
| S07 | free | 이관 | 있음: S2 설치 인스턴스, S1 CellDefinition membership. | N1의 IN-01/OUT-01/Host는 가상 사례 명칭이다. 실물과 등록 신원의 연결·누락 검사는 설치/장치 통합 역할의 몫이다. |
| S08 | free | 이관 | 있음: S2 설치 모델, B1 identity와 B5 model 대조. | 실제 모델을 선택하지 않았다. 장치 통합 역할이 모델 증명과 profile 대응을 확보해야 한다. |
| S09 | free | 이관 | 있음: S2 설치 버전과 B5 실제 controller/firmware 대조. | 설치 버전 묶음이 없다. 장치 통합·검증 역할이 허용 조합과 변경 영향을 확인해야 한다. |
| S11 | free | 이관 | 있음: S2 coordinates, S3 positions/zones 및 조합 제약. | BAY-01은 좌표값이 아니다. 설치 역할이 좌표계·변환·도킹 위치를 정하고 교정 오차/적용 범위를 검증해야 한다. |
| S12 | free | 이관 | 있음: S2 load combinations, S3 명시적 variant/range, S6 지지 범위. | 책이 든 소포라는 서술만 있다. 실제 소포/적재함의 하중·자세·지지 조합과 허용 범위는 기계/설치·검증 역할이 정한다. |
| S13 | free | 이관 | 있음: S2 Work의 actual sequence/parallel, S3 recipe/step semantics. 서비스 결합 관계 전용 슬롯은 없음. | N1의 내려놓기·유지·해제·후퇴 순서는 정의됐다. 실제 인계/병행의 타당성은 공정·검증 역할, 서비스 종료 결합 R-11은 업무 설계 역할의 추가 의미다. |
| S14 | free | 이관 | 있음: S1 역할표, S2 Work의 participant responsibilities. | N1은 RECIPIENT-01의 역할을 가정했다. 실제 수령 자격·위임·책임의 완전성/충돌은 업무·운영 절차 책임자가 정해야 한다. |
| S19 | free | 이관 | 있음: S2 validation results, S3 Qualification의 evidence/review. | 해당 장치·조합의 시험 결과는 없다. 검증 역할이 환경·합격 조건·원 결과의 연결을 확보해야 한다. |
| P01 | declared | 해당 없음 | 있음: B1 support_id, D3 §2 Name와 §4 ProfileFinding.support_id. | 실제 support_id는 미선정이다. 선택한 profile 식별자를 정해진 표현에 넣는 자리다. 모델·버전 타당성은 P02–P05와 설치 입력에 남는다. |
| P02 | free | 이관 | 있음: B1 manufacturer/model/hardware_revision 항목, B5 대조. | 실제 제품/하드웨어 조합이 없다. 장치 통합·검증 역할이 지원 범위를 확인해야 한다. |
| P03 | free | 침묵 | 있음: B1 firmware range 요구항목. 정밀 범위 문법·비교 규칙은 미완결. | 장치 통합 역할이 허용 firmware를, profile 형식 책임자가 비교/제외 의미를 정해야 한다. 표현 항목의 존재가 declared를 뜻하지 않는다. |
| P04 | free | 침묵 | 있음: B1 driver/controller versions 요구항목. native 버전/호환 문법은 미완결. | 버전 값과 호환 조합이 없다. 장치 통합과 profile 형식 책임자의 입력·검사가 필요하다. |
| P05 | free | 침묵 | 있음: B1 source commits 요구항목, B2 deployed source commit 의무. provenance 검사 형식은 미완결. | 배포된 binding/driver와 원 소스의 연결이 없다. 빌드/배포·검증 역할이 commit·artifact 일치를 확인해야 한다. |
| P16 | free | 이관 | 있음: B1 provided kinds/bodies, B2 Mobile robot, D3 §3 Kind/Body. | 도킹·제동·유지의 실제 native mapping이 없다. 장치 통합 역할이 접수/물리 완료 의미와 postcondition을 검증해야 한다. |
| P17 | free | 이관 | 있음: B1 observation schemas, D3 §3 Observation, S4 source/quality 규칙. | 식별·지지·분리 source의 schema/의미가 없다. 장치 통합·검증 역할이 센서 범위·단위·유효성을 확인해야 한다. |
| P18 | free | 이관 | 있음: B1 completion/failure/cancel evidence, M1 §3·6, D3 §3 Evidence. | 실제 native 결과와 postcondition 묶음이 없다. 장치 통합·검증 역할이 충분한 evidence를 정해야 한다. 이 결과 하나가 서비스 전체 완료는 아니다. |
| P19 | free | 이관 | 있음: B1 current-state/historical-result 구별, M1 §3·6. | 현재 지지와 과거 특정 호출 결과의 실제 조회 경로가 없다. 장치 통합 역할이 조회 범위·원 identity·보존 한계를 확인해야 한다. |
| P20 | free | 이관 | 있음: B1 conflict units, S6 동일 물품/인계 세대의 support resource. | N1은 논리 자원을 구별했지만 native 충돌/alias 근거는 없다. 제어/공정·검증 역할이 실제 충돌 집합과 지지 독립성을 확인해야 한다. |
| P29 | free | 이관 | 있음: B1 predicates, M1 §6 profile completion_rule, S4 제한 grammar. | 지지·분리라는 목표만 있고 장치 predicate는 없다. 장치 통합·검증 역할이 성공 조건을 정한다. 이 슬롯을 서비스 집계 규칙으로 확장해 읽지 않는다. |
| P30 | free | 이관 | 있음: B1 correlation, D3 §3 Correlation. | 호출/원 결과 연결을 장치가 보장하는지 미확인이다. 장치 통합 역할이 확인한다. 이 표에서 R-11의 P30은 물리 operation 결과의 연결만 맡으며 사람의 scope나 서비스 ID를 native_id로 대신하지 않는다. |
| P34 | free | 이관 | 있음: B1 stop results, M1 §7, B2 mobile braking 조건. | 실제 제동·정지·잔여 효과와 지지가 미검증이다. 장치 통합·기계/검증 역할이 응답 code와 물리 상태의 관계를 확인해야 한다. |
| P35 | free | 이관 | 있음: B1 release conditions, M1 §7, S6 sender release/alternative support. | 실제 release predicate와 전원/압력 상실 조건이 없다. 기계/공정·검증 역할이 잔여 명령·다음 owner 상태·지지를 확인해야 한다. |
| P36 | free | 이관 | 있음: B1 observation-age basis, D3 §3 freshness_basis, M1 §6 취득 age 제한. | 실제 source/cache 취득 경로와 오차 상한이 없다. 장치 통합·시간 검증 역할이 보장 범위를 정해야 한다. 사람의 UTC 관찰 시각과 별개다. |
| P42 | free | 이관 | 있음: B1 timing supporting evidence, S3 qualification. | 원 취득 age/반응 조건을 지지할 측정이 없다. 검증 역할이 조건·오차·시간값과 근거를 연결해야 한다. |
| P48 | free | 이관 | 있음: B1 evidence schemas, D3 §3 Evidence/Attestation. C4 §3은 schema 의미 이해를 요구. | 기계·사람 evidence를 해석할 실제 schema 선택/의미가 미정이다. 장치/profile·업무 절차 책임자가 각각의 source·권한·사용 범위를 정해야 한다. |
| P49 | free | 이관 | 있음: B1 human-attestation scope, M1 §6, D3 §3 Attestation의 6필드, C4 §3 권한/유효성 항목. | N1은 소포·수신자·확인자와 대체 금지 범위를 가정했지만 실제 신원·위임·기간·중복/늦은 선언 정책은 없다. 업무/수령 절차 책임자의 추가 사례 의미와 검증이 필요하다. |
| P50 | free | 이관 | 있음: B1 contradiction decisions, M1 §5·6, S4 충돌 시 UNKNOWN. | 실제 evidence 쌍의 양립/모순 규칙이 없다. profile·업무 절차 책임자가 소포 불일치·늦은 상충 선언의 판정과 원 근거 보존을 정해야 한다. |
| P51 | free | 이관 | 있음: B1 literature/laboratory/site findings, S3 evidence/review. | 해당 조합의 findings가 없다. 장치/현장 검증 역할이 주장과 적용 범위의 일치를 확인해야 한다. |
| P52 | free | 이관 | 있음: B1 actual test artifacts, C4 §4 RegisterQualification의 scope/authenticity/authority/version 검사. | 실제 시험 artifact가 없다. 검증 역할이 원 시험의 진위·권한·대상 범위를 확인해야 한다. |
| P53 | free | 침묵 | 있음: B1 validation dates 요구항목, D3 §2 기록용 UtcTime. 시험 사건과 날짜의 연결 형식은 미완결. | 시험 기록이 없다. 검증 기록 책임자가 어떤 사건의 날짜인지와 원 결과 일치 방법을 정해야 한다. |
| P54 | free | 침묵 | 있음: B1 validation versions 요구항목, S3 dependency hashes. 검증 대상/도구 버전 기록 형식은 미완결. | 검증 version 묶음이 없다. 검증 기록 책임자가 시험 대상·도구·profile 버전과 결과를 연결해야 한다. |
| P55 | free | 이관 | 있음: B1 validation conditions, S3 실제 환경/조합. | 조건별 시험이 없다. 검증 역할이 정상 및 전원·압력·통신 상실 조건의 적용 범위를 확인해야 한다. |
| P56 | free | 이관 | 있음: B1 validation limitations, S3 제약/축소 envelope. | 확인된 시험 한계가 없다. 검증·운영 역할이 미검증 범위와 허가 제한·재검증 조건을 연결해야 한다. |

부분매핑의 연결 입력을 포함한 33자리의 라벨은 declared 1 / free 32
(침묵 5, 이관 27)다. 이는 문서 21의 77자리를 다시 판정한 값이
아니다. R-11의 전용 자리 없는 결합 관계에는 새 declared/free 라벨을 발명하지 않았다.

## 4. OPEN-MOBILE-SUPPORT 판정

**판정: 불충분.** 기존 profile 규범의 형식·평가·검증만으로 이 이동형 receiver의
지지 자격을 결정할 수 없다. 연결된 free 자리의 실제 의미·검증이 남고, profile 외에
설치 조합의 OperatingEnvelope와 Qualification도 요구된다(S3, B5). profile 파일이
설치돼 있거나 이름이 일치한다는 사실로 이 의무를 대체할 수 없다.

불충분한 위치는 다음과 같다. 상세 요구는 §2와 §3의 같은 ID를 따른다.

- **장치 정체성과 버전:** S07/S08/S09, P02–P05. P01의 식별 표현 하나가 정해져 있어도
  실제 장치·소스·허용 조합의 일치를 대신하지 않는다.
- **조합·도킹·제동·인계:** S11/S12, P16/P20/P34/P35. 물품/적재함/자세 조합과 제동·지지
  근거가 필요하다. 동일한 stop 이름이나 개별 최대치의 조합으로 지지를 허가하지 않는다.
- **관측과 완료 근거:** P17/P18/P19/P29/P30/P36/P42/P48. source의 의미·범위·원 취득
  신선도, 실제 호출 결과와 현재 지지의 구분, 충분한 predicate/evidence가 필요하다.
- **상실 시 반응의 검증:** S19, P51–P56 및 P34/P35. 전원·압력·통신 상실 시 어떤 지지가
  남는지를 원 findings/test artifact와 조건·한계로 확인해야 한다.

**기존 표현 수단은 있다.** BindingProfile의 native 의미·evidence 항목, OperatingEnvelope의
조합, MaterialState의 복수 지지, 공통 resource_set과 Qualification을 쓰는 방향이다.
따라서 이 불충분을 “새 공통 계약이 반드시 필요하다”로 읽지 않는다. N2가 남기는 경계는
**profile별 입력 + 설치 조합/검증**이며, 현재 실제 값과 자격 근거는 미제공이다.
S3·S6·S7이 명시한 현장 검증은 profile 숫자를 채우는 일만으로 사라지지 않는다.

N3는 [문서 20 §6](20_first_handover_case.md)의 응답 유실·지지 자원 경합·받는 장치 고장
반례를 이 결손에 연결해 구체화한다. 이 문서는 그 반례를 실행하거나 장치 적합성을
검사하지 않았다. OPEN-MOBILE-SUPPORT와 NOT_COMMISSIONED 상태는 유지된다.

## 5. OPEN-RECEIPT의 기존 구성과 추가 의미

이 미결의 연결 슬롯은 S13/S14/P18/P30/P35/P48/P49/P50이며 라벨은 모두 free다.
같은 free 자리 안에서도 **기존에 기록할 수 있는 것**과 **추가로 정해야 할 의미**는 다르다.

| 범위 | 연결 입력 | 기존 기록·profile·업무 구성으로 되는 부분 | 추가로 정해야 할 사례 의미 |
|---|---|---|---|
| 선언의 기록 | P48/P49 | D3 §3 Attestation의 actor_id, procedure_digest, assertion_id, value, observed_at, scope와 Evidence 식별·schema가 있다. M1 §6은 native result와 인간 선언을 구분한다. | R-01/R-04–R-07: 누가 실제 수령자인지, 무엇을 관찰했다고 인정하는지, 절차의 의미와 유효기간. Name/UTC/digest의 형식만으로 이 판단이 끝나지 않는다. |
| 수령 자격·위임 | S14/P49 | S1의 책임 역할과 S2의 receipt/participant 입력, C4 §3의 authority/validity 요구가 있다. | R-02/R-03: 수령 권한의 출처, 위임 범위와 확인·철회 조건. 공통 operator 권한이 이 소포의 수령 권한은 아니다. |
| 중복·늦은 선언·불일치 | P49/P50 | 원 evidence를 보존하고 scope/유효성·양립/모순을 평가할 profile/절차 지점이 있다. M1 §5·6은 모순을 숨긴 성공 승격을 금한다. | R-08–R-10: 어떤 업무 선언이 중복인지, 늦은 선언을 인정할 범위, 다른 소포 주장과 실제 모순을 구분하는 정책. 정책 자체는 아직 정하지 않았다. |
| 서비스 전체 완료 | S13/P18/P30/P35/P48/P49/P50 (부분매핑) | Run/Activation/Operation의 연결(M1 §2), 물리 결과·human evidence·release 조건, S2 Work의 최종 완료 요구가 있다. | R-11: 같은 인계 건에 유효한 물리·인수 근거를 결합해 서비스 전체가 언제 끝났다고 기록할지. 단일 operation completion_rule로 완전대응되지 않으며 전용77슬롯은 없다. |

세부 경계도 유지한다.

- **ProcedureRecord를 정상 인수 API라고 간주하지 않는다.** C4 §2·4의 이 기록은
  case_id/case_revision과 InterventionCase의 절차에 묶인다. 정상 경로의 receipt를 기록하기
  위해 가짜 개입 case를 만들지 않는다. 기존 정상 인간 선언의 표현 근거는 Attestation이며,
  실제 수령 입력 경로·권한 검증이 구현됐다고 주장하지 않는다.
- D3 §5의 동일 RPC key 재전송 처리는 **업무상 중복 인수 선언의 의미**를 정의하지 않는다.
  서로 다른 요청으로 같은 소포를 재확인하는 상황의 정책은 R-08에 남는다.
- P30의 Correlation은 물리 operation/native result 연결을 맡는다. Attestation.scope에
  이름을 넣는 것만으로 검증된 소포/인계 건 연결을 얻었다고 주장하지 않는다.
- 사람의 observed_at은 기록용 UTC다. 원 장치 표본의 freshness_basis나 native 명령
  유효시간을 대신하지 않는다. 늦은 선언과 상충 선언도 서로 다른 판정이다.

**경계 판정:** 기존 record carrier와 profile/절차의 확장 지점은 사용할 수 있다.
수령 자격·위임·유효성·중복/늦은 선언 처리와 R-11의 서비스 결합은 **추가 사례/업무 의미**다.
특히 R-11에는 서비스 수준의 규칙/형식 후보가 필요하지만, 이 사실만으로 공통 wire 필드나
상태기계의 변경이 필수임을 입증한 것은 아니다. 공통 계약 확장 필요 여부는 기존 확장
지점으로 의미·근거·검증을 보존할 수 없다는 구체 반례가 있을 때 다시 판단한다.
OPEN-RECEIPT는 open이며, 이번 문서는 수령 규칙이나 법적 소유권 이전을 정의하지 않는다.

## 6. 문서 21의 free 필요 조건과 대조

아래 가운데 열은 문서 21 §10의 해당 행을 그대로 인용한 것이다. 오른쪽은 그 조건을 이번
요구에 적용한 범위와 차이다. 모든 연결된 free ID를 한 번씩 포함한다. N2는 그 필요 조건을
충족했다고 선언하지 않으며 새 수치·schema·정책을 승인하지 않는다.

| 슬롯 | 문서 21 §10의 필요 조건 | 이번 적용과 차이 |
|---|---|---|
| S07 | 인스턴스와 실물/Host 신원을 연결하고 누락·중복을 검출하는 등록 증거. | 인용한 필요 조건을 M-01의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| S08 | 장치가 제공하는 모델 증명과 profile 모델의 검증 가능한 대응표. | 인용한 필요 조건을 M-01의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| S09 | 실제 버전 수집·허용 조합 비교 및 변경 영향 검사. | 인용한 필요 조건을 M-02의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| S11 | 좌표계/변환 schema와 잔차·교정·적용 범위 검사. | 인용한 필요 조건을 M-04, M-07의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| S12 | 허용 하중·자세·도구 조합별 근거와 envelope 포함 여부 검사. | 인용한 필요 조건을 M-03, M-07의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| S13 | typed 작업 그래프와 병행/인계 전제, 독립성 증거 검사. | R-11의 서비스 완료 결합은 §10의 작업 그래프/병행 전제에 더해 명명한 관계다. 전용 슬롯 부재를 부분매핑으로 표시하며 실제 규칙을 만들지 않는다. |
| S14 | 참여자·권한·책임·인계의 완전성 및 충돌 검사. | R-02/R-03의 수령/위임 책임으로 구체화한다. 실제 역할 배정은 하지 않는다. |
| S19 | 시험 환경·조건·합격 기준과 결과의 기계 판독 가능한 연결. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P02 | 제조사/모델/hardware revision 조합과 검증된 지원 범위의 대응 규칙. | 인용한 필요 조건을 M-01의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P03 | firmware range 문법, 비교/제외 규칙과 검증된 허용 집합. | 인용한 필요 조건을 M-02의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P04 | 버전 식별 형식과 지원 조합·불일치의 기계 판정 규칙. | 인용한 필요 조건을 M-02의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P05 | 저장소·commit·빌드 provenance의 필수 schema와 배포 소스 일치 검사. | 인용한 필요 조건을 M-02의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P16 | 장치별 kind/body 의미와 native 결과·postcondition의 검증된 연결. | 인용한 필요 조건을 M-04의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P17 | source별 typed observation 의미·범위·신선도와 schema 적합성 검사. | 인용한 필요 조건을 M-05의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P18 | 결과 종류별 필요한 evidence 조합과 상관·유효성·모순 판정 표. | 인용한 필요 조건을 M-05, R-11의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P19 | 현재 관측과 역사 조회의 source·ID·보존 범위를 구분한 adapter 계약. | 인용한 필요 조건을 M-05의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P20 | 충돌·독립성·물품 alias 근거에서 자원 집합을 유도하는 검사. | 인용한 필요 조건을 M-04의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P29 | 작업 의미·source·검증된 성공 조건에서 predicate를 도출/검사하는 규칙. | 인용한 필요 조건을 M-05의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P30 | native ID/handshake/재시작별 결과 연결 가능성을 확인하는 검사. | 인용한 필요 조건을 M-05, R-11의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P34 | native stop result와 실제 정지/지지/잔여 효과의 evidence 판정 표. | 인용한 필요 조건을 M-04, M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P35 | 잔여 명령 불가·다음 owner 상태·물품 지지의 검증된 release predicate. | 인용한 필요 조건을 M-08, R-11의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P36 | freshness_basis별 취득 경로·clock 증명·오차 상한의 검사. | 인용한 필요 조건을 M-06의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P42 | 시간 측정 환경·오차·부하·반응별 합격 조건과 값/증거 연결 검사. | 인용한 필요 조건을 M-06의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P48 | evidence schema별 의미·source·권한·correlation과 사용 가능 조건의 검사. | 인용한 필요 조건을 M-05, R-01, R-04, R-11의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P49 | attestation별 역할·실제 관찰 범위·유효기간·대체 불가 근거의 typed 정책. | R-01–R-09의 수령자 식별·위임·기간·중복/늦은 선언 처리를 구체화한다. §10이 중복/늦은 선언을 별도 열거하지 않으므로 그 두 처리는 허용 범위/유효성의 추가 사례 의미로 명시한다. |
| P50 | evidence 쌍의 양립/모순·우선 처리와 적용 범위의 기계 판정 규칙. | R-09/R-10의 늦은 상충 선언·소포 불일치로 구체화한다. 단순 중복이나 지연 자체를 모순으로 정의하지 않는다. |
| P51 | finding의 조건·대상·주장과 envelope의 연결 및 적용 범위 검사. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P52 | 시험 artifact schema와 scope/authenticity/authority/version 검증 절차. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P53 | 검증 날짜의 사건 정의, UTC 필드, 원 시험 기록과의 일치 검사. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P54 | 검증 대상·도구·구성 버전 필수 필드와 시험 artifact의 일치 검사. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P55 | 시험 조건과 envelope 범위의 포함 관계 및 미시험 조합 거부 규칙. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |
| P56 | 검증 한계·미결의 typed 표현과 허가 축소·무효화로 이어지는 규칙. | 인용한 필요 조건을 M-08의 장치·물품·관측·검증 범위에 적용한다. 새 일반 요구를 추가하지 않는다. |

P49의 업무 중복/지연 정책과 S13 주변의 서비스 결합은 이 사례의 더 구체적인 질문이다.
이를 문서 21의 라벨 변경이나 규범 개정으로 취급하지 않는다. 부분매핑 관계를 숨겨 free
슬롯이 완전하게 덮었다고 주장하지도 않는다.

## 7. N2가 낸 것과 남긴 것

N2는 두 미결의 요구별 매핑, profile 규범만으로는 불충분한 위치, 기존 기록과 추가 업무
의미의 경계를 문서로 판정했다. N1의 두 open 상태, 실제 입력·자격의 부재, 문서 21의
재사용 계수 측정 불가는 그대로다. N3는 반례를 구체화하고, 이후 절차/구현·현장 검증이
값과 근거를 채워야 한다. 이 문서를 그 작업의 완료로 사용하지 않는다.

다음 관측이 나오면 N2 판정을 다시 검토한다.

- R-11의 결합 관계를 실제로 포괄하는 기존 전용 슬롯/규범을 제시하면 부분매핑 판정을
  고친다. 같은 단어의 유사성만으로 operation과 서비스 층위를 합치지 않는다.
- 연결된 free 자리의 타당성 판단을 완결하는 규범과 검증 경로가 발견되면 근거를 기록하고
  문서 21의 별도 개정 여부를 검토한다. 이 문서에서 라벨을 조용히 바꾸지 않는다.
- 문서 20의 요구가 표에서 빠졌거나 잘못 분해됐으면 요구 목록과 연결을 버전 있게 정정한다.
- 기존 profile/업무 확장 지점으로 이 의미를 보존할 수 없다는 반례가 나오면 새 공통 계약
  필요성을 검토한다. 현재 표는 그 필요성이 이미 입증됐다는 주장이 아니다.

관련 원장: [로드맵 N2](00_design_roadmap.md) · [핵심 미결](implementation/critical_open_items.md)
· [N1 두 미결](20_first_handover_case.md) · [고정 77자리와 기존 라벨](21_declaration_reuse_measurement.md).

### 7.1 원자료 재계산

저장소 루트에서 다음 코드를 실행한다. 의미상 적합성은 위 규범 인용을 별도로 검토해야 한다.

```python
from pathlib import Path
from collections import Counter
import re
old = Path("docs/21_declaration_reuse_measurement.md").read_text()
new = Path("docs/22_open_items_boundary.md").read_text()
def part(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]
def rows(text, pattern):
    return [[c.strip() for c in line.strip("|").split("|")]
            for line in text.splitlines() if re.match(pattern, line)]
fixed = {r[0] for r in rows(part(old, "## 2. ", "## 3. "), r"^\| [SP]\d\d \|")}
original = {r[0]: r for r in rows(part(old, "### 8.2 ", "## 9. "), r"^\| [SP]\d\d \|")}
original_needs = {r[0]: r[1] for r in rows(part(old, "## 10. ", "### 10.1 "), r"^\| [SP]\d\d \|")}
requirements = rows(part(new, "## 2. ", "## 3. "), r"^\| [MR]-\d\d \|")
catalog = rows(part(new, "## 3. ", "## 4. "), r"^\| [SP]\d\d \|")
comparison = rows(part(new, "## 6. ", "## 7. "), r"^\| [SP]\d\d \|")
assert len(fixed) == 77
assert len(requirements) == len({r[0] for r in requirements}) == 19
assert {r[0] for r in requirements} == {f"M-{i:02}" for i in range(1, 9)} | {f"R-{i:02}" for i in range(1, 12)}
states = Counter(r[2] for r in requirements)
assert states == {"완전매핑": 18, "부분매핑": 1}
edges = [(r[0], slot) for r in requirements for slot in r[3].split(", ")]
assert len(edges) == len(set(edges))
assert {slot for _, slot in edges} <= fixed
assert all(r[4] for r in requirements)
assert all("부분 이유:" in r[4] for r in requirements if r[2] == "부분매핑")
ids = [r[0] for r in catalog]
assert len(ids) == len(set(ids)) == 33
assert set(ids) == {slot for _, slot in edges}
assert all(r[1:3] == original[r[0]][1:3] for r in catalog)
free = {r[0] for r in catalog if r[1] == "free"}
assert len(comparison) == len({r[0] for r in comparison}) == len(free)
assert {r[0] for r in comparison} == free
assert all(r[1] == original_needs[r[0]] and r[2] for r in comparison)
print("requirements", len(requirements), "mapping", dict(states), "unmapped", states["매핑불가"])
print("unique edges", len(edges), "slots", len(ids), "labels", dict(Counter(r[1] for r in catalog)))
print("free conditions compared", len(comparison), "original labels unchanged", len(original))
```
