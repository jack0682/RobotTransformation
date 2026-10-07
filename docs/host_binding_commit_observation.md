# Host binding 교체 확인 계약 변경 기록

2026-09-29. 선택 Host process-configuration binding의 **revision 2**를 정의한다. 기본 protobuf field 번호와 RPC 이름은 유지하고, 구성 snapshot에 선택적 binding_commit 관측을 추가한다. 이 문서는 교체 확인의 범위와 호환성 기록이며, P의 적용 허가가 구현됐다는 뜻은 아니다.

관측은 원 commit 요청 ID, 계획 digest, 대상 셀, 변경 전/후 구성 digest와 설치 identity, 유지된 delivery/evidence 저널 ID, 변경 후 binding digest를 포함한다. Host는 현재 실행 중인 서비스의 설치 identity와 binding digest가 완료된 commit 기록에 일치할 때만 관측을 내보낸다. 과거의 완료 영수증, 준비/진행 중인 교체, 정지 상태의 기록은 현재 서비스의 교체 증거가 아니다.

P는 사용자 제공 JSON을 확인 증거로 받으면 안 된다. 인증된 Host 연결에서 시작 시각을 기록한 bounded read로 조회하고, 현재 Host boot/저널/전체 셀 범위와 원 배치 계획을 대조해야 한다. 확인은 binding 교체의 사실이며 공정 적용, native 상태, 자격 또는 실행 허가가 아니다. activation_authorized는 계속 false다.

호환성: 새 필드가 없는 기존 JSON은 미확인으로 읽을 수 있다. 새 필드가 포함된 JSON은 이전 strict decoder와 호환되지 않으므로 선택 binding의 source revision과 hash를 갱신한다. 정확한 hash 협상으로 P/Host/SDK 조합을 맞춰야 하며, 부재·미지원·오래된 관측을 성공으로 바꾸지 않는다. 기본 계약의 frozen manifest는 변경하지 않는다.

구현 순서: 공유 model/검사와 optional binding manifest → 생성 SDK → Host 현재 관측 → P의 사전 요청 기록과 실측 확인 → staged change 적용 조건 → 실제 이미지의 중단/재기동/잘못된 확인 반례. 마지막 P 확인·적용 조건을 연결하기 전까지 기존 HOST_BINDING_CHANGE_REQUIRED 차단은 유지한다.

현재 서비스 identity는 durable startup marker에 실제 Host boot가 일치할 때만 제공한다. 정지 상태 또는 같은 identity를 가진 다른 boot는 현재 확인 정보가 아니다. 로컬 mTLS 시험과 모델 반례는 [검증 기록](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/host_binding_observation_2026-09-29/README.md)에 있다. P 확인 정책은 아직 미구현이다.

## Source revision 3

P가 교체 전 evidence 저널 ID도 직접 저장·대조하도록 Snapshot.evidence_journal을 추가했다. 필드가 없으면 기준 확인을 미지원으로 처리하며 추정하지 않는다. 같은 정확한 hash 협상 규칙을 적용하고 SDK를 다시 생성했다. [P 요청 발급과 대조 검증](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/p_host_binding_intents_2026-09-29/README.md)을 참조한다.
