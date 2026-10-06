# M5 artifact candidate gates

These tools construct and check migration candidate artifacts on fresh Linux CI runners. Tool preparation and pure fixture tests are not runtime acceptance. The workflow never publishes a release/tag or receives a publisher private key.

## Boundaries

The producer reads the exact clean monorepo commit and records component paths, tree OIDs, raw Git leaf closure, toolchains and artifact hashes. The SDK consumer has no checkout: it installs the delivered wheel offline, consumes the installed CMake package, checks the public Rust contract source bundle and runs helper conformance. A separate trusted provisioner may read the delivery source bundle and verification kit. Every external-author container is independently checked for its selected image, read-only root and exact public author/registered-terminal mounts; no core source or signer private key is mounted.

`build_distribution_candidate.py` exports unchanged P/S source, verifies each file against its Git blob/mode, and archives the generated jobs1 Docker recipe separately. It builds exact developer P/S images and extracts three current sealed recovery witnesses. The binary installer consumes those images without rebuilding. APT is not snapshot-pinned, so bit-reproducible rebuilds are not claimed.

`build_sdk_artifacts.py` reuses the existing client builders and installed `external-sdk` exporter. Artifacts include a Python wheel/offline wheelhouse, CMake headers/library/config, prepared client sources, external helper/examples/interface index, two public Rust contract source crates, a provisioner verification kit, and a separately classified historical runtime consumer. The Rust export changes only the generated artifact workspace members/lock; a new dependency version/source/checksum fails the gate. P/S source manifests and locks remain unchanged. The shared Rust budget is Cargo jobs1; the existing client test deliberately retains its two CMake `--build -j2` invocations. Distribution Docker recipe CMake jobs1 is a separate scope. The external interface index is descriptive, not a new normative validator.

`local_sim_candidate.py` invokes the existing same-commit skill builder/installer tests without modifying them. LOCAL_SIM server/worker checks are separate from FILE_SIMULATION and registered EXTERNAL_ADAPTER_SIMULATION.

## Runtime and compatibility scope

`consume_runtime_artifacts.py` installs the binary distribution, exercises FILE_SIMULATION and invokes the four registered counter scenarios in `full_run`. Actual native entry, effect and durable completion are separate observations. A lost consumer CLI stdout is recovered by querying the original Run from a new process. It is not an HTTP packet-loss test. Cold external Host recovery remains unsupported: the negative cases require original UNKNOWN/held identity and unchanged native facts, never fabricated completion or replay. If warm recovery prevents the intended UNKNOWN precondition, that case fails.

Historical client files are recovered byte-for-byte from the published v0.4.0-rc.1 image. They are mounted read-only and run as the original `runtime` facade for skills/steps/compose/original-UUID composition recovery. This does not establish Execution-v2 or old wheel/CMake ABI compatibility. Independent old client wheel/CMake artifacts were not found in the preserved releases; historical-source-derived rebuilds must be labelled separately from historically published binaries.

No test reuses the preserved CP2 Run, TLS, DB, Docker resources or request identity. Every new case has a separate fresh installation. A failure is retained and cannot be replaced by a new request to obtain a green result. Author command logs support later cost measurement, but are not directly comparable with the prior 725-command scope.

## Publication and signing

Fresh package/review/qualification Ed25519 keys are CI fixtures only. They are separate from publisher provenance and do not establish product signing custody. Existing `sign_release.py` custody requirements are not bypassed.

Only private-value-audited evidence projections are uploaded. Raw private trees, TLS keys, passwords and tokens are excluded. A failed audit emits a non-secret refusal receipt and fails the job. Candidate source/binary artifact inventories independently exclude acceptance-time private inputs.

After actual checks pass, the owner downloads the exact selected artifacts, signs their reviewed CHECKSUMS offline, and verifies the detached signature with `verify_release_provenance.py`. Its public keyring hash is supplied by an independent reviewed policy, never unsigned artifact metadata. `gpgv` trusts the selected keyring and does not discover revocation/expiry; see the [official manual](https://www.gnupg.org/documentation/manuals/gnupg/gpgv.html). This proves exact-file publisher provenance, not package acceptance, physical qualification or `rx.release.v1` custody.

## Required gates

The independent Actions check `M5`, alongside existing `CI` and `DCO`, must pass for the exact PR/head/base and selected workflow. It runs for all main/develop PRs, with native amd64/arm64 runners in parallel and per-runner Cargo jobs1. Failed, skipped or cancelled child jobs fail the aggregate. Required-check settings and merge-helper workflow provenance are part of the reviewed integration overlay and require remote readback before the first M5 PR merge.

M5 acceptance additionally requires the exact candidate/source/contract/binding tuple, static and compiled identity receipts, supported profile evidence, owner signature verification and an explicit acceptance record. Simulation CI success is not production or physical readiness. GitHub-hosted job termination does not preserve live failed runtime state; public evidence is retained separately and the original CP2 environment remains untouched.

## Failed builds before acceptance

Before any LOCAL_SIM work/output exists, the producer can publish only a closed failure projection. It rechecks the exact workflow candidate and public source vocabulary, then emits fixed diagnostic kinds, compiler codes and bounded known source locations/byte counts. Unknown or ambiguous locations remain unknown. This branch copies no raw log, original JSON or source/binary artifact and leaves M5 failed. Build-time tests may create private keys; their output is never assumed public.

The generated Docker recipe copies the diagnostic sidecar outside `/source` and outside runtime image outputs. On a failed sealed test it emits only the closed projection and preserves the original nonzero exit. Source files, locks and original Dockerfiles are unchanged; generated recipe/sidecar/vocabulary hashes are recorded. Raw-log hashes stay in private work receipts and are not independently rehashable from the public projection. Resource values are post-command snapshots, not peak usage or OOM proof; a SIGKILL or exit137 message does not prove an OOM.

A producer diagnostic artifact is uploaded only if the current publication step created a fresh projection and set its readiness output. Existing files/symlinks remain untouched and never acquire readiness. Any LOCAL_SIM phase trace disables this early path; normal artifacts still require the existing actual-private-value audit. The first failed M5 attempt remains preserved and its ARM build cause remains UNKNOWN until a new run produces observations.
