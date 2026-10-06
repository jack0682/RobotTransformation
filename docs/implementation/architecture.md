# 구현 모듈과 근거

현재 책임 경계는 [아키텍처](../05_software_architecture.md)를 따른다. 상세 동작·지원 범위는 소유 모듈의 현재 README·명세를 확인한다.

| 소유 | 원본 |
|---|---|
| 순수 작업 모델과 판단 | [rx-domain](https://github.com/jack0682/rx-platform/tree/develop/crates/rx-domain) |
| 업무 요청·원자 상태 전이 | [rx-application](https://github.com/jack0682/rx-platform/tree/develop/crates/rx-application) |
| 저장·writer·전송·서비스 | [platform crates](https://github.com/jack0682/rx-platform/tree/develop/crates) |
| native gate·receipt·evidence | [rx-host](https://github.com/jack0682/rx-solutions/tree/develop/runtime/rx-host) |
| 작업 요청·영속 실행기·복구 | [rx-executor](https://github.com/jack0682/rx-solutions/tree/develop/runtime/rx-executor) |
| 앱·어댑터·이미지 구성 | [solutions](https://github.com/jack0682/rx-solutions) |

platform의 authority engine을 공유 SDK로 수출하지 않는다. solutions는 계약 타입·codec·검증기를 재사용하며 platform의 원장을 복제하지 않는다. 각각의 저장소는 규범·SDK의 고정 사본을 포함해 독립 checkout에서 빌드할 수 있어야 한다.

이전 단계별 아키텍처 설명은 [고정 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/implementation/architecture.md)에 보존한다. 거기에 있는 ‘후속’이나 시험 수를 현재 코드 상태로 자동 승계하지 않는다.
