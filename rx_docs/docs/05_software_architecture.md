# 05. 소프트웨어 아키텍처

RX는 공통 작업의 의미·권한·기록과 장비별 실행을 분리한다. ROS 비의존 Rust 코어를 유지하고, 연동과 앱은 별도 solutions 저장소가 소유한다.

| 계층 | 책임 | 소유 저장소 |
|---|---|---|
| Domain | 작업 동일성, 상태·조건·결과·자원 처분, 순수 전이 | rx-platform |
| Application·Runtime | 권한 검사, 단일 writer, 원자 상태·event·outbox | rx-platform |
| Storage·transport·API | 영속 저장, 인증·협상·프로토콜·운영 API | rx-platform |
| Host | 전달 gate·fence·grant·native receipt·evidence journal | rx-solutions |
| Adapter | 실제 장비 API·관측·제어권·lifecycle과 profile 연결 | rx-solutions |
| Executor·workflow | 작업 흐름 제안, 원래 요청·checkpoint·복구 연결 | rx-solutions |
| Apps·packages | 운영 화면, 서비스 정의, 설치별 구성·profile | rx-solutions |

platform은 장비 SDK나 ROS 타입에 의존하지 않는다. Host는 물리 관측과 전달 근거를 보고하며 상위 작업 결과와 운전 허가의 원장을 복제하지 않는다. UI는 승인된 API를 사용하고 별도 판정 원장을 만들지 않는다.

저장 transaction은 외부 물리 동작을 rollback하지 못한다. 일반 명령은 영속 전달 경계 뒤에 진입하며, 진입 이후의 응답 유실은 원래 작업 조회·조정으로 처리한다. 물리 보호 반응의 책임은 profile과 현장 설계에서 따로 확인한다.

## 현재 배치와 확장

현재 계약 v1.0은 같은 주 컴퓨터의 단일 권위 Runtime과 장비 Host 범위다. 두 소프트웨어 저장소와 두 제품 이미지가 여러 내부 프로세스를 가질 수 있다. 문서 저장소는 세 번째 제품 이미지가 아니다.

여러 운영 영역으로 확장하려면 권한 위임·신뢰·공유 자원·인계·통신 단절을 추가로 명세해야 한다. 기존 단일 writer나 CLOCK_BOOTTIME 가정을 검토 없이 여러 컴퓨터에 적용하지 않는다.

[구현 모듈 안내](implementation/architecture.md) · [작업 계약](contracts/v1.0/README.md) · [셀 운영 계약](cell_operations/v1.0/README.md)
