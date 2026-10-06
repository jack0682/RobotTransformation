# F9 관리자 완전 상실 뒤의 커널 조사와 명시적 재개

2026-09-24 · 확인하는 것은 원 직접 프로세스가 더 이상 실행 중인지다. 원 실행의 결과는 복원하지 않으며 UNKNOWN과 PastOutcome::Unresolved를 보존한다.

## 확인 범위와 선택 근거

F3의 `RecoveryEvidence::Investigation`은 문자열 finding만 받았고 실제 조사 제공자가 없었다. F9는 이를 커널 관측에서만 만들어지는 `ProcessInvestigation`으로 바꾼다. 먼저 실제 runtime 이미지의 UID 10001, CapEff 0, read-only, no-new-privileges 자세에서 boot_id, `/proc/PID/stat` starttime, PID/time namespace, cmdline·exe의 노출을 측정했다. 이름·포트·cmdline은 식별 근거로 채택하지 않았다.

`starttime`은 부팅 후 clock tick 단위의 생성 시점이다([proc stat 원본](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html)). PID만 존재한다고 원 프로세스가 살아 있다고 판단하지 않는다. 같은 PID가 실제 재사용되는 반례를 별도 private namespace에서 만들었고, 시작 시점의 차이를 커널 조사 제공자가 구별했다. 제품 자세에서 clone3 set_tid는 ENOSYS(38)였다. 반례 fixture만 UID0·CAP_CHECKPOINT_RESTORE·seccomp unconfined를 사용하며, 이 권한을 제품의 복구 근거로 삼지 않는다.

첫 상주 지원 범위는 기존 비구동 `rx/status-http` 한 개다. 이 작성자 레시피는 subprocess를 만들지 않는다. 일반 장비, 후손 프로세스 전체, 협업 자원, 물리적 완료나 안전을 이 직접 프로세스 조사로 판정하지 않는다.

## 원 배정과 귀속

OS backend가 아직 unreaped Child를 소유하는 동안만 생성 식별정보를 채집한다. private field의 `OwnedProcessIdentity`는 전체 launch request에 묶인다. Supervisor는 PID·식별정보·Starting을 같은 상태 변경에 기록하고, 등록 execution의 동일한 instance/run에 복사한다. 별도 backend hook이나 호출자 fingerprint 입력을 만들지 않았다. 시작 전후 crash 때문에 식별정보가 저장되지 않으면 조사 불가로 남는다.

저장 식별정보는 boot ID, 관찰자 PID/time/user/mount namespace, UID/EUID, proc mount/view, PID1의 start ticks, time namespace offsets, 원 PID와 start ticks를 포함한다. `/proc/self`가 실제 관찰자 PID와 일치해야 하며 hidepid·PID overlay·누락/권한 오류는 긍정 근거로 쓰지 않는다. scope를 두 번 일관되게 읽고 프로세스 관측 앞뒤에서도 비교한다.

`Registry::investigate(ObservationRef)`가 원 기록을 직접 읽는다. 원 revision/digest와 저장 식별정보가 다르면 처분·재개에 쓸 수 없다. `ProcessInvestigation`은 public 생성자·필드·Deserialize가 없다. 기존 문자열 `EvidenceReference::Investigation`은 읽기 전용 이력으로만 해석한다. 새 증거로 제출하거나 typed 조사 결과로 변환하지 못하며, 저장된 새 요약도 현재 근거가 되지 않는다. 네 개의 컴파일 거절 검사가 문자열 제출, 저장 이력 변환, 역직렬화, 외부 fingerprint 주입을 각각 다룬다.

**악의적 DB나 OS 작성자에 대한 암호학적 진실 인증을 주장하지 않는다.** 기존 신뢰 저장소와 커널 노출면을 전제로 한 귀속 경계다.

## namespace 수명을 건너는 영구 한계

동시에 살아 있는 두 컨테이너는 각각 PID1을 가진다. boot ID와 프로세스 starttime만 비교하면 다른 namespace의 PID를 원 프로세스로 읽거나 원 프로세스의 부재로 오독할 수 있다. 따라서 scope 일치가 선행 조건이다.

그 후 실제 통과선에서 더 좁은 반례를 발견했다. 컨테이너를 제거하고 새로 만들자 PID/time/mount namespace inode와 proc mount 번호까지 모두 재사용됐다. 최초 구현은 이 순차 교체를 같은 scope로 읽어 부재를 보고했고, 통과선의 단언이 실패했다. **이 실행은 전체 PASS로 세지 않았으며 실패 출력과 당시 결과를 보존했다.** 독립 재현에서도 namespace 번호는 같고 PID1 start ticks만 51697과 51711로 갈렸다.

이에 init birth와 time offsets를 추가하고 이중 일관 판독을 요구했다. init birth 일치는 같은 namespace라는 확신을 높이지만 암호학적이거나 영구적인 unique namespace UUID는 아니다. 기대는 수명 추론은 살아 있는 namespace끼리는 kernel inode를 공유할 수 없고 재사용은 이전 namespace 소멸 뒤에만 일어난다는 것이다. [namespace 원본](https://man7.org/linux/man-pages/man7/namespaces.7.html)과 [PID namespace 원본](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html)을 근거로 한다.

불일치 사유는 `saved-namespace-not-observable-in-current-scope`다. **저장된 namespace를 여기서 관측할 수 없으므로 현재 namespace의 PID 관측은 원 기록의 근거가 될 수 없다.** “옛 namespace가 죽었으니 원 프로세스도 죽었을 것이다”라는 수명 추론은 이 경로의 긍정 커널 관측이 아니며 재개 조건을 대신하지 못한다.

**컨테이너를 교체하면 그 기록은 이 커널 경로에서 영구히 Unverifiable이다.** namespace 수명을 건너 해소하려면 외부 증언 제공자가 필요하고 이는 F9 범위 밖이다. F9 이전 기록도 저장된 생성 식별정보가 없으므로 이 제공자로는 영구히 해소할 수 없다. 현재 PID를 읽어 소급 채우지 않는다. 두 한계는 일시적 기능 대기가 아니다. 실제 같은 namespace 안의 관리자 재시작과 컨테이너 교체를 구별한다.

## 세 결과와 명시적 재개

일치한 scope에서 `pidfd_open`의 ESRCH는 커널 PID 부재다. 파일이 보이지 않는다는 주장과 구별된다([pidfd 원본](https://man7.org/linux/man-pages/man2/pidfd_open.2.html)). PID가 있으면 proc stat을 두 번 읽는다. 같은 생성 시점의 살아 있는 프로세스는 MatchingProcessPresent로 차단하고, 다른 시점이면 PID 재사용에 따른 OriginalNotRunning으로 해석한다. 같은 tick에 식별자가 충돌하면 살아 있는 일치 프로세스로 남겨 보수적으로 차단한다. Zombie, process read race, scope read race, 누락·권한·가시성 문제는 각각 구별되는 Unverifiable이다. 관찰용 pidfd는 소유 Child 목록에 들어가지 않으며 신호·reap에 쓰이지 않는다.

`rx-solutionsd investigate CONFIG`는 조사 결과를 출력한다. 살아 있음이나 확인 불가에 자동 UnableToResolve 처분을 기록하지 않는다. F3의 처분 키가 불변이므로 자동 부정 처분을 쓰면 나중의 긍정 근거까지 영구 봉쇄하기 때문이다.

`rx-solutionsd resume CURRENT_CONFIG NEXT_CONFIG`가 명시적 재개 요청이다. 동일한 state root, 단일 status 선택, run ID 외 동일한 계획·카탈로그, restart budget 0만 허용한다. OriginalNotRunning 근거로 ConfirmedClosure를 기록하고, fresh 조사 결과와 기존 F3의 일회성 ResumeRequest/Permit으로 새 run·instance를 시작한다. 원 UNKNOWN, 결과 불명, 자원 회수 미주장과 업무 허가 미지원은 그대로다. 저장 요약만으로 permit을 복원할 수 없으며 소비·다른 run·다른 scope·등록 변경을 거절한다.

루트 `registration.db`는 여전히 하나이며 그 writer lock이 전체를 소유한다. 원 `supervisor.db`를 보존하고 **`runs/<run-id>/supervisor.db`**라는 실행 이력 저장소 종류를 추가한다. F3의 fresh execution store 요건을 충족하고 원 미결 상태를 덮지 않기 위한 책임 분리다. 일반 `run`은 이미 기록된 run만 선택하며 모르는 ID로 새 run 저장소를 자동 생성하지 않는다. 새 store 생성 직후 crash로 불완전한 저널이 남으면 자동 수리하지 않고 차단한다. 새 데몬·서비스·네트워크 API·production binary는 없다.

## 실행 증거와 호환성

구현 원본은 [rx-solutions f3a7d08c](https://github.com/jack0682/rx-solutions/commit/f3a7d08c53f71d481a9a06ecbe9597cf2e9e1274)와 [PR 31](https://github.com/jack0682/rx-solutions/pull/31)에 고정한다.

실제 관리자 프로세스를 SIGKILL한 뒤 새 관리자가 살아 있는 원 자식을 대조하고 재개를 거절했다. 외부 시험 관찰자는 namespace 수명을 유지하며 원 관리자의 소유 핸들을 전달하지 않았다. 시험 정리용으로만 상실 전에 연 pidfd로 자식을 종료·reap한 뒤, 새 관리자가 scope가 맞는 부재를 확인하여 새 run·instance로 재개했다. 이전 UNKNOWN과 미결 결과가 남았고 permit 재사용은 거절됐다. 별도 최소 권한 반례에서는 원 RX 자식의 PID8을 다른 프로세스가 실제 재사용했다. RX는 시작 시점 차이를 판별하고 대체 프로세스를 인수하거나 종료하지 않았다.

일반/특권 fixture 명령과 이미지·바이너리 해시, 최초 실패, 원시 출력, 기존 library 32단계와 resident/resource 통과선은 [검증 근거](../references/manager_loss_2026-09-24/README.md)에 있다. 커널 기구 검증, 실제 상주 연결, 미지원 경계를 분리한다. 실물 장비 검증·운영 배포·전체 상주 프레임워크 완성은 주장하지 않는다.

선택적인 생성 식별정보 필드가 저장 상태에 추가됐다. 이전 기록은 필드 없이 읽지만 조사 근거로 보완되지 않는다. 이전 writer의 downgrade 호환성은 보장하지 않는다. Rust Investigation 입력은 문자열에서 typed 근거로 바뀌고 Decision::Admitted에 optional identity 필드가 추가되어 소스 호환성 영향이 있다. 공유 SDK·wire/proto·규범 본문과 rx-platform, rx_ws/linux는 변경하지 않는다.
