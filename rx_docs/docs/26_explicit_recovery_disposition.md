# F3 명시적 복구 처분과 새 실행

2026-09-23 · **첫 provider: 실제 소유 Child 핸들이 남아 있는 비구동 실행의 종료 관측. manager 프로세스 전체 상실 이후의 외부 조사 provider는 미지원.**

이 문서는 F3의 범위를 기록한다. 후속 [F4](27_readiness_and_work_use.md)는 별도 자기 보고 준비 조건과 업무 판단 조회를 추가하지만, 과거 처분을 준비나 업무 허가로 승격하지 않는다.

## 결정과 원 관측

[F2](25_component_registration.md)는 실행 상실 뒤 등록과 UNKNOWN을 보존했지만 미결 배정의 다음 실행을 열 수 없었다. F3는 원 관측을 바꾸지 않는 별도 처분과 명시적 재개 요청을 추가한다. 과거 수행 결과의 확정·현재 자원의 복구·새 업무 허가는 서로 다른 판단이다. 이 구현이 여는 것은 한 비구동 호스트 실행의 새로운 배정 경로다. 물리 수행의 복구나 업무 허가는 아니다.

원 관측은 registration/instance, 저장 revision, 전체 Execution digest로 참조한다. 처분 뒤에도 원 `last_observed: UNKNOWN`, PID와 오류, 당시 catalog와 등록 revision이 그대로 남는다. 처분 기록은 새 schema/key의 이벤트·투영으로 원자적으로 저장한다. 처분을 가진 원 관측의 변경은 거절한다. 새 관측을 정정으로 덮어쓰는 대신 별도 근거가 필요하다.

등록 모듈은 계속 `Supervisor`, `Plan`, `State`나 OS에 의존하지 않는다. 독립 등록부가 기록과 차단 조건을 소유하고, 외부 `RecoveryAuthority`가 좁은 소프트웨어 처분·재개 정책을 판정한다. 실제 종료 근거는 `OsProcesses`가 제공한다. 이 배치는 구성요소 관리 책임의 최종 소유를 확정하지 않는다.

## 첫 근거 provider와 권한

`OsProcesses::observe_recovery_exit`는 현재 소유 중인 **비구동 direct Child**의 종료를 실제 OS 핸들로 관측하고 해당 핸들을 회수한 뒤에만 `OwnedExit`를 만든다. 살아 있는 child, 핸들 부재, 다른 효과 등급은 거절된다. 저장된 PID를 조회하거나 신호를 보내는 것으로 토큰을 만들지 않는다.

`OwnedExit`는 필드와 생성자가 외부에 공개되지 않고 Serialize만 지원한다. 저장 JSON을 Deserialize해 살아 있는 증거 토큰으로 복구할 수 없다. 처분 저장소에는 증거의 참조 ID와 digest만 남는다. 토큰을 부활시키는 대신 이미 검증된 처분의 독립 기록을 읽는다.

처분은 다음을 함께 확인한다.

- 원 관측의 정확한 instance/revision/digest와 저장 PID가 종료 증거에 일치한다.
- 보고의 행위자, `host/direct-child-exit` 범위, 실제 관측 시점, 절차가 존재하고 증거의 시점과 일치한다.
- `RecoveryAuthority`가 해당 요청을 허용한다. 기본 구현 `DenyRecovery`는 처분과 재개를 모두 거절한다.
- 원 관측이 UNKNOWN 또는 ASSIGNED의 미확정 범위다. 원 PID가 기록되지 않은 사례는 이 첫 provider로 확인할 수 없다.

`timeout`, 현재 idle, 프로세스 부재, 시간 경과만으로는 처분되지 않는다. 필드를 채운 문장이나 enum 이름을 확인된 종료 증거로 취급하지 않는다. 조사 보고는 별도의 해결 불가 처분에만 사용할 수 있다.

행위자 문자열은 인증이 아니다. 운영 통합은 호출 주체를 인증된 로컬 정책에 결속해야 하며 authority 구현은 트랜잭션 안에서 OS/네트워크 호출을 하지 않는 순수 정책 판정이어야 한다. typed 증거는 신뢰된 원 backend의 Child 관측을 결속한다. 임의 호스트 코드·OS·저장소를 변경할 수 있는 관리자를 격리하거나 임의 조사 내용의 진실성을 자동 보증하지 않는다. direct Child 종료는 자손 프로세스 종료·장치 상태·물품 지지·공유 자원 인계를 증명하지 않는다.

## 두 처분과 독립 판단

| 항목 | CONFIRMED_CLOSURE | UNABLE_TO_RESOLVE |
|---|---|---|
| 근거 | 소유 Child의 실제 종료 토큰 + 명시적 정책 | 권한 있는 조사 보고·시점·절차와 미해결 설명 |
| 원 관측 | 원 UNKNOWN과 이력 그대로 | 원 UNKNOWN과 이력 그대로 |
| past_outcome | UNRESOLVED | UNRESOLVED |
| resource_recovery | NOT_CLAIMED | NOT_CLAIMED |
| work_use_permission | UNSUPPORTED | UNSUPPORTED |
| 다음 실행 | 별도 명시적 재개 요청 필요 | 차단 유지 |

확인된 것은 direct Child의 폐쇄 조건이다. 과거 업무의 성공·실패나 물리 결과를 알아냈다는 뜻이 아니다. 해결 불가 조사를 확인된 폐쇄로 표시하거나 past_outcome을 SUCCESS로 표시하는 입력은 거절된다. 처분은 F1 Receipt를 복원하지 않고 자원 적용을 주장하지 않는다.

**현재의 지속 차단은 외부 조사 provider가 이번에 미지원이기 때문에 생기는 결과이며, 미해결이 자원을 영원히 막아야 한다는 설계 주장이 아니다.** 개념 명세 §10.4의 탈출구는 별도로 허용된 복구 절차가 현재 상태·잔여 명령·제어 권한·물품 지지 등 필요한 조건을 확인하고, 그 근거를 원 수행에 연결한 복구 처분으로 인계하는 것이다. 그 외부 provider는 이 칸에서 비어 있다. 현재 해결 불가 처분의 정정/후속 판정 체인도 구현하지 않았다. 원 기록을 지워 우회하는 기능은 제공하지 않는다.

## 명시적 재개와 한 번의 소비

확인된 처분만으로 새 배정이 열리지 않는다. 별도 `ResumeRequest`는 자신의 요청 ID, 행위자·시점, 처분 ID, 새 run ID를 갖고 새로운 `may_resume` 판정을 받아야 한다. 등록은 ACCEPTED여야 하고 검토한 catalog가 일치해야 한다. 과거 run을 재사용할 수 없다.

한 확인 처분에는 하나의 명시적 재개 요청만 결속한다. 미소비 요청을 같은 내용으로 재전달하면 권한과 현재 선언을 다시 확인해 토큰을 재발급할 수 있다. 이미 소비됐거나 다른 요청으로 바꾸려 하면 거절한다. `ResumePermit`도 Deserialize하지 않는다.

`RegisteredSupervisor::open_with_resume`는 **새 실행 저장소와 새 run**, 자동 재시도 예산0을 요구한다. 원 supervisor의 UNKNOWN을 Pending으로 바꾸거나 이전 instance를 재사용하지 않는다. 최초 새 배정과 재개 요청의 소비는 같은 등록부 트랜잭션이다. 실패하면 둘 다 rollback되며, OS 효과 전에 기록을 끝낸다. 현재 lifecycle 권한·등록 상태/revision/catalog·F1 수락은 새 시작에서 다시 확인한다.

소비 뒤 같은 토큰이나 같은 확인 처분으로 두 번째 재개를 시도하면 거절된다. 새 실행의 종료 후 통상의 명시적 다음 실행까지 과거 UNKNOWN 때문에 계속 막지는 않지만, 새 실행 자체가 미결이면 그것은 별도 차단 사유다. 이전 수행의 재호출이나 자동 재시작을 복구로 포장하지 않는다.

`View.recovery`는 처분, 명시적 요청/소비, `new_execution`의 현재 복구 차단 상태를 함께 제공한다. 이 필드는 복구 조건만 답하며 lifecycle 권한·F1 집행·기능 준비·업무 사용을 승인하지 않는다. 등록과 실행 관리의 두 저장소 및 OS를 하나의 분산 트랜잭션이라고 주장하지 않는다. 소비 후 다른 저장소의 기록 실패는 새 미결 배정을 남길 수 있고 같은 토큰으로 재생하지 않는다.

## 하나의 실제 Linux 통과선

F2의 기존 절차를 확장했다. 별도 시연 기능을 만들지 않았다.

```sh
python3 tools/registration_passage.py --image RX_RUNTIME_IMAGE --evidence /tmp/rx-f3-passage-new
```

기존 등록·F1 수락·인스턴스 HTTP·정상 종료·새 manager 프로세스의 조회를 유지한다. 그 뒤 기존 `lost-manager-ownership` 장면에서 다음을 이어서 실행한다.

1. 새 manager는 UNKNOWN을 보며 옛 backend는 실제 child 핸들을 보유한다.
2. 살아 있는 child의 종료 증거 발급은 거절된다. 옛 소유자가 정상 종료를 요청하고 실제 exit·핸들 회수를 관측한다.
3. 기본 처분 권한은 거절한다. 명시적 시험 정책은 별도 처분을 기록하고 원 UNKNOWN 및 이전 이력이 같음을 단언한다.
4. 처분만으로 배정하려는 시도를 실제로 거절한다.
5. 명시적 재개 요청을 소비해 새 run/instance로 실행하고, 새 F1 Receipt 및 인스턴스가 일치하는 HTTP 응답을 확인한다. 기존 Receipt는 복원하지 않는다.
6. 새 child의 정상 종료를 관측한다. 같은 요청과 소비된 토큰의 재사용을 모두 거절한다.

절차의 JSON은 `explicit-disposition`, `disposition-alone-rejected`, `explicitly-resumed-new-instance`, `resumed-child-terminated`, `second-resume-request-rejected`, `consumed-permit-rejected`를 구분한다. 마지막 limitations에는 **manager 프로세스 전체가 죽어 Child 핸들까지 사라진 경우의 외부 조사 provider 미지원**을 포함한다.

이 장면의 manager 재개는 객체·저장소 재개다. 옛 프로세스 전체를 잃은 뒤 새 프로세스가 OS 핸들을 복구했다고 주장하지 않는다. 앞 단계의 별도 manager 프로세스 재조회와 혼동하지 않는다. 실제 서비스의 F1 선언은 빈 요구이므로 어떤 자원도 집행하지 않는다. 자원 제한이 설정되었다는 사실은 최악 응답 시간을 입증한 것이 아니다.

## 검증과 남은 범위

| 증거 종류 | 범위 |
|---|---|
| 문서·정적 대조 | §10.2/10.4/12.4/12.6·AC17, 독립 등록 모듈, 새 local schema |
| 실제 macOS Child + SQLite | 약한 근거/권한 거절, 원 관측 보존, 새 신원, 중복 소비, 기본 거부, PID 바인딩 |
| 저장 실패 주입 | 처분 rollback, 소비+배정 rollback, 명시적 동일 요청 재시도 |
| 외부 크레이트 컴파일 공격 | private 증거 필드 생성, OwnedExit/ResumePermit 역직렬화 거절 및 정상 조회 API의 컴파일 성공 |
| 실제 Linux 실행 | 기존 상태 서비스의 확장된 단일 통과선과 단계별 원시 출력 |

준비 판정·업무 사용 허가(F4), 의존 결합(F5), Linux 자원 집행, 다중 호스트, 물리 수행 복구·실물 자격은 미지원이다. 전체 핸들 상실 또는 원 PID가 없는 미결에 대한 외부 조사, 자손/자원 인계의 확인, 해결 불가 처분의 후속 판정 체인은 추가 설계·provider가 필요하다. typed 토큰과 시험 통과 개수를 프레임워크 완성이나 물리 안전의 증거로 쓰지 않는다.

기존 공유 규범 v1.0·wire/proto·SDK·manifest는 변경하지 않는다. F2의 등록/실행 schema와 원 records를 변환하지 않으며 새 처분/재개 문서 타입과 조회 필드를 추가한다. F3 이전 바이너리로의 의미적 downgrade는 지원한다고 주장하지 않는다. 구버전은 새 처분을 실행 권한으로 해석하지 못하므로 차단할 수 있고, 처분 이후의 원 관측 보호 계약도 모르므로 같은 저장소의 writer로 사용해서는 안 된다.

## 이번 실행 기록

2026-09-23에 [구현 ceabf1b](https://github.com/jack0682/rx-solutions/tree/ceabf1b788b639141f05f8947fa3f8fb1da4a42d/runtime/rx-supervisor)를 실행했다. 새 복구 시험9개와 macOS 전체 workspace의 순차 실행296 passed / 0 failed / 17 ignored, 전체 clippy·format이 통과했다. 외부 크레이트의 증거 필드 생성은 E0451, 증거/재개 허가 역직렬화는 E0277로 실패했고 같은 consumer를 정상 조회 API로 복원하면 각각 exit0이었다.

기존 macOS 병렬 실행에서 새 복구 시험의 writer-lock 거절3건, 다른 전체 실행에서는 변경하지 않은 rx-host 시험의 같은 거절1건을 관찰했다. 새 실제 OS 시험은 시나리오별로 격리했다. 기존 host 시험/저장소 코드는 그대로 두었고, 원 기준 소스를 별도 source/target으로 실행한 병렬5회에서는 재현되지 않았다. 정확한 원인은 미확정이며 저장소 버그를 수정했다고 주장하지 않는다. 원시 실패와 순차/단독 성공을 함께 보존했다.

확장된 실제 Linux 절차는 parent 시험1개 안의 worker5단계에서13개 단계 관측을 남겼다. 원 인스턴스 `22287404-ff3d-4156-acc7-3b925efad68d`의 UNKNOWN은 그대로 남고, 처분 `8845f566-55b0-4f22-bbf1-8ee4407208e9` 뒤 새 인스턴스 `f44f2d2a-c75a-484d-a95c-2dce900b0b07`가 별도 요청의 단일 소비로 실행됐다. 새 F1 Receipt와 인스턴스 HTTP를 확인한 뒤 정상 종료했고 두 번째 요청/토큰은 거절됐다.

Runtime 이미지 `sha256:fcb56bfdfcc1f68bf8cfb6d28f7f24d5899f5e31030ee2a882f6e29e1e28b4a0`, Rust1.98.1 builder `sha256:ff521445a372125ed4f76e1453a1f8098f2d05332d1601d30db1c1f62757e730`를 사용했다. 실제 상태 서비스와 현재 원본 hash는 `c1101a2675e03a15f71d4e236a01c9c43140fb53364b03c3d0c3af52809c6975`로 일치했다. [절차](https://github.com/jack0682/rx-solutions/blob/ceabf1b788b639141f05f8947fa3f8fb1da4a42d/tools/registration_passage.py)와 [단계별 단언](https://github.com/jack0682/rx-solutions/blob/ceabf1b788b639141f05f8947fa3f8fb1da4a42d/runtime/rx-supervisor/tests/registration_passage.rs)을 함께 고정했다. 원시 명령·출력·SQLite는 절차의 evidence 디렉터리에 남는다. 이것은 물리 복구·자원 인계·업무 허가의 증거가 아니다.
