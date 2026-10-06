# RX의 후속 방향

> 2026-09-29부터 전체 작업 순서와 단계별 종료 기준은 [RX 프레임워크 마스터 플랜](42_framework_master_plan.md)을 따른다. 아래 N1–N6 제안과 상주 프레임워크 조각의 기록은 그 계획의 입력으로 유지한다.

2026-10-01 현재 진행 중인 초안 완성 작업의 모델·이행·검증 상태는
[실행 모델](45_resident_framework_execution_model.md)과 [완료 원장](implementation/resident_framework_completion.md)에서 확인한다.

기준일: 2026-09-16. 목표는 [이기종 로봇과 시설의 협업](01_product_definition.md)이다. 인계 사례의 N1 정의, N2 경계 판정, N3 문서 반례, N4 모의 명령 추적과 N5의 실제 ROS 컨트롤러·모의 하드웨어 시험을 기준으로 후속 구현·검증을 구체화한다.

## 다음 서비스 검증 제안

| 순서 | 할 일 | 확인할 결과 |
|---|---|---|
| N1 | [두 역할의 물품 인계 사례를 정의](20_first_handover_case.md) | 시작·끝·참여자·물품·자원·사람 개입과 최종 완료 조건 |
| N2 | [두 미결의 계약 경계 판정](22_open_items_boundary.md) · [선언·판정 지원도 측정](21_declaration_reuse_measurement.md) | 문서 판정 완료. 이동형 지지는 profile 규범만으로 불충분하며, 인수는 기존 기록과 추가 업무 의미를 구분했다. 두 미결은 open이고 **재사용 계수는 측정 불가**로 남는다. |
| N3 | [유실·경합·거부·인계 불명의 문서 반례 검토](23_handover_counterexamples.md) | 네 후보의 24단계·다섯 축 20개를 구체화하고 네 오독의 규범상 차단 지점과 현장 결손을 연결했다. 거부는 BUSY·오래된 permit 차단에 귀속한다. 실행한 장애 시험은 아니다. |
| N4 | [모의 명령 경로·추적 경계 구현](https://github.com/jack0682/rx-solutions/blob/df3b7416b71acc9cdfbd7a75b0658f88effb889f/examples/process/n1-handover/README.md) | 두 Host의 네 동작이 컴파일되고 모의 입력으로 실제 planner를 실행했다. 성공 뒤 명령 자원 인계를 기다리며, 해제 응답 불명은 원 operation을 보존하고 후퇴를 막는다. 구체 모의 값 8/77, 미충족 69(placeholder만 2 포함). P/Host의 N1 실행·물리 인계·정상 인수·잔여 점유·서비스 완료 검증은 남고 두 미결은 open, NOT_COMMISSIONED다. |
| N5 | [실제 ROS JTC·모의 하드웨어 연결 검증](https://github.com/jack0682/rx-solutions/blob/2548a93c854878c192bc0643e1f326a2a9039b2f/native/ros-jtc/controller_validation/README.md) | GenericSystem 모의 하드웨어에서 goal 수락·결과·UUID 취소·브리지 재시작 후 조회를 실측했다. N5 입력 18/77, N4 대비 추가 대응 ID 15개이며 합집합은 별도 산출물의 가용성이다. 실제 Authority·물리 지지·현장 검증과 N1 실행은 남는다. NOT_PERFORMED·SIMULATION_FIXTURE·NOT_COMMISSIONED 유지. |
| N6 | 여러 작업과 운영 영역으로 확장 | 공유 자원·신뢰·통신 단절·성능 요구의 추가 정의 |

N1–N6는 순서 제안이며 장비·일정·성능 수치를 확정한 계획이 아니다. 먼저 모든 도시 기능을 만들 필요는 없다. 현재 미결 중 선택한 사례에 실제로 영향을 주는 항목을 [미결 목록](implementation/critical_open_items.md)에서 연결한다.

## 설계 판단의 기준

### 상주 프레임워크의 첫 구현 조각 — 2026-09-23

[F1 실행 요구 선언과 단일 수락](24_host_execution_requirements.md)은 기존 Supervisor에
작성자 소유의 호스트 요구와 전체 묶음 거절 경계를 추가한다. 실제 기본 backend는 필수 자원
정책을 지원하지 않으면 실행을 거절한다. 긍정 적용은 모의 시험이며 cgroup v2·rlimit·장치
접근 집행, 등록 신원(F2), 명시적 복구(F3), 업무 사용 허용(F4), 의존 결합(F5)은 완료로 세지 않는다.
F1은 상주 실행 전체 경로의 완성이 아니며 후속 Linux 집행·복구 검증의 앞선 조각이다.

[F2 등록 신원과 실행 통과선](25_component_registration.md)은 등록을 실행·plan과 독립된
키로 보존하고, 기존 비구동 상태 서비스의 등록→수락→실행 관측→종료→재시작 뒤 대조를
연결한다. 등록과 마지막 실행 관측은 별도로 조회한다. 준비·업무 사용 허용, 명시적 복구
처분, 의존 결합 및 자원 집행은 후속 범위이며 M1 전체 완료로 세지 않는다.

[F3 명시적 복구 처분](26_explicit_recovery_disposition.md)은 원 UNKNOWN을 보존하면서
실제 소유 Child의 종료 증거와 별도 권한을 받아 처분을 기록한다. 새 실행은 명시적 요청을
한 번 소비해 새 run/instance로 시작한다. 전체 manager/핸들 상실의 외부 조사 provider,
준비·업무 허가·자원 집행·물리 복구는 미지원이다.

[F4 준비 조건과 업무 판단](27_readiness_and_work_use.md)은 작성자 조건을 현재 인스턴스의
자기 보고와 대조한다. 미평가·불충족·미지원·충족을 이름 붙은 조건으로 표시하며 생존을
준비로 승격하지 않는다. 업무 판단은 운영 영역의 책임이고 긍정 허가 provider는 아직
미연결·미지원이다. 자기 보고 조건 충족은 기능의 실제 동작이나 물리 자격의 증명이 아니다.

목적과 우선순위는 01, 평가 가설은 [02](02_value_and_business.md), 현재와 목표의 범위는 [03](03_product_scope.md)를 따른다. 작업 의미와 권한은 규범의 명시된 버전 범위를 따른다. 구현·시험은 해당 commit과 증거로 판단한다.

이전 산업 초안의 로드맵과 실행 기록은 [고정 원문](../references/README.md)에 남아 있다. 과거 납품 순서·특정 장비 선택을 현재 모든 연구의 선행 조건으로 삼지 않는다.

[F5 진단 소비 작업과 의존 결합](28_dependency_binding.md)은 실제 보고를 소비하는 진단 run과
결과를 지속하고, 준비/결과 생성/수행 구간의 의존 상실을 신규 배정·진행·결과 소비로 나눠
재판정한다. 초기·교체의 긍정 수용과 업무 허가는 미지원이며, 기존 plan-local `depends_on`의
네 동작과 물리 검증 경계는 유지한다.

[F6 검증된 외부 결정](29_verified_external_decisions.md)은 작성자 앵커와 정확한 대상에 결속된
외부 서명에서만 긍정을 만든다. 업무·초기 결합·교체 결합은 별개이며 만료·철회가 과거 기록을
덮어쓰지 않는다. 기본 제품은 앵커가 없어 승인하지 못하고 실제 운영 영역 연결은 미지원이다.
