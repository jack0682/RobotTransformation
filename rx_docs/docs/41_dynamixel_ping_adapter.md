# 41. Host 소유 DYNAMIXEL Ping 모의 어댑터 (G5.2)

이 문서는 구현자의 실행 근거와 지원 경계를 기록한다. 독립 수락 receipt는 별도 검증 기록이다.
최상위 검증 층위는 **모의 장비에 대한 실제 Linux 실행**이다. 실물 DYNAMIXEL 연결·운동·장비
자격·물리 안전을 검증하지 않았으며, G5 SDK 기준선과 ROBOTIS 다섯 제품 전체 번들도 미완료다.

## 선택과 소유권

기존 `VALIDATED_DRIVER`는 선언만 있고 factory에서 거절되던 예약 형태였다. 다른 구현의 의미를
덮어쓰지 않고, 정확히 `rx/dynamixel-protocol2-ping-simulation-v1` 한 프로파일만 연결했다.
일반 plugin registry나 임의 실행 파일 loader는 추가하지 않았다.

공식 [DYNAMIXEL SDK 4.1.0 고정 소스](https://github.com/ROBOTIS-GIT/DynamixelSDK/tree/f838bc90f72fcf5b9c279432d6e12fc24969daa8)를
외부 C++ helper 하나에서 사용한다. 원본 protocol2 구현과 인터페이스는 수정하지 않고
내용 SHA·Apache-2.0 고지를 보존했다. OS serial PortHandler 구현은 링크하지 않는다.
RX의 가상 model65500, ID1, firmware1, 고정 응답 지연250ms를 모의한다. 실제 ROBOTIS 모델의
사양이라고 주장하지 않는다. 송신은 protocol2 Ping 한 종류뿐이며 register write·torque·motion
유입구는 없다. `/dev/ttyUSB0` 및 다른 모든 endpoint는 열기 전에 이름 붙여 거절된다.

경로는 설치된 rxclcpp/rxclpy → `Session.Open` → `Cell.Open` → `Cell.SubmitOperation` →
기존 Host admission/SEND_ENTERED → helper다. 정확한 target·profile·program·parameter
산출물과 completion·cancel 선언을 검사하므로 임의 유한 프로그램을 Ping으로 해석할 수 없다.
두 SDK에는 driver·helper·장비 lock·인가 판단을 넣지 않았다. G3/G4 supervisor work-use를 SDK가
중개한다는 주장도 없다. 그 경로에는 여전히 gRPC 유입구가 없다.

두 통제가 서로 다른 경로를 막는다.

- listener 없는 상속 익명 소켓은 이미 선택된 helper 인스턴스에 다른 client가 접속하는 것을 막는다.
- Linux socket peer PID와 실제 부모 실행 파일 inode/device 검사는 caller가 자기 socketpair로
  두 번째 호출 가능한 helper를 만드는 것을 막는다. 고정된 설치 `rx-hostd`만 허용하며 argv0과
  환경변수의 주장으로 신원을 대신하지 않는다.

부모 실행 파일 검사만 끈 **분리된 변형**에서는 가짜 소켓을 만든 Python 호출자가 Ping을
완료했고 같은 거절 검사가 빨간불이 됐다. 제품 helper는 여섯 직접 호출을 모두 거절했다.
따라서 부모 검사를 부차적 보강이라고 부르면 틀린다. peer 자문에서도 그 표현을 교정했다.
선택된 인스턴스의 채널 비공개성과 실제 Host 부모 확인이 함께 필요하다.

신뢰 경계는 기존 G2와 같은 설치된 Rust 실행 파일·OS다. root·같은 UID의 ptrace/FD 탈취·
설치 파일 교체·악의적인 재컴파일을 격리하는 sandbox가 아니다. 부모 생존과 상속 채널을
검사하고 부모 종료 시 채널 폐쇄 및 Linux parent-death SIGKILL을 사용한다. 과거 PID 하나를
근거로 프로세스 신원을 복원하는 F9 회복 경로와 혼동하지 않는다.

## 등록, 실행 바이트와 기록

Host의 비공개 설치 staging에서 native instance UUID를 한 번 생성한다. `installation.json`과
native SQLite metadata가 같은 신원을 가져야 하며, G1 단일 작성자 lock이 동시 소유를 거절한다.
같은 모델 내용의 다른 인스턴스로 바꾸면 신원 대조가 실패한다. 이 결속은 **로컬 Host 설치
등록**이다. 별도 F7 Registry나 저장소 전체 복제·rollback 탐지를 추가한 것이 아니다.

소스 고정에는 Host·helper·공식 원본 pin·빌드 입력·SDK source-lock이 포함된다. 그것만으로
실행 파일을 신뢰하지 않는다. 실제 helper와 descriptor를 G2 인증된 릴리스 inventory에 넣고,
기존 컴파일된 개발 루트로 검증한 byte pin을 spawn 직전 다시 검사한다. 임의 실행 경로는 없다.
byte 확인과 고정 경로 실행 사이 설치 안정성 신뢰, offline 철회 최신성·제품 키 수탁·통째 상태
rollback의 기존 한계는 유지된다.

native journal은 helper 호출 전에 시도 신원을 영속화한다. helper 자신이 별도 audit 항목을
기록한 뒤 SDK를 호출하며, 성공 capture에는 SDK 결과와 model·TX/RX가 남는다. 결과가 없으면
lookup과 재시작은 재핑하지 않고 UNKNOWN을 유지한다. 미결 상태에서는 새 dispatch와
handover/release를 거절한다. capture는 과거 native 관측이지 현재 작업 허가나 물리 완료가 아니다.

호환성은 세 항목으로 확인한다. 공개 protobuf·strict profile 번들은 바뀌지 않았다. 기존
JTC/MELSEC 영속 표현은 frozen 값의 decode/encode가 같은 byte를 내며, 이전 G5.1 Host가 만든
FILE_SIMULATION 설치를 새 Host로 열어 실제 호출하는 별도 장면을 둔다. 새 adapter만
`DYNAMIXEL` 설치 arm과 `native-dynamixel` DB의 `dynamixel/`·`dynamixel-operation/`·
`dynamixel-invocation/` 이름공간을 추가한다. 기존 record를 변환하거나 덮어쓰지 않는다.
이전에는 지원되지 않던 VALIDATED_DRIVER 구성에는 명시적 endpoint가 추가됐다.

## 실행 결과와 한계

| 실제 Linux 장면 | 플랫폼 관측 | helper audit / native row | 핵심 관측 |
|---|---|---|---|
| Python 응답 유실 | KNOWLEDGE_ENDED / OUTCOME_SUCCEEDED | 1 / 1 | 원 요청 재전송과 C++ 같은 세션 재전송에서 동일 receipt |
| C++ 응답 유실 | KNOWLEDGE_ENDED / OUTCOME_SUCCEEDED | 1 / 1 | 원 요청 재전송과 Python 같은 세션 재전송에서 동일 receipt |
| Python helper 종료 | KNOWLEDGE_UNKNOWN / OUTCOME_NONE | 1 / 1, capture 없음 | 별도 OS 관측자가 실제 helper를 SIGKILL; 재호출 없음 |
| C++ helper 종료 | KNOWLEDGE_UNKNOWN / OUTCOME_NONE | 1 / 1, capture 없음 | 별도 OS 관측자가 실제 helper를 SIGKILL; 재호출 없음 |

각 행은 새로 만든 격리된 모의 설치다. 한 행 안에서 두 언어가 같은 살아 있는 Host 인스턴스와
같은 operation을 사용했다. 응답 유실은 암호화된 반환만 버리는 test tunnel로 만들었고, native
손실은 고정 모의 지연 중 외부 OS 관측자가 helper를 종료해 만들었다. 제품 fault switch는 없다.
새 client boot는 결과 조회에 사용하며, 폐기된 이전 boot는 실제 UNAUTHENTICATED로 거절됐다.

실제 Host의 여섯 거절은 `/dev`, 다른 profile, 다른 source digest, 다른 Ping program 산출물,
helper 내용 변조, helper와 함께 위조한 inventory다. 실제 helper의 여섯 Python/C++ 우회 시도와
네 endpoint 거절도 별도 관측했다. 설치·등록·소프트웨어 준비·cell 인가·native 결과를 하나의
READY 판정으로 합치지 않았다. 전체 material workflow 완료나 물리 자원 해제를 주장하지 않는다.

[원시 근거와 재현](../references/dynamixel_ping_2026-09-25/README.md)은 최초 실패와 수정된
조건을 함께 보존한다. 기존 아홉 통과선, G3 12장면·G4 22장면, Host 자기 발급 거절 셋과
새로 설치한 두 언어의 82 wire 벡터도 별도 검증했다. 과거 runner가 출력하는 당시 한계 문구는
원문으로 보존하며 이를 현재 구현 전체의 상태 판정으로 재사용하지 않는다.

## 남은 네 제품과 전체 번들

아래는 모두 필수 후속 통합이며 선택 사항이나 영구적인 범위 밖이 아니다. 선정 commit과
라이선스 원문은 [G5.1 조사 기록](40_strict_wire_and_clients.md)에 있다. 이 표는 설치 완료가 아니다.

| 대상과 선정 버전 | 다음 통합에서 닫을 경계 | 완료 증거 |
|---|---|---|
| DYNAMIXEL Hardware Interface 1.5.2 | hardware_interface/controller_manager와 RX Host가 같은 bus·joint를 각각 소유하지 않도록 현재 lifecycle·의존성을 먼저 측정 | 단일 소유 모의 ros2_control 경로, 구성·controller 손실·중복 client 거절, 필수 interfaces 포함 |
| AI Worker 2.2.7 | robot manager와 compose의 restart/privileged/dev 전제를 분해하고 RX와 내부 manager의 책임 계층 선택 | 선정 배포의 필수 ROS/MoveIt/navigation/controller 의존성 설치·기동·종료·손실 시험 및 중복 restart 소유 부재 |
| AI Sapiens 0.2.2 | controller manager·MuJoCo·sim2real·ONNX Runtime 및 네 policy asset의 버전·hash·license·실행 장치 제약 | 원본 자산 수령과 라이선스, 고정 모의 실행, 자산 누락/변조·manager 손실·권한 거절; 경로 존재만으로 완료 금지 |
| OpenMANIPULATOR 5.1.2 | s6-overlay/cyclo manager와 RX의 재시작 책임, DHI/ROS2 control/MoveIt/RealSense 의존성 | 선정 구성의 단일 관리 책임·모의 작업·응답 유실·종료/인계·직접 접근 거절 |

DYNAMIXEL도 이번에는 protocol2 Ping 모의 경로만 닫았다. 실제 serial transport, 선정 실물
모델·firmware·권한·관측·보호·현장 검증은 별도 승인과 근거가 필요하다. 이 문서를 실제 장비
운전 승인으로 사용할 수 없다. `robot_connected:false`, `simulated_adapter_connected:true`,
`physical_qualification:NOT_PERFORMED`, `sdk_baseline_complete:false`,
`robotis_bundle_complete:false`를 기계 판독 결과에도 유지한다.

## 호환 commit 조합

| 저장소 | 기여 commit | develop 병합 | 첫 PR CI |
|---|---|---|---|
| [platform PR25](https://github.com/jack0682/rx-platform/pull/25) | `b145366992c36b1227efbab7e7a776fae6d9c62f` | `7a825b346a02d5283498ebab8f8288a28357e32c` | [36107662073](https://github.com/jack0682/rx-platform/actions/runs/36107662073), attempt1, 409/0/16 |
| [solutions PR41](https://github.com/jack0682/rx-solutions/pull/41) | `039aa0d0459b8087e708ec77fdccfbd48fadc1d0` | `fccc996ae60062ea4ef42acf88bc594bc698d20c` | [36107754317](https://github.com/jack0682/rx-solutions/actions/runs/36107754317), attempt1, 437/0/20 |

서명·DCO를 확인한 병합 도구를 사용했고 기여 tree와 병합 tree가 같다. 이 문서의 commit을
위 코드 조합과 함께 사용한다. 새 DYNAMIXEL helper CI와 기존 client CI도 첫 시도에 통과했다. `main` 승격, 외부
package registry 배포, 실제 운영 배포는 이번 작업에 포함하지 않는다.


최종 설명 교정 [solutions PR42](https://github.com/jack0682/rx-solutions/pull/42)의 기여 commit은
`71aec7e7f1e2d6723884e30e97b9dd4ba97fb502`, develop 병합은
`0996f0f5ac7b66a76388983e5c100a386458ba29`다. 두 통제가 모두 필수라는 주석만 바꾸었지만
소스 고정값이 바뀌므로 새 G2 서명 이미지에서 네 장면을 모두 다시 실행했다. 최종 호환 조합은
platform `7a825b346a02d5283498ebab8f8288a28357e32c`와 solutions
`0996f0f5ac7b66a76388983e5c100a386458ba29` 및 이 문서 commit이다.
[최종 PR CI](https://github.com/jack0682/rx-solutions/actions/runs/36108618125)도 attempt1에
437/0/20으로 통과했다. `release-clarified`의 helper·나머지 다섯 실행 파일은 이전과 바이트가
같고 Host만 컴파일된 source descriptor pin이 바뀌었다. 실제 네 장면·여섯 Host 거절과 helper
거절을 새 이미지에서도 관측했다. 이전 근거를 지우거나 새 소스의 실행으로 이름 바꾸지 않았다.
