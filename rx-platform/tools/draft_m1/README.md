# DRAFT-M1 isolated simulation roundtrip

This directory prepares a new installation and checks the actual operator bundle → P → Executor → Host → external provider path. It uses existing application APIs, signed package tools, Host acknowledgements and six-area qualification. It is a test harness, not a product service or a browser shell gateway. A passing run is a technical acceptance candidate; the owner still accepts the milestone explicitly.

Run only on authorized isolated Linux. `run.py` refuses other operating systems. The preserved Mac is for editing and static inspection only. Every case requires a new private workspace, public evidence directory, installation identity, signing keys, TLS identities and Docker state. CI assigns each case a separate Ubuntu runner; no later case shares CPU/I/O with preserved earlier services. This removes a known test-environment interaction, not proof that load caused the historical preentry failures. It never accesses the historical CP2 installation.

## Build from this repository

The minimal image uses the exact P/S source and operator bundle in this repository, the existing external-process provider, and the real C++ BT engine. It does not build ROS, DHI, controller packages or the full distribution. Runtime binaries use the repository's release profile, matching the existing runtime installation tests; this is still a simulation integration candidate, not a product release. The source-pinned Rust recovery tests and disposable signing exporter retain their normal test profiles.

From the RobotTransformation root on Linux:

```sh
docker build \
  -f rx-platform/tools/draft_m1/Simulation.Dockerfile \
  --build-context btcpp=https://github.com/BehaviorTree/BehaviorTree.CPP.git#6e469c6ba133aaa842dac9b096b41f2d33ee2b0e \
  -t rx-draft-m1:current .
python3 -m venv /tmp/rx-m1-browser
/tmp/rx-m1-browser/bin/pip install playwright==1.62.0 cryptography==50.0.2
/tmp/rx-m1-browser/bin/python -m playwright install --with-deps chromium
/tmp/rx-m1-browser/bin/python rx-platform/tools/draft_m1/run.py \
  --platform-image rx-draft-m1:current --solutions-image rx-draft-m1:current \
  --workspace /tmp/rx-m1-normal-private --evidence-dir /tmp/rx-m1-normal-evidence \
  --case normal
```

One immutable image supplies distinct P, Host and Executor containers. Runtime services are non-root, have read-only root filesystems and no host devices or Docker socket. Only terminal HTTPS is bound to loopback. Existing test fixture export/signing runs separately with network disabled and cannot grant runtime authority by editing P's ledger. The default fixed fixture signing keys are replaced with newly generated Ed25519 keys before creating any signed packages. The generated SIM author principal has ENGINEER and OPERATOR roles; verifier and release identities remain separate. No production principal is changed.

## Cases and scope

- `normal`: configure/save/reopen A, execute six operations, inspect independent provider effects and same graph after reload.
- `changed-material`: save A and B in the same installation, prove A's saved receipt unchanged, execute B with its different material/angle input.
- `groove-missing`: provider genuinely reports status 10 at A2; no rotation or regrasp follows, shelf occupancy remains visible in evidence.
- `completion-loss`: the existing simulation result-loss mTLS relay forwards the real Host Authorize request and withholds its response only after the Host confirms native entry. It also holds that original operation's evidence publication and receipt queries. Normal provider facts/effects remain intact; P must show UNKNOWN with original operation identity and retained resource/slot custody. The relay remains BLOCKED and no subsequent effect is permitted. It does not test general restoration or certify CP3. The earlier native-output wrapper experiment at `5389655` remained MAY_HAVE_EXECUTED; its [failed PR run](https://github.com/jack0682/RobotTransformation/actions/runs/37656274630) remains historical evidence, not UNKNOWN acceptance.
- `lost-start-response`: Playwright discards an actually committed P Start response and recovers using exactly the same request key and body. Independent provider records must show no duplicate effect.

Each case preinstalls a single bounded execution domain containing material A and B. The browser's saved request must exactly match an approved candidate. The one pattern slot represents the simulation shelf seat because the existing v2 inventory contract requires a pattern resource; it does not add a tray workflow. Other configurations require the existing installation and qualification procedure.

The harness performs a missing-material negative UI check before any Run. Existing Rust tests cover broader revision/authority/package changes; a browser PASS alone does not claim all T01–T10 regressions passed. `--prepare-only` leaves an installation ready for inspection and explicitly makes no browser/runtime completion claim.

## Evidence and preservation

Upload **only `--evidence-dir`**. The private workspace contains credentials, TLS private keys and disposable signing keys and must never be included in CI artifacts. Public evidence includes source/image identity, original API requests and responses, exact signed public packages, qualification evidence, screenshots, browser diagnostics, native effects/state, and failure logs. Login requests and cookies are not recorded.

The harness never calls generic Docker cleanup. Containers, volumes, original request IDs and private workspace remain after success, failure and UNKNOWN. `installation.json` in the private workspace lists every owned container/volume/network. `preservation.json` records this disposition in public evidence. GitHub-hosted runner disposal ultimately destroys live Docker state: retained public evidence is not a resumable installation, and must not be described as one. Do not claim durable UNKNOWN restoration from CI artifacts alone.

No case reset, automatic retry with new identities, timeout relaxation, forced release, fake Host receipt or direct P database mutation is part of this harness. A failure is retained and requires diagnosis before testing a changed candidate in a new case directory.
