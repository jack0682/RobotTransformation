# 40. strict-wire-v1 공개와 첫 C++·Python 클라이언트 (G5.1)

상태: G5.1 독립 수락 완료 (`g5-strict-wire-and-first-client-claude-2026-09-25`). G5 SDK 기준선 및 ROBOTIS 전체 번들의 완료 기록이 아니다.

## 사용자 요구와 단계 경계

2026-09-25 사용자는 rxclcpp/rxclpy와 ROBOTIS 공식 다섯 저장소의 필수 의존성을 모두 지원하는
기본 전체 개발 번들을 요구했다. 01·13 문서의 기본 포함 의무 부재 문장을 이 추가 지시로
명시적으로 바꾸었다. 공통 작업·권한·결과 계약의 제조사 중립성은 유지한다. 기존 고정 v1.0
계약의 8개 규범 문서·필드 번호·협상 manifest는 변경하지 않았다.

G5.1은 공개 wire profile, 같은 번들에서 생성한 두 언어 개발 인터페이스, 설치된 외부 소비자,
기존 FILE_SIMULATION의 실제 런타임 호출까지다. **로봇 하나를 연결하지 않았다. 따라서 공통
계약이 ROBOTIS 제품을 실어 나를 수 있다는 것도 아직 미증명이다. G5 SDK 기준선 완료도,
다섯 제품군 통합 완료도 아니다.**

후속 [G5.2](41_dynamixel_ping_adapter.md)는 첫 DYNAMIXEL 모의 어댑터의 실제 Linux 연결을 다룬다. 승인된 경계는 공식 SDK4.1.0을
외부 native helper 하나에서 사용하는 read-only protocol2 Ping, 명시적 모의 transport/model,
실제 /dev endpoint 거절, 토크·운동 조작 없음이다. 두 Client Library에 드라이버를 각각 넣지
않고 RX Host의 같은 지속 호출·중복 방지·cell admission을 통과시킨다. 이후 나머지 네 제품,
설치·업데이트·의존성 및 서비스 소유 관계를 차례로 닫는다. 나머지 제품을 선택 사항이나
영구적인 범위 밖으로 바꾸지 않는다.

## 확인한 계획 오류와 구현 결함

기존 조사에는 표준 protoc 클라이언트가 전부 거절된다는 문장이 있었으나 실제 표준 prost
바이트는 strict decode를 통과했다. 문제는 인코딩을 새로 발명해야 한다는 것이 아니라,
서버가 요구한다고 광고한 `strict-wire-v1`의 추가 적합성 조건이 공개되지 않았다는 것이었다.
명시적으로 인코딩된 enum0과 생략된 proto3 기본값도 구분해야 한다.

`Operation.Submit`과 `Lookup`은 의도적으로 UNIMPLEMENTED다. 첫 경로는
`Session.Open → Cell.Open → Cell.SubmitOperation → Operation.Get`이며 응답 유실은 원래
cell 요청을 같은 key로 재전송해 회복한다. cell admission을 우회하는 새 유입구는 만들지 않는다.
G3/G4 supervisor work-use에는 gRPC 유입구가 없으며 SDK가 그 관문을 중개·대신 판단하거나
결과를 합성한다고 주장하지 않는다. 플랫폼 cell admission은 자신의 현재 인가를 계속 검사한다.

별도로 clean generate_protocol에서 Host configuration IDL 저장 호출이 빠져 9개 대신 8개만
생성되는 결함을 발견했다. 누락된 write를 보완했고 기존 9개 RPC IDL 해시가 모두 같음을
확인했다. 이전 체크인 파일이 결함을 가리고 있었으며, 적합성 벡터 작업과 별개의 실재 결함이다.

## 단일 원본과 벡터

규범은 platform `proto/strict-wire-v1/README.md`의 SW01–SW16이다. fixed vectors와
TCK-only probe descriptor도 같은 source bundle에 들어간다. `export_protocol.py`는 16개
파일을 SHA-256으로 묶고 Python/C++는 그 번들에서 메시지를 생성한다. 손으로 복제한 업무
메시지 정의가 없다. 번들 해시는 일관성 검사이며 발급자 인증이나 작업 권한이 아니다.

82개 입력·기대 결과를 규칙과 IDL 번호에서 작성했다. 구현의 출력을 golden으로 추출하지
않았다. 69개는 실제 공개 메시지, 13개는 공개 RPC에서 닿지 않는 깊이·map·추가 scalar를
검사하는 합성 descriptor다. 후자는 새로운 runtime service가 아니다.

기존 Rust typed decode와 generated re-encode 경로를 검사했다. Python/C++는 같은82개
입력의 확장 바이트 해시·상태·명시된 재인코딩 결과가 모두 같았다. 별도 source/target에서
단수 중복 거절을 끈 변형과 명시적 enum0 거절을 끈 변형이 각각 고정 벡터를 실패시켰다.
원본 코덱과 벡터 해시는 바뀌지 않았다.

profile은 정규 protobuf 바이트열을 약속하지 않는다. 특히 shared work budget은 field
occurrence와 packed element를 따로 세므로, 65536개 unpacked real은 decode되지만 표준
packed re-encode는 header 비용 때문에 거절될 수 있다. 이 기존 동작을 이름 없이 바꾸지 않고
규범·기대 결과에 명시했다. 의미적인 필수값·신원·인가·준비·완료 판정은 여전히 runtime 책임이다.

## 개발자 표면

Python은 설치 가능한 `rxclpy` wheel이며 생성 모듈을 자체 namespace 아래 둔다. C++는
`rxclcpp::rxclcpp` CMake exported target, 설치 헤더와 shared library를 제공한다.
외부 CMake 소비자는 core source include 없이 find_package로 빌드했다. Python도 설치된
site-packages에서 같은 corpus를 실행했다. 준비되지 않은 source tree의 package build는 거절한다.

두 라이브러리는 mTLS unary transport, profile 검사, 알려진 계약/필수 feature 협상을 제공한다.
자동 재제출, 자동 취소, 로컬 작업 권한 발급, 장비 제어 또는 별도 지속 원장은 없다. TLS client
private key는 전송 신원용이며 G3/G4의 작업 판단자 키가 아니다. 전송 timeout은 작업 실패가
아니며 이후 같은 요청 조회·재전송과 실제 runtime 기록으로 대조한다.

## 다섯 공식 프로젝트의 고정 조사 기준선

다음은 2026-09-25 조회한 태그와 그 태그의 실제 소스다. 조회 시 main과 같은 commit이었지만,
릴리스 선택은 `main`이라는 이름이 아니라 아래 태그/commit으로 고정한다. 프로젝트 자체
LICENSE는 각각 Apache-2.0이며, 전이 의존성·모델 자산의 조건까지 동일하다고 추론하지 않는다.
아래 다섯은 **G5.1 설치·RX 어댑터 연결을 수행하지 않았다**. 조사·후속 설계 상태이며 전체
포함 요구는 유지된다.

| 프로젝트 | 태그와 commit | 실제 소스에서 확인한 의존성·구성 | 다음 통합에서 닫을 조건 |
|---|---|---|---|
| [DYNAMIXEL SDK](https://github.com/ROBOTIS-GIT/DynamixelSDK/tree/f838bc90f72fcf5b9c279432d6e12fc24969daa8) | 4.1.0 · `f838bc90f72fcf5b9c279432d6e12fc24969daa8` | C++·Python 구현. Python metadata4.1.0, pyserial, Python<3.9에서는 importlib_resources. ROS wrapper는 ament_cmake/ament_cmake_python | G5.2의 단일 Host native helper, 모의 Ping, 실제 장치 접근 거절, 재전송 중복 방지. C++/Python SDK에 드라이버를 중복 삽입하지 않음 |
| [DYNAMIXEL Hardware Interface](https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface/tree/6bb5f93ecad1fe3c231e3ece580344e8f0a6efc3) | 1.5.2 · `6bb5f93ecad1fe3c231e3ece580344e8f0a6efc3` | rclcpp, hardware_interface, pluginlib, realtime_tools, dynamixel_sdk, dynamixel_interfaces. CI .repos는 두 의존성을 main으로 참조 | ROS2 controller_manager가 실제 bus를 소유하는 경계와 RX의 상위 요청·변경·정지 책임, controller 활성화/torque 효과, 모델·펌웨어·port 배타성 |
| [AI Worker](https://github.com/ROBOTIS-GIT/ai_worker/tree/897ef342ff0e1b2ef59d6afbb5195b410d57b85f) | 2.2.7 · `897ef342ff0e1b2ef59d6afbb5195b410d57b85f` | ffw metapackage, robot manager·swerve/spring/joystick controllers, MoveIt·navigation·teleop. Bringup은 ROS2 control/Gazebo/rviz, manager는 DYNAMIXEL interface. robotis_hand/robotis_interfaces도 의존 | 기존 robot manager의 하위 제어·상태 기능을 재사용. Compose의 restart:always와 RX 재시작을 중복시키지 않음. ZED 자산/장치·RT 권한 및 모델별 기동 효과 검증 |
| [AI Sapiens](https://github.com/ROBOTIS-GIT/ai_sapiens/tree/611a070fad83d2a9ef9c1bc82213988450cf471c) | 0.2.2 · `611a070fad83d2a9ef9c1bc82213988450cf471c` | controller_manager, impedance/RC controllers, MuJoCo·RadioMaster interfaces, sim2real. Docker는 ROS Jazzy와 ONNX Runtime1.23.2, amd64/arm64 분기 | ONNX runtime과 실제 policy/model 자산을 별도 목록화. 시뮬레이션/실기 전환·USB/IMU/지원 상태·잔류 제어를 검증하고 모델 가중치 누락을 설치 성공으로 가리지 않음 |
| [OpenMANIPULATOR](https://github.com/ROBOTIS-GIT/open_manipulator/tree/0a4af6a923b8b7d80b8c20506d1839c54d2e993e) | 5.1.2 · `0a4af6a923b8b7d80b8c20506d1839c54d2e993e` | ROS Jazzy, DYNAMIXEL hardware/interface, robotis_interfaces, MoveIt/Gazebo. Docker는 RealSense, s6-overlay3.2.1.0, cyclo_manager agent를 포함. ROS 서비스는 기본 자동 실행 대신 s6 관리 | RX와 s6/cyclo_manager가 같은 process를 이중 감독하지 않도록 최종 소유자를 정함. arm64/amd64·카메라·장치/모드별 의존성·수동 정비 인계를 검증 |

확인 원본은 각 태그의 `package.xml`, `.repos`, Python packaging metadata 및 Dockerfile이다.
CI의 main 참조와 Docker의 jazzy branch clone·floating image는 RX 릴리스 lock으로 그대로
사용할 수 없다. 전체 번들에서는 그 전이 의존성·apt/pip closure·image digest·자산 hash와
라이선스를 잠근다. 이 조사는 그 closure를 전부 설치하거나 호환성을 검증했다는 뜻이 아니다.

### 기본 번들의 감독 관계

설치는 다섯 모두 제공하는 것을 목표로 하지만 설치만으로 모든 로봇 서비스를 시작하지 않는다.
RX가 상위 process lifecycle을 소유하면 기존 s6/Compose의 경쟁 restart 정책을 제거하거나
하나의 하위 관리자에 명시적으로 위임한다. ros2_control controller_manager의 제어 loop와
장비 bus 소유를 RX 언어 클라이언트가 복제하지 않는다. 기동이 torque/운동을 유발하는 구성은
그 효과를 profile과 진입 조건에 넣어야 한다. 문서 권고만으로 배타성을 입증하지 않는다.

첫 검증 환경은 Linux arm64/Ubuntu24.04, Python3.12.3, C++20, distro protoc/libprotobuf3.21.12,
gRPC C++1.51.1, Python grpcio1.84.0/protobuf7.36.2다. 실제 설치 버전은 별도 dpkg/pip receipt로
기록한다. 이는 전체 ROBOTIS stack의 호환 행렬이 아니다. 특히 C++ protobuf ABI는 버전 간
호환을 가정하지 않아 installed CMake config가 빌드한 Protobuf 버전을 EXACT로 요구한다.
[Protobuf의 공식 호환성 규칙](https://protobuf.dev/support/cross-version-runtime-guarantee/)
또한 Python 생성 코드와 runtime의 지원 범위를 별도로 규정한다.

## 다음 단계의 완료 기준

- **G5.2:** 위 단일 DYNAMIXEL 모의 Ping adapter를 두 SDK에서 같은 실제 P/H 경로로 호출,
  무장비·모델 불일치·응답 유실·같은 endpoint 경쟁·UNKNOWN을 실제 거절/보존으로 증명.
- **G5 SDK 기준선:** 현재 generic unary 표면 외의 등록/준비/작업 허가·취소·교체·복구 지원 범위를
  실제 runtime 유입구에 맞춰 정하고, 없는 경로는 별도 구현 전까지 미지원. 연결 재개를 권한
  복원으로 해석하지 않음.
- **전체 ROBOTIS 번들:** 나머지 네 제품, ROS2·모델/데이터/시뮬레이터 자산을 포함한 한 번의
  설치, import/link/기동 전 검사, 실제 관리 소유 관계, 부분 업데이트/기록 유지·복구를 확인.
  최초 제품 연결이나 패키지 목록만으로 이 판정을 대신하지 않음.

## 실제 실행 결과

현재 소스의 실제 `rx-platformd`/`rx-hostd`와 Linux boottime, persistent writer, mTLS를 사용했다.
기존 signed process package·compiler·등록된 terminal의 승인·qualification을 재사용하고
SDK는 E의 클라이언트 역할만 대체했다. 전송을 확인하기 위해 가짜 운영 승인이나 DB seed를
추가하지 않았다. 설치된 wheel/CMake 소비자 기준으로 다음 네 장면이 통과했다.

| 언어·장면 | 실제 runtime 결과 | native 효과 | 연결 단절 뒤 대조 |
|---|---|---|---|
| Python 응답 유실 | KNOWLEDGE_ENDED / OUTCOME_SUCCEEDED | 1회 | 같은 요청의 원 receipt 회복, 새 client와 C++ 조회에서 같은 operation ID |
| C++ 응답 유실 | KNOWLEDGE_ENDED / OUTCOME_SUCCEEDED | 1회 | 같은 요청의 원 receipt 회복, 새 client와 Python 조회에서 같은 operation ID |
| Python native I/O 실패 | KNOWLEDGE_UNKNOWN / OUTCOME_NONE | 0회 | 재시작·C++ 조회에서 UNKNOWN 보존 |
| C++ native I/O 실패 | KNOWLEDGE_UNKNOWN / OUTCOME_NONE | 0회 | 재시작·Python 조회에서 UNKNOWN 보존 |

응답 유실은 TLS를 해독하지 않는 test TCP tunnel에서 P→client 반환을 보류한 뒤 실제 Host
file 효과를 관측하고 연결을 끊어 만들었다. SDK가 timeout을 성공으로 합성하지 않았고,
명시적 같은 cell 요청 재전송은 새 native 호출을 만들지 않았다. UNKNOWN은 읽을 수 있지만
쓸 수 없는 effect file에 대한 실제 native I/O 실패로 만들었다. 그 상태를 임의의 FAILED나
NOT_EXECUTED로 바꾸지 않았다. OUTCOME_NONE을 최종 UNRESOLVED로 보고하지도 않는다.

같은 유효 요청/session이라도 등록되지 않은 표면의 certificate를 쓰면 P의
PERMISSION_DENIED(`certificate is not registered`)이고, 위조 mandate도 거절됐다. 유효한
제출 전 native 효과는0이었다. SDK에 G3/G4 supervisor work-use 다리가 있다고 주장하지
않으며, 해당 관문을 대신 판단·합성하지 않는다. 기존 관문은 별도 G3/G4 회귀로 유지했다.

macOS 전체 workspace는 platform408/0/16, solutions388/0/17이며 기존 시험은 줄지 않았다.
새 Client libraries CI는 profile 누락/변조 거절, 설치 wheel, 외부 CMake 소비자와82개 corpus를
필수 작업으로 실행한다. [원시 증거](../references/strict_wire_clients_2026-09-25/README.md)가
성공뿐 아니라 생성기 누락·두 변형·이미지 조립 환경·실패한 최초 테스트 기대값도 보존한다.

자산 조사에서도 이름만 생략하지 않았다. AI Sapiens의 고정 소스에는 k1의 walk_default,
dance1, dance2, squat에 해당하는 `policy.onnx` 네 경로가 존재한다. 파일 경로 존재는 실제
weight 설치·해시·실행 호환성 또는 모델 라이선스 검증이 아니다. 해당 자산과 외부 추가 다운로드를
G5 후속 bundle inventory에서 별도로 닫는다. 다른 네 저장소의 이번 확장자 검색에서 weight
파일이 없었다는 사실도 외부 모델 의존성이 없다는 뜻이 아니다. 원본은
[고정 AI Sapiens assets](https://github.com/ROBOTIS-GIT/ai_sapiens/tree/611a070fad83d2a9ef9c1bc82213988450cf471c/ai_sapiens_sim2real/assets)이며,
각 프로젝트 LICENSE 원문 hash와 manager/asset 경로는 `robotis-source-receipt.json`에 보존한다.

기존 아홉 경계(등록 library/resident, 배포 출처, 자원, 관리자 손실, 작업 사용, 의존성 교체,
지원 한계, 잠금 수명)는 현재 소스의 별도 실행으로 통과했다. resident는 resource runner에
포함된다. G3 12장면·G4 22장면도 통과했으며 Host 자기 발행 거절 세 장면의 출력은 G4와
바이트 단위로 같다. 이 회귀는 supervisor work-use의 SDK 유입구를 새로 증명한 것이 아니다.

## 호환 commit 조합

| 저장소 | 기여 commit | develop 병합 |
|---|---|---|
| [platform PR24](https://github.com/jack0682/rx-platform/pull/24) | `cffbe286829d8ba104b44a0dd18e70865b84e098` | `6c1e7d6219add7652c7ee18d25eb21b39d159076` |
| [solutions PR40](https://github.com/jack0682/rx-solutions/pull/40) | `5207f2c57503cb00c0f4f5d5b3ab959b2bcda1d1` | `1edc8457370c4691171cbbdd7831315564fe565c` |

두 PR의 첫 CI는 platform409/0/16, solutions432/0/20이며 platform의 필수 Client libraries
작업도 통과했다. 이 문서의 commit을 위 코드 조합과 함께 사용한다. `main` 승격이나 외부
패키지 registry 게시는 수행하지 않았다. 공개 source PR, 로컬 wheel/설치 패키지, 로컬 검증
image와 실제 운영 배포를 구분한다.
