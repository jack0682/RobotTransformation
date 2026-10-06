# G1 저장소·Host 소유 락 수명

2026-09-24. 정상 해제와 단일 writer 거절 보존을 함께 검증한다. SIGKILL/abort의 잔존 descriptor 창은 제거했다고 주장하지 않는다. 인증된 배포 출처·운영 영역 판단자·물리 인계는 이번 수정에 포함하지 않는다.

[F12 분류와 당시 실패 기록](35_open_items_and_support_limits.md)의 저장소 락 행은 이 문서의 정상 해제 수정으로 갱신한다. F12의 원 관측과 G1의 SIGKILL 잔여는 각각 보존한다.

## 출발점과 먼저 반증한 구현

부모의 필드 선언은 이미 `connection` 다음 `_ownership`이었다. 부모가 연결을 먼저 닫는 순서는 결함이 아니었다. 결함은 close만으로는 fork 자식이 가진 같은 open file description의 복제가 사라지지 않는다는 점이었다.

실제 Linux에서 소유자의 LOCK_UN 뒤에는 자식의 복제가 살아 있어도 재획득됐다. 동시에 살아 있는 소유자에 대한 거절, 새 소유자가 생긴 뒤 옛 자식의 unlock/close/exit가 그 소유자를 풀지 못함을 확인했다. 그러나 **자식이 상속한 FD로 무조건 unlock하면 살아 있는 부모의 락까지 풀렸다.** 따라서 F12의 실험 원형을 그대로 제품으로 옮길 수 없었다. 이 반례를 보존하고 생성 프로세스만 해제하도록 바꿨다.

커널 근거는 [flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html), [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html), [Rust File::unlock](https://doc.rust-lang.org/std/fs/struct.File.html#method.unlock)다. 커널 의미와 아래의 실제 관측을 구별한다. flock은 협력적 소유 프로토콜이며 악의적인 OS·작성자나 임의 raw syscall을 격리하지 않는다.

## 실제 해제 경계

원본 rx-storage의 `ExclusiveFileLock`은 File/FD를 공개하지 않고 Clone을 제공하지 않는다. 획득은 한 번의 nonblocking try_lock이며, 실패한 경쟁자는 unlock guard를 얻지 못한다. 새 Unix 락 파일은0600(umask 적용)으로 생성하고 기존 파일 권한은 다시 쓰지 않는다.

`SqliteRepository::close(self)`는 repository를 소비하고 실제 `Connection::close()` 성공을 확인한 다음 LOCK_UN을 수행한다. Drop도 같은 순서를 쓴다. SQLite가 생긴 뒤 초기화가 실패하는 경로 역시 같은 repository 종료 경로를 탄다. close가 panic으로 중단돼도 확인 전에 guard의 destructor가 unlock하지 않도록 한다.

close 실패 시에는 connection과 **이 프로세스의** 락 descriptor를 프로세스 종료까지 남긴다. 별도 능동 격리 서비스가 생긴 것이 아니다. 상속된 사본은 그 뒤에도 락을 유지할 수 있다. 명시적 close는 typed 오류를 반환하며 Drop은 오류를 반환할 수 없다. unlock 오류도 확인된 해제로 바꾸지 않고 descriptor를 남기며 자동 재시도하지 않는다.

생성 시의 프로세스 PID와 현재 PID를 연산 진입과 해제에서 대조한다. 이것은 같은 PID namespace의 ordinary fork에 대한 일시적인 런타임 검사다. 영속 PID 복구 권한이나 인증된 프로세스 신원이 아니다. Rust 타입은 fork를 막지 못하므로 실제 집행은 이 대조다. 상속된 connection에 SQLite destructor를 호출하지 않고 exec/exit까지 사본의 자원을 남긴다. 임의의 post-fork 코드에서 SQLite를 사용해도 된다는 보증은 아니다.

## 빌린 transaction도 예외가 아니다

`transact`의 callback이 받은 transaction도 fork로 복제된다. repository 입구만 검사하면 자식이 그 transaction으로 SQL을 실행하거나, callback이 반환·unwind할 때 부모의 transaction을 commit/rollback할 수 있다.

따라서 borrowed Transaction의11개 진입점과 commit·rollback 정리에도 생성자 검사를 둔다. 자식의 Ok·Err·panic은 부모 transaction에 SQLite 정리를 수행하지 않는다. 부모의 오류·panic은 기존 rollback을 유지하며, repository가 살아 있는 동안 다른 writer는 계속 거절된다.

실제 Linux에서 자식의 read/write/commit이 거절되고 세 callback 종료 방식 모두 부모의 원 기록과 integrity를 보존했다. 이 확인은 “정상 close가 빨라졌다”와 별개로 단일 writer 보존을 확인하는 반대 시험이다.

## typed 오류와 Host 연결

공유 port에 `OwnershipFailure` / `OwnershipError` / `StoreError::Ownership`을 추가했다. Contended, Acquire, ForeignProcess, ConnectionClose, Release를 구분한다. non_exhaustive가 아닌 enum의 추가 변형으로 드러난 downstream exhaustive match를 명시적으로 처리했다. HTTP/gRPC의 저장소 오류는 기존 unavailable 응답 의미를 유지한다.

SDK는 rx-platform 원본에서 `export_host_sdk.py`로 재생성하고 `check_host_sdk.py`로 대조한다. 사본을 직접 편집하지 않는다. Host의 별도 runtime lock은 같은 원본 guard를 사용하되 기존 service/maintenance 전체 수명을 유지한다. generic guard 자체가 adapter의 safe-to-drop이나 물리 권한을 판단하는 것은 아니다.

F12의 문자열 어댑터는 제거했다. `rx.support-refusal.v1`은 typed 오류에서 조건을 만들며, 같은 오류 문구를 넣은 일반 Unavailable 문자열은 ownership 진단으로 승격하지 않는다. owner_identity는 계속 NOT_ESTABLISHED다. 실패한 try_lock은 실제 홀더를 식별하지 않는다.

## 겹침 장면과 반대 방향 확인

| 장면 | 정상 해제 또는 허용 | 함께 확인한 거절 |
|---|---|---|
| 정상 close / Drop + 살아 있는 fork 복제 | 자식 종료 전 재획득 | 해제 전에는 경쟁자 거절; 옛 자식 종료 뒤에도 새 writer가 경쟁자를 거절 |
| 자식의 상속 repository close / Drop | 부모만 정상 종료 가능 | 자식 SQL과 unlock 거절; 부모는 계속 쓰고 다른 writer를 거절 |
| Host 소유 guard의 자식 복제 | 부모의 명시적 해제 뒤 재획득 | 자식의 해제는 거절; 새 guard의 거절 보존 |
| callback 안의 fork, 자식 Ok / Err / panic | 부모 transaction만 정상 commit | 자식 연산·commit·rollback 불가; 부모 record1개·integrity·진입 거절 보존 |
| 실제 Command pre_exec, 성공 exec / 실패 exec | 정당한 부모 close 뒤 창 안에서 재획득 | live writer 거절 및 자식 처리 완료 뒤 새 writer 거절 보존 |
| SQLite close 실패 | 홀더 프로세스 종료 뒤 재획득 | 실제 미종결 statement 때문에 close가 실패하면 다른 writer가 계속 거절됨 |
| 초기화 실패 / rollback / unwind | 정당한 소유자 종료 뒤 재획득 | 실패한 경쟁자·rollback·panic이 살아 있는 소유자의 락을 해제하지 않음 |
| 관리자 SIGKILL + pre-exec 자식 | 상속 description이 닫힌 뒤 재획득 | 자식이 복제를 보유한 동안 Contended 거절; 원 업무 결과는 주장하지 않음 |

## SIGKILL 경계는 남는다

**G1은 abrupt loss 경우의 거절을 없애지 않는다. 상속 description의 수명으로 그 창을 한정할 뿐이다.** Drop이 실행되지 않으므로 죽은 소유자가 LOCK_UN을 수행했다고 간주할 수 없다. 새 writer는 `storage/exclusive-writer-not-established`로 거절되며 진단은 살아 있는 소유자 또는 잔존 description 가능성과 명시적 재개방 조건을 나타낸다. 조용한 대기나 성공으로 바꾸지 않는다.

F9의 원 결과 UNKNOWN/Unresolved, 소유 인수 금지와 명시적 recovery는 그대로다. 저장소가 다시 열린다는 사실은 이전 동작의 완료·물리 복구·자원 인계가 아니다.

## 범위·호환·검증 기록

Rust API에는 추가 변형과 close/guard API가 생겼다. SQLite schema/version, 영속 Document와 wire/protobuf 표현은 바꾸지 않았다. 규범 본문·manifest와 SDK 사본의 동기화를 별도로 대조한다. 지원 근거는 실제로 실행한 로컬 Linux/파일시스템과 macOS 회귀에 한정하며, 원격 파일시스템·다른 PID namespace로 객체 이동·물리 장비를 포괄하지 않는다.

[명령·출력·반례·반복 결과](../references/storage_lock_2026-09-24/README.md)에 실행 환경과 바이너리 hash를 고정한다. Linux11개 겹침 장면과 SQLite 실제 close 실패 검사를 구별해 기록한다. Host stress는 정해 둔50회 전체를 `--test-threads=16`으로 실행하며, 어떤 실패도 다음 성공으로 덮지 않는다. 현재 관측에서는50/50 통과했고 추가 실패가 없었다. 이 결과만으로 역사적 F9 한 건의 원인을 확정하거나 모든 미래 실패를 같은 원인으로 단정하지 않는다.

F12의 원 실패와 격리 원형은 이전 근거로 유지한다. 이번 제품 구현은 생성자 검사, 연결 close 확인, 실패 시 자원 보존, 상속 transaction 정리를 추가한 별도 구현이다. 실험용 raw fork와 pre_exec unsafe 코드는 standalone 측정 fixture에만 있고 제품 crate의 unsafe 금지는 유지한다.

## 호환 조합과 변경 링크

구현 기여 조합은 다음과 같다. SDK 일치 검사는 이 둘에서 통과했다.

| 저장소 | 기여 commit | PR |
|---|---|---|
| rx-platform 원본 | [e387dec6](https://github.com/jack0682/rx-platform/commit/e387dec6f2d51f3c5b497808eba5c45b68e18969) | [PR19](https://github.com/jack0682/rx-platform/pull/19) |
| rx-solutions 재생성 SDK·Host | [9a59bffb](https://github.com/jack0682/rx-solutions/commit/9a59bffb8f659e07acdf9dae507500a69390ccba) | [PR35](https://github.com/jack0682/rx-solutions/pull/35) |

최종 실행 코드의 develop 조합은 platform [98030850](https://github.com/jack0682/rx-platform/commit/980308500d321c4275c0e4a391f6c0a5c693cbbb) + solutions [5a3e2a20](https://github.com/jack0682/rx-solutions/commit/5a3e2a20a6a826dab135e817b96a0c264ad444f1)다. 두 병합 트리는 각 기여 트리와 같고 source/SDK 검사가 일치했다. platform [병합 CI35997048541](https://github.com/jack0682/rx-platform/actions/runs/35997048541)은399/0/16, solutions [병합 CI35997526310](https://github.com/jack0682/rx-solutions/actions/runs/35997526310)은420/0/20으로 통과했다. 이 문서 PR은 위 두 PR을 연결하는 검증·호환 기록이며 main 승격이나 배포를 뜻하지 않는다.
