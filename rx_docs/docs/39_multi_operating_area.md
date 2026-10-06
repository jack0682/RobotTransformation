# 39. 컴파일된 다중 운영 영역과 교차 권한 거절

상태: G4 구현·직접 검증 완료, 독립 수락 대기. 운영 배포·실물 자격 주장이 아니다.

## 문제와 변경

G3의 공개 F6 규약과 봉인된 수신 API는 이미 여러 권한을 담을 수 있었지만 실제 연결은
한 영역뿐이었다. G4는 컴파일된 두 영역을 각자의 키·발급자·역할·프로그램·규칙에 연결한다.
같은 작업 관리자가 두 프로그램을 동시에 소유하는 Plan에서 선택된 영역의 판단만 작업
결과 저장으로 이어진다. 다른 영역의 정상 결정은 권한이 되지 않는다.

| 항목 | SUPPORT (A, G3 유지) | COMPACT (B) |
|---|---|---|
| 영역 | development/support-area | development/compact-support-area |
| 발급자 | development/support-gap-judge-v1 | development/compact-support-judge-v1 |
| 키 ID | rx/development-work-judge-v1 | rx/development-compact-judge-v1 |
| 프로그램 | rx/status-work-http | rx/status-compact-work-http |
| 역할 | work/support-gap-report | work/compact-support-gap-report |
| 요구 native packages 상한 | 10000 | 2000 |
| 요구 support profiles 상한 | 64 | 8 |
| TTL 상한 (ms) | 30000 | 15000 |

두 규칙 모두 입력에서 부족분을 계산하는 비작동 보고서만 허가한다. 더 좁은 B 규칙은 개발용
분리 사례이며 실제 현장 정책의 적합성을 입증하지 않는다. 승인 결과는 **F10**의 기존 원자적 결과·소비 기록 경계로 들어간다. 출력은 현재 허가가 아닌 역사다.

## 신뢰 근원과 검사 순서

영역 목록은 platform 원본 Rust 안의 고정 레코드다. 사용자 설정·환경변수·영역 JSON은
항목이나 키를 추가하지 못한다. 추가에는 소스 검토와 재빌드가 필요하다. 서명 도구는 제공된
개인키의 공개키와 일치하는 컴파일 항목을 고르고, 키 ID·발급자·규칙을 검사한 뒤 서명한다.
호스트에는 개인키나 서명 명령이 전달되지 않는다. G2 배포 키와 A/B 판단 키는 서로 다르다.

수신 측은 봉인된 소유자의 **program**으로 키와 역할을 고른다. 요청 Task의 area나 응답의
주장으로 키를 고르지 않는다. 각각의 recipe에 그 영역의 권한 하나만 들어간다. 기본 catalog는
계속 anchor가 없으며 G3의 명시적 단일 영역 동작도 유지된다.

검사는 층마다 다르다. adapter의 key/area/role 사전 거절은 아직 검증하지 않은 주장에 대한
거절이다. F6는 정확한 현재 challenge/context를 먼저 비교하고 그 다음 서명을 검증한다.
따라서 모든 교차 공격의 첫 실패가 서명이라고 주장하지 않는다. 별도 키는 추가적인 분리다. 서명은 판단 프로그램이 실제 규칙을 실행했다는 증명이 아니다.
자기 영역의 키 보유자가 규칙 밖에서 직접 서명하는 경우까지 규칙 실행을 증명하지 않으며,
수신 측은 신뢰한 키의 범위와 현재 context를 검증한다.
대상 영역의 정확한 challenge를 다른 영역 키로 서명하고 대상 키 ID를 주장하면 서명에서
거절된다. 서명된 공개 DTO, 과거 assessment, 보고서에는 살아 있는 허가 생성 능력이 없다.

## 두 개의 서로 다른 개수·중복 규칙

컴파일 카탈로그는 **맵을 만들기 전에** 1..8개 선언과 영역·발급자·key-id·공개키·program
유일성을 검사한다. 중복을 맵의 마지막 값으로 덮어쓰지 않는다. 0/9개와 중복 5종은 각각
이름 있는 원인으로 거절된다. 이 함수에 임의 레코드를 주어 검증해도 제품 catalog에 등록되지는
않는다. 실제 출하 구성과 실제 다중 프로세스 검증 범위는 두 영역이며 8영역 실물 지원 주장이 아니다.

일반 F6 Policy의 기존 1..8 authority 제한은 별개다. 같은 영역·발급자에 키 여러 개가 있는
저작 정책도 계속 허용된다. G4의 카탈로그 유일성을 F6 전체로 확대해 기존 계약을 축소하지 않았다.

## 남아 있던 단일 영역 상수 여덟 개

| G3 이름 | G4 상태와 살아 있는 경로 |
|---|---|
| KEY_ID | SUPPORT 별칭 유지. catalog program은 sealed subject의 레코드 key_id 사용 |
| ISSUER | SUPPORT 별칭 유지. recipe·판단자·폐기 검사는 선택된 레코드 issuer 사용 |
| AREA | SUPPORT 별칭 유지. 판단자 규칙은 선택된 레코드 area 사용 |
| ROLE | SUPPORT 별칭 유지. registered.rs의 별도 고정 ROLE 제거; owner program의 role 사용 |
| PROGRAM | SUPPORT 별칭 유지. daemon의 선택·작업·resume 지원 검사는 catalog 조회 |
| MAX_TTL_MS | SUPPORT 별칭 유지. challenge policy와 판단자 모두 선택된 max_ttl_ms 사용 |
| RULE | SUPPORT 별칭 유지. 판단·거절 출력은 선택된 rule로 영역 식별 |
| PUBLIC_KEY | SUPPORT 별칭 유지. recipe·도구는 선택된 public_key 사용 |

기존 `development_work_program` 호출은 명시적으로 SUPPORT를 선택하는 호환 함수다.
무관한 저작 library program의 기존 provider fallback은 유지된다. catalog program이
fallback에 들어가지 않는 것은 모든 항목의 실제 선택 레코드와 B의 별도 역할·키 시험으로 고정했다.

## 관측 증거와 경계

최종 명령·원시 출력·해시·호환 commit 조합은 아래 증거 묶음에 연결한다. 설명은 검사를
대체하지 않는다. 수정 전후 주입 거절, 동일 정상 결정의 자기 영역 통과와 반대 영역 거절,
각자 규칙의 상한, Task 영역 조작, foreign role/program, 대상 요청에 대한 다른 키의 서명을
별도로 관측한다. 각 Plan에는 A/B 프로세스 둘이 있고 한 관리자가 소유한다. CLI는 한 번의
호출에서 작업 요청 하나를 처리한다. 여러 작업을 위한 network routing/monitor는 제공하지 않는다.

F6 wire 형태는 바뀌지 않았다. SDK 115파일은 원본에서 재생성한다. O2의 Prepared 위조
문서 시험은 네 필드를 모두 제공하며 오직 E0451(private fields)로 거절된다. 누락 필드 오류에
기댄 이전 시험을 그대로 근거로 삼지 않는다.

| 남은 경계 | 의미 |
|---|---|
| 개발용 판단·키 보관 | 실제 안전·품질·장비 자격, 운영용 custody/rotation 미확립 |
| 명시적 checkpoint | 연속 감시·온라인 폐기 조회·네트워크 판단 서비스 없음 |
| 수신·저장 간격 | 협력 mailbox lock과 F6 ledger lock은 SQL commit까지 유지 |
| 시간·자체 보고 | F10의 post-cut IO 중 TTL 진행, HTTP 자체 보고의 as-of 시점 잔여 유지 |
| 비협력 파일 쓰기 | 임의 외부 publisher의 교환 파일 변경을 전역적으로 순서화하지 않음 |
| G2 신뢰 경계 | 설치된 Rust/OS 신뢰; 전체 상태 rollback/deletion 미탐지, offline 폐기 최신성 미확립 |
| G1/F9 | 강제 종료 시 상속 fd 수명·UNKNOWN 및 명시적 회복의 기존 경계 유지 |
| 실물·배포 | 수행하지 않음. main 승격 없음 |

## 실패 기록

첫 daemon 빌드는 새 보조 함수와 tokio main 속성 배치 실수로 E0728이 났고 위치를 바로잡았다.
그 뒤 실제 디스크 부족으로 macOS 검사와 판단자 빌드가 ENOSPC로 중단됐다. 원시 실패 로그를
보존하고 재생성 가능한 target만 정리했으며, debug 심벌과 incremental 저장을 줄여 저장소별로
빌드했다. 테스트 thread를 직렬화하거나 시험을 제외하지 않았다. 직후 Docker 이미지 blob EIO는
제품 시작 전 환경 실패이며 엔진 재시작 후 같은 이미지 ID를 확인했다. 제품 수정으로 부르지 않는다.

처음 역할 변조 fixture는 살아 있는 불변 request를 바꾸어 mailbox 충돌이 먼저 거절했다(저장0).
판단 규칙 자체를 검증하도록 별도 공격 입력 사본에서 issuer를 실행하도록 fixture를 수정했다.
원래 거절과 실패 단언은 그대로 남긴다. 이 사건들을 G3의 원인 미확정 E0463 메타데이터 사건과
동일 원인으로 합치지 않는다.


## 직접 실행 결과

macOS 전체 workspace: platform **407 통과 / 0 실패 / 16 ignored**, solutions **388 / 0 / 17**.
기존 G3의 405/386보다 각각 둘 늘었으며 ignored 수는 같다. 두 workspace clippy 및 repository
검사, standalone judge clippy, SDK 재생성 일치도 통과했다. O2의 raw rustdoc 오류는 E0451의
네 private field이며 E0063 누락 필드는 없다.

실제 Linux 다중 영역 passage **22장면**은 한 Plan의 두 status 프로세스를 띄워 관측했다.
정상 A/B는 각각 work row 2개(파생 결과+소비 기록)를 commit했다. 동일 서명 결정 바이트를
반대 영역에 제시한 두 장면은 issuer-scope에서 거절됐고 row 0개다. 대상 challenge를 외부에서
다른 영역 키로 서명한 두 장면은 signature-mismatch에서 거절됐다. 그 외부 서명은 OpenSSL로
해당 외부 키에 대해 검증했고, 메시지 바이트는 실제 Rust canonical signing_message 출력과
일치시켜 JSON 인코딩 실패와 키 불일치를 혼동하지 않았다.

G3의 단일 영역 12장면은 전부 통과했고 기존 호스트 자체 발행 거절 3장면 before/after는
바이트 단위로 같다. A의 key/issuer/area/role/kind/max-TTL/policy-digest와 owner program/catalog
identity도 G3 기준과 같다. 수정 전후 설정 영역·키 주입 및 파일+환경 주입은 모두 거절된다.

고정 runtime image의 native payload 위에 이번 소스에서 빌드한 Rust 바이너리를 별도로 마운트해
실행했다. 전체 native image를 새로 빌드하거나 운영에 배포했다는 주장이 아니다. runtime image
59020개 파일과 코드 저장소 커밋 트리에서 B 개인키는 검출되지 않았고, 최종 두 바이너리에는
A/B의 PEM·DER·seed·hex/base64 형태가 없다. 이는 특정 키에 대한 범위 검사다.


추가로 마지막 G1 회귀의 첫 Host 빌드는 완료 기록 없이 래퍼 exit120으로 끝났다. 당시 디스크는
118MiB까지 내려갔고 Docker가 실행 중/종료됨을 서로 다르게 보고했다. Python 예외 원문은
남지 않았으므로 ENOSPC가 그 exit120의 직접 원인이라고 확정하지 않는다. 아직 G1 실행 장면은
시작하지 않았으며 원본 target·명령을 보존했다. 멈춘 Docker 종료를 복구하고 같은 Rust parent에
DEBUG=0/INCREMENTAL=0만 적용한 빌더로 원본 G1 스크립트·단언을 바꾸지 않고 한 번 새로
실행해 통과했다(11 lifecycle 장면, unfiltered Host 50회 실패0). 이 빌드 프로파일 변경은 테스트 thread 직렬화나 RX 자원 집행의 근거가 아니다.


기존 아홉 경계는 현재 소스로 모두 통과했다: 등록 library, resident, release origin, resource,
manager loss, work use, dependency replacement, support limits, storage lock. resident는 resource
스크립트에 포함된다. storage lock의 첫 빌드 exit120/예외 미포착과 compact 빌더의 새 통과는
서로 다른 관측이다. `support_limits` 원시 결과의 `LOCK_LIFETIME_UNRESOLVED`는 보존한 F12
스크립트의 역사적 라벨이며, G1의 현재 독립 결과를 덮어쓰는 최종 분류로 읽지 않는다.

## 호환 commit 조합

| 저장소 | 기여 commit | develop 병합 |
|---|---|---|
| [platform PR23](https://github.com/jack0682/rx-platform/pull/23) | `38c49ebab0887eff81b85b1d76b5b2c8210d0d9f` | `7d1a31fac35ee84c4714efe7c1ebd0cce8616663` |
| [solutions PR39](https://github.com/jack0682/rx-solutions/pull/39) | `314a50ee211bf5a79f4fb7e5765979af4d2d7ce5` | `6b92bab6af35dbbca3c3fdd16225a58e84ca26aa` |

각 기여와 병합 tree가 같고 OpenPGP·DCO를 검증했다. 두 PR의 첫 CI는 각각 Linux
408/0/16, 432/0/20이며 전체 main은 바뀌지 않았다. 이 문서의 commit을 위 조합과 함께
사용한다. [원시 증거와 재현 안내](../references/multi_operating_area_2026-09-25/README.md)가
실제 명령·결과·실패·바이너리 및 이미지 해시를 잇는다.
