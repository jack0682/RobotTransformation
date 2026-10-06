# F8 Linux 주소 공간 상한 집행

2026-09-24 · RX가 소유한 비구동 자식에 **프로세스별 가상 주소 공간 사용 상한**을 적용하고 관측한다. 확보 용량, 물리 메모리, 그룹 합산 예산이나 물리적 인계는 제공하지 않는다.

## 측정으로 고른 첫 범위

실제 runtime 이미지의 UID 10001, CapEff 0, read-only, no-new-privileges 조건에서 먼저 후보를 비교했다. cgroup2 마운트는 읽기 전용이었고 하위 생성은 EROFS(30)로 거절됐다. 이 실행 자세에는 위임된 cgroup 쓰기 권한이 없었다. 적절히 위임한 다른 호스트에서도 cgroup을 쓸 수 없다는 뜻은 아니다. 위임 조건은 [Linux cgroup v2 문서](https://docs.kernel.org/admin-guide/cgroup-v2.html)를 따른다.

같은 컨테이너의 부모와 기본 자식은 주소 공간 상한이 unlimited였다. 별도 자식만 64MiB로 낮추자 부모가 `/proc/PID/limits`에서 soft·hard 각각 67108864를 읽었고, 부모 자신의 값은 그대로였다. 128MiB `mmap`은 기본 자식에서 성공하고 제한한 자식에서 ENOMEM(12)로 거절됐다. 종료를 확인한 직후 해당 `/proc/PID`도 사라졌다. 이 단계는 기구 선정용 probe이며 RX 구현 수락 근거와 구분했다.

`Capacity::AddressSpaceBytes`를 추가했다. 기존 `MemoryBytes`를 다른 뜻으로 재해석하지 않았다. RLIMIT_AS는 가상 주소 공간을 제한하고 fork/exec 수명에서 상속되는 프로세스 속성이다. RSS·물리 RAM·예약 용량·할당 가용성 보장과 다르다. 커널 의미의 원본은 [getrlimit/prlimit 매뉴얼](https://man7.org/linux/man-pages/man2/getrlimit.2.html)이다.

## 실제 상주 레시피와 선택한 값

기존 `rx/status-http` 작성자 레시피에 268435456 bytes, 즉 256MiB 상한을 선언했다. 실제 이미지의 status 기동 `VmPeak`는 52219904 bytes(약 49.8MiB)였고, 이 상한에서도 health 응답을 관측했다. 선택값은 그 관측치의 약 5.14배다. 이 비율은 해당 시작 장면의 공학적 여유이며 모든 부하에서의 가용성을 증명하지 않는다. 구속력은 아래의 별도 초과 할당 장면으로 확인한다.

F7의 빈 요구 선언이 바뀌므로 **catalog digest도 바뀐다.** 기존 F7 등록을 새 데몬으로 열면 `resident catalog digest changed`로 거절된다. 실제 비교 절차에서 거절 전후 registration과 supervisor entity가 동일함을 확인한다. 이전 배치는 검토 전까지 새 레시피로 기동하지 않는다. 기존 기록 삭제, 자동 등록 교체나 무제한 실행을 이행 수단으로 제공하지 않는다.

비Linux에서는 요구를 건너뛰지 않고 명시적으로 거절한다. 이 때문에 Linux 전용 상한을 선언한 현재 status 레시피를 다른 OS에서 집행했다고 주장할 수 없다. 별도의 macOS 시험이 이 거절을 단언하며 새 `ignore`를 추가하지 않았다.

## 적용·관측·실행의 한 경계

초기 지원은 release hash로 확인한 `/usr/bin/python3` 비구동 프로그램이다. 실행 관리자 하나가 실제 Child를 소유하고, 그 자식은 고정된 내장 bootstrap에서 private Unix socket을 기다린다. 새 데몬·설치형 helper·서비스·네트워크 API는 없다. Bootstrap은 Python `-I -B`로 실행해 현재 디렉터리·user-site 모듈이 제한 적용 전에 끼어들지 못하게 한다. 로컬 `json.py`를 둔 별도 프로세스 반례도 거절했다. [Python 격리 모드 원본](https://docs.python.org/3/using/cmdline.html#cmdoption-I)을 따른다.

부모는 안전한 `rustix::process::prlimit` API로 그 Child의 soft·hard 상한을 적용하고 `/proc/PID/limits`를 읽는다. 그 뒤 등록과 lifecycle 권한을 다시 확인해야 EXEC를 보낸다. 자식은 같은 PID에서 최종 프로그램으로 exec하고 제어 소켓은 close-on-exec된다. 부모는 EOF만 믿지 않고 커널 명령행이 최종 argv인지, 같은 PID의 제한이 맞는지, 소유 Child가 아직 관측 가능한지 확인한다. 이 확인 뒤에만 영수증이 나온다. 프로젝트의 `unsafe_code = forbid`는 그대로다.

`LINUX_RLIMIT` 근거는 private field의 `KernelObservation`을 담고 전체 요청에 결속된다. 자기 보고인 HostReport나 Simulation에서 자동 승격되지 않는다. 영수증은 한 번의 시작 관측이며 지속 감시나 정책 정당성 인증이 아니다. 저장소용 `StoredLimit`은 별도 DTO라 역직렬화해도 현재 KernelObservation·Receipt가 되지 않는다.

## 실패와 전부 아니면 전무

미지원 종류가 섞이면 적용 전에 전체 묶음을 거절한다. CPU millicores, 물리 메모리, ReservedCapacity, ExclusiveAccess, SharedAccess는 요구별 사유를 가진 미지원으로 남는다. 같은 종류의 상한을 여러 개 선언하는 경우도 현재는 거절한다. 이미 상속한 hard limit을 올려야 하거나 필요한 권한이 없으면 묵시적 성공으로 바꾸지 않는다.

적용 뒤 관측이나 권한이 실패하면 EXEC 전의 소유 자식을 종료하고 wait로 종료를 확인해야 전부 미적용 거절이 된다. 명시적 exec 오류도 같은 방식으로 처리한다. 종료 확인 불가, EXEC 전달 불확실, 실행 창에서 자식이 죽어 최종 프로그램을 확인할 수 없는 경우는 Child를 보유한 채 `Uncertain`으로 남긴다. 시간 경과나 실패한 kill을 rollback 성공으로 바꾸지 않는다.

실제 Linux 시험은 hard limit을 낮춘 뒤 다시 높이려다 생긴 EPERM, 적용 후 관측 실패, 적용 후 권한 변경, exec syscall 실패와 exec 창의 자식 종료를 각각 다룬다. 앞의 네 장면은 자식 종료를 확인하고 실제 대상 프로그램이 실행되지 않았음을 단언한다. 마지막 장면은 EOF로 영수증을 만들지 않고 불확실성을 보존한다.

**여러 커널 정책의 부분 적용까지 검증했다고 주장하지 않는다.** 지원 정책은 하나이며 그 적용 뒤 후속 단계 실패와 rollback을 검증했다. 다른 종류가 섞인 묶음의 지원 부분만 적용하는 경로는 없다.

## 잔여 정책과 과거 기록

기존 Supervisor 저장소의 `Record.resources`에 마지막 관측과 수명 상태를 남긴다. 새 저장소는 추가하지 않는다. 과거 관측은 `NOT_ESTABLISHED_BY_HISTORY`라는 현재 집행 경계와 함께 표시한다.

| 상태 | 의미 |
|---|---|
| `OBSERVED_AT_START` | 해당 실행의 시작 시 커널 상한을 관측했다 |
| `NO_POLICY_REMAINING_AFTER_REJECTED_START` | 거절된 시도의 자식 종료를 확인했거나 적용 전 거절했다 |
| `UNCONFIRMED` | 소유·적용·종료 중 필요한 확인이 없으며 현재 집행이나 부재를 추론하지 않는다 |
| `DIRECT_CHILD_EXITED_DESCENDANTS_UNASSESSED` | 소유한 직접 자식의 종료만 확인했다. 후손의 정책 수명은 확인하지 않았다 |

관리자 재개 후에는 과거 관측을 유지하면서 Application은 `Unconfirmed`이고 영수증은 복원되지 않는다. 사용 상한과 별도로 `capacity_reservation`을 표시하며, 이 backend가 예약을 만들지 않았음을 확인한 경우에만 `NONE_CREATED`다. 불확실한 시도는 `NOT_ESTABLISHED`다. `physical_handover`는 항상 `NOT_ASSESSED`다. 자식별 상한을 모두 더한 총량, 후손 종료, 협업 자원 반환을 주장하지 않는다.

## 실제 검증과 호환성

구현 원본은 [rx-solutions `fa8ea7e5`](https://github.com/jack0682/rx-solutions/commit/fa8ea7e53076ede4bf76a838c7c26a70ffaa7647)에 고정된다.

`tools/resource_enforcement_passage.py`는 기존 resident 통과선을 먼저 실행한다. 그 뒤 실제 새 데몬의 자식 제한을 **supervisor 밖의 별도 프로세스**가 읽는다. 부모는 unlimited이고 자식은 256MiB이며, Docker Memory·NanoCpus·Ulimits 옵션에 자원 제한을 주지 않았음을 함께 기록한다. 설정 성공 출력만으로 수락하지 않는다.

별도로 작성한 시험 카탈로그의 64MiB 자식은 실제 RX backend 경로로 시작되고, 128MiB mmap이 ENOMEM으로 거절된다. 이 시험의 별도 관측자 PID도 supervisor와 다르다. 시험용으로 조인 상한이며 production status의 정상 부하를 실패시켰다고 주장하지 않는다.

기존 library 통과선은 32단계를 유지한다. 바뀐 카탈로그에 맞춰 이전 `NO_REQUIREMENTS` 단언을 `LINUX_RLIMIT` 및 정확한 soft·hard 값 단언으로 강화했고, 시험용 Owned wrapper가 요구 경로도 실제 OS backend에 전달하게 했다. 기존 등록·복구·준비·의존·외부 서명 장면을 삭제하거나 ignore하지 않았다. 기존 resident 통과선의 단언은 유지한다.

로컬 Rust의 Capacity·Evidence와 저장 상태의 선택 필드가 늘었으며 이전 state는 필드 없이 읽힌다. 이전 writer가 새 필드와 의미를 이해하는 downgrade 호환성은 주장하지 않는다. 공유 SDK·wire/proto·규범 본문은 바꾸지 않았다. 직접 의존성으로 고정한 rustix 1.1.4는 기존 lockfile에도 있던 버전이며 unsafe 정책을 완화하지 않는다.

원시 성공·실패 출력, 명령, 이미지·바이너리 해시와 집계는 [검증 근거](../references/linux_address_space_2026-09-24/README.md)에 있다. 주소 공간 상한 한 종류의 통과를 전체 자원 관리·상주 프레임워크·실물 장비 적격으로 확대하지 않는다. 실제 guarded 통합, 총체적 관리자 상실 복구, 운영 영역 업무 판단 집행, 의존 교체와 기존 제어 신호 경쟁은 후속 범위다.
