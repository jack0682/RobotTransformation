# G3 개발용 오프라인 운영 영역 판단자

2026-09-25. 상주 Host가 승인하는 대신, 별도 판단자가 자기 규칙을 평가하고 서명한 결정만 받는다. 대상은 F10의 무해한 support-gap 보고 생성이다. 물리 안전·품질·장비 적격이나 자기보고의 진실성을 승인하는 기관을 연결한 것이 아니다.

## 먼저 확인한 거절과 소유 경계

수정 전 실제 Linux에서 세 장면을 실행했다. 출하 앵커 부재는 `author-policy-absent`, 시험용 공개 앵커가 있으나 provider가 없으면 `Unsupported`, Host가 승인 Claim과 가짜 서명을 만들면 `decision/signature`로 거절됐다. 작업 행은 각각0개였다. 수정 뒤 같은 probe에서도 세 거절과0행이 유지됐다. 이번 작업은 거절을 약화해 전후 차이를 만든 것이 아니라, 외부 서명 결정이 들어오는 정당한 경로를 연 것이다.

WorkUsePort와 live Request/Gate는 원래 solutions 소유다. 그 trait를 platform에 구현하면 역방향 의존이 생긴다. 따라서 이미 public이던 F6 wire DTO·서명 message·오류 선언만 platform `rx-package::external_decision`으로 옮기고 기존 solutions 경로에서 재수출한다. live Request, Challenge, Prepared, VerifiedDecision의 봉인은 그대로다. 이동 전후 같은 입력의 직렬화·결정 및 철회 서명 대상·14개 Failure 문자열을 실제 비교했고6225바이트가 같았다. 큰 Counter와 비ASCII 문자열도 포함했다.

판단 규칙과 공유 Task 표현은 platform, 협조적 파일 교환은 G1의 소유 guard를 재사용하는 rx-storage mailbox, 수신 WorkUsePort adapter와 살아 있는 권한 검증은 solutions에 둔다. 크레이트 밖 필드 접근·생성자 호출 거절도 확인한다. public Claim은 데이터이며 승인 능력이 아니다.

## 기본값과 명시적 opt-in

기존 `rx/status-http`와 기본 catalog 전체에는 계속 앵커가 없고 기본 provider도 미연결이다. 새 recipe는 기본 목록에 넣지 않고 계획이 그 이름을 명시적으로 선택할 때만 추가한다. 기존 아홉 통과선의 스크립트·단언을 바꾸지 않는다. 새 `rx/status-work-http`는 같은 비작동 status/readiness/address-space recipe에 하나의 개발용 author policy를 결속한 명시적 선택이다.

- 영역: `development/support-area`
- 역할: `work/support-gap-report`
- 종류: `WORK_USE`만
- 원래 challenge에서 측정하는 최대 TTL:30000ms
- 키: G2 release 키와 다른 개발용 work-judge 키

startup의 선택 항목 `operating_area_mailbox`는 기존 실제 디렉터리만 지정한다. 키·권한·issuer·서명 실행 명령을 지정하지 않는다. `rx-solutionsd run|activate CONFIG WORK_TASK`로 작업을 요청한다. 같은 비작동 opt-in recipe는 기존 명시적 software rearm/resume 경계를 사용한다.

## 판단자가 실제로 판단하는 것

platform의 별도 one-shot `rx-operating-area-judge`는 Host가 실행하지 않는다. 개인키는 외부 판단자에만 제공하며 Host의 mount나 환경에 넣지 않는다. 공개키·영역·역할은 author 코드에 고정한다. 개인키 수탁·회전·실제 제품 권한의 의식은 여전히 확립하지 않았다.

판단자는 정확한 report operation, 영역·역할·종류·프로그램, owner 문맥과 제한된 요구 수치를 확인한다. native-package 요구는10000 이하, support-profile 요구는64 이하인 개발 규칙이다. 부족분을 **보고하는 것**은 허용하므로 장비가 요구를 만족해야만 report를 쓸 수 있는 규칙이 아니다. 요구 profile65는 자기 규칙으로 거절하며 서명 승인을 내지 않는다. 무엇이든 서명하는 oracle로 구현하지 않았다.

거절 보고 자체는 Host에서 검증된 issuer 신원으로 승격하지 않는다. 수신자는 이를 명시적으로 *unverified negative issuer report*로 표시한다. 긍정 proof는 오직 기존 F6 `Challenge::verify`에서 나온다. 서명은 해당 키의 승인이며 정책 실행의 원격 증명이나 물리 진실은 아니다.

## 판단과 실제 사용 사이

1. Host는 현재 소유·readiness·등록·Task에 결속된 live challenge 하나를 만들고 완성된 요청 파일을 공개한다.
2. 외부 판단자가 자기 규칙을 평가하고 서명된 응답을 공개한다. polling은 최초 nonce와 deadline을 유지한다. 새 수신자에게 옛 파일을 읽혀도 live 요청을 복원하지 않는다.
3. Host가 F6 검증을 통과한 Prepared의 **scoped 판단 관측**을 보고한다. 이것은 아직 work 결과가 아니다.
4. 다음 commit checkpoint에서 서명된 철회를 다시 읽고, F10의 입력·등록 revision·readiness·현재 context를 다시 확인한다. 유효하면 실제 파생 report와 decision 소비가 같은 Repository transaction에서 commit된다.
5. 결과와 이력의 `current_permission`은 `NONE; HISTORICAL_WORK_RESULT_ONLY`다.

unscoped Registry.query에는 Task·scope·live receiver가 없으므로 계속 NotEvaluated다. 과거 등록을 현재 허가로 바꾸지 않는다. 요청 문맥 검사가 provider 호출 전에 실패한 경우도 이전 pending 관측을 그대로 재사용하지 않고 현재 거절로 끝낸다.

Mailbox는 단일 writer의 G1 lock과 완성된 불변 파일을 쓴다. Host는 최종 철회 읽기부터 F10의 물리 SQL commit 반환까지 같은 lock을 보유한다. 협조하는 issuer가 이 사이에 철회를 공표할 수 없음을 별도 프로세스의 lock 시도로 확인했다. 이미 공개한 요청이 응답의 완전한 공표를 기다리는 것은 bounded pending이며, 사용 시도나 nonce/TTL 갱신이 아니다. commit 시 경합·사용 불가는 이름 붙은 거절로 끝나며 성공할 때까지 자동 재시도하지 않는다. 부분 파일이나 충돌 응답도 임의로 지워서 진행하지 않는다.

## 실제 거절과 반대 방향

| 조건 | 이름 또는 표시 | 확인 |
|---|---|---|
| 미연결 | `work-use/operating-area-provider`, `work-use/unconnected` | opt-in key가 있어도 외부 결정 없이는 사용 불가 |
| 발급자 범위 밖 | `work-use/issuer-scope` | author 범위 밖 요청 및 응답 key 거절 |
| TTL 만료 | `work-use/ttl-expired`, F6 `decision/expired` | 판단 관측 뒤 기다리면 실제 commit 거절 |
| 영역 불일치 | `work-use/operating-area-mismatch` | 신뢰되지 않은 claimed area를 거름; issuer 신원 검증으로 부르지 않음 |
| 역할·종류 불일치 | `work-use/role-kind-mismatch` | claimed role과 kind를 각각 변조하여 거절 |
| 서명 불일치 | `work-use/signature-mismatch` | 승인 문구나 가짜 서명만으로 proof 생성 불가 |
| 철회 | `work-use/revoked`, F6 `decision/revoked` | 판단 뒤 외부 서명 철회 공표 →0 work 행 |
| 판단자 규칙 거절 | `work-use/judge-policy-denied` | profile65 요구를 외부 판단자가 거절 |
| 전송 대기·사용 불가 | pending / mailbox-unavailable | original deadline 유지; 사용 시 lock 경합은 거절 |

실제 Linux12장면에서 정상 승인1건과 위 공격·거절을 관측했다. 정상 결과는 native675/요구1000/부족325, profiles4/요구6/부족2를 담은 실제 work report다. 거절은 모두 work 행0개였고, 정상은 결과·소비2행이었다. 관리자를 보는 외부 observer가 판단 뒤 정지 구간을 만들고 철회·만료·lock 경합을 일으켰다. 관리 프로세스의 생존을 작업 완료로 세지 않았다.

## 실패를 보존한 구분

재기동 시험의 첫 가정은 틀렸다. F9는 관리자를 다시 열면 즉시 새 요청을 내주지 않고 기존 실행 불명을 거절한다. 이 assertion 실패를 남기고 F9를 약화시키지 않았다. 옛 proof는 Epoch로 만료됨을 확인하고, 명시적 새 수신자에 옛 응답을 넣어 Context 거절을 별도로 확인했다.

기존 등록 passage는 기본 목록의 모든 recipe가 앵커를 갖지 않는다고 단언했다. 처음에 opt-in recipe를 기본 목록에도 넣어 이 검사가 실패했다. 실패를 보존하고 단언은 그대로 두었으며, 새 recipe를 명시적 계획 선택 때만 추가하도록 수정했다.

G1 standalone probe의 lockfile에도 새 storage→rustix 의존 edge 갱신이 빠져 `--locked` 빌드가 거절됐다. 이것은 원인이 확정된 의존 파일 누락이다. 버전·probe 코드·단언은 바꾸지 않고 lockfile 한 줄을 맞췄다. 이어 같은 passage의 고정 실행 파일 목록과 충돌한 mailbox integration-test 세 건은 내용·단언 그대로 기존 storage 단위시험 실행 파일로 옮겼다. SDK도 원본에서 재생성했다. 미규명 E0463과 같은 사건으로 묶지 않는다.

최종 Linux 관측기의 첫 실행은 제어용 JSON 파일을 작성 중 읽어 빈 내용을 본 경합으로 실패했다. 제품 mailbox의 문제가 아니었다. 읽기를 재시도해 숨기지 않고, 관측기 파일도 완성 후 atomic rename으로 공개하도록 수정했다. 원 실패와 새 실행을 구별한다. 컴파일 타입 추론 오류와 큰 enum에 대한 clippy 지적도 개발 로그에 보존했다.

별도 사건 **UNRESOLVED_COLD_BUILD_METADATA_LOOKUP**도 남긴다. 관리자 상실 passage의 cold build 중 외부 의존 세 개(curve25519_dalek, ed25519, sha2)에 E0463이 발생하여 runtime은 시작하지 못했다. 실패 target의 파일은 존재하고0바이트가 아니었으며, 보존된126개 artifact의 hash 변화 없이 metadata 추적 로그를 켠 진단 빌드는 성공했다. 이것은 수정 증거가 아니다. 원인은 확정하지 않았고 단순 파일 부재·0바이트 가설을 뒷받침하는 관측도 없었다. 디스크 여유에 대한 별도 관측과 새 격리 디렉터리 재현을 함께 기록한다. G3 제품 행위 실패나 F9의 과거 flake 원인으로 귀속하지 않는다.

## 지원 한계

| 항목 | 현재 의미 |
|---|---|
| 미규명 빌드 사건 | UNRESOLVED_COLD_BUILD_METADATA_LOOKUP. 첫 manager 시도는 실행 전 실패; 진단 성공을 수정으로 부르지 않음 |
| 판단자 | 한 개발용 영역·report 규칙. 실제 생산 권한 수탁·회전·안전 기관 연결은 미확립 |
| 물리 안전·품질·장비 자격 | 부여하지 않음. component self-report의 진실성도 독립 증명하지 않음 |
| 비협조적 파일 공표자 | lock 순서 보장 밖. 임의 외부 전달 전체를 강제한다고 주장하지 않음 |
| TTL | F10 logical cut 뒤 commit IO 중에도 흐름 |
| HTTP | 자기 시각의 as-of 관측이며 SQL commit과 물리적으로 원자적이지 않음 |
| 과거 등록·파일·report | live 요청이나 현재 허가로 복원하지 않음 |
| 네트워크 판단 | 이번 범위 밖. 온라인 서비스·연속 감시 없음 |
| 다중 운영 영역 | G3에서는 미검증. 후속 [G4](39_multi_operating_area.md)가 두 컴파일 개발 영역의 교차 거절과 각자 결과 저장을 검증함; 실물·운영 자격 아님 |
| G2 신뢰 | verifier/OS 신뢰, 통째 DB rollback 미탐지, offline release 철회 최신성 미확립은 유지 |

[G2의 O1](37_authenticated_release_origin.md)도 한계표에 추가했다. 운영자 공급 패키지 검증 정책은 배포 image의 누락 파일이 아니라 별도 가변 로컬 구성이다. 릴리스 인증이 그 패키지 신뢰 선택을 제약하지 않는다.

아홉 통과선을 통과했다고 보고할 때에도 첫 manager 시도는 미규명 빌드 사유로 실패했고 같은 target의 진단 및 새 격리 전체 재현으로 통과했다는 사실을 함께 유지한다. 원 사건은 수정됐다고 부르지 않는다.

명령·원시 출력·호환 commit·검증 범위는 [근거 기록](../references/operating_area_2026-09-25/README.md)에 둔다. 규범·wire 형식과 기존 아홉 통과선은 유지하며, main 승격·배포·실제 장비 검증은 하지 않는다.


최종 코드 조합은 platform [75e19331](https://github.com/jack0682/rx-platform/commit/75e19331ec1c3bfdb275f75480188f485c86d64b) + solutions [ed3d90f9](https://github.com/jack0682/rx-solutions/commit/ed3d90f9bd1e54e78023b77ae399b4d237c8e4b4)다. 각각 [PR21](https://github.com/jack0682/rx-platform/pull/21)·[PR22](https://github.com/jack0682/rx-platform/pull/22), [PR37](https://github.com/jack0682/rx-solutions/pull/37)·[PR38](https://github.com/jack0682/rx-solutions/pull/38)의 결과이며 source/SDK115개 파일이 일치한다. exact merge CI는 platform406/0/16, solutions430/0/20으로 모두 attempt1 통과했다. macOS는405/0/16,386/0/17이며 단위시험 배치 이동은 같은 세 시험을 보존한다. 아홉 통과선 완료와 첫 manager의 미규명 빌드 실패·재현 이력을 함께 유지한다.


최종 산출물 고정 중에는 작성자가 live-source 빌드와 checkout/pull을 동시에 실행하는 순서 결함도 있었다. 일시적인 구형 checkout과 빌드 lock 거절 시각이 겹쳤고, 고정된 원본·격리 복사본의 Cargo.lock은 같았다. 원래 E0463과 구별한다. 이후 소스를 고정하고 `--locked`로 새로 빌드했으며, 달라진 최종 daemon hash를 대상으로 실제 판단자12장면을 다시 통과했다. 원 실패·reflog·시각 대조를 근거에 보존한다.
