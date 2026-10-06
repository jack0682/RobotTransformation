# Repository foundation — 2026-09-14

세 저장소를 제조사 중립 개인 프로젝트와 Apache-2.0 기준으로 정리했다. 현재 작업 트리의 회사별 필수 지원·카탈로그·샘플을 제거하고 generic device/ROS JTC 및 명시적 simulation fixture를 사용한다. 과거 초안은 Git 이력과 archive 태그에 보존한다.

## 검증 근거

- [솔루션 검증 요약](../../references/repository_foundation_2026-09-14/summary.json): 소스 e81825b2e440ded36e25c5cb8125f7d68281f6da, Linux arm64 이미지와 Rust/UI/ROS 모의 검증 범위.
- [이미지 smoke](../../references/repository_foundation_2026-09-14/image-smoke.json).
- [Supervisor 수명주기·변조 거부](../../references/repository_foundation_2026-09-14/supervisor-smoke.json).
- [실제 C++ ROS 브리지와 모의 action](../../references/repository_foundation_2026-09-14/ros-jtc-bridge-final.json).

이 검증은 소프트웨어와 모의 장비 범위다. 실장비 commissioning, production JTC Authority, Linux arm64 이외의 이미지, APT snapshot 고정은 검증 완료로 주장하지 않는다. Rust 환경 의존 시험 14개는 로컬 실행에서 ignored다.

## 저장소 운영

각 저장소의 CONTRIBUTING.md와 repository-settings.json이 main/develop Git Flow 및 GitHub 설정의 관리 기준이다. 필수 종합 검사 이름은 CI이며 모든 하위 검증이 성공해야 통과한다. Apache-2.0 LICENSE/NOTICE와 제3자 고지는 각각의 저장소에 포함한다. 실제 원격 결과는 각 저장소 Actions와 Rules 화면에서 확인한다.
