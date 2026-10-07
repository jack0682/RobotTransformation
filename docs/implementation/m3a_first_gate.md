# M3a 첫 관문 — 2026-10-03

관문 범위는 승인된 반례 1–5와 기존 P/Executor 등록 경로다. 신규 관문을 추가하지 않았다.
고정 v1 UI 실패를 숨기지 않고, 사용자가 승인한 [격리 조건](../../contracts/semantic/workflow-execution/v2/legacy-isolation.md)을 적용했다.
이 문서는 구현 precheck이며 merge 후 사용자의 M1/M2 제품 smoke 수락을 대신하지 않는다.

| 기존 항목 | 실행 근거 | 판정/경계 |
|---|---|---|
| 1 v1 유지 | P/S 전체 workspace, 기존 strict/golden corpus, 8개 규범 baseline/SDK 동기화 검사; 변경 전후 같은 고정 v1 설치의 실제 운전 | PASS. 고정 runtime bytes 및 기존 데이터 의미를 바꾸지 않음 |
| 2 고정 v1 주입 | [구버전 runtime](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/execution_v2_design_2026-10-02/legacy-runtime-injection.json), [구버전 UI 실패 및 새 UI 거절](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/execution_v2_design_2026-10-02/legacy-ui-injection.json) | **고정 UI 자체 FAIL 유지**. 승인된 설치 격리 하에서 PASS: 새 P↔구 UI, 구 P↔새 UI 혼합은 manifest에서 거절; 새 UI는 v2 참조/추가 policy를 거절; P의 독립 legacy Start 거절 유지 |
| 3 다른 selection/type/unit/frame | `cross_run_and_other_selection_replay_is_rejected_even_with_same_parameter`, `execution_materialization_recomputes_stored_values_and_matches_preapproved_reports`, actual-object binding/slot custody transactions | PASS. 다른 part/slot/model/node, unit/frame 및 실제 객체 provenance를 확인 |
| 4 변조/불완전 index/상한 | `parameter_tampering_and_non_parameter_intent_changes_are_rejected`, `strict_artifact_decoding_refuses_forgery_and_ambiguous_json`, `index_cannot_omit_duplicate_reorder_or_exceed_published_domain`, `derived_qualification_recomputes_every_candidate_even_with_a_valid_signed_report` | PASS. 서명된 잘못된 최종 index entry도 재계산에서 거절 |
| 5 override/비고정 입력 | materialization의 60 mm/20..40 mm/kg 및 WRONG_FRAME 거절, 같은 공통 resolver의 geometry/force constraints; M2 dense/60 N/100 mm/kg/구간 경로의 기존 사용자 수락 | PASS. 최종 사용자 확인은 merge된 환경에서 A/B 및 BLOCKED smoke로 재확인 |

등록 P↔S Executor의 [최종 normal/Begin/Submit/Complete 응답 유실 4종](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/execution_v2_design_2026-10-02/m3a-registered-final.json)이 통과했다.
새 선택을 만들지 않고 원 요청을 query/reconcile하며 2 Part/2 operation/budget 2를 확인했다.
기존 handover 정체 수정 후 [20회 연속, 실패 0회](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/execution_v2_design_2026-10-02/m3a-handover-repeat.json)도 보존한다.
이 두 결과의 Host 완료/인계 입력은 합성이며 frozen test clock을 사용한다. native v2 Host나
실제 UNKNOWN 복구 운전을 입증하지 않는다. 해당 운전/RC 항목은 **M3b/M3c 이관**이다.

고정 Executor는 주입된 Plan을 읽기 전에 유효한 v1 Part를 한 번 할당한다. 시도 budget 1과
미완료 Part는 그대로 기록된다. operation/permit/장치 효과는 생성되지 않고 mandate는 회수된다.
PAUSED 또는 서비스 종료 후 RECOVERY_REQUIRED를 보존했으며 정상 완료나 자동 재시도로
바꾸지 않았다. 이 시험에는 기존 미정산 native operation이 없으므로 그 복구를 주장하지 않는다.

최종 로컬 검사: P workspace 606 passed/21 ignored, S workspace 442 passed/19 ignored,
두 workspace Clippy 및 repository/binding/SDK 검사 통과. UI 80 tests와 bundle 3 tests,
format/build 통과. P의 수동 installed-bundle 격리 시험은 고정 manifest SHA를 직접 비교하고
거절했으며 새 실제 bundle은 읽었다. ignored 수에는 환경 의존 검사와 별도 실행한 설치
격리/기존 dense 수동 측정이 포함된다. 전체 제품 또는 물리 qualification의 PASS가 아니다.

다음 순서는 commit-range별 PR 본문, 최종 exact-head CI/DCO, P → S develop merge,
merge된 head에서 재생성한 환경의 제품 CLI M1/M2 smoke다. 사용자 수락 전 M3a 완료로
표시하지 않으며, 다음 프레임워크 작업은 시작하지 않는다.
