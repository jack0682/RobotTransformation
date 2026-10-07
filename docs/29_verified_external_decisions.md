# F6 검증된 외부 결정

2026-09-23 · **운영 영역의 서명 결정을 검증해 긍정을 표현한다. RX 호스트는 발급자가 아니다. 기본 제품 카탈로그에는 앵커가 없으므로 출하 기본값은 아무것도 승인할 수 없다.**

## 긍정이 뜻하는 것

[F4](27_readiness_and_work_use.md)의 업무 판단과 [F5](28_dependency_binding.md)의 초기·교체 결합 판단에 `Verified(Box<VerifiedDecision>)` 응답을 추가했다. 긍정은 외부 서명 검증을 통과한 opaque 증거를 전달해야만 나온다. bool이나 JSON 기록으로 이 증거를 만들 수 없다.

**검증이 보증하는 것은 선언된 키의 보유자가 정확한 대상에 대해 서명했다는 것뿐이다. 그 결정이 옳다거나, 기능·장비가 준비됐거나, 실제 운영 영역이 무엇을 승인했다는 사실까지 증명하지 않는다.** 이 검증에서 실제 발급자는 시험용 외부 프로세스다.

표시 상태 `VERIFIED`는 해당 조회 시점에 외부 승인을 검증했다는 기록이다. 현재 유효한 증거 자체가 아니다. 이후 사용할 때는 현재 수신 경계에서 증거의 대상·수명·철회를 다시 확인해야 한다. 업무 판단은 준비·등록·실행 상태를 바꾸지 않고 결합 수용도 주지 않는다. 결합 승인은 업무 허가를 주거나 제안된 제공자를 자동 적용하지 않는다.

## 신뢰 앵커의 소유와 위협 범위

선택적인 `decision_policy`는 작성자 `Program` 및 진단 `Catalog`의 일부다. issuer/key/public key, 운영 영역, 허용 role/kind와 최대 TTL을 포함한다. 전체 정책은 catalog digest에 들어가며 현재 등록 revision/catalog와 일치해야 sealed request를 만든다. 키를 바꾼 catalog로 기존 등록을 다시 열면 거절한다. `None`은 직렬화에서 생략해 기존 기본 catalog/plan digest를 유지한다.

정책에는 `Deserialize`와 site/env/key-file loader가 없다. site Process의 알 수 없는 필드는 거절되며, 공개 API에서 임의 키를 넣어 긍정 증거를 만드는 verifier도 없다. 포트는 수신자가 만든 sealed request를 받아 이미 고정된 정책으로 challenge를 요청할 수 있다.

이 보증은 **신뢰되지 않은 site 및 decision 입력까지**다. 임의의 작성자 Rust 코드 변경, 신뢰된 호출자의 registry 오남용, OS 또는 이미지 교체는 포함하지 않는다. 등록부의 digest pin은 작성자 출처를 독립적으로 인증하는 root가 아니다. 소스나 DB를 마음대로 바꾸는 호스트까지 격리했다고 주장하지 않는다.

**이름 붙은 미지원: 인증된 불변 release root.** 더 강한 행위자를 방어하려면 이 root 또는 저장소 밖의 보호 경계가 필요하며 이번 구현에는 없다.

기본 release Program들과 기본 진단 Catalog에는 정책이 없다. 실제 운영 영역 서비스/RPC와 키 배포·rotation·신뢰 provisioning도 이번 범위 밖이다. 시험은 별도로 작성한 test catalog를 새 등록에 고정하며 공개된 known-private 키를 기본 신뢰로 넣지 않는다.

## 서명 대상과 세 판단의 분리

하나의 검증기가 다음 세 kind를 구분한다.

| kind | 정확한 대상 |
|---|---|
| `WORK_USE` | 현재 F4 등록/revision/catalog, 실행 run/instance/PID, 설정 digest, 운영 영역과 role |
| `INITIAL_BINDING` | 소비 등록/revision/catalog, 지정된 관계와 제공자 실행/설정, 운영 영역과 profile |
| `REPLACEMENT_BINDING` | 기존 관계 전체와 별도 후보 등록/catalog 및 제안 generation |

교체 긍정에는 후보 generation이 명시되어야 한다. 기존 generation 없는 조회 API는 계속 사용할 수 있지만 긍정 증거를 받는 경로는 열리지 않는다. 후보 좌표는 서명 결정의 대상이지 물리 가용성의 독립 관측이라고 주장하지 않는다. Work-use의 현재 범위는 F4 구성요소 실행과 role이며, 개별 물리 명령 dispatch 허가가 아니다.

검증은 벤더된 `rx_package::verify_detached_message`의 Ed25519 strict 구현을 그대로 사용한다. 새 암호 알고리즘이나 SDK 수정은 없다. `SignatureEnvelope`는 기존 key/signature DTO를 재사용한다. 서명 메시지는 별도 domain과 key ID 및 canonical claim을 포함한다. claim은 **`APPROVE` verdict**, verifier epoch, nonce, 전체 context와 policy fingerprint, decision ID 및 TTL을 덮는다. 단순 `ACKNOWLEDGED` 응답이나 다른 schema를 긍정으로 읽지 않는다.

같은 키를 쓰더라도 업무 결정을 결합 수용에 제시하거나 그 반대로 제시하면 거절한다. 다른 등록·scope/role·generation·관계도 거절한다. 서명 ID를 다른 내용이나 더 긴 TTL로 다시 정의할 수 없다. 검증 전에 context나 signature를 바꾸면 거절된다.

## 만료, 복제, 재시작과 철회

challenge가 생성될 때 수신자의 local `Instant`를 잡는다. 허용 기간은 그 시점부터이며 **도착/import 시각부터 다시 시작하지 않는다.** TTL은 양수이고 작성자 상한 이하여야 한다. 작성자 정책의 절대 상한은60000ms이며 시험 정책은30000ms를 사용한다. 이 값은 소프트웨어 입력 제한이지 모든 장비에 적합한 권한 시간이라는 뜻이 아니다.

원격 벽시계 deadline은 입력으로 사용하지 않는다. 지연된 서명을 들여오거나 동일 서명을 재검증하거나 증거를 복제해도 원래 deadline을 늘리지 않는다. 수신자는 최대512개의 결정 identity를 보유하며 한계에서는 새 결정을 거절한다.

`VerifiedDecision`의 필드와 생성자는 외부에 없고 `Deserialize`도 없다. clone은 원래 deadline과 수신자 ledger/철회 상태를 공유한다. 소유 수신 객체를 닫으면 남겨진 request/challenge/proof까지 무효화되며, 다시 열 때는 새로운 epoch다. 저장 참조나 유효했던 옛 서명으로 새 monotonic 수명을 복원할 수 없다.

별도 서명된 철회는 정확한 decision reference를 지목한다. 검증된 철회가 들어오면 clone과 재import를 포함한 다음 사용을 거절한다. 잘못된 키의 철회는 적용되지 않는다. 실제 원격 철회 feed, 자동 갱신, 재시작 후 과거 lease 복원은 제공하지 않는다. 실제 장비 명령까지 포함한 권한 확인·dispatch·철회의 원자 gate도 이번 범위가 아니다.

## 과거 기록과 현재 권한

명시적인 `record_verified_decision`과 `record_verified_revocation`은 등록 Repository에 참조/digest를 별도 append한다. 일반 준비/판단 조회가 자동으로 history를 쓰도록 바꾸지 않았다. 저장되는 것은 live deadline·키 capability가 아니라 읽을 수 있는 과거 관측이다.

만료·철회 후에도 원 판단 기록과 진단 결과는 그대로다. 새로운 철회 기록이 옛 긍정의 JSON을 덮어쓰지 않는다. `recorded_decision`으로 과거를 읽는 것과 현재 proof를 사용하는 것은 다르다. 과거 `VERIFIED` 표시를 현재 허가로 복원해서는 안 된다.

## 호환성과 보존한 경계

- Rust Program과 진단 Catalog literal에는 선택적 `decision_policy` 필드가 추가된다. 기존 객체는 `None`으로 유지하며 직렬화에서는 생략된다.
- 긍정 reply는 bool을 받지 않고 boxed opaque proof만 받는다. 새 enum 변종을 처리하려면 외부 exhaustive match가 갱신되어야 한다.
- F5 `AcceptanceAssessment`의 변경 가능한 공개 필드는 읽기 accessor로 바꿨다. 외부가 기존 미지원 결과를 받아 state를 긍정으로 덮어쓸 수 없게 했다. 기존 시험의 값·사유 단언은 유지하고 접근 방식만 이행했다.
- 새 로컬 문서/조회 형식은 공유 wire/proto·SDK·manifest·규범 v1.0 변경이 아니다. 이전 writer가 새 의미를 집행하는 downgrade 호환성은 주장하지 않는다.
- F1 카탈로그 요구/수락, F2 등록 신원과 UNKNOWN, F3 opaque 종료 증거/별도 처분, F4 준비와 업무 판단 분리, F5 의존 구간과 결과 소비를 유지한다. `depends_on` 네 동작과 process/supervisor lifecycle은 바꾸지 않았다.

## 실제 Linux 검증과 한계

같은 `tools/registration_passage.py`에 decisions worker를 추가했다. 기존6 worker의 단언을 유지하고 전체는 parent1·worker7·관측32단계다. 이를 독립 시험32개로 세지 않는다. 실제 설치된 상태 서비스를 읽고 새 Rust 검증 경로를 실행한다.

외부 issuer는 별도 OpenSSL 프로세스에서 매번 새로운 ephemeral Ed25519 키를 만든다. private key는 production API·production 코드·커밋에 들어가지 않는다. 시험에는 OpenSSL3 CLI가 필요하며 [공식 pkeyutl 문서](https://docs.openssl.org/3.0/man1/openssl-pkeyutl/)의 `-sign -rawin` 경로를 사용한다. 출하 기본값에 시험 키를 추가하지 않는다.

관측 장면은 미검증 서명 거절, 검증된 업무 승인, 독립 초기/교체 승인, 양방향 kind 혼용 거절, 등록·scope·generation 재사용 거절, 만료/철회 후 거절과 과거 보존, receiver 재개 후 옛 proof 거절이다. signed statement와 public test policy를 출력해 근거를 남기고 private key는 출력하지 않는다.

**긍정 장면이 증명하는 것은 시험 발급자가 키를 보유했다는 것이지 실제 운영 영역이 무엇을 승인했다는 것이 아니다. 기본 production catalog에 앵커가 없으므로 출하 기본값은 아무것도 승인할 수 없다.** 서명 유효성을 결정의 올바름·기능 준비·장비 안전·품질로 승격하지 않는다.

실제 운영 영역 연결, 장비 동작·물리 자격, 협업 자원 결합, Linux 자원 집행, 외부 조사 provider, 기존 제어 효과 신호 경쟁, 다중 호스트와 인증된 불변 release root는 미지원 또는 기존 미결로 남는다.

## 구현과 관측한 검사

구현은 [rx-solutions `679e0492`](https://github.com/jack0682/rx-solutions/commit/679e0492d99640d76e12110be6da48574bd2b278)에 고정된다. 재현 경로는 [판단 시험](https://github.com/jack0682/rx-solutions/blob/679e0492d99640d76e12110be6da48574bd2b278/runtime/rx-supervisor/tests/verified_decision.rs), [외부 시험 서명자](https://github.com/jack0682/rx-solutions/blob/679e0492d99640d76e12110be6da48574bd2b278/runtime/rx-supervisor/tests/support/external_signer.rs), [동일 Linux 절차](https://github.com/jack0682/rx-solutions/blob/679e0492d99640d76e12110be6da48574bd2b278/tools/registration_passage.py)다.

- macOS workspace: **329 통과, 0 실패, 17 ignored**. 전용 target과 `--test-threads=1`을 사용했다. 새 앵커/결정 시험10개는 이 수에 포함된다.
- 전체 workspace/all-targets/all-features clippy `-D warnings`, fmt, repository·invariant·문서 표 검사를 통과했다.
- 외부 안전한 Rust consumer의 날조/역직렬화/키 경계/표시 변경 시도14종은 예상 컴파일 오류로 거절됐다. 각 consumer를 정상 reader로 복원하면14종 모두 컴파일됐다.
- 실제 Linux는 parent1·worker7·관측32단계로 완료했다. Runtime `sha256:fcb56bfdfcc1f68bf8cfb6d28f7f24d5899f5e31030ee2a882f6e29e1e28b4a0`, builder `sha256:ff521445a372125ed4f76e1453a1f8098f2d05332d1601d30db1c1f62757e730`을 사용했고 기존 상태 서비스 source hash는 동일하다. 전체 native 재빌드나 이미지 배포는 하지 않았다.
- 기존 runtime 시험50파일은 선택 필드 None 초기화와 읽기 accessor 이행만 정규화하면 기존 단언과 동일하다. plan에는 작성자 정책 검증3줄만 추가했고 기존 의존 알고리즘은 동일하다. supervisor/process 수명 본문은 byte 단위로 동일하다.

첫 시험 시도는 새 시험의 serde_json Value 대입에 필요한 변환을 빠뜨려 컴파일 단계에서 멈췄고 수정했다. clippy는 큰 긍정 enum payload 두 곳을 지적해 Box로 전달하도록 보완했다. 초기 오류 로그와 이후 실제 실행 결과를 별도로 보존했다. 최종 결과를 초기 오류가 없었다는 뜻으로 쓰지 않는다.
