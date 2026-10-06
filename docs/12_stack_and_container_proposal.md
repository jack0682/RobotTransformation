# 12. 구현 기술과 컨테이너 경계

Rust 코어의 ROS·BT·SDK 비의존성을 유지한다. 장비별 ROS/native stack과 workflow engine은 solutions에서 공통 계약에 연결한다. 기술 선택은 실제 작업·지원 플랫폼·유지 비용과 검증으로 판단한다.

고속 actuator 제어 sample을 플랫폼 업무 transaction에 넣지 않는다. 플랫폼은 세션·허가·관측 근거·결과를 관리하며 현지 제어 주기와 물리 보호는 해당 연동 범위에 남긴다.

[platform](https://github.com/jack0682/rx-platform)과 [solutions](https://github.com/jack0682/rx-solutions)의 toolchain·lockfile·Dockerfile이 현재 빌드 원본이다. 과거 문서의 패키지 버전을 현재 설치 명령으로 복사하지 않는다. [이미지 명세](14_image_support_spec.md)를 함께 읽는다.

이 주제의 이전 산업 초안은 [고정 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/12_stack_and_container_proposal.md)에 보존한다.
