# 14. 이미지 구성과 지원 선언

| 이미지 | 포함할 책임 | 기본 경계 |
|---|---|---|
| rx-platform | 코어·Runtime·원장·운영 API·프로토콜 | ROS와 장비 SDK에 의존하지 않음 |
| rx-solutions | Host·실행기·앱·선택한 연동/구성 | 특정 제조사의 전체 stack을 공통 필수 의존으로 삼지 않음 |

정확한 이미지 구성은 각 저장소의 Dockerfile과 고정 의존성 목록을 따른다. 장비별 source commit·전이 의존성·license·OS/CPU/GPU/device 권한·설정·profile을 선언하고 필요한 조합만 검증한다.

이미지 build 성공·software ready는 모델 지원 완료나 장비 activate 허가가 아니다. Driver 기동·종료의 물리 효과, 관측 신선도·명령 배타성·잔류 명령·물품 지지 조건은 별도 profile 검증 대상이다.

platform DB와 Host journal은 별도 소유 volume이다. 백업에는 identity·generation·journal 연결을 포함하며 과거 outbox를 자동 운전 명령으로 재생하지 않는다. 전체 privileged와 전체 device mount를 기본 요구로 삼지 않는다.

기존 이미지 digest와 모의 시험은 [이전 증거](../references/README.md)에 한정한다. 현재 중립 이미지의 검증은 새 commit·실행 결과로 남겨야 한다. [지원 등급](13_device_support_matrix.md)과 [유지보수](08_delivery_and_maintenance.md)를 따른다.

이 주제의 이전 산업 초안은 [고정 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/14_image_support_spec.md)에 보존한다.
