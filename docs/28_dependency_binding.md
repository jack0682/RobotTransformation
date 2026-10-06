# F5 진단 소비 작업과 의존 결합

2026-09-23 · **지원 범위: 실제 구성요소 보고를 소비하는 비구동 진단 작업의 수명·기록·구간별 재판정. 초기 결합·교체 결합의 긍정 수용과 업무 사용 허가는 미지원이다.**

후속 [F6](29_verified_external_decisions.md)은 초기·교체 판단에 검증된 외부 승인을 추가한다. 승인 검증이 관계를 자동 변경하지 않고 기본 제품은 앵커가 없어 승인할 수 없다. 아래 F5 당시의 결과와 미지원 표기는 과거 범위로 보존한다.

## 세 대상이 실제로 생긴 범위

기존 상태 서비스를 두 번 등록하면 서로를 소비하지 않는 보고자 두 개가 생긴다. 기존 [F4](27_readiness_and_work_use.md)의 `assess_use`도 동기 자기 보고 snapshot이므로 그 자체가 진행 중 소비 작업은 아니다. 이 한계를 확인한 뒤, 프레임워크가 제공하는 최소 read-only 진단 소비 작업을 별도로 만들었다. 새 바이너리·native 서비스·이미지는 추가하지 않았다.

`registration::diagnostic::Consumer`는 F2와 같은 `Repository` 포트를 통해 다음을 기록한다. `Supervisor`, 프로세스 `Plan`과 `State`, OS 종료 기능에 의존하지 않는다.

| 대상 | 실제 객체와 동작 |
|---|---|
| 신규 배정 | 진단 run을 `Assigned`로 기록하는 `assign` |
| 진행 중 수행 | `begin`으로 `Running`이 된 run; `poll`은 필요한 현재 보고를 수집하고 `finish`는 결과 생성 조건을 확인 |
| 이미 생성된 결과의 소비 | 완료한 run과 결속된 `DiagnosticResult`; `consume_result`가 현재 진단 소비 가능성을 별도 판정 |

`finish`는 실제 수집한 보고·출처·요청 참조·제공자 신원을 소비해 결과 본문과 digest를 만들고, 결과 기록과 `Completed` 전이를 같은 저장 transaction으로 커밋한다. 기록 실패 시 부분 결과나 완료 이력이 남지 않는다. 독립 profile은 실제 작성자 catalog 내용을 요약한 결과를 만든다. 단지 상태 프로세스가 살아 있다는 사실을 작업 수행으로 바꾸지 않는다.

**모든 run과 결과는 `DIAGNOSTIC_ONLY`다. 결과의 `work_use`는 `UNSUPPORTED`이며 진단 소비 가능은 업무 사용 허가가 아니다.**

## 작성자 선언과 세 필요 구간

소비 기능은 별도 작성자 `Catalog`를 갖는다. 이 catalog의 program/version/profile/dependency 전체 digest를 소비 등록에 결속한다. 현장 요청은 작성된 작업 이름과 제공자 후보를 고를 수 있지만 기존 profile의 필요 구간을 덮어쓸 수 없다. 낮춘 catalog로 같은 등록을 열면 거절된다. 기존 `Program`과 상태 서비스의 catalog/digest는 변경하지 않았다.

| 선언 | 의미 |
|---|---|
| `Undeclared` | 작성자가 구간을 선언하지 않음 → `UNSUPPORTED` |
| `Unknown` | 범위가 아직 알려지지 않았다는 이름 붙은 사유 → `NOT_EVALUATED` |
| `Independent` | 작성자가 제공자 입력이 필요 없다고 명시한 catalog-summary 작업 |
| `Required` | 제공자 role·해석 이름·필요 구간을 명시 |

`Required`의 세 구간은 다음과 같다.

| 구간 / 기본 profile | 입력을 요구하는 경계 | 생성된 결과의 진단 소비 |
|---|---|---|
| `PreparationOnly` / `snapshot-after-preparation` | 배정 때 현재 입력을 캡처하고 이후 해당 run은 그 입력을 소비 | 과거 snapshot으로 읽음; 제공자 종료만으로 무효화하지 않음 |
| `ResultGeneration` / `snapshot-at-generation` | 배정·시작은 결과 envelope 준비; `finish` 직전 현재 입력 필요 | 생성 시점 snapshot으로 읽음; 이후 생존을 영구 요구하지 않음 |
| `Continuous` / `current-report-collection` | 배정·시작·수집·완료의 각 checkpoint에서 현재 입력 필요 | 같은 제공자 실행/설정과 현재 보고 digest까지 대조하고 현재 소비를 판단 |

지속 구간은 **호출자가 구동하는 명시적 checkpoint에서 확인하는 범위**다. 자율 감시 스레드, 주기 보장, 두 관측 사이의 연속 가용성 또는 물리 보호를 구현한 것이 아니다. 결과 생성 시점 구간에서 입력 부재가 신규 진단 배정을 막지 않는 것은 조건 적용 시점을 뒤로 둔 선언의 의미이지, 현재 입력을 확인했다는 뜻이 아니다.

## 등록 결합·관측·출처

제공자는 기존 `rx/status-http` 등록이며 소비자는 실행 파일이 없는 프레임워크 진단 기능의 별도 등록이다. 각각의 저장소를 사용할 수 있다. 이를 다중 저장소 원자 transaction이나 분산 등록 권위로 보고하지 않는다.

`TrackedBinding`은 소비/제공 등록·revision·catalog, 작업 profile, 운영 영역을 기록한다. 제공자 실행이 0개여도 이 관계를 조회할 수 있다. 최초 유효 입력은 제공자의 run/instance/PID/설정 digest를 고정한다. **이 기록은 진단 추적 관계이며 수용된 업무 결합이 아니다.**

관측 I/O는 `RegisteredSupervisor`의 별도 `Source` adapter가 담당한다. 기존 F4의 현재 소유 Child와 HTTP 관측 경로를 재사용한다. 매 호출의 opaque `Probe`는 nonce·관계·진단 run·단계·제공자 참조·범위를 묶으며 `ProviderObservation`은 외부 생성·역직렬화가 불가능하다. 과거 응답, 다른 등록/revision/catalog, 다른 실행이나 설정은 현재 입력으로 승격되지 않는다. 저장 `Sample`은 읽을 수 있는 과거 데이터이며 생존 증거나 수용 토큰으로 복원되지 않는다.

보고 값의 출처는 F4와 같다. instance는 환경변수, native count는 시작 시 audit, profile counts는 시작 시 catalog, schema와 operator 상태는 릴리스 정적 선언이다. 진단 결과가 이를 보유하더라도 독립적 기능 동작·보정·물리 조건·안전·품질을 입증하지 않는다. 신뢰된 작성자와 로컬 관측 adapter/저장소가 전제이며 악의적인 OS/DB 관리자를 격리하는 구조가 아니다.

## 상실 시 세 판단

`inspect`는 `new_assignment`, `ongoing`, `result_consumption`을 각각 반환한다. 각 축은 F4의 `NOT_EVALUATED`, `NOT_MET`, `UNSUPPORTED`, `SATISFIED`와 이름 붙은 조건을 사용한다. 부족한 입력을 일반 성공/실패 하나로 덮지 않는다. 조회는 기존 진단 이력을 바꾸지 않는다.

| 관측한 장면 | 신규 배정 | 진행 중 | 기록된 결과 소비 |
|---|---|---|---|
| 준비 때 실제 입력을 얻은 뒤 제공자 종료 | 새 캡처 불가 | 캡처한 입력으로 계속 완료 | 원 snapshot 유지 |
| 지속 수집 중 제공자 종료 | 현재 입력 없음 | 다음 수집/완료 보류, 새 결과 없음 | 현재 소비 보류; 원본은 유지 |
| 결과 생성 직전 제공자 종료 | 입력 요구 전 배정 가능 | 결과 생성 보류 | 이미 생성된 snapshot은 유지 |

현재 소비의 보류와 과거 결과 삭제는 다르다. `recorded_result`는 원본과 digest·완료 run 결속을 확인해 과거 기록을 읽는다. `consume_result`는 현재 등록 및 해석/출처 조건까지 적용하며 조건을 충족하지 못하면 소비 결과를 반환하지 않는다. 예를 들어 보고 내용이 바뀌면 지속 profile의 기존 결과는 현재 소비가 보류된다. 소비 등록 퇴역도 현재 사용을 막지만 과거 기록을 덮어쓰지 않는다.

이 모듈에는 프로세스 정지 API가 없다. 제공자 상실은 해당 관계·run·결과를 재판정한다. 실제 Linux 절차에서 이미 진행 중이던 무관한 catalog-summary 작업은 상실 후에도 자신의 결과를 기록했다. 이것이 모든 작업의 무중단 보장은 아니다.

## 초기 수용과 교체 수용

`BindingJudgment`는 소비 측 작업 판단 책임의 기본 미지원 포트다. 요청은 `Initial`과 `Replacement`를 구분하고, 교체에는 별도 제공자 후보가 필요하다. 응답은 미평가·거부·미지원뿐이며 긍정 변종이나 호스트 발급 경로가 없다. 명시적 거부는 decision reference를 갖고, 판단자 미연결은 `binding/consumer-judgment-provider` 미지원이다. 비어 있거나 과대한 사유도 named 미지원으로 처리한다.

같은 형식/조건을 만족하는 새 실제 제공자도 기존 binding에 자동으로 들어오지 않는다. 같은 등록이 새 instance로 재시작해도 고정한 실행 세대를 승계하지 못한다. 교체 판단 조회는 원 관계와 진행 run 및 결과를 변경하지 않는다. 새 진단 관계를 명시적으로 기록할 수는 있지만 새 ID이며, 이전 작업을 승계하거나 업무 결합을 수용한 것이 아니다.

긍정 결합 수용 provider와 긍정 업무 허가 provider는 모두 미지원이다. 이 부재 때문에 진단 수행을 수용된 업무로 부르거나, 반대로 실제 보고 읽기/기록까지 구현 불가능하다고 처리하지 않는다.

## 기존 경계와 저장 범위

`depends_on`은 plan-local 검증·위상 수용, 기동 게이팅, 실행 중 의존 상실 표시, 역순 종료 차단이라는 네 동작을 그대로 유지한다. 새 기능 의존을 이 필드에 넣지 않았다. 기존 plan/supervisor 본문과 기존 시험 단언을 보존한다. F1 수락·F2 등록 신원·F3 증거/복구·F4 준비/허가 축은 진단 결과로 승격되거나 대체되지 않는다.

새 catalog와 저장 문서는 로컬 진단 API의 추가다. 공유 규범·wire/proto·SDK·manifest·dependency/lock은 변경하지 않는다. 기존 `Program` literal이나 F4 query의 직렬화 형식 변경은 없다. 옛 writer가 F5의 새 의미를 집행한다는 semantic downgrade 호환성은 주장하지 않는다.

등록당 관계64개, run512개, run당 sample16개로 제한한다. 수집은 완료용 마지막 sample 공간을 남긴다. 삭제·자동 만료·archive API는 없다. 보존한 기록은 해당 repository의 수명을 따르며 용량 한계에서는 새 작업을 거절하고 별도 보존 정책을 요구한다. 진행 중 run 취소/이관, 자동 재시도·스케줄링, 다단계 의존 그래프는 현재 지원하지 않는다.

## 검증의 종류와 범위

같은 `tools/registration_passage.py` 절차에 진단 worker를 추가했다. 기존5 worker의 단언은 그대로이며 전체는 parent1개·worker6개·관측24단계다. 실제 설치된 상태 서비스를 읽고 consumer repository에 결과를 기록한다. 이 수를 독립 시험24개로 세지 않는다.

단위/통합 시험은 명시적 HTTP fixture의 보고 변경, 계획된 종료와 비계획 종료, scope 강등, 동일 형식/새 세대, 관측 재생, 등록 퇴역, 용량 경계와 저장 rollback을 구별한다. fixture 값은 실제 audit 결과로 가장하지 않는다. 외부 consumer에서 catalog 편집/역직렬화·초기/교체 긍정 변종·opaque 관측 생성·과거 기록의 생존 증거 승격을 시도하고 정상 reader로 복원하는 대조도 실행한다.

실제 장비 동작, 협업 자원 경합/결합, Linux 자원 집행, 다중 호스트, 긍정 업무 허가, F3 외부 조사 provider, F4 제어 효과의 group-target 신호 경쟁은 미지원 또는 기존 미결이다. 새 진단 결과는 이 경계를 해소하지 않는다.

## 구현과 실행한 결과

구현은 [rx-solutions `8e5051cd`](https://github.com/jack0682/rx-solutions/commit/8e5051cd1c02a2d6876d7e2dcf9c640771086f2e)에 고정된다. 재현 진입점은 [같은 Linux 절차](https://github.com/jack0682/rx-solutions/blob/8e5051cd1c02a2d6876d7e2dcf9c640771086f2e/tools/registration_passage.py), [소비 작업 시험](https://github.com/jack0682/rx-solutions/blob/8e5051cd1c02a2d6876d7e2dcf9c640771086f2e/runtime/rx-supervisor/tests/dependency_binding.rs), [실제 의존 장면](https://github.com/jack0682/rx-solutions/blob/8e5051cd1c02a2d6876d7e2dcf9c640771086f2e/runtime/rx-supervisor/tests/support/dependency_passage.rs)이다.

- macOS workspace: **319 통과, 0 실패, 17 ignored**, 전용 target에서 `--test-threads=1`로 실행했다. 새 진단 시험10개는 이 수에 포함된다.
- 전체 workspace/all-targets/all-features clippy `-D warnings`와 fmt, 저장소·문서 표·invariant 검사가 통과했다.
- 외부 compiler 공격10종은 예상 `E0277`/`E0616`/`E0624`/`E0599`로 거절됐고, 같은 consumer를 정상 읽기 코드로 복원하면10종 모두 컴파일됐다.
- 실제 Linux 절차는 parent1·worker6·관측24단계로 완료했다. Runtime image `sha256:fcb56bfdfcc1f68bf8cfb6d28f7f24d5899f5e31030ee2a882f6e29e1e28b4a0`, builder `sha256:ff521445a372125ed4f76e1453a1f8098f2d05332d1601d30db1c1f62757e730`을 사용했다. 기존 publisher source hash는 바뀌지 않았다.
- 기존 runtime 시험 파일48개와 plan/supervisor 본문을 byte 단위로 대조했다. 단일 passage는 기존 단언을 유지하고 worker·관측을 추가했다.

초기 실패도 남겼다. 새 시험의 비계획 종료 대기는 기존 `all_exited` 의미를 잘못 사용해 `Exited`와 소유 handle 회수 확인으로 고쳤다. 퇴역한 소비 등록의 조회는 이른 오류 대신 현재 사용 불가 사유를 반환하도록 보완했다. 최종 경계 검토에서는 새 실행이 아직 없는 구간을 다른 실행으로 바뀐 것으로 분류하던 결함을 먼저 실패 시험으로 재현한 뒤, 근거가 없는 구간을 미평가로 유지하도록 고쳤다. 실제 새 실행이 관측되면 기존 결합 승계는 계속 거절된다.
