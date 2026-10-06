# 08. 배포와 유지보수

배포 단위는 검증한 platform·solutions 버전, 규범·SDK·profile, 필요한 장비 의존성과 구성의 묶음이다. 문서 저장소는 제품 이미지를 만들지 않는다.

| 단계 | 확인할 것 |
|---|---|
| 개발 | feature 브랜치와 PR, 해당 변경의 검사·계약 영향 |
| 통합 | develop의 호환성, 두 저장소의 SDK·규범 동기화 |
| 릴리스 | main에 반영할 정확한 commit·구성·시험·미결 |
| 설치 | 이미지·artifact·설정·identity·저장 volume·권한 |
| 기동 | software ready와 장비 activate·운전 허가의 구분 |
| 교체·복원 | 원장·세대·잔류 명령·자원 상태·명시적 재시작 |

이미지 기본 동작은 진단 중심이며 장비의 토크·이동을 자동 활성화하는 근거가 아니다. SDK·driver·CPU/GPU variant는 선택한 profile로 고정하고 source·license·빌드 근거를 함께 남긴다.

전체 현장 복원·장기 운영·실물 종료 경로는 [현재 미결](implementation/critical_open_items.md)이다. 백업 복원을 기존 작업의 자동 재생 허가로 사용하지 않는다. 저장소 개발 흐름은 [기여 안내](../CONTRIBUTING.md)를 따른다.
