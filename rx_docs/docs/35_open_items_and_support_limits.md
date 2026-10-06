# F12 이월 미결과 실제 지원 제한

구현 고정: [rx-solutions bfd66e7a](https://github.com/jack0682/rx-solutions/commit/bfd66e7a0433340fc1d7e900989475fb4b2abb1f).

2026-09-24. 첫 기준선은 출하 `rx-solutionsd`의 status 진단 및 문서화된 guarded Host/Executor 소프트웨어 수명 경로, 명시적 recovery/work/replacement API다. status 시험만 실행했다는 이유로 guarded 경로를 제외하지 않는다. 물리 제어 명령의 승인이나 장비 적격을 첫 기준선으로 바꾸지도 않는다.

분류는 **어떤 실행 경로가 해당 조건을 지나는가**로 정한다. 해결, 런타임에서 거절하는 지원 제한, 지원 계약 안에서 허용된 의미, 경로가 통과하지 않는 범위를 구별한다. “후속 작업” 자체는 분류가 아니다. 확정하지 못한 사실은 별도로 남긴다.

## 분류와 동작·진단·문서 대조

| 이월 항목 | 첫 기준선 경로 | 분류와 실제 동작 | 진단 및 실행 근거 |
|---|---|---|---|
| status script와 inventory 동시 교체 | 모든 resident 명령 → release_programs | 지원 제한 집행. 설치 script/catalog가 컴파일에 포함된 원본 내용과 다르면 거절 | `release/source-pin-mismatch`; 기존 0/1/0 반례가 정상0/script변조1/함께변조1로 바뀜 |
| 인증된 불변 릴리스 출처 | 같은 기동 경로의 신뢰 전제 | F12 시점에는 미해결. [G2](37_authenticated_release_origin.md)가 개발 루트에 대한 내용 인증과 보존 상태의 rollback·철회 거절을 추가함. 현재도 verifier/OS, 통째 상태 복원, offline 최신성, 제품 키 수탁은 명시적인 신뢰·미확립 경계 | `release_boundary.trust`, `authenticated_immutable_provenance: NOT_ESTABLISHED`; F12 source 고정을 배포 서명으로 부르지 않음. G2 개발 서명도 verifier/OS 자체 인증이나 제품 권한 수탁으로 승격하지 않음 |
| guarded 종료 신호 실패/종료 관측 경합 | GuardedServices → terminate → tick → guarded final report | 지원 제한 집행. 실패한 전달은 완료가 아니며 소유 핸들을 유지. 이후 같은 자식의 실제 종료와 현재 final report가 둘 다 있어야 confirmed | 실제 Linux 자식 + 명시적 실패 주입에서 StopRequested 유지; final report 없음은 guarded_shutdown_confirmed=false, 유효 보고+exit0만 true |
| 강제 종료와 물리 lifecycle 권한 | guarded service stop 및 RequiresPlatformAuthority 입구 | 지원 제한 집행. guarded force 거절, 직접 물리 lifecycle 권한은 GuardedServices가 발급하지 않음 | 실제 guarded_os 시험에서 force 거절 및 leader에만 TERM; platform-authority recipe는 기존 admission 시험에서 거절 |
| Host 런타임 소유 락 실패 | Host run / maintenance stopped_store | 지원 제한 집행. 서비스 진입 거절, 소유자 신원 추정 금지 | `host/runtime-ownership-unavailable`; 별도 Linux 프로세스가 실제 락을 보유한 장면에서 DB/상태 불변, 홀더 종료를 관측한 뒤 명시적 재시도 성공 |
| 저장소 writer 락 실패 / F9 flake | resident·Host·Executor의 SQLite open | 지원 제한 집행. 기존 배타 락 거절을 유지하고 세 기존 데몬이 이름 붙은 거절을 출력. **F12 시점에는 락 수명 미해결; G1의 정상 해제 수정과 abrupt-loss 잔여는 [후속 검증](36_storage_lock_lifetime.md) 참조** | `rx.support-refusal.v1`, `storage/exclusive-writer-not-established`, owner_identity=NOT_ESTABLISHED. 두 resident writer 락의 실제 거절 장면. 실패 원인을 다른 Runtime의 존재로 단정하지 않음 |
| exec 후 자식의 저장소 FD 상속 | 실제 resident spawn → status 자식 → 관리자 SIGKILL | 관측 범위에서 장기 FD 누출 없음. 이를 모든 fork 구간의 해결로 확대하지 않음 | 두 실제 자식의 FD에 DB/writer 락 없음. 자식들이 살아 있는 채 관리자 종료 후 두 락 재획득 |
| fork 후 exec 전 락 잔존 | 다중 스레드 프로세스의 spawn과 store drop 중첩 | F12에서 미결 원인을 재현함. 이후 [G1](36_storage_lock_lifetime.md)이 원본·SDK의 정상 close/Drop 해제를 수정하고 live writer 거절을 보존함. SIGKILL/abort 뒤 상속 description 잔존은 계속 이름 붙은 거절 | F12 역사: 변경 전 product SqliteRepository + 실제 Command::spawn pre_exec barrier에서 drop 후 재열기 거절. 당시 원형은 격리 사본. G1은 생성자·연결 종료·borrowed transaction 검사까지 별도 구현 및 검증 |
| 저장 실패와 응답 유실 | registration/execution/recovery/work/replacement의 원자 저장 경계 | 지원 제한 및 이미 해결된 원자성. 성공 기록을 만들지 못하면 새로운 실행/산출물을 성공으로 승격하지 않음. 성공 commit 뒤 응답 유실은 이력 조회 | 기존 lifecycle·recovery·work·replacement 저장 실패 시험과 실제 passage. 결과·소비·경로의 부분 성공을 만들지 않음 |
| guarded 초기화 Entered/부분 완료와 재기동 | init/run/activate → initialization journal | 지원 제한 집행. Entered는 재실행하지 않으며 부분/변경 목록은 run 불가. guarded 자동 재시작과 software rearm도 거절 | 기존 실제 initializer subprocess 시험과 초기화 거절 검사를 runtime에서 실행. 별도 조사/처분 없이 새 ID로 우회하지 않음 |
| 기록·로그 보존과 자동 rotation 부재 | diagnostic track/replace 및 journal/log 쓰기 | 지원 계약 내 보존 의미 및 지원 제한. 결속64개 한도, 저장 불가 시 전이/산출물 보류. 무한 용량이나 자동 archival 보증 없음 | 기존 binding-capacity 거절 및 storage-failure latch/CAS 시험. 호스트 디스크 부족을 성공으로 전환하지 않음 |
| 오래된 등록·선택 집합·catalog digest | resident open/rearm/resume | 지원 제한 집행. 자동 이관·기록 삭제·묵시적 초기화 거절 | resident/resource passage의 changed digest 및 selection 거절, 원 entity 보존 |
| 신규/알 수 없는 저장 형식 및 구형 identity | SQLite version, strict record decode, F9 investigation | 지원 제한 집행. 미래 schema downgrade 거절; birth identity 없는 F9 이전 기록을 보충하지 않고 Unverifiable | 기존 SQLite/registration 호환 거절과 manager-loss/legacy 조사 시험. 새 writer의 의미를 구형 writer가 집행한다는 보증 없음 |
| 컨테이너/namespace 수명 교체 | F9 investigate/resume | 지원 제한 집행. 저장 scope가 이곳에서 관측되지 않으면 영구 Unverifiable, resume 불가 | `saved-namespace-not-observable-in-current-scope`; manager-loss passage의 새 container 거절 |
| 관리자 상실 뒤 원 작업의 결과 | F9 disposition/resume | 지원 계약 내 허용 의미. 프로세스 부재 증명은 원 결과의 복원이 아님 | UNKNOWN / PastOutcome::Unresolved 유지; 명시적 새 instance만 허용 |
| TTL의 논리적 cut 이후 만료 | F10 commit 및 F11 apply | 지원 계약 내 허용 의미. 성공 transaction의 마지막 live check가 cut이며 IO 완료까지 TTL 유지라고 주장하지 않음 | 기존 지연 주입 시험에서 반환 시 Expired여도 원자 이력은 보존. “만료 장면을 거절한다”로 잘못 분류하지 않음 |
| HTTP 관측과 SQL commit의 비원자성 | F10 입력 재관측 / F11 후보 재관측 | 지원 계약 내 허용 의미. 자기 시각·instance의 관측이며 외부 세계의 commit 시각 불변 보증이 아님 | artifact/receipt의 관측 시각·출처. 등록/경로/소비는 Immediate 락, 철회는 F6 ledger 락으로 별도 직렬화 |
| 출하 운영 영역 판단 제공자 부재 | F6 수신 → F10 prepare/commit / F11 prepare/apply | 지원 제한 집행. 출하 앵커 부재로 긍정 거절. 서명된 시험 발급자는 실제 운영 승인으로 승격하지 않음 | work passage의 author-policy-absent와 health 유지/업무 행0; replacement default-denial 시험. 서명은 정책의 타당성이 아님 |
| CPU·RSS·확보 용량·장치 정책 | 실행 요구 bundle → OS backend | 지원 제한 집행. 지원은 직접 자식별 virtual-address-space upper bound 하나. 미지원 bundle은 자식 생성 전 거절 | resource passage의 실제64MiB/128MiB 실패와 요구 거절; capacity reservation NONE_CREATED. 컨테이너 격리 옵션은 RX 집행 근거가 아님 |
| 상태 기록으로 현재 소유/자원 복원 | 재시작과 ResourceHistory/registration/receipt 읽기 | 지원 제한 집행 및 명시적 이력 의미. 저장된 PID/receipt는 신호·소유·새 작업 권한이 아님 | F9/F11 manager-loss 장면에서 NoSource 신규 배정 불가, UNKNOWN 유지, 새 receiver가 옛 proof 거절 |
| 의존 확인과 상시 감시 | F5/F11 ASSIGN/BEGIN/POLL/FINISH/INSPECT/APPLY | 지원 계약 내 허용 의미. 작성된 interval마다 호출 시 관측; 호출 사이와 최대 탐지 지연 보장 없음 | CheckpointPolicy와 old-source-loss 장면. 영향 작업은 보류, 원 결과 보존, 무관한 작업 지속 |
| 물리 인계·자손/공유 자원 복구 | 현재 F9 direct-child 부재, F11 diagnostic routing | 현재 경로가 그 행위를 실행하지 않음. direct-child/diagnostic이라는 범위를 유지하고 그 결과를 물리 인계로 읽지 않음 | process_ownership UNCHANGED / physical_handover NOT_ASSESSED. guarded Host 자신의 adapter proof 책임은 별도로 유지 |
| 다중 호스트·분산 소유권 | 첫 기준선은 로컬 Repository와 로컬 owned Child | 해당 실행 경로 없음. 로컬 PID/namespace 증거를 원격 소유권으로 재사용하는 API를 제공하지 않음 | F9 scope 비교와 local-only backend. 여러 로컬 Host/Executor 프로세스 지원과 다중 호스트 실증을 혼동하지 않음 |
| 실제 장비 안전·품질·생산 승인 | 진단·software boot·보고 결과 계산 | 물리 적격 판정 경로 없음. 첫 기준선의 긍정으로 확대하지 않음 | NOT_PERFORMED / NOT_COMMISSIONED. 실제 장비 운전은 이번 검증에 없음 |

## 신뢰 근원의 정확한 변화 (F12 시점)

기존 inventory는 자신을 인증하지 않으면서 뒤의 digest 검사의 근원으로 쓰였다. 무해한 comment를 status script에 추가하면 기존 inventory로는 거절됐지만, inventory의 해당 hash까지 바꾸면 통과했다. 실제 runtime에서 재현한 우회다.

이제 status script와 device catalog의 **원본 bytes를 컴파일할 때 바이너리에 포함**하고 그 bytes의 digest와 설치 파일·inventory 항목을 대조한다. inventory에서 기대값을 생성하지 않는다. 새 release의 source와 런타임 bytes가 일치해야 하므로 inventory 동시 변경으로 통과하지 못한다. Rust 이미지 빌드 단계에도 해당 원본을 복사한다.

이것은 설치된 Rust 바이너리와 OS를 신뢰한다는 F6 경계 안의 content 고정이다. Python OS 실행 파일과 설치된 Host/Executor Rust 실행 파일의 digest는 여전히 inventory 대조를 사용한다. 그 실행 주체 자체의 악의적 교체를 인증하는 체계는 없다. AUTHENTICATED_RELEASE_ORIGIN은 배포된 바이너리·OS·manifest의 독립 인증, 갱신/철회/롤백과 변경 불가성의 실제 근거를 닫아야 한다. 이 미결을 “기준선에 영향 없음”으로 지우지 않는다.

후속 [G2](37_authenticated_release_origin.md)는 컴파일된 개발 공개키에 대한 signed release 내용 인증과 통상 재기동의 rollback·철회 재생 거절을 추가한다. verifier/OS 인증, 통째 상태 rollback 탐지, offline 철회 최신성, 실제 제품 릴리스 권한 수탁·교체는 각각 이름 붙은 한계로 유지한다. 아래 F12 관측을 현재 전체 구현의 미해결 목록으로 읽지 않는다.

## 락 오류: 관측과 귀속을 분리한다

F9의 단일 CI 실패는 당시 기전 미규명이었다. F12에서 macOS 병렬50회는 재현하지 못했고 실제 Linux에서는 Host 락과 writer 락 실패가 재현됐다. 새 F12 시험을 제외해도 기존 시험은 round2에 실패했다. 원래의 crash-child 생성 시험까지 제외한 **측정 대조군**은50회 통과했다. 이 제외는 제품 시험 변경이 아니며 CI/최종 전체 suite의 시험을 직렬화하거나 제거하지 않았다.

일반 flock 상속, RX 저장소의 의도적 descriptor 전달, 변경하지 않은 RX 저장소와 실제 Command::spawn의 pre_exec barrier를 차례로 측정했다. 부모가 닫은 뒤에도 fork된 자식의 exec 전 descriptor가 락을 유지할 수 있다. CLOEXEC는 exec 시 닫는 속성이지 fork 직후의 복제를 없애는 속성이 아니다. 반대로 실제 resident status 자식에서는 exec 이후 DB/writer 락 FD가 관측되지 않았고 관리자 상실 후 살아 있는 그 자식이 락 재획득을 막지 않았다. 따라서 장기 자식 누출을 이 제품에서 발견했다고 쓰지 않는다.

격리된 사본의 explicit-unlock 원형은 connection을 먼저 닫고 소유 guard를 해제한다. 원래 crash-child 시험을 포함한 동일 병렬 suite50회가 통과했다. 이것은 원인 가설을 지지하는 대조이며 제품 수정도, 역사적 F9 실패 한 건의 확정 귀속도 아니다. 원형·실패·대조 로그를 보존한다.

F12 당시에는 platform/SDK를 수정하지 않았다. 당시 세 데몬은 락을 얻지 못하면 `storage/exclusive-writer-not-established`로 거절하고 소유자 신원을 단정하지 않는다. 당시 진단은 pinned SDK의 옛 비정형 오류 접두사에 대한 좁은 호환 adapter였으며 정책 우회나 새 권한이 아니다. 기존 오류 자체가 API 사용자에게서 사라졌다고 주장하지 않는다. 이후 [G1 STORAGE_LOCK_LIFETIME](36_storage_lock_lifetime.md)은 원본 storage의 명시적 lock lifetime/typed error, 연결 close 확인 후 해제, 상속 repository·transaction 거절, SDK 재생성 및 Host guard를 별도 검증했다. 문자열 adapter는 제거됐고 현재 진단은 typed OwnershipError에서 만들어진다. 정상 해제와 달리 SIGKILL/abort 뒤 상속 description이 남는 동안에는 계속 거절하며, G1도 이 창을 없앴다고 주장하지 않는다.

락 파일을 삭제하거나 모르는 PID를 종료하지 않는다. 현재 소유 또는 상속 descriptor가 실제로 해제됐는지 확인한 뒤 명시적으로 재시도한다. 잠깐의 false refusal도 이번 칸에서 fixed라고 부르지 않는다.

## 검증 범위와 남은 책임

[원시 근거](../references/support_limits_2026-09-24/README.md)는 정상과 거절, 실패한 계측, 기전 대조를 함께 보존한다. 기존 여섯 통과선과 전체 suite의 정확한 결과는 그 집계에서 확인한다. 제품 코드·진단 출력·이 표를 대조하며, 더 낙관적인 해석을 채택하지 않는다.

새 데몬·서비스·네트워크 API·DB 파일은 없다. SDK·platform·규범 문서·출하 catalog 내용은 바꾸지 않는다. 새 진단 JSON은 기존 CLI의 거절을 구체화하며, source mismatch는 기동 전에 거절된다. 이 문서는 모든 미결의 해결 선언이 아니라 각 경로의 집행과 남은 책임에 대한 기록이다.
