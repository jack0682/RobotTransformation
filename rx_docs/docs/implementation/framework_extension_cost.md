# F0 — 외부 확장 비용 기준선

2026-10-03. 사용자가 M3a smoke를 수락한 뒤 요청한 **측정만** 수행했다.
제품 코드는 수정하지 않았다. **사용자가 F0를 수락했다.** 아래 1–6절은 측정 당시의 근거이며,
수락 후 새 순서와 F1′ 계획은 7–8절, 구현·검증 이력은 9–17절에 기록한다.
**현재 상태: CP1·CP2·CP3를 모두 사용자가 수락했으며 F1′은 종료됐다.**
최종 수락은 18절이 기준이다. 앞 절의 착수/수락 대기 문구는 당시 이력으로 보존한다.
F2′ CP2 정상 운전 사전 검증을 마쳤으며 사용자 수락을 기다린다(23절). CP3는 미착수다.
M3b/M3c의 이관 기록은 유지한다.

**F0 측정 당시 관측 결론:** S3는 데이터만으로 추가·해석됐다. S2의 새 Task 이름·속성·규칙·Skill 매핑도
기존 저작/해석/컴파일 경로가 받아들였다. S1의 독립 backend는 배포 Host의 닫힌 선택지에서
막혔다. 다만 Python finite-skill로 감싸는 대안은 이미 있다. 이 대안을 새 NativeAdapter 등록의
성공으로 바꾸어 기록하지 않는다. 세 확장의 전체 운전/UNKNOWN 복구는 입증하지 않았다.

## 1. 기준과 측정 방법

| 항목 | 고정 값 |
|---|---|
| Platform develop | `f8913d8a70a08afb682f619cb7d008f967713bdb` |
| Solutions develop | `606e9add28c9ab44f92e11dad260bb96780f2df9` |
| Docs develop | `df8efadbeff7f2d6484e210cde3f73ccc7356600` |
| Scratch | 각 저장소 `feature/f0-extension-baseline`; merge하지 않음 |
| 외부 패키지 원본 | 로컬 `rx_ws/.build/framework-f0/extensions`, 별도 Git scratch commit `e01a05a` |
| 저작 환경 | 별도 새 LocalInstallation, loopback API 8093. 기존 M3a/M1/M2 저장소 미사용 |
| 실행 코드 | 위 develop에서 빌드한 `rx-hostd`, `rx-process-compile`, `rx-device-package` 및 해당 source의 `rx` CLI |
| 경계 검사 | 전후 모두 63 modules / 79 files / 18 seam pairs / 31 references |

줄 수는 위 외부 패키지 **실제 UTF-8 파일의 물리 행 수(빈 행 포함)**다. JSON은 2칸 들여쓰기다.
이는 시도에 작성한 양이지 완성된 생산용 확장 비용이 아니다. 생성된 환경/manifest/receipt/
컴파일 산출물과 원래 workflow 복사본은 별도다. 미래 코어 구현의 추가·삭제 LOC는 작성하지
않았으므로 **미측정**이다. 이를 0 또는 임의의 예상 숫자로 채우지 않는다.

명령 수는 `commands.jsonl`에 기록한 시나리오 실행 호출 수다. 제품 명령, 작성 보조,
컴포넌트 측정, 잘못된 호출의 재시도를 구분했다. 검색·편집·Git·문서 검사는 이 수에 포함하지
않는다. 공통 초기화/빌드는 16회(성공 12, 시작 직후 연결 및 그 후속 입력 부재 실패 4)이며
각 시나리오에 중복 합산하지 않았다. 사용자 본인의 소요 시간은 아직 측정하지 않았다.

## 2. 시나리오별 비용 표

| 시나리오 | 실제 제품/코어 변경 | 확인된 필요 변경 또는 차단 경계 | 외부 개발자 작성 파일·행 | 명령 수 | 실제 도달한 지점 / 막힌 지점 |
|---|---|---|---|---|---|
| **S1 공압 척 I/O backend** | **0파일 / +0 −0행** | 같은 배포 `rx-hostd`에 새 backend를 넣으려면 최소 **2파일·6개 닫힌 선택 지점**의 변경이 필요. 추가/삭제 LOC는 미측정. 아래 소스 표 참조 | 독립 backend 시도 3파일/26행 + Python skill 대안 3파일/37행 = **6파일/63행** | **12회** = 제품·작성 보조 7 + 측정 fixture 3 + 호출 실수 2 | 실제 `rx-hostd inspect`가 새 backend를 거절(rc=1). Python 대안은 unsigned DEVICE_REFERENCE 조립 및 Host 컴포넌트에서 clamp/unclamp 값 소비 성공. 독립 adapter 등록·센서 관측·custody 공급 경로가 아님 |
| **S2 rotation-align Task/Skill** | **0파일 / +0 −0행** | **새 Task 유형 때문에 필요한 코어 변경은 관측되지 않음(0파일/0행)**. 게시 v2를 실제 Host에서 운전하는 공통 연결 미완료는 별도이며 필요한 LOC 미측정 | **6파일/570행** | **15회** = 제품·작성 보조 11 + 측정 fixture 2 + 호출 실수 2 | 새 Task를 넣은 9단계 workflow 저장·해석·컴파일, unsigned package 조립, Host 컴포넌트에서 95°/0.5° 소비 성공. signed 설치·자격·P→Executor→Host의 전체 실행은 미검증 |
| **S3 세 번째 부품·fixture 유형** | **0파일 / +0 −0행** | 요청한 데이터 추가/해석 범위에서 **0파일/0행** | **1파일/152행**, 6개 정의 | **4회** = apply / resolve / 동일 요청 재적용 / report 재열기 | ObjectType/Model/Instance와 ResourceType/Model/Instance를 추가하고 기존 8단계 workflow에서 해석. 재적용 receipt 동일. 데이터 확장 회귀 PASS; 장비 실행/qualification PASS는 아님 |

**숫자 해석:** S1의 2파일은 현재 Builtin 구성 방식을 유지할 때 확인한 최소 변경 접점이다.
완성된 외부-process 프로토콜, restart/custody 연계, 패키지 검증에 필요한 전체 파일·LOC를
측정했다는 뜻이 아니다. S2/S3의 0은 관측한 단계의 수치이며 전체 운영 경로 완성을 뜻하지 않는다.

패키지 외에 공통 작성 보조 2파일/27행(`compile-inputs.py` 16, `prepare-library.py` 11)을
썼다. 보고서→정확한 template/input/environment 참조를 조립하는 코드이며, 생성 산출물로
숨기지 않고 공통 저작 비용으로 남긴다. Host 권한을 만드는 측정 fixture는 이 비용과 분리했다.

| 외부 원본 파일 | 행 수 |
|---|---:|
| S1 `adapter.json` / `adapter.py` / `backend.json` | 13 / 7 / 6 |
| S1 Python 대안 `recipe.json` / `skill.json` / `skill.py` | 13 / 8 / 16 |
| S2 `definitions.json` / `task.json` / `compose.py` | 372 / 141 / 12 |
| S2 `recipe.json` / `skill.json` / `skill.py` | 13 / 8 / 24 |
| S3 `definitions.json` | 152 |

S2는 기준 workflow 3,125행을 수정하지 않고 12행 composition 보조로 새 package를 생성했다.
생성된 전체 workflow는 3,266행이며 570행 작성량에 다시 합산하지 않았다.
명령 실행 wall-time 합은 S1 7.31초 / S2 7.88초 / S3 1.42초다. 파일 작성·탐색·사람의 판단
시간을 제외하므로 설치 시간이나 사용자 작업 시간으로 해석하면 안 된다.

## 3. 실제 시도와 경계

### S1 — 닫힌 backend와 이미 있는 finite-skill 대안을 구분

새 모의 backend의 명령은 `clamp`, `unclamp`, 관측은 `chuck.clamped`로 선언했다.
`EXTERNAL_PROCESS`는 현재 지원된 규격이라고 가정한 이름이 아니라 외부 adapter 등록을
시도한 명시적 입력이다. 기존 `FILE_SIMULATION`을 같은 제품 CLI로 읽는 양성 대조는 통과했다.
현재 develop의 실제 `rx-hostd inspect` 결과:

```text
unknown variant `EXTERNAL_PROCESS`, expected one of
FILE_SIMULATION, PYTHON_SKILL_SIMULATION, PYTHON_SKILL_PACKAGE,
PYTHON_SKILL_LIBRARY_PACKAGE, JTC_PACKAGE, MELSEC_PACKAGE, VALIDATED_DRIVER
```

별도의 Python skill 대안으로 기존 report에서 나온 `clamp` 및 `unload` 입력을 소비했다.
원래 8단계 workflow에는 독립 `unclamp` Task가 없고 `unload` primitive 내부에 unclamp가 있다.
따라서 대안 시험에서 `unload` 입력을 unclamp I/O로 매핑했지만, 이것으로 로봇의 unload 전체나
물품 지지/인계를 구현했다고 주장하지 않는다. 외부 장치 기록은 다음 두 건이다.

```json
{"node":"clamp","coil_clamp":true,"sensor_clamped":true}
{"node":"unload","coil_clamp":false,"sensor_clamped":false}
```

Linux 환경을 실제 준비한 뒤 현재 `rx-device-package python-library-assemble`로 조립한
후보는 `UNSIGNED_CANDIDATE`, `activation_authorized=false`였다. 독립 backend 선언은
채택되지 않았고, 성공한 것은 기존 Python backend가 실행할 finite program 대안이다.
Python adapter의 source observation은 support adapter에 위임되며 외부 skill의 I/O 관측을
새 NativeAdapter 관측/인계 계약으로 등록하지 않는다.

### S2 — 새 이름과 새 인자는 이미 데이터 경로를 통과

Object 쪽 `nominal_angle=90 deg`, `angle_tolerance=0.8 deg`와 fixture 쪽
`rotation_offset=5 deg`, `angle_tolerance=0.5 deg`를 패키지로 등록했다.
새 Task `rotate-align`은 ADD/MIN rule을 통해 각각 **95 deg**, **0.5 deg**를 받는다.
각 값의 저장 provenance에는 rule member와 해당 object/resource reference·revision이 남았다.
새 Skill implementation은 `f0.rotation-align`, primitive는 `rotate-align`이다.

기존 load와 clamp 사이에 새 Task를 넣어 9개 step을 저장했다. 서버 report는
`RESOLVED_NOT_QUALIFIED`, 실제 compiler 산출물은 `COMPILED_NOT_QUALIFIED`였다.
특수 Task enum이나 각도 전용 Rust 분기를 추가하지 않았다. 준비된 Python 프로그램이 실제
subprocess에서 95/0.5를 읽어 independent file-device record를 썼고 Host receipt는
`RESULT_CAPTURED`였다. 이것은 아래에 제한한 컴포넌트 시험이며 전체 workflow 실행은 아니다.
Linux용 unsigned DEVICE_REFERENCE 후보 조립도 통과했다.

### S3 — 데이터만으로 되는 회귀 확인

`type.f0-third → part.f0-third → object.f0-001`과
`type.f0-fixture → fixture.f0-model → fixture.f0-site`를 한 정의 package에 추가했다.
기존 type 상속·규칙을 사용하되 부품 55×30 mm, fixture family `F0/70`을 선언했다.
제품 CLI로 기존 workflow의 `part`와 `jig` context를 새 instance에 바인딩해 8단계 report를
얻었다. 이는 실제 서버 저장·검증·해석이며 로컬 JSON 계산으로 대체하지 않았다.
동일 apply 재시도는 같은 reference/revision/receipt를 반환했고 저장 report도 재열렸다.

### 공통 미완료와 측정 fixture의 한계

M3a 수락은 authoring/resolution smoke와 계약·P·Executor landing이었다. native Host의
execution-v2 서비스 연결은 M3b와 함께 이관됐다. 현재 Host RPC router에는 v1 구성·자격·실행
서비스가 등록돼 있고 execution-v2 SDK가 생겼다는 사실만으로 v2 Host 구현이 생기지 않는다.
이 공통 미완료를 S1/S2가 각각 새로 요구한 코어 비용으로 중복 계산하지 않았다.

Host 컴포넌트 측정은 제품의 `Host::prepare/authorize`, 기존 PythonSkill 및 실제 subprocess를
사용했지만, 측정용 caller/permit과 ManualClock을 사용했다. P enrollment, signed package
설치·software review·qualification, 실제 Executor의 9단계 운전, 무응답/UNKNOWN 정산은
수행하지 않았다. 직접 `rx skill run` 또는 LOCAL_SIM 별도 runner를 전체 제품 실행으로
대체하지도 않았다. 새 프로토콜·registry·핸들러 구현은 하지 않았다.

Linux 환경 준비에는 보존된 amd64 이미지의 Python 인터프리터만 사용했고, 실행한 `rx`/
preparation source는 현재 develop을 읽기 전용으로 mount했다. Host 값 소비 시험은 macOS
네이티브 환경으로 별도 수행했다. Linux 후보가 실제 배포 Host에 설치·실행됐다는 주장이 아니다.

호출 실수도 비용에서 숨기지 않았다. S1/S2 각 2회는 `rx skill` 하위 명령 누락과 컨테이너
Python 경로 오기였다. 이를 framework 기능 차단으로 분류하지 않는다. 실제 S1 backend
거절 2회(typed decoder와 제품 CLI)는 동일한 닫힌 등록 경계의 관측이다.

## 4. 변경 접점 — 미래 LOC와 기존 소스 위치를 혼동하지 않기

아래 링크는 측정 기준 commit에 고정돼 있다. 제품 소스 diff는 끝까지 0이다.

| 범위 | 확인한 기존 파일·위치 | 무엇을 바꿔야 하거나 재사용해야 하는가 |
|---|---|---|
| S1 같은 배포 Host에서 새 backend 선택 | [config.rs L50–83](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/config.rs#L50) | 닫힌 Backend 선언 34행. 이 구간에 추가 가능한 package 식별 경계가 현재 없음. **34행을 수정해야 한다는 뜻은 아님** |
| S1 현재 factory의 새 adapter 연결 | [factory.rs](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/factory.rs#L10) | BuiltinAdapter L10, delegate L17, validate L74, initialize_metadata L109, open_passive L159: 5개 선택 지점 |
| S1 가능한 다른 배포 선택 | [AdapterFactory L31](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/mod.rs#L31), [rx-hostd L112/124](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/bin/rx-hostd.rs#L112) | 공개 trait/initialize_with/run_with는 이미 있음. 외부 Rust factory를 묶은 별도 Host release는 가능한 대안이지만 현재 binary에 package를 추가하는 경로가 아니며 이번에 구현·검증하지 않음. 모든 가능한 설계가 코어 수정을 강제한다고 단정하지 않음 |
| 패키지 교체 신원·인계 검토 | [NativeInstallation L86](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/mod.rs#L86), [binding_change.rs L25](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/binding_change.rs#L25) | 향후 generic registry가 실제로 닿을 때 검토할 기존 의미 경계. 지금 필수 patch 파일/LOC로 확정하지 않음 |
| S2 타입/규칙/컴파일 | [workflow model](https://github.com/jack0682/rx-platform/blob/f8913d8a70a08afb682f619cb7d008f967713bdb/crates/rx-domain/src/workflow/model.rs), [workflow compiler L116](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-process/src/workflow.rs#L116) | 이번 Task/각도/허용오차에 수정 불필요. 기존 typed resolver와 정확한 implementation/version/primitive mapping을 재사용 |
| 공통 v2 실제 실행 연결 | [Host RPC router L99](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/rpc/mod.rs#L99), [python_skill.rs L80](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/python_skill.rs#L80) | 선택된 원 operation의 parameter bytes를 기존 Host gate/runner로 연결해야 함. 현재 Python 등록은 고정 input/Intent digest와 일치해야 함. 새 Task마다 별도 실행 경로를 추가할 근거가 아님 |
| S3 타입·instance 상속 | [definition.rs L184](https://github.com/jack0682/rx-platform/blob/f8913d8a70a08afb682f619cb7d008f967713bdb/crates/rx-domain/src/definition.rs#L184) | 데이터 추가로 통과; 수정 불필요 |

## 5. F0 측정 당시의 범용 메커니즘 후보

1. **배포 Host의 adapter package 등록·선택 경계.** 이미 있는 NativeAdapter/AdapterFactory를
   버리고 새 Host를 만드는 대신, package의 외부 구현을 기존 관문에 연결할 registry와
   프로세스 프로토콜의 범위를 정해야 한다. package 신원·원 호출·관측·중단/인계·UNKNOWN은
   Host가 계속 소유한다. 이는 K-a/K-b/K-c/K-d에 닿는 공통 기능이며 공압 전용 core 분기는 아니다.
2. **기존 v2 선택값을 기존 Host 실행으로 전달하는 공통 연결.** Task별 새 실행 경로보다
   기존 typed resolver/compiler, 승인된 selection/parameter identity와 Host gate를 연결하는
   것이 관측된 공통 장애물이다. 새 Task 이름/각도 자료형 때문에 별도 Task DSL/enum을 추가할
   근거는 이번 측정에서 나오지 않았다. F2 범위는 이 사실을 보고 다시 정해야 한다.
3. **선언·환경·template·고정 input을 조립하는 저작 도구.** 공통 27행 glue와 여러 CLI를
   확장 작성자가 반복해야 했다. 기존 package 조립/검증 API 위의 scaffold/pack/conformance
   흐름이 후보이며 새 권한·원장을 만드는 이유가 아니다. S3는 지금의 데이터 경로를 유지한다.

이 목록은 검토용 제안이다. F1/F2/F3 구현, source 이동, 새 gate/반례, SDK 배포 방식 변경을
시작하지 않았다. seam 수와 실행 경로 수를 줄였다고도 주장하지 않는다.

## 6. 직접 읽을 제품 명령과 증거 위치

```sh
source /Users/ojaehong/RX_automation/rx_ws/.build/framework-f0/cli.sh
f0flow --format text report "$F0_HOME/s2-report.receipt.json"
f0flow --format text report "$F0_HOME/s3-report.receipt.json"
```

S1 등록 차단을 같은 제품 CLI로 재확인하는 명령(rc=1 예상):

```sh
/Users/ojaehong/RX_automation/rx_ws/.build/linux-install-bundle-target/debug/rx-hostd inspect /Users/ojaehong/RX_automation/rx_ws/.build/framework-f0/host-s1.json
```

작업 root는 `rx_ws/.build/framework-f0`다. `baseline.json`에 기준 SHA,
`commands.jsonl`에 정확한 argv·rc·시간, `cost.json`에 파일별 행 수·SHA와 source diff가 있다.
`evidence/s1`, `evidence/s2`, `evidence/s3`의 stdout/stderr를 보존했다.
`device-s1/effects.jsonl`, `device-s2/alignment.json`은 별도 file-device 기록이다.
`extensions`는 원본이고 `s1-candidate`, `s2-candidate`, `*-environment`, `*-compiled`는
생성 산출물이다. 측정 harness는 별도 `probe`와 helper 파일에 있으며 실제 배포 비용으로
숨겨 넣거나 제품 실행 증거로 승격하지 않았다.

**F0 측정 종료 당시:** 제품 수정 0, scratch merge 0, 신규 parking 0. 이후 사용자 수락과
재계획은 아래에 기록한다.


## 7. F0 수락 후 재계획 — 2026-10-03 사용자 결정

**원래 F2(Task 유형 패키지화)를 삭제한다.** S2는 새 Task·각도/허용오차·resolution rule·Skill
매핑을 코어 0줄로 선언·해석·컴파일할 수 있음을 보였다. 따라서 별도 Task 유형 체계나 DSL을
새로 만드는 단계를 두지 않는다. 다만 F0 컴포넌트 시험을 전체 운전 성공으로 승격하지 않는다.
현재 우선 장애물은 v2에서 선택한 실제 값이 기존 Host 실행·복구 경로 끝까지 도달하지 않는 점이다.

| 새 순서 | 목표 | 종료 기준 |
|---|---|---|
| **F1′ 끝까지 실행** | 기존 v2 선택값을 기존 Host gate/runner에 연결한다. 새 실행 경로는 만들지 않는다 | 사용자가 S2 9단계의 게시된 workflow를 N개 운전하고, 무응답→UNKNOWN→원 operation 정산→다음 Part 완료와 연결된 Run 기록을 제품 CLI로 확인 |
| **F2′ adapter registry** | S1을 외부 adapter package로 등록하고 같은 운전·복구 경로에서 사용 | S1 확장 개발자의 코어 변경 0줄. 범용 registry 자체의 코어 개발량과 확장량을 분리 기록 |
| **F3′ 저작 도구** | 선언·환경·template·package 작성 반복을 줄인다 | 같은 S2를 다시 작성해 F0의 파일/행/명령 수와 비교하고, 외부 개발자 1명이 S1을 직접 수행. 생성 파일·공통 준비·사람의 시간은 같은 기준으로 분리 |

프라임(′)은 변경된 milestone 순서를 구분한다. execution **v2 계약 버전**과 **v1.1 계약 개정
절차**를 바꾸는 표기가 아니다. F0 scratch 브랜치는 merge하지 않는다. 구현 승인 후에는 현재
명세·기준 develop을 확인하여 구현용 feature 브랜치를 사용하고 Docs → P → S 절차를 따른다.

## 8. F1′ 승인 계획 — 체크포인트별 직접 수락

### 목표와 실행 경로

S2의 `pick → load → rotate-align → clamp → close-door → process → open-door → unload → place`
9단계를 하나의 게시 버전으로 N개 실제 ObjectInstance/예약 slot에 실행한다. 최초 사용자 수락
표본은 **N=3**을 제안한다: Part 1 정상 완료, Part 2의 `rotate-align`에서 무응답, 원 operation
정산과 남은 단계 완료, Part 3 정상 완료. N을 고정한 별도 실행기를 만들지는 않는다.

경로는 **기존 P의 선택·admission·outbox → 명시적 Host-v2 ingress → 기존 Host prepare/
authorize·journal → 기존 Python/native runner → 기존 receipt/evidence·정산·handover**다.
이미 계약에 있는 v2 RPC는 ingress에서 기존 경로로 연결한다. 별도 workflow loop, 새 권한
원장, Task 전용 executor, CLI가 Part를 순회하며 장치를 직접 호출하는 경로는 만들지 않는다.

### 연결할 최소 범위

- **설치/자격:** 기존 signed package, v2 configuration acceptance와 qualification acknowledgement를
  실제 Host에 연결한다. SDK에 DTO가 있다는 것과 Host가 이를 집행하는 것을 구분한다.
- **선택값 소비:** Host는 승인된 template/환경과 Run·Part·node·operation binding 및 실제
  parameter bytes/schema/size/digest를 확인한다. 준비 receipt와 같은 원 operation에 영속화하고,
  Authorize에서는 같은 binding과 기존 permit/grant/epoch/expiry 조건을 재검사한다. 전역 mutable
  input 교체나 승인된 모든 slot의 고정 input을 미리 나열하는 방식으로 우회하지 않는다.
- **기존 runner 재사용:** 검증된 concrete input을 기존 실행 호출에 전달한다. 레이저/rotation
  이름에 따른 코어 분기는 금지한다. v2 입력 envelope를 읽는 역할과 모의 장치 의미는 서명된
  시나리오 package에 둔다. canonical input을 몰래 v1로 바꾸거나 digest를 다시 승인하지 않는다.
- **S2 package 구성:** 기존 tending 기능과 rotation skill을 기존 Python 환경/package 방식으로
  구성한다. 한 native 호출이 한 승인된 primitive만 수행하며, package 내부에 9단계 순회기를
  만들지 않는다. F0의 unsigned 후보와 test permit은 실제 설치·운전 자격으로 사용하지 않는다.
- **사용자 표면:** 기존 `rx` CLI에서 설치/게시 버전 적용, 객체 바인딩, N개 시작, 상태/UNKNOWN
  조회, 원 요청 정산 및 Run 기록 읽기를 이어 준다. 정확한 명령은 각 연결을 실제 실행한 뒤
  제공한다. 아래 계획의 동작 이름을 지금 존재하는 CLI 명령으로 주장하지 않는다.

주 변경 대상은 S의 Host RPC 연결·기존 gate/journal의 binding 보존·PythonSkill 입력 경계다.
P/Executor는 이미 있는 선택·전송·frontier·정산 경로를 재사용하고 실제 연결을 막는 부분만
수정한다. registry, 새 Task 체계, 저작 도구 재설계, 새 UI 운전 화면, RC installer 작업은
이번 단계에 넣지 않는다. 기존 승인된 호환성·권한·복구 검증을 유지하며 새 관문을 추가하지 않는다.

### 세 구현 단위와 실행 가능한 체크포인트

| 순서 | 구현 단위 | 종료 시 사용자에게 보일 제품 결과 |
|---|---|---|
| **1. 실제 Host로 1 Part** | 기존 v2 구성·자격·실행 요청을 Host에 연결하고 S2 package의 9단계 입력을 전달 | 제품 CLI로 게시 버전/실제 객체를 선택해 N=1 실행. 9개의 실제 native 호출·완료/인계 기록과 95°/0.5° 등 선택값의 소비를 확인. 합성 Host receipt나 cargo test를 실행 가능 결과로 대체하지 않음 |
| **2. 같은 Run에서 N Part** | 기존 객체/slot 예약, 순서, budget, Part 완료와 다음 객체 대기를 연결 | 제품 CLI로 N=3 정상 운전. Part마다 object/slot/parameter 참조와 단계 순서가 고정되고, 다음 Part가 현재 권한/참조 검사 뒤에만 시작됨을 확인 |
| **3. 무응답·UNKNOWN·정산** | 아래 하나의 fault를 실제 연결에 주입하고 기존 복구·기록 경로를 끝까지 연결 | Part 2에서 UNKNOWN/보유를 확인하고 원 operation을 정산. 같은 Part의 잔여 단계와 Part 3 완료를 확인. Run 기록에서 사용한 게시/정의/규칙/report/parameter 버전과 원 operation/invocation·정산 근거를 다시 열기 |

각 체크포인트는 정확한 head의 CI·DCO 통과 후 **develop에 P → S 순서로 병합한 뒤** 넘긴다.
관련 Docs 변경은 먼저 반영한다. 장기 draft PR을 만들지 않는다. 종료 시 **반드시 멈추고**
사용자가 직접 실행할 제품 CLI 명령과 receipt를 제공한다. **사용자가 해당 체크포인트를
수락하기 전에는 다음 체크포인트를 시작하지 않는다.** 모든 실행 receipt에 실제 대상인
**S2 9단계 workflow 및 SIMULATION 장치**를 명시한다.
단위 하나가 약 하루 내 실행 가능한 체크포인트로 내려오지 않으면, 막힌 연결 한 곳과 현재
실행 가능한 범위를 먼저 보고한다. 다른 범용 메커니즘을 추가하며 체크포인트를 미루지 않는다.
F1′ 전체는 세 체크포인트의 사용자 직접 수락으로 닫는다. 체크포인트 3 수락 전에는 F2′에
착수하지 않는다. 체크포인트 3의 UNKNOWN·자원/slot 보유·정산 결과는 **제품 CLI 상태 조회와
저장 기록**에 보여야 한다. 테스트 로그는 사용자 수락 증거가 아니다.

### fault와 정산의 정확한 의미

선택한 Part 2 operation의 Host native 호출이 시작된 뒤 **P가 결과를 받지 못하도록 통신을
차단**한다. Host와 Python worker는 유지하여 실제 완료와 원 receipt를 남길 수 있게 한다.
별도 evidence publisher가 먼저 결과를 전달하여 시험이 무응답을 건너뛰지 않도록, 같은
operation의 결과 전달도 관측 창 동안 보류한다. 이것은 SIMULATION 시험의 전송 제어이며,
결과·receipt·P 상태를 조작해 UNKNOWN을 만든다는 뜻이 아니다.

P/CLI에서 UNKNOWN과 operation 자원·slot 보유, 다음 Part 미시작을 먼저 관측한다.
통신 복구 후 **동일 operation/invocation을 조회·정산**한다. 이 수락 시나리오는 원 호출이
완료된 근거를 회수하는 경우다. native 호출을 다시 발행하지 않고, 완료 및 인계 증거가
모인 뒤 같은 Part의 남은 단계와 다음 Part를 진행한다. 모의 장치 효과 기록으로 중복 호출이
없음을 확인한다. 이 경로에서 호스트 재부팅/콜드 복구나 자동 재시도 지원을 주장하지 않는다.

완료 근거가 없거나 상충하면 UNKNOWN/보유를 유지한다. 운영자의 확인 버튼·idle 상태·timeout만으로
완료나 미실행을 만들지 않는다. 정산을 임의의 같은-slot 재시도 또는 다음-slot 이동 허가로
간주하지 않으며, 기존 [operation 계약](../contracts/workflow-execution/v2/operation-admission.md)과
[retry 계약](../contracts/workflow-execution/v2/retry-admission.md)의 증거/권한 경계를 유지한다.

### 수락과 중단 기준

체크포인트 1은 N=1의 9단계, 체크포인트 2는 같은 Run의 N Part, 체크포인트 3은 위 N=3
fault/정산 시나리오를 사용자가 각각 제품 CLI로 실행하고 수락한다. 저장된 Run 기록에서
동일한 버전·값·원 operation·정산 연결을 확인한다. 자동 시험/CI는 각 수락 전의 검증이다.
구현한 공통 기능과 시나리오 package 변경량은 따로 기록하고 seam 기준 18쌍/31참조는 늘리지 않는다.

첫 구현 단위에 앞서 기존 v2 계약이 package 환경·입력 envelope·복구 연결을 표현하는지
대조한다. 계약 변경, 별도 실행 경로 또는 domain-specific core 분기가 필요하면 구체적인
불일치와 한 가지 권고를 먼저 제시하고 중단한다. F0의 custom Host factory 재빌드 대안을
승인 없이 다른 배포 방식으로 채택하지 않는다. 신규 아이디어는 실제 F1′ 차단 근거가 없으면
parking으로 보낸다.

추가 요청된 **dense/my-tray의 슬롯 z와 surface_height 불일치**는 [parking](parking.md)에
기록했다. F1′ 수락은 기존 M2 supply-site의 명시적 pose를 사용하며 해당 두 데이터를 조용히
고치거나, 그 높이 정합성 제약이 적용됐다고 주장하지 않는다.

**승인 상태:** F0 수락 및 F1′ 계획 승인. 체크포인트별 직접 CLI 수락·develop 병합·중단 조건을
반영했다. 현재는 체크포인트 1의 계약 대조 중이며, 아래 개정 판단 전 제품 코드는 변경하지 않았다.
F0 scratch merge 0. 높이 정합성 parking 1건은 유지하며 이번 승인 반영에서 신규 추가는 0건이다.


## 9. 체크포인트 1 계약 대조 — Python 실행 profile의 명시적 opt-in 필요

상태: **권고안 검토 대기. 규범/제품 구현 미변경.** 사용자 조건에 따라 계약 개정이 필요한
지점에서 멈췄다. 이 절은 정식 계약 개정이나 실행 권한 부여가 아니다.

### 확인한 간극

- 공통 `rx.execution-template-catalog.v2`는 template ActionBinding과 NodeContract, 서명된
  family/profile/adapter 문서 참조를 선언한다. 하지만 Python 환경과 이 template들을 연결하는
  native Python profile 형식·기존 고정 입력 profile과의 구분은 아직 정의되지 않았다.
- 현재 [Python package documents](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/python_package.rs#L43)는
  `rx.python-skill-registration.v1`과 실제 고정 `input`의 digest/size가 ProgramGoal.parameter_set과
  같아야 한다. [Library binding 검사](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/service/python_library.rs#L119)는
  configured Intent 집합과 등록된 프로그램 집합을 비교한다.
- 기존 [PythonSkill guard](https://github.com/jack0682/rx-solutions/blob/606e9add28c9ab44f92e11dad260bb96780f2df9/runtime/rx-host/src/python_skill.rs#L319)는
  전체 Intent digest로 고정 프로그램을 찾는다. 동일 환경이라도 v2가 선택한 parameter digest가
  달라지면 등록된 고정 Intent와 달라진다. 이는 v1의 정상적인 제한이다.

따라서 v1 package를 그대로 둔 채 입력만 바꾸거나, 값 하나를 미리 고정한 N=1 성공으로
일반 선택값 전달을 대체하지 않는다. 이미 정의된 v2 ingress만 구현하는 것과, Python package가
승인하는 입력 범위를 새로 표현하는 것은 별개다.

### 권고안 하나: 명시적인 Python execution profile v2 추가

기존 execution-v2 계약의 **Python package profile 명세를 추가**한다. 새 wire RPC나 권한 모델을
만들지 않고, 이미 승인된 template/operation-binding 의미를 기존 Python 실행 경계에 연결한다.

| 명세에 고정할 내용 | 제안 범위 |
|---|---|
| 명시적 버전 선택 | 별도 `rx.python-execution-profile.v2`와 그 adapter/assembly 식별자로 opt-in. 기존 registration/library v1의 고정 입력·digest 의미와 reader 거절을 유지 |
| 불변 프로그램 선언 | SIMULATION, installation/Host/cell, 준비된 환경과 program artifact의 정확한 pin, signed template catalog 및 각 NodeContract를 결합. 경로·실행 파일은 runtime input이 선택하지 않음 |
| operation별 실제 입력 | 기존 HostExecutionService Prepare의 binding 및 canonical parameter bytes를 확인한 뒤, 기존 operation 준비 기록에 같은 원 신원으로 보존. Authorize는 같은 binding과 기존 permit/grant/epoch/expiry를 요구 |
| 실행·조회·복구 | 기존 Host prepare/authorize/journal, Python runner와 원 operation/invocation의 receipt/query/reconcile 경로를 재사용. 다른 원장·Task 실행기·전역 mutable input 또는 자동 재호출 없음 |
| 기존 범위 유지 | 이미 승인된 v2의 노드·입력 크기·SIM 제한 사용. 고정 library의 16개 input 제한을 늘리거나 모든 Part 입력을 나열해 우회하지 않음. registry는 F2′에 남음 |
| 수락 표시 | 제품 CLI receipt/조회에서 S2 9단계 게시 버전 및 SIMULATION을 권위 있는 구성/기록과 연결하여 표시. 테스트용 qualification/permit을 제품 권한으로 사용하지 않음 |

개정 승인 후 v1.1 절차로 profile 명세·호환성·영향과 해시를 먼저 고정하고, Docs → P(필요한
공통 경계만) → S 순서로 체크포인트 1을 구현한다. 기존 승인된 회귀와 호환성 검사를 적용하며
새 milestone/gate를 만들지 않는다. 체크포인트 2/3 구현에는 착수하지 않는다.


## 10. Profile 개정 승인 — 체크포인트 1 착수

사용자가 `rx.python-execution-profile.v2` 개정을 승인했다. Host는 Prepare bytes가 자기
qualification acknowledgement에 연결된 승인 집합에 속하는지 직접 대조한다. 입력 envelope·
binding·집합 대조는 공통 execution-v2 계약에 두며 Python profile에는 환경/program pin만 둔다.
F2′ adapter가 같은 의미를 재개정 없이 사용해야 한다. 추가 범위는 없다.

[공통 Host 입력 대조](../contracts/workflow-execution/v2/host-input-membership.md)와
[Python 고유 profile](../contracts/workflow-execution/v2/python-execution-profile.md)을 분리하고
v1.1 절차의 revision `2026-10-03.2` 및 파일 해시를 고정한다. F0 scratch는 merge하지 않고,
승인된 측정/계획 문서만 현재 develop 기반 구현 문서 브랜치로 복사해 이어 쓴다.
현재 구현 범위는 **체크포인트 1(N=1, S2 9단계, SIMULATION)**뿐이다. 정확한 head CI·DCO 후
P → S develop 병합, 제품 CLI 명령/receipt 제공, 중단 및 사용자 수락 대기 순서를 유지한다.
체크포인트 2/3은 아직 착수하지 않는다.

## 11. CP1 중간 연결 검증과 정상 5초 호출의 경계

사용자 요청에 따라 CP1 완료 전 중간 커밋을 남겼다. P `3d60fd2`, S `5efde01`은
서명·DCO 커밋이며 아직 병합하지 않았다. Host 자체 승인 집합/parameter bytes 대조,
기존 v2 cell coordination 선택, 원 Run에 연결된 보고서 읽기를 포함한다.

실제 Linux arm64 P/Executor/Host와 서명 S2 패키지의 제품 CLI에서 pick, load,
rotate-align, clamp, close-door의 5개 operation이 SUCCEEDED/RELEASED로 정산됐다.
95°/0.5°를 받는 rotation을 포함해 장치 호출에 도달했다. 5초 process 호출에서는
Host가 native submit의 반환까지 gate를 점유했고, 현재 Host RPC의 고정 3초 timeout과
ready source의 2초 freshness를 초과하여 P가 UNKNOWN/QUARANTINED,
Run을 RECOVERY_REQUIRED로 유지했다. 실제 장치 기록은 process까지 6건이다.
완료/해제를 강제하거나 원 호출을 재발행하지 않았으며, CP1 완료나 CP3 수락으로 세지 않는다.

실행 snapshot의 100ms 경계는 변경하지 않는다. [중간 CP1 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-03-f1-checkpoint1/interim-receipt.json)는 NOT_READY를 명시한다. amd64 에뮬레이션의 GetSnapshot 왕복
111.306791/114.148750ms는 arch와 실제 관측 상태를 구분해 CP1 receipt에 기록한다.
arm64 native에서는 RECOVERY_REQUIRED 상태의 같은 읽기 RPC가 5.581584/4.788416ms였다.
두 측정은 Run 상태/부하가 달라 동등 부하 비교가 아니다. 이 수치는 정상 5초 호출의
RPC timeout과 별도 관측이며, 그 원인을 단독으로 입증하지 않는다.

현재 [Host gate 계약](../contracts/v1.0/02_identity_durability_recovery.md)은 gate 안의
검사와 native 진입 사이에 fence/취소가 끼어드는 것을 금지하며, 진입한 호출이 반환하지
않으면 자원을 새 소유자에게 넘기지 못하게 한다. 승인된
[입력 경계](../contracts/workflow-execution/v2/host-input-membership.md)는 기존 freshness·epoch·
자격·admission 상한을 늘리지 못하게 한다.

**검토할 권고안 하나:** 공통 execution-v2에 기존 runner의 native 진입 확인과 완료 회수를
분리하는 경계를 명시한다. 최종 검증·SEND_ENTERED·native 진입 확인까지 같은 gate를
유지하고, 이후 동일 operation/invocation의 완료를 기존 Host journal/evidence 경로로
회수한다. 진행 중에는 자원을 보유하고 새 명령/재실행/인계 권한을 만들지 않는다.
진입 또는 완료의 근거를 잃으면 UNKNOWN을 유지한다. 100ms, 기존 freshness 및 timeout
상한을 늘리지 않고 Python profile의 환경/program pin과 자체 승인 집합 대조도 유지한다.
새 실행기나 독립 원장을 추가하지 않는다. 이 반환·완료 경계의 명세/호환성/해시는 사용자
검토 후 v1.1 절차로 고정해야 하며, 이 단락은 규범 개정이나 구현 착수 승인 자체가 아니다.

## 12. Native 완료 경계 개정 승인

사용자는 2026-10-03에 진입·완료 분리 개정을 승인했다. 공통 의미는 execution-v2에,
진입 확인 근거는 profile별로 두며 Python 근거는 Python profile에 고정한다. 외부 adapter는
공통 계약 개정 없이 자기 근거를 정의해 재사용한다. 명세·호환성·해시 revision
2026-10-03.3을 먼저 고정한다. 구현 범위는 5초 process를 포함한 CP1 9단계 정상 완료,
CI·DCO 후 P→S develop 병합과 제품 CLI 인계까지다. CP2/3은 시작하지 않는다.

## 13. CP1 develop 병합·제품 실행 완료 — 사용자 수락 대기

공통 계약 revision 2026-10-03.3은 [Docs #106](https://github.com/jack0682/rx_docs/pull/106)으로
명세·호환성·해시를 먼저 고정했다. Host는 자체 qualification 승인 집합과 실제 Prepare bytes를
대조하며, 공통 native entry/completion 경계를 사용한다. Python profile은 검증된 환경과
원 요청의 내구 기록 후 소유된 채널에서 받은 원 신원·요청 byte hash 일치 응답을 진입 근거로
정의한다. 같은 자식 프로세스의 완료와 회수만 관찰하며, Host의 기존 writer가 capture를
commit한 뒤 자원 보유를 해제할 수 있다. v2 전송 전 내부 reader marker 3을 기록하여
이 의무를 모르는 reader 2의 재개를 거절한다.

병합 전 제품 CLI Run은 [premerge summary](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-03-f1-checkpoint1/premerge-product-summary.json)에
기록했다. S2 9단계 모두 SUCCEEDED/RELEASED, FILE_SIMULATION 효과 9건, rotation
95°/0.5°, process 요청 5초·실측 5.000141초다. 저장 보고서 재열기는 동일 승인 bytes와
일치했고 원 request ID 재조회는 추가 효과를 만들지 않았다. 이 정상 실행 증거는
N-Part 또는 UNKNOWN 정산 수락을 대신하지 않는다.

P/S 전체 all-feature workspace test, all-target/all-feature Clippy, 실제 Python subprocess
6건, SDK 162파일 동기화와 기존 repository/contract 검사가 통과했다.
P [#76](https://github.com/jack0682/rx-platform/pull/76)과
S [#88](https://github.com/jack0682/rx-solutions/pull/88)에 commit-range별 범위를 기록했다.

실행 snapshot 100ms 경계는 그대로다. 기존 amd64 emulated와 arm64 native 왕복 실측은
arch·관측 상태를 분리해 보존한다. 두 관측을 동등 부하 성능 비교로 해석하지 않는다.
기존 실패 Run, UNKNOWN 및 거절 기록은 보존했으며 수동 완료나 DB 변경은 하지 않았다.

정확한 PR head의 CI·DCO를 확인한 뒤 P → S 순서로 develop에 병합했다.

| 저장소 | 검증한 PR head | develop merge |
|---|---|---|
| P #76 | 4ae6d58 | 00fd6599bd3be983ff3cdbead5ef9e5e2e023b80 |
| S #88 | 2d807ff | 889ba434772fc1335e7107ffbc572f9c21f4a418 |

두 merged head로 이미지를 다시 구성하고 새로운 전용 P/Host/Executor와 데이터 볼륨을
설치했다. 실제 제품 CLI Run 01a1010d-e81f-77a0-89af-52d5c41f538d는 9단계 모두
SUCCEEDED/RELEASED, SIM 효과 9건, process 실측 5.004813초로 완료됐다.
원 request 재조회는 효과를 추가하지 않았고 inspect --reports는 같은 승인 보고서를 열었다.

[최종 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-03-f1-checkpoint1/receipt.json),
[제품 CLI 원문 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-03-f1-checkpoint1/product-receipt.json),
[직접 실행·재열기 명령](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-03-f1-checkpoint1/RUN_CP1.md)에 head·arch·보고서 참조를 고정했다.
P/Host/Executor는 Docker daemon에 분리되어 실행 중이다. 사용자용 별도 object instance는
미사용으로 남겨 두었다. **사용자 CP1 수락은 아직 받지 않았으며 여기서 멈춘다.**
CP2/3, F2′/F3′는 시작하지 않았다.

## 14. CP1 사용자 수락 및 CP2 착수 — 2026-10-04

CP1 제품 CLI 명령은 사용자의 요청으로 Claude가 사용자 Mac에서 실행했고,
사용자가 결과를 수락했다. SIM/COMPLETED, 9/9
SUCCEEDED·RELEASED, 단계 순서, process 5초 완료, 장치 기록의 95°/0.5° 소비,
정확히 9줄 증가 및 inspect 일치를 확인했다고 보고했다.

CP2 범위는 **같은 Run의 N=3 S2 9단계 SIM 정상 운전**이다. 기존 P의
객체/slot 예약·budget·Part 전이와 Host/Executor 경로를 사용하고 제품 CLI를 연결한다.
사용자 추가 요청에 따라 모의 effects.jsonl에 원 operation/invocation ID를 기록한다.
이는 중복 효과를 P의 기존 Run/Part/operation 기록과 대조하기 위한 로그 상관 정보이며,
권한·승인된 parameter bytes·main(inputs)·wire 의미를 바꾸지 않는다.
원 ID는 runner가 이미 보유한 private request에서 전달한다. 새로운 실행 경로나
권한 원장은 추가하지 않는다.

CP2는 정확한 head CI·DCO 후 develop에 병합하고, 병합된 환경의 제품 CLI 명령을
제공한 뒤 중단한다. P 변경이 실제로 필요하면 P → S 순서를 지킨다.
CP3의 무응답 주입·UNKNOWN·정산 구현은 아직 시작하지 않는다.

## 15. CP2 같은 Run N=3 제품 검증

병합 전 실제 제품 CLI Run 01a1042c-247a-71ab-be6c-f30ce8768a41에서 3개 Part가
CONFIRMED_COMPLETED, 27개 operation이 SUCCEEDED/RELEASED로 완료됐다.
[병합 전 요약](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint2/premerge-summary.json)은
각 Part의 실제 object·slot·parameter·report 참조와 원 operation/invocation을 기록한다.
각 Part의 장치 순서는 S2 9단계와 같고 rotation은 95°/0.5°를 소비했다.
process의 선택값은 각각 5초다. inspect --reports는 같은 보고서를 열었고
원 요청 재조회 후 장치 기록은 27줄, 고유 operation/invocation 쌍도 27개였다.

P의 기존 예약·budget·Part·현재 권한/참조 검사를 사용했다. P와 Rust Host/Executor
변경은 0줄이다. S 변경은 제품 CLI의 순서 있는 객체 공급, runner의 두 로그용 ID,
모의 skill의 두 effect 필드, 관련 검증/사용 설명에 한정한다.
runner가 제공하는 ID는 원 private request의 상관 정보이며 승인 입력이나 권한이 아니다.
main(inputs)와 승인된 parameter bytes, 공통 계약/manifest/wire는 변경하지 않았다.
구버전으로 조립된 패키지의 runner digest 불일치는 실행 전 거절됐으며,
동일 소스 조립 도구로 재생성·서명한 패키지를 새 설치에서 사용했다.

S [#89](https://github.com/jack0682/rx-solutions/pull/89)의 정확한 head
214307154849dd9d188bd96d6fd26cf20a28ced1에서 CI·DCO를 확인한 뒤
develop dbbefebdccab0343dc4398b0848a07c6890aa122에 병합했다.
P는 변경 없이 이미 병합·검증된 00fd6599bd3be983ff3cdbead5ef9e5e2e023b80을 유지한다.

병합된 소스로 이미지를 다시 구성하고 전용 새 설치에서 제품 CLI Run
01a10436-2771-77fd-8ee7-3cd5d441bab0를 실행했다. 같은 Run의 3개 Part,
27/27 SUCCEEDED/RELEASED, Part별 순서 및 27개의 고유 operation/invocation 쌍 일치를
확인했다. 저장 보고서 재열기와 원 요청 재조회도 일치했고 추가 효과는 0건이었다.

[최종 CP2 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint2/receipt.json),
[제품 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint2/product-receipt.json),
[장치 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint2/effects.jsonl),
[직접 실행·조회 명령](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint2/RUN_CP2.md)을 남겼다.
사용자용 세 객체는 미사용이며 서비스는 Docker daemon에 분리되어 실행 중이다.
**CP2 사용자 수락 대기에서 멈춘다. CP3는 시작하지 않았다.**

## 16. CP2 사용자 수락 및 CP3 착수

CP2 제품 CLI 명령은 사용자의 요청으로 Claude가 사용자 Mac에서 실행했고,
사용자가 결과를 수락했다. SIM/COMPLETED, 3개 CONFIRMED_COMPLETED Part,
27/27 SUCCEEDED·RELEASED, Part별 순서·실제 객체·slot 3/4/5, 신규 27행의
operation/invocation 27쌍 일치 및 보고서 재열기가 확인된 것으로 보고됐다.

CP3는 §8의 결과 전달 손실 경로만 진행한다. N=3을 ECC_51 / ECC_99 / ECC_51로
구성하고, Part 2 rotate-align에서 실제 native 진입 후 P로의 receipt/result와
같은 operation의 evidence 전달을 보류한다. Host·worker와 보통의 source 관측은
유지한다. P 상태나 결과를 조작하지 않는 외부 SIM 전송 제어를 사용한다.
제품 CLI에서 UNKNOWN·실제 자원/slot 보유·Part 3 미시작을 확인한 뒤 통신을 복구하고,
원 operation/invocation의 기존 조회·정산으로 Part 2 잔여 단계 및 Part 3을 완료한다.
재발행과 새 operation을 통한 대체는 하지 않는다.

혼합 모델의 기존 치수·힘·process 시간은 유지하고, rotation용 object 속성은
서명 패키지 데이터로 구분한다. 각 Part의 실제 선택값과 원 ID를 장치 기록 및
재열린 Run/report/parameter 참조에 대조한다. 다른 항목은 추가하지 않으며
CI·DCO 후 P→S develop 병합과 제품 CLI 인계 뒤 사용자 수락 대기에서 멈춘다.

## 17. CP3 혼합 모델 결과 손실·원 호출 정산 검증

P의 기존 Run 조회에 현재 resource holder와 원 reconciliation 기록을 노출하고,
CLI에 UNKNOWN에서 관측을 반환하는 옵션과 해당 Run의 slot 보유 조회를 연결했다.
외부 SIM gRPC 중계기는 payload를 재작성하지 않고 실제 native 진입 응답을 받은 뒤
원 receipt/result·evidence 전달만 보류한다. Host/worker, 보통 source 조회, 기존
qualification·fence·grant 경로는 유지하며 결과나 P/Host DB 상태를 조작하지 않는다.

첫 시도에서는 원 rotate-align의 UNKNOWN→동일 invocation 성공·해제·정산 COMPLETE까지
성립했으나 다음 clamp가 native 진입 확인 응답을 받기 전에 permit 시간을 소진했다.
[보존한 첫 시도](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/preserved-first-attempt.json)에
1초 permit, Host Prepare 시점, 파일 wall time을 현재 boottime offset으로 변환한
약 3ms 잔여 시간 추정과 그 가정을 분리해 기록했다. 이 실패를 완료 처리하거나 재발행하지 않았다.
기존 sender가 Prepare와 Authorize를 다른 순회에서 처리하던 대기를 제거하여,
준비 receipt를 기록한 직후 한 번의 Authorize를 이어 처리하도록 수정했다.
두 단계 모두 writer의 현재 권한 검사를 새로 거치며, 불확실한 전송은 계속 원 receipt만 조회한다.
permit/freshness/100ms 상한과 공통 계약·wire 의미는 변경하지 않았다.

수정 후 [병합 전 제품 검증](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/premerge-summary.json)에서
같은 Run의 ECC_51/ECC_99/ECC_51 순서로 Part 2 rotate-align이 UNKNOWN·보유 상태가 됐고
Part 3은 생성되지 않았으며 장치 기록은 12행이었다. 통신 복구 후 동일 operation/invocation이
SUCCEEDED/RELEASED 및 reconciliation COMPLETE가 되었고 잔여 단계와 Part 3까지
27/27 완료했다. 원 target Authorize 전달은 1회이며 모든 장치 ID 쌍이 제품 기록과 일치했다.
Run/report를 다시 열고 원 request를 재조회해도 추가 효과가 없었다.

| Part 모델 | grasp width | grip force | rotation/tolerance | process |
|---|---:|---:|---:|---:|
| ECC_51 | 47mm | 25N | 95°/0.5° | 5s |
| ECC_99 | 77mm | 17.5N | 185°/0.3° | 7s |
| ECC_51 | 47mm | 25N | 95°/0.5° | 5s |

각 값은 실제 장치 기록의 소비 값과 일치했다. 모델 변경은 패키지 데이터이며
레이저/ECC 이름 분기를 코어에 넣지 않았다.

정확한 PR head CI·DCO를 확인하여 [P #77](https://github.com/jack0682/rx-platform/pull/77) →
[S #90](https://github.com/jack0682/rx-solutions/pull/90) 순서로 develop에 병합했다.

| 저장소 | 검증 head | develop merge |
|---|---|---|
| P | c511ab4d4412b7ae8ab49c4b7384d44be383ea67 | 4fd1c16631d819b9eb776de92d7fc366af4439f3 |
| S | ce7ed3aa64d4175f43123b559ec74297a0a6ba7f | 45dc6eac4befbffd38615575477152baa5361411 |

병합된 소스로 이미지를 다시 구성하고 전용 새 설치에서 Run
01a1066b-a7c2-73a3-b77a-4c1500330421에 같은 전체 fault·복구 절차를 실행했다.
원 operation 01a1066c-075e-7362-ba64-d31c8a6c46ce / invocation
1aa0619a-6362-407e-91aa-beafdff2de32가 UNKNOWN·보유를 거친 뒤 같은 ID로
SUCCEEDED/RELEASED 및 reconciliation COMPLETE가 됐다. Part 3은 UNKNOWN 중
시작하지 않았고, 복구 후 3개 Part와 27개 효과가 완료됐다.
원 Authorize 전달 1회, 고유 ID 쌍 27개, 혼합 선택값 일치 및 Run/report 재열기를 확인했다.

[최종 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/receipt.json),
[UNKNOWN 제품 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/unknown-product-receipt.json),
[완료 제품 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/completed-product-receipt.json),
[장치 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/effects.jsonl),
[사용자 실행·조회 절차](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/RUN_CP3.md)를 남겼다.
사용자용 혼합 세 객체는 미사용이며 네 서비스는 Docker daemon에 분리 실행 중이다.
**CP3 사용자 수락 대기에서 멈춘다. F1′ 전체 수락은 아직 주장하지 않는다.
F2′/F3′는 미착수다.**


## 18. F1′ 사용자 수락 완료·종료

CP3 명령은 **사용자의 요청으로 Claude가 사용자 Mac에서 같은 request ID로 실행했고,
사용자가 결과를 명시적으로 수락했다.** 실행 주체(Claude)와 수락 주체(사용자)를 구분한다.
이로써 **체크포인트별 제품 CLI 검증과 사용자 수락을 CP1·CP2·CP3 모두 완료하여
F1′을 닫는다.** 자동 검증 결과를 사용자 수락으로 대체한 것이 아니다.

사용자 산출물은 로컬 `rx_ws/.build/framework-f1-checkpoint3/live3/claude-check/`에 있다.
[수락 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f1-checkpoint3/user-acceptance.json)에 사용자 보고,
읽기 전용으로 대조한 결과, 원 파일별 SHA-256을 구분해 남겼다.
사용자 Run은 `01a106b4-968e-752f-897a-7a2f0294f165`, request는
`f071c378-3f18-4bfc-a1f0-4a4d42d6a026`이다.

- 최초 run은 사용자 보고상 rc=2였다. 저장된 제품 기록에서 Part 2 rotate-align만
  UNKNOWN/QUARANTINED이고 자원 holder가 원 operation임을 확인했다.
  Part 2 slot은 consumed=false, Part 3 slot은 part=null이며 Part 기록은 2개다.
  relay는 BLOCKED/NATIVE_ACCEPTED다. 이 시점의 장치 효과 12행 및 185°/0.3° target 행
  존재는 사용자 요청으로 Claude가 관측한 결과로 보고됐다.
- 통신 복구 후 같은 Run이 COMPLETED이며 3개 Part가 CONFIRMED_COMPLETED,
  27개 operation이 SETTLED/SUCCEEDED/RELEASED다. 원 operation
  `01a106b4-f663-7342-828f-529ae37c5999`와 invocation
  `1883b13c-7c9c-49cc-b6db-73d6d5164af8`가 유지되고 reconciliation은 COMPLETE다.
- 신규 27개 장치 행의 operation/invocation 쌍이 제품 기록과 모두 일치하고 target 효과는
  한 행뿐이다. ECC_51/ECC_99/ECC_51의 값과 Part별 9단계 순서도 일치했다.
  재열린 제품 result는 snapshot_id와 observed_at.ticks_ns만 달랐고 승인 보고서는 같았다.

이 수락은 기록된 SIM 경로에 대한 것이다. 기존 실패·수정·이관·parking 근거는 보존한다.
**F2′·F3′는 시작하지 않는다. 다음 사용자 목표가 올 때까지 추가 구현이나 계획을 진행하지 않는다.**

Superseded by the F2′ goal (2026-10-04)

위 대기는 후속 목표가 설정될 때까지만 유효했다. F2′ 목표가 현재 범위를 결정하며,
F3′는 계속 미착수다.

## 19. F2′ CP1 — 외부 adapter 계약 검토

2026-10-04 후속 F2′ 목표를 적용했다. CP1은 **Docs만 작성하고 사용자 수락을 기다린다**.
F1′ 종료와 그 SIM 근거는 유지한다. CP3 실행 주체 정정 `cc121ef3`를 보존하고,
CP1·CP2의 실행 주체(사용자 요청으로 Claude)와 수락 주체(사용자)도 별도 커밋으로 정정했다.
수락 전 검증 receipt의 당시 NOT_RUN/READY 상태와 측정값은 덮어쓰지 않았다.

[CP1 계약 제안](f2_adapter_registry_cp1.md)에 package identity/서명/설치·명령/관측 타입,
Host 소유 protocol과 evidence 조회·재시작 거절 조건을 고정했다.
**원 완료 증거와 현재 custody 증거가 모두 필요하며 adapter 재시작만으로 UNKNOWN을 해제하지 않는다.**
unclamp 독립 노드는 포함하고, 보유 중 package 교체는 거절하며 hot replacement는 parking으로 보냈다.
공통 registry 자체의 P/S 비용과 B1 동결 후 S1 외부 작성 비용을 분리하여
F0의 6파일/63행/12명령과 비교한다. 아직 registry 구현량·S1 확장량은 미측정이다.

현재 제안은 common execution-v2의 provider별 증거 확장점을 사용하고 기존 Python v2는
다른 finite skill에 그대로 사용한다. 기존 계약/manifest/trait·P/S 제품 코드 변경은 없다.
새 ledger/권한/상태기계 또는 seam 증가가 필요해지면 구현하지 않고 중단·질문한다.
[RUN_CP1](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f2-checkpoint1/RUN_CP1.md)과
[기준선 receipt](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f2-checkpoint1/baseline.json)를 남긴다.
**CP1 사용자 수락 전 CP2를 시작하지 않는다. 자동 검증 PASS는 수락이 아니다.**

## 20. F2′ CP1 조건부 수락·CP2 선행 점검 — 2026-10-05

사용자가 CP1을 세 조건으로 수락했다. CP2 외부 저작 전에 코드 변경 없이 제품 CLI로
같은 Run의 두 Host 분산 실행을 입증하고, unclamp 전 지지는 기존 관측/guard/로봇 primitive로만
표현한다. 불충분하면 중단·질문하며 multi-Host 수정은 registry 비용에 포함하지 않는다.
CP3에는 Host B clamp UNKNOWN 동안 Host A 미진행과, 완료 기록 전 adapter 종료 후
UNKNOWN·무재발행·Run 미진행을 유지하는 별도 미완료 사례를 포함한다.

Codex가 설치 제품 `rx-hostd inspect`로 지원 guard 선행 검사를 실행했다.
원 Python 설정 rc=0, 복사한 binding에 `gripper.part_held`를 추가한 설정 rc=1
(`Python execution template bindings differ`)이었다. 기존 Python builtin의 native source는
ready/sim/ready에 한정되고 S2의 지지 확보·unclamp·인출은 unload 내부에 함께 있다.
조건 2에 따라 여기서 구현을 중단한다. **두 Host 실제 Run은 아직 미검증**이며
registry 또는 S1 작성, P/S 수정, CP3 주입은 하지 않았다.
[근거·재현·단일 권고안](f2_cp2_prerequisites.md)을 검토 후 다음 범위를 결정한다.
실행 주체는 Codex, CP1 수락 주체는 사용자다. 이번 선행 검사는 CP2 수락이 아니다.

## 21. 지원 범위 결정 — 순서만 사용하는 SIM 제한

사용자는 S2 예제 unload의 acquire-support/withdraw 분리만 별도 커밋·별도 비용으로 허용했다.
Python Host 관측 경로 연결은 허용하지 않았다. 이번 SIM의 unclamp는 **같은 Part의
acquire-support가 SETTLED/SUCCEEDED인 뒤 기존 Run 경로로 진행하는 순서 보장만 사용한다**.
fresh support observation은 없으며 실제 셀에 필요한 보장보다 약하다. 문서·receipt에 이를
명시하고 registry 완성 후 gripper 지원 관측을 선언·연결해 unclamp guard로 쓰는 후속을 보류한다.

S2 패키지 분리 비용은 registry 비용과 분리한다: skill.py +18/−2행, README +16행,
패키지 동작 테스트 101행(별도). Host/P/Executor 구현 변경은 0행이다. 테스트는 실제 장치
관측이나 Run 순서를 입증하지 않는다. 실제 Run의 settled 순서·두 Host dispatch는 별도로 확인한다.
조건 1(코드 변경 없는 두 Host Run, 실패 시 중단)과 조건 3(CP3 완료 전 종료 negative case)은 유지한다.
S1 외부 저작은 두 Host 선행 검증 전 시작하지 않는다.

## 22. 코드 변경 없는 두 Host Run 선행 검증

Docs #115 → S #91 순서로 범위 기록·패키지 분리를 병합했다. S의 별도 scenario commit은
`2c6b4cb`, develop merge는 `438d4371a63289662c86ff1822f3d524f66a1811`이다.
정확한 head CI·DCO가 통과했다. 이 패키지 분리는 registry 비용이 아니다.

Codex가 기존 F1 P `4fd1c16` / S runtime `45dc6ea` 이미지로 새로운 SIM 설치를 구성했다.
두 Host 모두 기존 Python builtin이고 하나의 S2 9단계 Run에서 A는 clamp 이외, B는 clamp를
수행한다. 이는 registry 없이 기존 P/Executor dispatch를 검증하기 위한 별도 선행 측정이다.
새 package 구현·core patch 없이 Host별 signed template/catalog·설치 configuration만 변경했다.
설치용 서명에는 기존 test-only fixture signer를 사용했으며 S1 외부 저작 경로의 증거로 세지 않는다.

제품 CLI Run `01a10a14-0c8c-72b7-8810-d08b5a0440cf`는 rc=0/COMPLETED, 1 Part,
9개 SETTLED/SUCCEEDED/RELEASED operation이다. 실제 effect 순서 A 3 → B clamp → A 5와
고유 operation/invocation 9쌍이 Run 기록에 일치했다. 제품 CLI inspect --reports 재열기도 같다.
두 Host 바이너리 SHA-256은 동일하고 P/Host/Executor source 변경은 0줄이다.
[명령·receipt·제한](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-two-host/RUN.md)을 남겼다.
이 검증은 split-support 11단계·registry·S1·UNKNOWN/CP3의 수락을 뜻하지 않는다.
fresh support observation은 없고, 이후 SIM unclamp에는 같은 Part의 완료 순서만 사용한다.
사용자 CP2 수락은 아직이며 다음 작업은 공통 registry 구현이다.

## 23. F2′ CP2 — 외부 S1 등록·혼합 N=3 정상 운전

**사용자 수락 대기에서 멈춘다.** Codex가 명령을 실행했고 아직 사용자는 CP2를 수락하지 않았다.
[RUN_CP2](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/RUN_CP2.md)에 사용하지 않은 수락용
ECC_51/ECC_99/ECC_51 객체와 제품 CLI 명령을 제공한다. SIM이며 fresh gripper support
observation은 없다. 같은 Part의 acquire-support SETTLED/SUCCEEDED 이후 unclamp 순서만 사용한다.
실제 셀에 필요한 보장보다 약하며, 기존 parking의 registry observation/guard 후속은 유지한다.

### 병합과 B1 동결

S #92의 공통 registry를 `54ddf257`에 병합했다. 설치 CLI에 없던 기존 API 전달·qualification
서명 입력 생성만 최소로 노출한 P #78 → S #93은 각각 `22d8b18d` / `0fed87b5`에 병합했다.
모든 정확한 PR head CI·DCO를 확인했다. 새 권한·원장·P API·공통 계약은 추가하지 않았다.
공유 SDK 162개 파일은 P export와 같은 바이트이며 engine seam은 18쌍/31참조 그대로다.
S2 예제 분리 S #91은 이 비용에서 별도다.

[B1](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/B1.json)에 merged source, 설치 이미지,
SDK/client/Host 해시를 동결한 뒤 S1 저작을 시작했다. 외부 디렉터리에서 설치된 package tool,
SDK/client, 공개 export 데이터와 OpenSSL만 사용했다. P/S source checkout을 mount하거나
import하지 않았고 Cargo/test signer를 호출하지 않았다. 설치 API의 낮은 수준 JSON 조립과
서명·qualification 입력은 작성 helper로 계상했다. F3′ 저작 UX 작업은 시작하지 않았다.

### 실제 결과

동일 B1 rx-hostd에서 등록 S1 inspect rc=0, 미등록/unsigned/tampered는 각각 rc=1이었다.
S1 프로그램은 clamp/unclamp와 typed `chuck.clamped`를 패키지로 선언한다. Robot은 기존
Python builtin, chuck은 registry provider로 같은 Run을 수행했다.

Run `01a10ac1-d3af-728b-a228-a7b6ea06565d`는 3개 Part, 33개
SETTLED/SUCCEEDED/RELEASED operation으로 COMPLETED다. 장치 33행의 고유 operation/invocation
33쌍이 Run 기록에 일치하며 Host B의 clamp/unclamp는 6개다. Part별 11단계 순서와
47/77/47 mm, 25/17.5/25 N, 95/185/95°, 0.5/0.3/0.5°, 5/7/5 s가 일치했다.
지원 확보와 unclamp는 같은 Part에 속하고 순서도 일치한다. report 재열기의 Run/Part/work와
승인 보고서가 같았다. P에서 `chuck.clamped`의 host/sim-b, boolean/v1, usable=true 관측을 확인했다.

두 Host의 SHA-256은 B1과 같은 `1332000944c7d4b4fc1c615c117cedb77d9c8c4d0291e6f54f05282b140538b7`이다.
**S1 저작 구간의 P/S diff는 각각 0파일/+0 −0행**이다. 아래 공통 개발 비용을 숨겨서 0이라고
부르는 것이 아니다. [제품 요약](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/summary.json)과
[원문·파일 해시](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/sha256.json)를 보존했다.

### 비용 — 공통 구현과 외부 작성 분리

| 범위 | 파일 / 물리 행 | 명령·해석 |
|---|---|---|
| F0 S1 기준선 | 6 / 63 | 12회. 독립 backend 실패 + Python 대안; 전체 운전 경로가 아니었다 |
| 공통 registry + 최소 설치 저작 연결 P | 2파일 / +38 −1 | 코드 1파일 +25 −1, 설명 1파일 +13. 기존 qualification 서명 메시지 export |
| 공통 registry + 최소 설치 저작 연결 S | 25파일 / +2497 −2 | runtime·CLI·SDK·테스트·설명·빌드 포함. 파일별 값은 B1에 분리 기록 |
| S2 별도 scenario 분리 | 3파일 / +135 −2 | skill +18 −2, README +16, 테스트 +101. S1/registry 비용과 구분 |
| S1 runtime 원본 | 1파일 / 87행 | 외부 adapter.py. 설치 SDK와 제공된 S2 모델을 사용하며 core source import 없음 |
| 외부 저작 전체 원본 | 22파일 / 1296행 | S1 원본 + launch 선언 + workflow composition + signing/provision/review helper와 실패 재개 helper 포함 |
| 외부 시도 전체의 기록된 leaf 명령 | 725회 | setup 328회와 나머지 397회를 포함. 최종 설치 시도 157회(setup 80/나머지 77) |
| S1 고유 core diff | P/S 각각 0파일 / +0 −0 | B1 이후 core 수정·binary 교체 없음 |

[세부 cost](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/cost.json)는 파일별 행 수와 네 시도별
명령·rc를 남긴다. 중첩 helper 실행은 leaf와 중복 합산하지 않고 따로 표시했다. 임의의 읽기 전용
진단·검색·편집·Git/문서 검사 호출은 이 명령 계수에 포함하지 않아 총 사람 작업량의 하한이다.
nonzero에는 의도한 거절도 있으므로 모두 오류라고 세지 않는다. 제공/복사 SDK·client·S2 환경과
helper에서 생성한 JSON·package·report는 별도 산출물이며 원본 행에 이중 합산하지 않는다.
F0와 작업 범위가 다르므로 비용 감소율을 주장하지 않는다. 실제 수동 저작/설치 부담은 크다.

### 실패 보존과 한계

한 설치는 외부 보고서 helper의 필드 오기로 validator 정책을 수정·재기동한 뒤 Host continuity가
증명되지 않아 자격화 전 멈췄다. 다음 Run은 venv/lib64 심볼릭 링크를 복사에서 펼친 탓에 기존
verifier가 환경을 거절했고, 또 다른 Run은 Part 2 Python 진입 대기 중 만료 가까이에서 멈췄다.
각 UNKNOWN operation과 장치·원장을 보존하고 Docker pause로 메모리/상태를 남긴 채 부하를
분리했다. 권한 시간 경계, 결과, 자원 소유, core 코드는 수정하지 않았다. 마지막 정상 검증은
별도 SIM 장치/설치이며 앞선 UNKNOWN을 정산했다고 주장하지 않는다.
[보존 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-checkpoint2/preserved-attempts.json)을 확인한다.

수동 API 응답 형태·서명 policy·환경 복사·호출 pacing의 저작 마찰은 F3′ 근거다. 이 사전 검증은
독립 외부 개발자의 시연, physical support, 임의 부하 성능, S1 failure/restart 검증이 아니다.
CP3에는 Host B UNKNOWN 동안 Host A 미진행, 원 완료+현재 custody로 정산하는 회복 가능 사례,
entry 후 durable completion 전 종료해서 UNKNOWN·무재발행·미진행을 유지하는 별도 사례가 남는다.
**여기서 멈추고 CP2 사용자 수락을 기다린다.**
