# 구현 초안에서 현재 프로젝트로의 인계

기준일: 2026-09-14. **기존 초안 v0.1은 2026-09-13에 마감됐으며 현재 제조사 중립 구성을 위한 출발점이다.** 이전 인계 문서는 [당시 고정 원문](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/docs/implementation/draft_handoff.md)에 변경 없이 보존한다.

## 재사용하는 구조

platform은 작업 의미·권한·결과·원장·API, solutions는 Host·장비 연동·작업 실행기·운영 앱·적용 패키지를 소유한다. 모의 셀의 작업 전달·결과 회수·자원 인계와 부분 재시작·오프라인 점검 경로를 구현한 초안에서 이어간다.

## 과거 검증의 정확한 범위

| 대상 | 당시 고정 기준 |
|---|---|
| platform runtime | `5f9986beb951b28c960860bb53a1b4673bdb14ac` |
| solutions runtime | `3d323f717af074ce147bfca2ff7a5668c4b2a36c` |
| 문서·검증 기록 | `7c193755dd1878a30eab0a5496451faf27a71840` |
| 모의 인수 | Linux arm64, 당시 두 이미지, 설치·서명/검토·UI 시작·소재 2개/effect 2회·종료 |

[마지막 결과 원본](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/references/implementation/draft-v0.1-final-acceptance/result.json)과 [마감 manifest](https://github.com/jack0682/rx_docs/blob/6111a7d1dcf33052f38c3e67c6585aec2b44df3c/references/draft_closure/closure_manifest.json)는 그 구성에만 적용한다. 당시 P390·UI49·S259 등의 수치는 각 단계의 증거이며 이번 개정에서 재실행한 시험 수가 아니다.

## 현재 변경과 한계

특정 제조사의 기본 포함 정책과 지원 요구를 제거하고 공통 장비 profile·CI·기여·브랜치 정책을 정비한다. 문서의 지원표·규범 hash 변경은 새 중립 구성에 대한 의미·호환 검토이며 실물 또는 전체 이미지 검증 완료가 아니다.

실제 Authority Provider, 절차 신뢰 연결, 명시적 운영 재개·전체 복원, 장기 부하·다중 운영 영역은 [미결](critical_open_items.md)이다. 실물 설치는 NOT_COMMISSIONED다. door-to-door와 도시 확장은 목표이며 검증된 기능 목록에 포함하지 않는다.

조사 처분 WIP는 platform `42ce1ea7e6d104000402155efdf069d8bf6edde5`, solutions `3d5f6d09058a44ff9706924cabf3adf50616e828` 및 기존 `codex/investigation-wip`에 보존되어 있다. 이번 중립화로 그 WIP를 검증되거나 병합된 기능으로 승격하지 않는다.

새 실행 방법과 정확한 검사 명령은 [platform README](https://github.com/jack0682/rx-platform)와 [solutions README](https://github.com/jack0682/rx-solutions)를 따른다. 다른 개발자의 로컬 절대 경로나 과거 이미지가 있어야 문서를 읽을 수 있는 구조를 요구하지 않는다.
