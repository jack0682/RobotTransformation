# 0F 레이저 셀의 버전 있는 데이터 모델

2026-10-02. **M1·M2 사용자 수락 완료, M3 구현 중**이다.
게시·운영·RC 완료를 뜻하지 않는다. [WF 요구](../46_workflow_product_experience.md),
[전체 계획](framework_delivery_plan.md), [코어 헌장](../43_core_charter.md), RF 원장은 변경하지 않는다.

## 범위와 단계

M1은 패키지 적용 → Type/Model/Instance 조회 → 상속/덮어쓰기 출처 → 서버의 슬롯 좌표 계산 →
새 모델을 데이터만 추가 → 같은 API 결과의 UI 표시다. 사용자가 직접 실행해 수락한 뒤 M2의
Task 실행값 해석·제약, M3의 Preview·게시·runtime binding·모의 운전/UNKNOWN 복구를 진행한다.
최종 RC의 Linux 재현 45분, 새 품목/트레이 데이터 추가 10분은 아직 측정하지 않았다.

## 현장 근거와 모의 값

Solutions의 `examples/process/laser-heat-treatment/tooling-reference.json`에는 실제 공정의
ECC_51/ECC_99/CVR_F/FLANGE_L/FLANGE_R 명칭, 14/17형 구분과 지그 대응이 있다.
14/17은 식별자이며 mm 치수가 아니다. 치수·중량·힘·TCP·위치는 원본에서 미정이다.
이번 데이터는 ECC_51-14와 ECC_99-14의 명칭/지그 대응을 근거로 삼고, 수치가 필요한 모든 모델과
인스턴스는 **SIMULATION**으로 표시한다. 모의 수치를 실측값으로 승격하지 않는다.

패키지는 Property, 상속 Type, Model, Instance, 품목별 Property Set, 위치 생성 규칙을 제공한다.
트레이의 높이·너비·행·열·피치·깊이·원점·좌표계, 품목의 치수·중량·허용 힘,
척/지그·단일 그리퍼·문·pick/place station의 선언을 데이터로 둔다.
장비 주소나 실제 동작 권한을 부여하지 않는다. 누락값은 누락으로 반환한다.

## 공통 저장과 계산 계약

- 기존 definition-catalog WIP의 카탈로그 ACL, 단일 writer, CAS, 원 요청 복구,
  불변 `catalog/id/revision/digest`, Property→Type→Model→Instance 상속을 재사용한다.
- 속성은 한 번 정의한 Property를 참조한다. 값의 타입·단위·범위와 출처는 서버가 검사하고 반환한다.
  Instance에는 현장 변경값만 저장하며 Model r2 생성으로 기존 r1 참조를 자동 변경하지 않는다.
- CLI 패키지는 순서 있는 정의 목록과 로컬 참조를 갖는다. CLI는 서버가 반환한 정확한 참조를
  후속 요청에 연결할 뿐 상속·좌표·실행값을 계산하지 않는다. 각 저장은 기존 원 요청/CAS 경로다.
  전체 패키지가 단일 transaction이라는 주장은 하지 않는다. 중단 시 적용된 정의와 미적용 정의를
  구분하고 동일 요청으로 이어간다. 이 단계의 패키지 적용은 저작 자료의 적용이며 실행 패키지 게시가 아니다.
- M1의 위치 생성은 버전 있는 **유한 Cartesian point pattern** 규칙이다. 규칙 데이터가 대상
  Resource Type, 원점·자세·좌표계 필드, 축별 개수·피치 필드와 로컬 방향을 지정한다.
  서버는 `원점 + R(q) × Σ(축 index × pitch × direction)`을 계산한다.
  q는 명시된 unitless 단위 quaternion `[x,y,z,w]`이며 출력 자세에도 보존한다.
  자세가 누락되거나 단위 quaternion이 아니면 오류이며 identity 회전을 추정하지 않는다. 마지막 축이 가장 빠르게 변한다.
  트레이/품목 이름·특정 행열 수·실측값은 알고리즘에 넣지 않는다.
- 원점/피치는 명시된 동일 길이 단위, 축 개수는 양의 정수/unitless, 방향은 단위 벡터를 요구한다.
  누락·단위 불일치·유한성·타입 불일치·과대 개수는 위치를 포함한 오류다. 좌표계를 추정하지 않는다.
  최대 100,000점, 페이지 최대 100점으로 제한하고 정확한 대상/규칙 revision을 페이지마다 고정한다.
- 결과는 대상·규칙 참조, 입력값과 출처, 총 개수, 각 index/축 index/좌표·단위·좌표계 및
  위치 있는 오류를 반환한다. UI는 이 서버 응답을 표시하며 자체 좌표 계산이나 별도 정의 저장소를 두지 않는다.

기존 process-source.v1·실행 wire·원장/인계 의미를 변경하지 않는다. 신규 저작 API와 정의 종류는
현재 미통합 WIP를 기반으로 추가하며 구버전 소비자에게 기존 형식을 다른 의미로 반환하지 않는다.
기존 계약 파괴가 필요해지면 v1.1 영향과 권고를 먼저 사용자에게 보고한다.

## 구현 책임과 검증

Docs는 이 모델과 범위, Platform은 범용 정의/패턴·서버 검사/조회, Solutions는 생성 SDK·기존 `rx`
CLI 클라이언트·셀 패키지·기존 Definitions 화면을 맡는다. 시나리오 전용 코어 코드 0줄을 유지한다.
별도 definition-catalog WIP는 재사용하되 R7·재자격 WIP는 흡수하지 않는다.

M1 검증은 다음을 실행한 근거로만 갱신한다: 모델/인스턴스 상속·덮어쓰기/버전 고정, 새 모델의 데이터
적용, 고밀도 슬롯 전체 페이지/경계, 타입/단위/누락/상한 오류, 권한 격리, 응답 유실 후 원 요청
복구, CLI와 UI의 같은 서버 결과, 서버 재시작 뒤 재조회. 먼저 API·CLI를 구현·검증하고 UI를 연결한다.
사용자가 실행할 정확한 명령과 UI 순서는 검증 후 이 문서에 기록한다.

현재 제품 실행·사용자 수락은 미완이며 코어 변경량/패키지 작성량·설치 시간은 최종 소스로 측정한다.

## M1 첫 구현 체크포인트

2026-10-01. 기존 definition-catalog 브랜치에서 범용 PointPattern 정의·입력 검사·출처를 포함한
페이지 조회 API를 추가했다. 기존 `rx`에 definitions apply/show/points를 연결하고 셀의 모의 정의
54개와 새 트레이 모델 데이터 예시를 작성했다. 이 변경은 아직 코드 PR 통합 전이었다.

API crate의 all-targets check와 개발 API binary build는 통과했다. 카탈로그 대상 시험 7개가
통과했으며, 추가 시험은 고밀도 모델 2,400점의 전체 페이지·마지막 좌표, 상속/덮어쓰기 출처,
새 모델 15점 생성, 과거 revision 보존, 누락·비정수 개수·단위·digest·페이지 범위·카탈로그 격리를
대조했다. 전체 workspace·Linux 설치·UI·Preview·운영 근거는 아니다.

실제 CLI 적용은 개발 API 로그인에서 HTTP 403으로 두 번 거절됐다. 패키지 저장 전에 실패했고,
사용자의 동일 문제 두 번 중단 조건에 따라 인계한다. 서버 Host 정책과 CLI의 transport/public-origin
구성이 어긋난 것으로 정적 분석했다. urllib는 unredirected header를 우선하므로 뒤늦은 일반 Host
header 지정이 이를 교체하지 못한다. 이 시점에는 수정 후 실행을 하지 않았다.
다음 한 단계는 서버 정책을 유지한 채 CLI 개발 transport를 수정·검증하는 것이다.
M1 사용자 실행 준비·SDK 동기화·UI 연결·사용자 수락은 계속 미완이다.


## M1 API·CLI·UI 사전 검증

동일한 2026-10-01 후속 작업에서 Host 헤더 문제를 수정했다. 공개 host/origin과 실제 연결 주소를
구분하며 서버 ingress 정책과 TLS Terminal 경계를 유지한다. urllib의 실제 header 우선순위를
재현하는 테스트와 새 API 설치의 실제 요청이 통과했다.

- Platform 소스: `aee48699acd879c8f6bf84dd38c994909a7d7d66`.
- Solutions 소스: `dca80d659f5b2fa036fa3eb49ea3d23cafa18a8e`.
- [셀 패키지와 CLI 순서](https://github.com/jack0682/rx-solutions/blob/dca80d659f5b2fa036fa3eb49ea3d23cafa18a8e/examples/definitions/0f-laser-simulation/README.md).
- [API 실행 검증 결과](../../references/cell_model_m1_2026-10-01/api-acceptance.json).
- [CLI와 UI의 동일 revision·행 대조](../../references/cell_model_m1_2026-10-01/ui-cli-match.json).

셀 패키지는 58개 정의이며 0F 품목 ECC_51-14/ECC_99-14, 일반/고밀도 트레이,
척, PART1/14 지그, 단일 그리퍼, 문, pick/place station과 품목별 Property Set을 제공한다.
Task 실행값 해석과 장비 운전은 포함하지 않았다. 일반 트레이 24점, 고밀도 2,400점,
별도 JSON으로 추가한 새 모델 15점을 같은 서버 규칙으로 생성했다.

실제 새 SQLite/API 프로세스에서 전체 데이터 적용·같은 요청 재적용·상속과 덮어쓰기 출처,
고밀도 전 페이지·회전된 모델·잘못된 quaternion 거절·digest 변조 거절을 확인했다.
실제 서버 commit 뒤 클라이언트에 응답 유실을 주입하고 동일 요청으로 revision 하나를 복구했다.
서버 프로세스를 종료·재시작한 뒤 같은 pinned pose report가 바이트 의미상 일치했다.
장비/executor 결함 주입과 UNKNOWN 복구(M3)는 아직 수행하지 않았다.

기존 Definitions 화면에서 CLI 자료를 열고 별도 검증용 인스턴스의 원점과 높이를 수정·저장했다.
서버가 만든 r2의 24개 좌표를 CLI 응답과 전부 대조했고, 좌표계·quaternion·주체/규칙 revision이
일치했다. UI는 API 결과를 표시하며 자체 좌표 계산을 추가하지 않았다.

현재 로컬 검사: P 전체 workspace 541 passed / 0 failed / 19 ignored 및 Clippy 통과;
S UI 68시험·번들 3시험·타입/format/build 통과; 정의 CLI 4시험·기존 runtime CLI 8시험 통과;
생성 SDK 133파일 원본 일치와 저장소/계약/불변식 참조/경계 검사를 확인했다.
19개 제외 시험, Linux CI 결과, 최종 RC 설치와 사용자 수락을 이 로컬 결과로 대신하지 않는다.

공통 코어에 추가한 것은 카탈로그 ACL·불변 정의/참조 저장·타입 상속/값 출처·유한 Cartesian pose
규칙과 조회다. 트레이·척·품목 이름/치수/작업 순서에 따른 분기는 없으며 셀 자료는 S 패키지에 둔다.
기존 Definitions WIP를 재사용했고 이번 작업에서 새 시각 디자인·CSS 개선을 하지 않았다.
WF/RF 장기 항목은 완료로 표시하지 않는다. 사용자 M1 수락 전 M2를 시작하지 않는다.

## M1 사용자 수락과 M2 전 보완

2026-10-01 사용자가 M1 정상 동작을 직접 확인했다. 사용자 보고는 CLI apply 재적용의
idempotence, supply 24 / dense 2400 / my-tray 20, UI Calculate points와의 결과 일치다.
이는 M1 수락이며 M2/M3·최종 RC 수락을 뜻하지 않는다.

사용자는 다음 세 항목을 M2 전 검토 대상으로 지정했다.

1. **높이의 의미.** 현 PointPattern은 `origin + R(q) × offset`만 사용하며 legacy
   `surface_height`는 계산 입력이 아니다. 기본 모델의 origin.z=0 / surface_height=900은
   두 값의 관계가 정의되지 않은 공백을 보여준다. M2의 새 해석에서는 슬롯 기준면 pose를
   위치의 원본으로 삼고 슬롯별 표면 위치를 여기서 파생한다. 독립 측정 높이가 필요하면
   동일 frame/unit과 허용 오차를 명시한 제약으로 대조한다. 기울어진 트레이에서 모든 슬롯에
   동일한 world-z를 강제하지 않는다. 부품 높이·깊이·접근 여유를 적용할 기준점과 로컬 방향도
   Task 계약으로 명시해야 한다. 기존 M1 저장본·규칙·출력은 소급 변경하지 않는다.
2. **읽을 수 있는 출처.** UI는 UUID 대신 정확한 참조 revision의 label과 revision을 표시하고
   원 UUID/catalog/digest는 세부정보로 보존한다. 최신 label을 과거 참조의 이름으로 사용하지 않는다.
   key는 현재 CLI 패키지의 별칭이므로 서버의 전역 식별자로 가장하지 않는다. CLI는 선택적
   `--format text`에서 alias/label과 출처를 표시하며 기본 JSON과 원 참조는 유지한다.
3. **생성 충돌 진단.** expected=null은 create-only이며 기존 ID에 대한 새 요청은 거절해야 한다.
   STALE_REVISION 뒤 동일 권한의 현재 조회로 존재/현재 revision을 확인하여 원인을 보충한다.
   이 조회는 거절 당시의 원자적 snapshot이 아니므로 'current read'로 표시한다. 조회를 못 하면
   원래 오류를 유지하며 원인을 추정하지 않는다. 자동 upsert·expected 교체·재시도를 하지 않는다.
   원 응답이 불명인 요청의 복구 의미와 동일 요청 idempotence도 유지한다.

②③은 기존 API의 클라이언트 표시·진단 보완이다. 공개 응답 형태, 코어/SDK, 기존 저장본의 의미를
변경하지 않는다. ①의 실제 파생 계산·정합 제약은 M2 구현에 남으며 문서 결정만으로 완료 처리하지 않는다.

## M2 구현 경계 — 버전 있는 Workflow 모델과 해석 보고서

2026-10-02, 로컬 사전 검증 완료·통합 중. 기존 M1 Definition/PointPattern JSON과 API는 그대로 유지한다.
M2는 같은 카탈로그 권한·writer 위에 별도의 versioned Workflow 모델을 추가한다. 기존 Task
선언을 실행 계약으로 소급 해석하지 않는다. 새 모델은 명시적인 schema로 Task 계약·규칙·제약과
순서 있는 node→Task 참조를 저장한다. 각 member의 신원은 Workflow의 정확한 revision/digest와
member ID로 고정한다. 다른 규칙을 수정해도 기존 Workflow revision의 member는 변하지 않는다.

- Task 계약: 사용 context 슬롯/허용 type/단일·다중, Property Registry 참조와 순서 있는 source
  chain, required capability, Skill→primitive/parameter mapping, timeout 속성, done 관측 계약,
  알려진 실패의 stop과 UNKNOWN의 hold/reconcile 정책. 지원·완료 관측은 선언이며 실제 권한이 아니다.
- 규칙: 이름 있는 유한 DAG. field/property/rule lookup, 같은 단위의 덧셈·뺄셈·min/max,
  unitless 배율, vector 성분, 명시된 quaternion을 따르는 pose offset만 지원한다.
  임의 스크립트·네트워크·시간·수식 문자열 평가는 없다. cycle·복잡도 초과는 오류다.
- 값: 단위와 scalar/vector/text/bool을 구별한다. 수치 구간은 min/max를 유지하고 제약은
  가장 불리한 조합으로 검사한다. 제공된 잘못된 Override/입력을 낮은 우선순위 값으로 덮지 않는다.
- 출처: 선택된 source tier, 정확한 정의/Workflow/member 참조, 사용한 입력과 규칙을 보존한다.
  제약은 Override 선택 이후 검사하고 node/property 위치와 이유를 반환한다.
- 슬롯 위치·표면 z는 M1의 full pose에서 얻는다. 접근은 선언한 로컬 방향과 part/clearance로
  계산하고 그 결과의 z를 읽는다. legacy surface_height를 추가 offset이나 실행값 원본으로 쓰지 않는다.
- M2 해석 요청은 선택한 part/model·resource·property set·Override·실행 입력과 slot index를
  고정한다. 한 부품의 모든 node 값을 해석한다. N개 부품의 순서·runtime binding·실행은 M3에서
  각 부품의 동일한 해석 경로와 원 보고서 참조로 연결한다.

새 `/api/v1/workflow-models`, `/api/v1/workflow-model`은 원 요청/CAS/불변 revision으로 모델을
저장·조회한다. `/api/v1/workflow-resolutions`는 권한을 확인한 정확한 자료로 계산하고 immutable
보고서를 저장하며, `/api/v1/workflow-resolution`은 같은 보고서를 조회한다. 새 자료는 별도 record
schema/index를 사용하여 M1 목록·decoder에 새 enum/필드를 섞지 않는다. 카탈로그 권한·원장·DB를
따로 만들지 않는다. 모든 CLI/UI는 이 API를 사용한다. M2 사전 검증 근거는 아래에 제한하며 사용자 수락을 대신하지 않는다.

## M2 데이터와 사전 검증

M1 58개 정의를 보존하고 M2 정의 46개를 추가했다. Workflow 데이터는 Task 8개, 규칙 23개,
제약 23개이며 pick→load→clamp→close-door→process→open-door→unload→place를 선언한다.
타입·속성·품목·트레이·지그·그리퍼·기계 이름과 수치는 Solutions 패키지에만 있다. Platform은
자료 조회·단위/타입/frame 검사·유한 규칙 해석·구간 제약·권한/불변 보고서 저장만 제공한다.
레이저 전용 코어 분기는 추가하지 않았다. 기존 Normative v1.1 계약의 의미·해시는 변경하지 않았다.

### 슬롯 높이와 접촉 기준

새 M2 트레이 Type은 legacy surface_height를 포함하지 않는다. Model은 TRAY_LOCAL의 슬롯
입구 원점 [0,0,0]과 형상을, Instance는 world frame·origin·orientation을 함께 선언한다.
슬롯 입구 pose를 위치 원본으로 삼으며 z는 파생 성분이다. 지그 표면은 지그 원점에서 명시한
로컬 법선 방향으로 지그 높이만큼 이동한다. 별도 독립 높이 측정값은 이번 데이터에 없다.

접촉 위치는 모의 부품 중심을 datum으로 하여 `입구 + 법선 × (부품 높이/2 - 안착 깊이)`,
접근 위치는 `입구 + 법선 × (부품 높이 - 안착 깊이 + clearance)`다. 실측 TCP·기하 적합성·충돌
검증을 뜻하지 않는다. 힘/폭/질량·피치·트레이/지그 크기·안착 깊이·planning frame·동작 시간·지그
family 제약은 Override 적용 후 평가한다. 범위 연산은 외향 반올림하고 독립 최악 조합으로 검사한다.

### 실행한 반례와 경계

- ECC_51-14 / ECC_99-14의 pick 폭 47/77 mm, 힘 25/17.5 N, 접근 z 795/825 mm와 load
  접근 z 885/915 mm를 독립 기대값과 대조했다. open-door의 false와 수치 0을 누락으로 바꾸지 않는다.
- dense tray, 힘 60 N/0 N, 폭 70..130 mm, 잘못된 힘 단위 kg, 상충 Property Set를 위치와
  함께 차단했다. 폭 100 mm Override가 그리퍼 최대폭 검사만 통과했던 반례를 발견하고 **패키지
  제약**에 슬롯 pitch 검사를 추가했다. 코어에 트레이 전용 조건을 넣지 않았다.
- 안전 구간 20..40 N도 concrete=false / BOUNDED_INPUT_NOT_EXECUTABLE로 보존한다.
  값이 모두 고정되고 제약을 통과해도 RESOLVED_NOT_QUALIFIED다. 게시·운전 권한이 아니다.
- 세 번째 Object Type/Model과 회전한 트레이 Model/Instance를 데이터로만 추가하고 같은
  Workflow revision/rules로 재해석했다. 개발자의 실제 10분 측정과 실행 증거는 아직 없다.
- 실제 임시 SQLite/API 서버에서 커밋 후 응답 유실·원 요청 복구·프로세스 재시작·저장 보고서
  재조회/목록을 확인했다. 해석 중 권한 철회, 잘못된 digest·타 catalog 참조는 별도 시험으로 거절했다.
  이 응답 유실은 저작 API 시험이며 장비 UNKNOWN/자원 보유/운전자 복구 시험이 아니다.
- UI는 CLI가 저장한 같은 보고서를 재열어 8개 노드의 101개 값·단위·선택 source를 대조했다.
  정의/규칙의 pinned 이름과 입력 출처, 위반 클릭의 node 이동을 확인했다. report 목록은 서로
  구분되는 전체 ID를 표시한다. UI 계산 경로는 없다.

Platform 전체 workspace 시험·Clippy, SDK 137개 파일의 원본 일치, CLI 요청 복구 6개 시험,
UI 77개 시험·typecheck/build와 실제 API 회귀가 통과했다. PR의 정확한 head CI와 통합 상태는
병합 결과로 따로 기록한다. 사용자 M2 수락, Preview/게시/actual-part runtime binding/모의
운전·UNKNOWN 복구, 최종 RC와 Linux 45분 재현은 미완이다. 기존 RF/WF 완료 판정은 올리지 않는다.

## M2 사용자 CLI 확인과 인계 보완 — 2026-10-02

사용자는 A/B 값·상태, dense/60 N/100 mm/kg의 BLOCKED(rc=2), 20..40 N의 구간 상태,
report와 resolve 출력 일치, 기존 출력 파일 보호를 직접 확인했다. UI는 인계용 M1/M2 리스너
네 개가 종료되어 확인하지 못했다. crash 로그 없이 함께 종료된 현상은 exec 수명 연동이
의심되지만 원인으로 확정하지 않는다. 따라서 M2 전체 수락과 M3 시작 조건은 아직 미충족이다.

CLI 출력 보호의 시점을 보완했다. `resolve --output` 대상이 이미 있으면 로그인·조회·해석 요청
전에 rc=1로 거절하고 출력 경로 충돌임을 설명한다. 서버에 보고서를 만든 뒤 파일 충돌을 알리는
기존 동작과 구별된다. 요청 이후 발생하는 별도 I/O 실패는 원 요청 journal로 복구한다.
유효한 고정값은 rc=0, BLOCKED는 rc=2, BOUNDED_INPUT_NOT_EXECUTABLE은 rc=3으로 구별한다.
report/recover도 같은 상태 코드를 사용한다. text는 고정값·구간을 읽기 쉽게 표시하고, 한 속성의
동일 provenance만 중복 표시하지 않는다. 저장 JSON·규칙·계산 결과는 변경하지 않는다.

macOS 개발 인계 서비스는 사용자 launchd domain에서 실행하여 터미널/exec 수명과 분리했다.
기존 DB를 재사용하고 네 프로세스의 parent PID=1·HTTP 응답을 확인했다. 로컬 RUN_M2에는
정확한 시작·상태·종료 명령과 로그 위치를 기록한다. 로그인 시 자동 시작·물리 장비 연결은 없으며
로그아웃/재부팅 후 다시 시작해야 한다. 이는 최종 Linux RC 설치 방식에 대한 증거가 아니다.

출력 경로의 일반 파일·디렉터리·dangling symlink를 접속 전에 거절하는 시험과 text 보존 시험을
포함해 workflow CLI 8개 시험이 통과했다. 실제 임시 API/CLI 시험에서 기존 출력 충돌 전후의
서버 보고서 목록이 동일했고, concrete/blocked/bounded 종료 코드 0/2/3 및 구간 보고서 재조회가
일치했다. 사용자 UI의 보고서 선택·위반 이동·새로고침 재열기는 재확인 대기다.


## M2 수락과 M3 첫 연결 — 2026-10-02

사용자가 M2 전체를 명시적으로 수락했다. CLI receipt ID의 A/B 보고서 선택과 값 일치,
Sources and rules의 label/revision/member 경로, 60 N 위반에서 다른 node 선택 후 pick 이동,
새로고침 후 같은 보고서 재열기와 CLI 수정 세 건을 직접 확인했다. M2 수락 조건은 충족됐으며
다시 수락을 요청하지 않는다. 이는 M3나 최종 RC 수락을 뜻하지 않는다.

비차단 UI 보완은 위반 property 행의 focus·스크롤·강조, worst-case 양변의 값/단위 표시,
보고서 목록의 context·Override·생성 시각이다. 기존 목록 응답을 바꾸지 않고 명시적
`view=details` 읽기 projection을 추가했다. 정확한 저장 Workflow defaults와 요청 context를
결합하고 보고서에 고정된 이름을 표시한다. created_at은 monotonic clock이므로 달력 시각으로
변환하지 않는다. 서버가 생성한 UUIDv7의 시각을 'record ID clock'으로 표시하고 원 clock/ticks를
보존한다. 과거 보고서와 기본 CLI JSON은 소급 수정하지 않는다.

M3 첫 연결은 Solutions의 기존 rx-process 컴파일러에 저장 해석 보고서를 입력하는 경로다.
정확한 보고서 reference/digest·slot·node·Skill parameter mapping으로 content-addressed
parameter artifact를 만들고, 기존 ProcessSource→ResolvedProcess→BT XML 경로를 사용한다.
패키지 template이 host·program·resource set·단위/frame·timeout 상한을 제공한다. 보고서의
실행값은 새로 계산하지 않는다. 현재 compiler profile은 Task당 Skill 한 개만 지원하며 다른
구조를 조용히 평탄화하지 않는다. 결과는 **COMPILED_NOT_QUALIFIED**다.

컴파일 입력과 template은 신뢰되지 않은 저작 자료다. report digest 일치만으로 서버 발행이나
운전 허가가 증명되지 않는다. 실제 게시 경로에서는 저장 보고서 재조회와 package 검증이 필요하다.
현재 개발 시험의 program/profile은 test fixture이며 실행 가능한 장비 구현이 아니다.
독립적인 A/B 기대값(폭 47/77 mm, 힘 25/17.5 N)과 8개 node의 parameter 파일 hash/size,
원 report/slot 연결을 실제 컴파일 명령으로 확인했다. 원본 참조 위조, 범위값, unit/frame 불일치,
누락 매핑, timeout 상한 초과를 거절하는 시험이 있다.

아직 구현되지 않은 M3 부분은 같은 compiled version의 모의 Preview 실행·게시,
실제 품목 입력 시 재해석/제약 검사, N개 실행과 장비 무응답 UNKNOWN/자원 보유/정산/다음 품목,
Linux RC와 최종 사람의 45분/10분 재현이다. 기존 runtime CLI는 BOUND_CONFIGURATION이고
Host 입력은 고정된 parameter artifact에 연결되므로 이 경계를 실제로 연결해야 한다.
LOCAL_SIM Python 순차 실행이나 UI의 예시 trace로 이를 대체하지 않는다.

## M3 값 소비 모의 장비 — 구현 중

기존 FILE_SIMULATION 기본 장치는 Intent 내용을 사용하지 않고 완료 capture를 기록한다.
따라서 그것만으로는 해석된 좌표·힘·시간이 장비에 쓰였다고 할 수 없다. 새 0F 모의 장비 프로그램은
기존 Host Python 실행기 뒤에서 `rx.workflow-parameters.v1`을 소비하고 독립 상태/효과 파일을
갱신한다. 공정 순서는 P/Executor의 책임으로 유지하며 별도 Workflow 실행기를 만들지 않는다.

공통 추가는 한 Host의 단일 지원/불명 상태 관리 아래 여러 고정 Python 입력을 선택하는 기능이다.
새 `rx.python-skill-library.v1`과 `PYTHON_SKILL_LIBRARY_PACKAGE`를 사용하고 기존 단일 프로그램
형식은 바꾸지 않는다. 한 서명된 DEVICE_REFERENCE 패키지의 모든 프로그램·입력·원본·operation
선언을 재조립/대조한다. 라이브러리는 한 environment의 고정 프로그램 최대 16개, 입력당 64 KiB로
제한한다. 바뀐 입력·서명만 유효한 불일치 선언·미승인 Intent는 거절한다. 한 프로그램이 불명이면
다른 프로그램의 자원 인계도 막는다. 물리 환경은 지원하지 않는다.

시나리오 코드는 Solutions의 `examples/process/laser-heat-treatment/simulation/`에 둔다.
입력 pose/force/width로 모의 상태를 바꾸고, clamp의 명시적 release_gripper와 door/process
순서를 검사하며 process duration을 실제로 기다린다. 상태 파일은 Host journal과 분리된다.
정규화된 quaternion·단위/frame·고정값·상태 전이를 검사하지만 실제 충돌/접촉/열전달이나
기능 안전을 모델링한 것은 아니다. 이미 소비된 슬롯을 반복 사용하지 않는다.

Host prepare/authorize와 실제 Python 프로세스를 사용한 시험에서 A/B 각각 8개 효과와
폭 47/77 mm, 힘 25/17.5 N, contact z 760/767.5 mm, clamp/door/holding 전이 및 5/7초
대기를 대조했다. prepare는 장비 효과를 만들지 않았고 원 요청 재조회도 효과를 추가하지 않았다.
다른 입력을 선택하는 라이브러리 시험과 타임아웃 후 공유 자원 인계 거절 시험도 통과했다.
이는 직접 Host 시험이며 P 등록·mTLS·Executor까지 포함한 전체 경로 시험을 대체하지 않는다.

P/Executor 연결, 실제 품목 바인딩과 N개 슬롯별 선택, 무응답/정산/다음 품목, 최종 RC는 미완이다.
기존 `program_inputs::Policy`는 develop/SDK에 이미 있는 순수 bounded-selection primitive다.
그것의 실제 runtime/schema/Host/qualification/frontier 연결은 아직 없으므로, 고정 Intent 비교를
삭제하거나 다른 값을 opaque 참조 뒤에 숨겨 통과시키지 않는다. 기존 v1의 의미/bytes를 유지하는
명시적 버전 경계를 먼저 설계해야 한다.

## M3 실행 v2 개정 결정 — 2026-10-02

사용자가 명시적 실행 v2 계약 개정을 승인했다. 구현 전 결정은
[공통 실행 v2 계약](../contracts/workflow-execution/v2/README.md)에 고정한다.
**v2는 계약 버전**, **v1.1은 기존 계약 개정 절차의 이름**이다. 기존 v1 bytes와
exact-Intent 의미를 유지하며 새 형식을 명시적으로 협상한다. 이 절은 구현/수락 완료가 아니다.

1. 승인 표현은 **template·rule·입력 closure와 전체 report digest index 승인 + 서버의
   결정적 재계산 일치 검사**다. concrete ArtifactRef를 슬롯마다 나열하지 않는다.
   게시 때 모든 후보를 해석·검증하고, 실행 직전에 선택 후보를 다시 검사한다.
   실제 품목 instance의 값이 승인 candidate와 다르면 새 resolve·Preview·게시가 필요하다.
   결과 hash만 같다는 이유로 Run 권리를 재사용할 수 없다.
2. slot은 **게시된 row-major 순서 규칙으로 P가 선택**한다. 운전자는 실제 품목 instance와
   수량을 입력하고 P가 입력 주체·원 요청·Run/Part·품목 revision·slot을 기록한다.
   임의 slot 선택/건너뛰기는 지원하지 않는다. Run을 새로 만들어 소비된 slot을 재사용할 수 없다.
3. 게시된 의존 정의의 현재 revision이 바뀌면 **새 효과를 차단**한다. 값이 같아도 차단하며
   무관한 정의 변경은 영향이 없다. 이미 접수한 원 operation의 조회·정산은 계속 가능하다.
   새 값은 resolve → Preview → publish·재자격 후 새 Run으로만 사용한다.
4. 반례 2는 **현재 설치된 Linux v0.4.0-rc.1의 v1 P/Executor/Host/UI 원본 bytes**를
   고정해 v2 계획을 주입한다. 이 설치의 runtime은 현재 정지돼 있고 M2 macOS 개발 서버와
   구분한다. 현재 코드의 legacy 분기나 구버전 소스 재빌드로 대체하지 않는다.

상한은 후보 8개 × slot 2400개 × node 16개, index 2 MiB, 보고서 900,000 bytes,
node parameter 64 KiB, 정책 envelope 128 KiB다. 정의 closure는 512개/16 MiB,
전체 자격 의존성은 1024개 이하다. 기존 64-choice 순수 정책과 Python package 32-asset
상한을 임의로 올리지 않고 v2 파생 의존성을 명시한다.

[크기 산출 근거](../../references/execution_v2_design_2026-10-02/sizing.json): A/B × 2400 × 8에서
concrete parameter는 38,400개, reference 배열만 5,284,801 bytes다. 현재 v1 payload를
외삽하면 parameter 48,499,200 bytes, report 929,577,600 bytes다. 선택한 report index는
362,633 bytes이고 8개 후보 상한에서는 1,450,373 bytes다. 이는 직렬화 크기 산출이며
dense 실제 해석/성능 시험이 아니다. 기존 dense geometry는 계속 BLOCKED다.
자격 검증은 index 한 개로 계산이 사라지는 것이 아니다. A/B의 공통 정의 82개를 포함한
전체 입력 closure를 검사하고 4800회 해석·제약 검사, 최대 38,400개 parameter 생성을
수행해 index를 대조한다.

2026-10-02 [2400-slot 실측](../../references/execution_v2_design_2026-10-02/dense-performance.json)은
M2의 A/B 품목·8개 Task·해석 규칙을 그대로 사용했다. 원본 dense는 두 품목 모두 pitch
위반으로 BLOCKED임을 확인했다. 성공 경로 측정은 별도 임시 DB에서 **새 model/instance**를
만들어 40×60개 슬롯을 유지하고 pitch를 80 mm, 외곽을 4800×3200 mm로 설정한
SIMULATION 데이터다. 원본 패키지·운영 DB를 바꾸거나 원본 dense를 적합 판정하지 않았다.

Apple M5/16 GiB, macOS 27.0, Rust 1.98.1 release 빌드의 단일 측정(빌드 시간 제외):

| 측정 구간 | wall-clock 시간 | 실제 수행 범위 |
|---|---:|---|
| Preview 생성·저장 | 89.866943 s | 4800개 report, 38,400개 parameter 생성 |
| 게시 | 0.086322 s | 저장 Preview/currentness 확인, 서명 package 재검증·commit |
| 자격 보고서 검증 계산 | 92.219652 s | 서명·의존성 검사와 4800개 report 전수 재계산·index 대조 |

검증 의존성은 108개(상한 1024), 검증 입력 artifact는 19개/541,885 bytes였다. 입력 closure
114,686 bytes, index 362,633 bytes, policy 21,502 bytes다. 검증 계산은 600 s ticket
상한의 15.37%이며 계산상 여유는 507.780348 s다. 이는 해당 환경에서의 계산 비용 비교다.
fixture의 서명·6개 영역 증거·권한 clock은 시험용이며 실제 ticket 발급/취득/commit,
reviewed change 적용·Host 확인, 독립 승인, Linux 지연이나 실행 자격을 입증하지 않는다.
첫 관문은 이 측정만으로 통과하지 않으며 실제 ticket 경로 확인은 남아 있다.

재현은 P의 `external_dense_publication_and_qualification_timing` ignored test를 사용한다.
S 입력 commit/hash, P 측정 코드와 fixture hash는 위 실측 JSON에 고정했다.
`RX_DENSE_FIXTURE`를 해당 S checkout의 `examples/definitions/0f-laser-simulation`으로 지정하고
P에서 다음을 실행한다. 2-slot fixture preflight 값은 2400-slot 성능 근거로 사용하지 않는다.

```sh
RX_DENSE_MEASUREMENT_SLOTS=2400 cargo test --release --locked -p rx-application --test transactions external_dense_publication_and_qualification_timing -- --ignored --nocapture
```

UNKNOWN은 원 operation의 효과가 확인될 때까지 자원을 보유하고 진도를 막는다.
적용·완료가 확인되면 같은 Part/slot의 남은 node만 진행한다. 무효과와 안전한 이전 상태가
증명되면 복구 권한으로 같은 node를 **최대 한 번 명시적으로 재시도**할 수 있다.
새 operation은 원 정산 ID와 같은 선택을 연결하고 현재 revision/제약/permit을 다시 검사한다.
한 Part의 모든 done이 끝나기 전 다음 slot은 금지한다. 부분 효과·충돌·불명 상태나 abort에서
자동으로 다음 slot을 고르지 않는다. 다른 Run 승인 재사용과 정산 후 retry/next-slot 혼동을
각각 반례 9·10으로 추가했다.

구현 순서는 **계약·P·Executor(반례 1–5) → Host → UI**, 릴리스는 대응 버전을 담은
단일 묶음이다. 반례 2의 옛 Host/UI 시험과 새 Host/UI 구현을 구분한다.
기존 반례 8(실제 P↔Host 무응답, UNKNOWN/보유/원 정산/다음 품목)은 **M3 사용자 수락**으로
분리한다. 이번 문서 고정으로 M3 또는 최종 RC를 수락 처리하지 않는다.


## M3 재계획 — 2026-10-03 사용자 지시

M3를 아래 세 checkpoint로 나눈다. 각 checkpoint는 사용자가 직접 실행해 확인한 뒤에만
다음으로 넘어간다. 현재 M3 제품 운전 절차는 아직 제공되지 않았으며, 개발 시험이나
`cargo test`를 사용자 실행 checkpoint로 대신하지 않는다. 기존 M1/M2 수락은 유지한다.

| Checkpoint | 동결할 범위와 산출물 | 사용자 수락 |
|---|---|---|
| **M3a Land** | #75/#87은 기존 첫 관문(계약·P·Executor, 반례 1–5)에 필요한 코드·수정·근거만 포함한다. missing handover 원인 조사에 최대 3시간을 쓰고, 미확정이면 관측/미확정/다음 판단을 보고하고 중단한다. 원인 수정, 기존 관문 통과, commit-range별 문제·변경·근거 요약, 정확한 head CI 확인 후 P → S 순서로 develop에 merge한다. 새 Host/UI 및 추가 rigor 작업은 착수하지 않는다. | merge된 head에서 재생성한 개발 환경과 **제품 CLI**로 기존 M1/M2 A/B 해석·위반 차단·저장 보고서 재열기 smoke를 제공한다. 사용자가 이를 실행하고 landing을 확인한다. 실행 전에 정확한 환경/명령을 문서에 고정하며, 아직 실행되지 않은 명령을 “지금 가능”으로 제시하지 않는다. |
| **M3b Operate — 이관** | 이미 게시된 workflow를 CLI로 N개 실제 ObjectInstance에 바인딩하여 SIM device에서 실행한다. P↔Host 무응답 1회를 주입하고 UNKNOWN·자원 보유를 확인한다. 원 operation을 정산한 뒤 같은 Part의 남은 단계와 다음 Part가 완료되고, Run record에서 게시/정의/규칙/report/parameter 버전이 일치해야 한다. 그 다음 기존 UI에서 같은 경로를 제공한다. | 사용자가 문서의 제품 CLI 명령을 먼저 실행한 뒤 UI에서 같은 Run·UNKNOWN·정산·다음 Part·기록을 확인한다. API fixture, 합성 Host evidence, cargo 시험은 수락을 대체하지 않는다. 기존 승인된 복구 규칙만 구현·검증하고 추가 변형은 parking으로 보낸다. |
| **M3c Ship — 이관** | 호환 P/S/UI를 담은 단일 RC installer와 QUICKSTART를 제공한다. main 릴리스는 별도 사용자 지시 전에는 하지 않는다. 깨끗한 Linux에서 M1–M3를 재현하고 새 part/tray를 package data만으로 추가한다. | 사용자가 QUICKSTART만으로 M1–M3를 45분 이내에, 세 번째 part/new tray 추가를 10분 이내에 수행한다. 마지막에 설치시간·명령 수·데이터 추가시간·package 파일/줄 수·generic/domain core 변경량·SIM/실물 경계를 한 번 기록한다. |

**M3a 범위 동결:** 현재 PR #75의 기반 head는 `6442e76`, #87은 `7983bfe`다. 이후 미커밋
등록 mTLS fixture, 첫 관문에 필요한 고정 v1 주입 및 missing-handover 수정만 이 landing에
포함한다. 이미 얻은 dense 2400 계산 결과는 재측정하지 않는다. 기존 반례·gate의 실패를
고치는 데 필요하지 않은 신규 반례, 측정, hardening은 제안자가 누구든 parking에 기록한다.
범위를 늘리는 아이디어를 구현으로 옮기기 전에 M3a/b/c 중 어느 수락을 실제로 막는지
한 문장과 현재 근거로 명시한다. “더 확실해질 수 있다”는 추가 착수 사유가 아니다.

**현재 진단:** P는 native 성공/valid integrity를 확인했지만 S journal의 원 operation
`RECONCILE_OPERATION`이 `PREPARED`에서 정체됐다. trace에서는 execute 진입 또는 enter 전후
100ms read 유효기간이 끝나 RPC가 전송되지 않았다. 이 경로가 `RefreshRequired`를 정상 cycle로
반환하여 service의 통신 grace가 계속 갱신되고 `RUNNING`으로 남았다. P의 Reconcile은 현재
등록된 peer를 확인하는 원 operation 조회·정산 계획이며 새 production invocation을 발급하지
않는다. 따라서 새 효과용 freshness 검사와 원 operation 조회의 전송 경계를 분리하는 것이
수정 후보다. **수정은 아직 적용/검증하지 않았고, 100ms 제한 확대나 새 실행 guard 제거로
해결하지 않는다.** read 시간 소모의 세부 breakdown과 부하 성능은 이 진단으로 입증하지 않았다.

현재 등록 mTLS의 normal/응답 유실 3종은 한 순차 suite에서 통과했지만 추가 반복의 handover
정체가 재현되어 안정 통과로 승격하지 않는다. 고정 v1 원본으로 valid v1 positive control은
통과했고, 실제 v2 주입은 미완료다. 첫 관문·M3a·M3b·M3c 모두 사용자 수락 전이다.

사용자 지시에 따라 현재 진단을 기록한 뒤 goal을 일시정지한다. 재개 시 새 설계 항목을
추가하지 않고 위 M3a의 남은 수정·관문·요약·merge부터 수행한다.


### M3a 재개와 handover 수정 근거 — 2026-10-03

후속 framework 확장 목표의 선행 조건으로 **M3a landing과 사용자 smoke를 먼저 끝내고
멈춘다**. F0–F3는 그 수락 전에는 시작하지 않는다.

원 operation reconciliation만 실행 snapshot의 freshness 전송 조건에서 분리했다. 요청은
기존 journal의 Run/operation/Intent/key에 고정되고 P가 현재 등록 peer와 cell 접근을 검증한다.
새 Begin/Submit/Complete의 100ms 조건은 유지한다. `RefreshRequired`는 degraded/error 경로로
보내 통신 grace를 계속 갱신하지 않으며, 유효한 read에서 native 결과를 기다리는 상태는
기존 operation 관측으로 구분한다.

첫 반복의 4회째에는 handover 두 건이 모두 응답됐지만 완료 read 만료로 명시적으로 pause됐다.
RPC가 약 94–97ms를 소비하는 것을 확인했고, 이미 active_run에서 검증한 immutable 정의를
advisory read가 다시 projection하는 중복을 제거했다. read는 현재 instance의 정확한
reference/model·Run·ordinal·slot·pool 소유를 검사한다. 새 효과의 전체 projection/currentness
검사는 기존대로 남긴다. 이 변경은 M3a의 필수 반복 검증을 막는 read 경로에만 적용했다.

수정 뒤 동일한 등록 mTLS 시나리오는 [20회 연속, 실패 0회](../../references/execution_v2_design_2026-10-02/m3a-handover-repeat.json)를 기록했다.
매 회 2 Part/2 operation, budget 소비 2, 두 번째 실제 object를 기다린 뒤 바인딩하여 완료했다.
이 결과는 frozen clock·합성 Host 완료/인계 증거를 사용한 P/S integration precheck다.
고정 v1 주입 관문, exact-head CI/commit-range 요약/merge, merge 후 제품 smoke는 아직 남아 있다.
따라서 M3a 또는 이후 checkpoint의 사용자 수락으로 표시하지 않는다.

### 현재 진단 후 일시정지 — 2026-10-03

사용자의 중단 지시에 따라 위 진단과 기존 수정/20회 반복 근거까지만 보존하고 일시정지한다.
수정은 P/S 작업 트리에 있으며 아직 merge되지 않았다. 고정 v1 P/Executor/Host/UI에 대한
v2 주입은 미완료이고 첫 관문을 통과했다고 주장하지 않는다. M3 제품 실행 명령은 **none yet**다.
재개 후 단일 다음 작업은 기존 고정 v1 주입 관문을 마치는 것이다. 이후 M3a의 commit-range
요약·정확한 head CI·P→S merge·제품 smoke 순서를 유지하며, 사용자 수락 전 M3b를 시작하지 않는다.
M3b는 CLI→UI 운전/UNKNOWN 정산/다음 Part/버전 참조 기록, M3c는 깨끗한 Linux의
RC installer+QUICKSTART 재현으로 끝낸다. 각 단계는 사용자가 실행한 뒤에만 수락한다.

정리 기록상 `.build/workflow-platform-target/debug/deps`, `debug/incremental`과 미참조 이미지
`3ac0aa417604`, `f26dfa5727aa`, `566320238338`을 삭제했다. 이번 중단 시점에 여유 공간
90.75 GB를 재확인했다. 신규 parking 항목은 0개이며 기존 M3 재계획의 4개 보류 항목을 유지한다.


### M3a만 재개 — 2026-10-03 사용자 지시

현재 작업은 M3a만 끝내고 멈춘다. 기존 고정 v1 주입 및 첫 관문만 완료하고 새 관문을
추가하지 않는다. PR 본문에 commit-range 요약을 작성하고 정확한 head CI 확인 후
P → S 순서로 merge한다. merge된 head로 환경을 재생성하여 사용자가 실행할 M1/M2
제품 CLI smoke(A/B 해석, 위반 차단, 저장 보고서 재열기)를 제공한다.

**M3b/M3c는 다음 프레임워크 작업으로 이관**하며 이 작업에서 시작하지 않는다. 위 표의
운전/복구/RC 내용은 이관 대상의 기록이다. 신규 아이디어는 parking으로 보낸다.

고정 v1 UI 주입에서 검토한 v2 참조와 실제 v1 Start 사이의 불일치가 관측됐다. 사용자는
[설치 격리 및 명시적 거절](../contracts/workflow-execution/v2/legacy-isolation.md)을 승인했다.
고정 원본의 FAIL은 보존하며, 승인된 격리 검증 전에는 첫 관문을 통과로 표시하지 않는다.

기존 첫 관문의 구현 검증은 [M3a 첫 관문 기록](m3a_first_gate.md)에 모았다. 고정 UI FAIL과
승인된 격리 결과를 분리했다. 다음은 최종 commit/CI/P→S merge와 merge 후 사용자 smoke다.
