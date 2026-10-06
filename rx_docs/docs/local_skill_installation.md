# 한 명령 설치와 로컬 스킬 개발판

2026-09-28 · `0.3.0-rc.2` · LOCAL_SIM Python computation profile.

외부 개발자가 Rust·ROS를 빌드하지 않고 설치한 RX에 Python 스킬을 등록하고 실행 결과를 조회하는 첫 배포 경로다. 실제 로봇용 Platform/Host/Executor 설치·자격 검증을 대체하지 않는다.

## 사용 흐름

Python 3.11 이상, curl, 실행 중인 Linux Docker Engine 또는 Docker Desktop이 필요하다. 배포물은 Docker 엔진의 amd64/arm64에 맞춰 선택된다.

```sh
curl -fsSL https://github.com/jack0682/rx-solutions/releases/download/v0.3.0-rc.2/install.sh | sh
~/.local/bin/rx skill add --example add
~/.local/bin/rx run add --input '{"a":2,"b":3}'
~/.local/bin/rx ui
```

예제의 결과는 `sum: 5`다. 자신의 스킬은 `rx skill new ./my-skill`로 만든 뒤 `skill.py`와 `skill.json`을 작성하고 `rx skill add ./my-skill`로 등록한다. 스킬 함수는 `main(inputs)`이며 JSON 객체를 반환한다. 코드와 입출력 정의가 동일한 이름·버전에 고정된다.

웹 화면은 등록된 스킬, 성공·실패·결과 불명 건수, 실행 시간과 개별 결과를 표시한다. `rx token`으로 확인한 로컬 토큰을 입력해 접속한다. 이 화면은 기존 셀 운영 UI와 별도인 로컬 개발 프로필의 조회 화면이다.

## 책임과 기존 구조의 관계

| 책임 | 구현 |
|---|---|
| 등록·입출력·요청 동일성·결과 정책 | platform의 `rx-application::software_skill` |
| 단일 상태 쓰기 | 기존 `rx-runtime::writer`와 새 프로필의 Processor |
| 원자 기록과 프로세스 소유 | 기존 `rx-storage::SqliteRepository` |
| 실행 지식·결과·불명 상태 | 기존 `rx-domain::Operation` |
| HTTP·조회 화면 | platform의 `rx-skill-server` |
| Python 실행과 미전달 결과 보관 | solutions의 별도 worker 컨테이너 |
| 설치·패키징·CLI | solutions의 `deployment/local-skills` |

새 프로필은 자체 설치 식별과 저장소를 갖는다. 기존 셀 DB를 인수하거나 권한·자격을 복제하지 않는다. 장비 Host를 통과하지 않는 코드로 물리 동작을 수행해도 된다는 의미가 아니다. 이 개발판에는 Cell/Host 운전 API가 노출되지 않는다. 기존 공통 규범·wire·Host SDK는 변경하지 않았다.

## 동작과 경계

- 서버와 실행부는 서로 다른 컨테이너·데이터 볼륨을 사용한다. 서버만 호스트 loopback에 포트를 노출하며 worker는 내부 네트워크에 있다. 비루트·읽기 전용 root·장치와 Docker socket 미연결 상태로 실행한다.
- 신뢰하는 개발자의 표준 라이브러리 기반 Python 코드를 대상으로 한다. 자원 제한은 악성 코드 격리 보증이 아니다. 다중 사용자·인터넷 노출 배포는 범위 밖이다.
- 요청 UUID는 전송 전에 CLI가 보관한다. 응답 유실 시 같은 입력과 같은 UUID로 조회·재요청하며 새 실행을 만들지 않는다.
- worker가 실행에 진입한 뒤 결과가 불명확해지거나 서버가 재시작되면 UNKNOWN/UNRESOLVED를 보존한다. 미확정 작업을 자동으로 재실행하지 않는다. 늦은 결과로 격리를 조용히 지우지 않으며, 사람의 정식 조정·해제 흐름은 아직 없다.
- 실행은 직렬이다. 스킬 버전 128개·실행 1000개·소스 256 KiB·입출력 64 KiB·100–60000 ms deadline 범위다. 상한 도달 시 기록을 삭제하지 않고 신규 접수를 거절한다.
- 출력이 성공했다고 실제 장비 정지·소재 인계·자원 해제·기능안전을 주장하지 않는다. 실행 시간은 worker의 monotonic 측정값이고, 전체 서비스 성능이나 물리 deadline 증거가 아니다.
- `rx down`은 상태를 보존하고 `rx up`은 같은 설치를 다시 연다. 같은 버전 재설치는 멱등적이다. 버전 간 자동 이행·삭제/초기화 도구는 이번 범위가 아니다.

## 검증과 배포

로컬 arm64 Docker 설치에서 새 설치·외부 Python 함수·원 요청 중복·실제 응답 본문 유실·입출력 오류·시간 초과·worker 강제 종료·재기동·물리 manifest 거절을 검증했다. [고정 소스의 로컬 인수 결과](../references/local_skills_2026-09-28/arm64-local.json)

solutions CI의 필수 `skills` job은 amd64와 arm64의 네이티브 runner에서 이미지를 빌드하고 동일한 설치 인수 시험을 수행한다. 릴리스에는 그 산출물, 소스 커밋·이미지 ID, 체크섬 및 서명을 함께 보관한다. 로컬 결과만으로 다른 아키텍처 통과를 선언하지 않는다.

[배포물·상세 설치 안내](https://github.com/jack0682/rx-solutions/tree/main/deployment/local-skills) · [Platform 프로필 명세](https://github.com/jack0682/rx-platform/blob/main/crates/rx-api/SOFTWARE_SKILLS.md)

## Docker 엔진 간 설치 호환 수정

설치 배포물 rc.1은 CI의 Docker config digest와 Docker Desktop의 OCI manifest digest를 같은 표현으로 가정해 다운로드 설치가 거절됐다. 해당 설치 릴리스를 초안으로 회수했고 기존 소스 태그는 보존했다. rc.2는 체크섬으로 고정된 아카이브의 실제 config·manifest·index 내용을 검증해 같은 이미지로 연결되는 식별자만 허용한다. 알 수 없는 ID·내용 변조·아키텍처 불일치는 계속 거절한다. [실제 아카이브 대조](../references/local_skills_2026-09-28/image-portability.json)

rc.2는 설치 배포물의 수정이며 서버 컴포넌트는 검증된 rc.1 소스를 재사용한다. 실제 장비 지원 범위는 늘어나지 않는다.
