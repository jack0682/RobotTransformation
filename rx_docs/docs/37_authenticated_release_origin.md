# G2 컴파일된 개발 루트에 대한 배포 내용 인증

2026-09-24. 가변 inventory에서 컴파일된 개발 공개키로 릴리스 내용의 권위를 옮긴다. 설치된 검증 바이너리와 OS 자체의 인증, 실제 제품 릴리스 권한의 수탁·교체·의식은 확립하지 않았다. 서명은 운영 영역의 업무 허가나 물리 적격 판정이 아니다.

## 구현 전에 반증한 후보

기존 패키지 경로의 `policy::read` → `Policy::load` → `verify_package`를 실제 Linux에서 호출했다. 같은 바이너리와 같은 서명된 무해한 패키지에서 정책 JSON의 키 목록만 바꿨다. 키가 없을 때 `UNTRUSTED`, 키를 추가한 뒤 `ACCEPTED`였다. 정책 파일을 릴리스에도 그대로 재사용하면 권위를 한 가변 파일에서 다른 가변 파일로 옮기는 데 그친다. 이 후보를 먼저 제외했다. 기존 패키지 정책의 명시적인 로컬 구성 의미를 바꾸는 작업은 아니다.

선택한 경로는 rx-platform의 `rx-package::release::root`에 공개키 bytes와 키 ID, 개발 채널을 소스 리터럴로 둔다. SDK는 원본에서 재생성한다. 런타임 파일·환경변수·CLI 인자·metadata로 키를 추가하거나 바꾸는 경로는 없다. 검증 바이너리를 교체할 수 있는 자는 이 리터럴도 바꿀 수 있다. 따라서 새로운 OS 신뢰 등급을 얻었다고 주장하지 않는다.

개인키는 이번 작업의 로컬 개발키이며 소스·Git·이미지에 들어가지 않는다. 사전 서명된 무해한 시험 자료에는 개인키가 없으므로 CI도 비밀 없이 실행한다. 결정적 시험용 개인키를 출하 루트로 삼지 않는다. 실제 commit tree와 내보낸 runtime filesystem에 해당 개인키가 없는지 별도로 검사한다.

## 실제 인증과 저장 경계

`rx.release.v1`은 채널·양의 단조 판번호·inventory 원 bytes의 SHA256을 서명한다. 서명 message는 릴리스/철회 domain, 서명자 ID, canonical JSON을 결속한다. strict JSON과 Ed25519 strict verification을 재사용한다. inventory는 인증된 기대값을 찾는 일치 색인이며 신뢰 키를 공급하지 않는다. 상대 경로의 모든 indexed file과 지원되는 외부 interpreter `/usr/bin/python3`의 실제 bytes를 대조한다. inventory 밖 OS·공유 라이브러리 전체를 인증한다는 뜻은 아니다. F12의 status script·catalog 소스 pin도 유지한다.

F12의 컴파일된 소스 preflight는 writable state에 접근하기 전에 수행하는 거절 전용 검사다. 그 검사를 통과해 릴리스 인증 경로에 진입한 뒤, 서명된 철회 목록은 자기 단조 판번호를 갖는다. 낮은 판번호 재생, 같은 판번호의 다른 내용, 높은 판번호에서 기존 철회 축소를 거절한다. **후보 릴리스가 거절되더라도 유효한 새 철회는 먼저 저장한다.** 그렇지 않으면 철회한 후보를 거절한 뒤 목록만 예전 것으로 돌려 다시 허용할 수 있다. 릴리스 바닥은 실제 내용 검증 뒤에만 높이며 같은 판번호의 다른 릴리스도 거절한다.

rx-solutionsd의 실제 init·run·activate·investigate·resume은 부수효과 전에 이 저장된 상태를 참조한다. `Repository`의 단일 transaction/CAS/control append가 바닥과 이력을 원자적으로 바꾼다. 실패한 저장을 성공으로 보고하지 않는다. 되돌려 받은 opaque proof도 현재 저장된 철회를 다시 통과해야 한다.

바닥은 `/var/lib/rx-solutions/release.db`에 둔다. 이는 실행별 `state_subdirectory` 밖의 고정된 설치 단위 저장소다. 실행 디렉터리를 새로 골라도 바닥을 초기화하지 못한다. G1의 단일 writer와 명시적 close가 적용된다. 로컬 store 하나가 추가되며 daemon·서비스·네트워크 API는 추가하지 않는다. 입장 checkpoint를 commit한 뒤 store를 닫으므로 상시 감시자나 모든 실행을 독점하는 전역 Runtime 락이 아니다. 그 뒤 다른 invocation이 floor·철회를 갱신해도 이미 입장한 실행을 자동 무효화하지 않는다. 입장 commit과 나중의 exec·외부 철회 갱신을 하나의 원자 동작으로 보장하지 않으며, 이미 입장한 실행은 캡처한 recipe를 사용한다.

`inspect`는 캡처한 내용의 인증 관측만 보고한다. 바닥을 높이거나 현재 실행 허가를 발급하지 않는다. `release_boundary()`와 결과는 현재 업무 권한으로 읽을 수 없다. 직접 OS/Host/Python 실행이나 신뢰된 사용자 Rust 구성 전체를 이 supervisor 경계가 sandbox하지 않는다.

## 여섯 거절과 반대 방향

| 조건 | 외부에서 관측되는 이름 | 장면 |
|---|---|---|
| 서명 없음 | `release/unsigned` | 원래 미서명 runtime image를 새 daemon이 거절 |
| 잘못된 서명 | `release/invalid-signature` | signature 변조 및 컴파일 키 ID 사칭 |
| 모르는 키 | `release/unknown-key` | 정책 파일·키 파일·환경변수로 시험 키를 주입한 서명 |
| 철회된 릴리스 | `release/revoked` | 서명된 새 목록에 현재 후보 identity가 있음 |
| 롤백 | `release/rollback` | 2판 수락 뒤 별도 컨테이너 기동에서 1판 제시; 철회 목록 재생도 거절 |
| 내용 불일치 | `release/content-mismatch` | 실제 script 변경 및 script+inventory 동시 위조 |

각 조건은 `rx.release-refusal.v1`로 출력한다. malformed·state-invalid·state-store-failed는 별개다. 지원 제한 회귀의 첫 실행에서는 소스 변조가 읽기 전용 release DB 오류에 가려졌다. 이 assertion 실패와 당시 바이너리를 보존했고, F12 소스 preflight를 저장소 접근 전으로 복원했다. 그 실행의 Host 병렬50회는 모두 통과했으므로 이 실패를 락 flake로 묶지 않는다. 기존 스크립트와 단언을 바꾸지 않은 새 실행으로 검증한다.

첫 G2 실제 검사에서 거절은 됐지만 `Release(Unsigned)`라는 Debug 출력이 드러났다. 실패를 보존하고 CLI의 typed 진단을 수정한 뒤 별도 실행에서 위 이름들을 관측했다. panic을 거절로 세지 않는다.

반대 방향으로 서명된 1·2·3판은 실제 RX 자식이 `PROCESS_READY`가 됐다. 관리자 밖의 별도 observer가 이를 보고 명시적으로 TERM을 보내 정상 종료를 확인했다. 2판 철회 이후 새 3판은 수락됐다. 온전한 상태를 같은 디스크에 둔 별도 컨테이너 재기동에서 바닥과 철회 재생 거절이 유지됐고, 실행 state_subdirectory 변경도 우회가 되지 않았다.

## 지원되는 것과 남은 신뢰

| 항목 | 지원/한계 | 의미 |
|---|---|---|
| 통상 재기동의 바닥과 철회 재생 | 집행됨 | 온전한 기존 상태가 보존된 재기동에서 낮은 버전·낡은 철회 목록 거절 |
| 통째 DB rollback·삭제 | `NOT_DETECTED` | OS와 상태 보존은 신뢰 기반이다. SQLite와 flock은 하드웨어 단조 counter가 아님 |
| verifier 바이너리와 OS 자체 | 인증되지 않은 선언된 신뢰 기반 | 바이너리 교체자는 컴파일 키도 바꿀 수 있음 |
| 운영자 공급 패키지 검증 정책 | 인증된 릴리스 밖의 가변 로컬 구성 입력 | 정책 파일은 이미지에 배포되지 않는다. 릴리스 인증은 현장이 어떤 패키지를 신뢰할지를 제약하지 않는다 |
| 제품 릴리스 키 수탁·교체·의식 | `NOT_ESTABLISHED` | 이 키는 개발용. 실제 제품 권한을 주장하지 않음 |
| 오프라인 철회 목록의 최신성 | `NOT_ESTABLISHED` | 전달되지 않은 새 철회를 알 수 없음 |
| 확인과 실제 사용 사이 | `EXPLICIT_CALLER_DRIVEN_CHECKPOINTS` | 입장 시 인증과 기존 exec 직전 hash 재검사. 사이의 설치 bytes 안정성은 신뢰 |
| 상시 변경 감시·자동 중단 | `NO_TIMER_OR_BACKGROUND_MONITOR` | 실행 중 파일/철회 변경을 지속 탐지·집행한다고 주장하지 않음 |
| 물리 안전·품질·업무 권한 | 별도 책임 | release 서명이나 PROCESS_READY로 승격하지 않음 |

[TUF specification의 신뢰 metadata 보존과 version 검사](https://theupdateframework.github.io/specification/v1.0.27/)도 클라이언트가 보존한 신뢰 metadata를 기준으로 rollback을 판단한다. 로컬 상태를 통째 교체하는 적에 대한 저항을 그 비교만으로 얻는 것은 아니다. 이는 같은 종류의 보존 전제가 있다는 비교이며 이 구현의 TUF 준수·동등성 주장이 아니다. TUF의 역할 분리·만료·키 회전은 구현하지 않았다.

G1의 정상 close 수정과 SIGKILL/abort 뒤 상속 description 잔여는 [G1 기록](36_storage_lock_lifetime.md)에 유지한다. [F12 분류](35_open_items_and_support_limits.md)의 기존 관측은 지우지 않고 시점을 표시한다. G2는 미결을 없앤다는 이름 아래 위 네 신뢰 한계를 지우지 않는다.

## 재현·검증·호환 기록

[명령과 원시 결과](../references/release_origin_2026-09-24/README.md)는 구현 전/후 키 주입, 최초 진단 실패, 정상 수락, 여섯 거절, 서명 이미지 파생, 전체 회귀와 개인키 부재 검사를 구분한다. 서명 파생은 기존 이미지의 inventory를 고정하고 public `release.json`/`revocations.json`만 더한다. 개인키는 build context에 넣지 않는다. 기존 여덟 passage 스크립트와 단언은 수정하지 않고 `--image`만 서명 파생 이미지로 바꾼다.

검증 이미지는 고정된 기존 native runtime에 공개 서명 metadata만 더한 것이다. 기존 passage가 현재 checkout에서 빌드한 verifier/시험 바이너리를 별도 mount하여 실행한다. 기존 이미지 안 Rust 실행 파일의 내용도 서명 inventory에 결속되지만, 이번 작업이 전체 native image를 새 소스로 재빌드·배포했다는 뜻은 아니다. verifier 자신과 OS의 인증 제외를 이 차이로 가리지 않는다.

공유 규범·wire/protobuf·SQLite schema version을 변경하지 않는다. Rust API와 서명된 로컬 metadata 형식은 추가된다. 구형 미서명 설치는 새 supervisor에서 거절되며 서명 단계를 거쳐야 한다. 운영 배포·main 승격·실물 장비 검증은 수행하지 않는다.

호환 코드 조합은 platform [PR20](https://github.com/jack0682/rx-platform/pull/20)의 기여 [95fbba23](https://github.com/jack0682/rx-platform/commit/95fbba235bd0c28ffcf51a7fe71717c8ab17d41f) / 병합 [1966319f](https://github.com/jack0682/rx-platform/commit/1966319fbb9b17d840c930915235f7744ccde595), solutions [PR36](https://github.com/jack0682/rx-solutions/pull/36)의 최종 기여 [1f9cc7de](https://github.com/jack0682/rx-solutions/commit/1f9cc7def3f1aa30c7a32472f0220f16fe9b508d) / 병합 [1430e1b1](https://github.com/jack0682/rx-solutions/commit/1430e1b1e8f813a6e86405a04e16039e83861909)다. SDK 원본 대조는 이 코드 조합을 대상으로 한다. 문서 PR과 exact merge CI 결과는 아래 근거 기록에서 함께 고정한다.

최종 exact merge CI는 platform [36017648598](https://github.com/jack0682/rx-platform/actions/runs/36017648598) 402/0/16, solutions [36018722975](https://github.com/jack0682/rx-solutions/actions/runs/36018722975) 420/0/20이며 모두 attempt1 성공이다. 새 소스의 기존 여덟 통과선도 모두 통과했고 source/SDK111개 파일은 새 export와 같았다. 로컬 두 실패와 수정 근거는 별도로 보존한다.
