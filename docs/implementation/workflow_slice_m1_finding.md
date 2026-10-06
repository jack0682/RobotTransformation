# 0F Workflow 세로 경로 — 이전 목표의 착수 조사

2026-10-01 후속 사용자 목표가 모델·API·CLI 우선으로 교체되었다. 아래는 이전 목표의 조사 기록이며, 현재 범위와 M1은 [셀 모델](laser_cell_model.md)을 따른다.

당시 사용자 목표는 한 품목·단일 그리퍼의 pick → load → clamp → close →
process(done 대기) → open → unload → place를 모의 장비에서 작성·게시·운영하는 것이다.
이 기록은 [장기 계획](framework_delivery_plan.md), [WF 요구](../46_workflow_product_experience.md),
[RF 원장](resident_framework_completion.md)을 변경하거나 완료로 승격하지 않는다.
M1 사용자 실행 확인 전 M2를 시작하지 않으며, M3 후 RC를 사용자가 QUICKSTART만으로
45분 안에 재현해야 최종 완료다. 제외 범위는 [parking](parking.md)에 기록했다.

## 이번 조사 범위

원격 fetch 후 확인한 develop: Docs `97c1164c0c906b5ca88b48bf13b58320afa5160d`,
Platform `fb6bb347c2656c9c05c8e011787fd4fca23ee567`,
Solutions `2367a2a508e1a32d754509b546feadc710fd8af1`.
오래된 기본 체크아웃을 현재 구현으로 해석하지 않았다. 별도 definition-catalog WIP는
읽기만 했으며 R7·재자격 작업과 함께 수정·흡수하지 않았다.

## 확인한 차단 지점

1. 현재 UI 라이브러리는 구조 노드와 초안 안의 operation binding 이름을 제공한다.
   TaskDefinition 카탈로그를 Workflow에 연결하는 경로가 아니다.
   [라이브러리 소스](https://github.com/jack0682/rx-solutions/blob/2367a2a508e1a32d754509b546feadc710fd8af1/apps/operator/src/workflow-canvas.tsx#L6).
2. 저장·검증의 ProcessSource는 엄격한 v1 타입이다. Operation은 `binding`만 가지며
   Success/Failure 전이나 Task 정의·입력 참조를 표현하는 필드가 없다.
   [모델](https://github.com/jack0682/rx-platform/blob/fb6bb347c2656c9c05c8e011787fd4fca23ee567/crates/rx-process-contract/src/model.rs#L5),
   [검증기](https://github.com/jack0682/rx-platform/blob/fb6bb347c2656c9c05c8e011787fd4fca23ee567/crates/rx-process-contract/src/source_validation.rs#L54).
   UI의 Operation도 출력 포트를 반환하지 않는다.
   [포트 코드](https://github.com/jack0682/rx-solutions/blob/2367a2a508e1a32d754509b546feadc710fd8af1/apps/operator/src/workflow-graph.ts#L16).
3. 초안은 불완전한 JSON도 보존할 수 있지만, 저장 성공은 해당 의미의 검증·컴파일 지원이 아니다.
   저장 준비는 같은 코어 검증기로 보고서를 만든다.
   [저장 준비](https://github.com/jack0682/rx-platform/blob/fb6bb347c2656c9c05c8e011787fd4fca23ee567/crates/rx-application/src/process_draft.rs#L83).
   새 자료를 임의 JSON이나 화면 상태로 보존하는 것으로 M1을 완료 처리할 수 없다.
4. 별도 W04 WIP는 정의 저장·상속 출처 표시를 구현 중이다. 그 자체의 체크포인트도
   그래프 연결·Task source chain 계산·로봇 후보 경로 및 SDK 동기화를 미완으로 기록한다.
   이 미통합 작업을 완성된 기반으로 간주하지 않았다.

위 1–3은 고정 소스의 정적 확인이다. 이번 조사에서 제품 서버·브라우저·시뮬레이션을 실행하거나
장애를 주입하지 않았다. 기존 시험 수나 WIP 기록을 이번 실행 증거로 쓰지 않는다.

## 왜 여기서 멈추는가

사용자가 “코어 변경이 불가피하면 중단하고 finding으로 보고”하도록 지정했다.
기존 저작·검증·컴파일 경로에 위 의미를 연결하려면 공통 계약/검증 경계 확장이 필요하다.
`rx-process-contract`와 draft writer는 [코어 헌장](../43_core_charter.md)의 코어 분류에 속한다.
패키지/UI만 바꿔 지원되지 않는 의미를 지원한다고 표시하지 않는다.

**사용자 결정(2026-10-01, finding 보고 후):** “공통 기능의 최소 확장 허용.”
M1에 필요한 공통 저작 확장(Task 정의/값 출처·적합성 및 Success/Failure 의미의
저장·검증 연결)을 이 목표의 선행 변경으로 허용했다.
레이저 명칭·품목·작업 순서·수치·장비 binding은 패키지에만 두고,
공통 코어 변경량과 시나리오 전용 코어 변경량을 별도로 보고한다.
이 허용은 기존 계약 파괴의 승인이 아니다. 기존 계약을 깨야 한다면 별도로 v1.1 영향과 권고안을 먼저 제시한다.

M1 수락용 실행 명령/클릭 경로는 아직 제공할 수 없다. 이번 변경은 이 finding과 parking 문서뿐이다.
제품 코어 변경 0줄, 시나리오 패키지 작성 0파일/0줄이며 설치시간·명령 수·사용자 수락은 미측정이다.
