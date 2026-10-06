# Advisory workflow simulation diagnosis

This is an investigation of the existing CI failure in run 37522256416. It never
replaces the required CI, DCO or M5 checks and does not reclassify that failure.
The workflow runs on a fresh Linux x86_64 runner only when these diagnostic files
change in a PR, or when explicitly dispatched. It has no retry loop or tolerated
test failure. Python 3.11 or newer is required; the workflow installs Rust 1.98.1
and explicitly requests the rustfmt component.

The control checkout supplies the reviewed diagnostic tools. A separate source
checkout is fixed to commit `314c9f323a7dd8865a3f9e2b1347325684858c8e`. Every tracked
source blob, mode, the tree ID, and the original bounded source-identity proof are
checked before copying to a disposable projection. Both checkouts remain unchanged.
Only `rx-solutions/runtime/rx-host/tests/workflow_simulation.rs` changes in the
projection. No product runtime, binding, deadline or UNKNOWN policy is changed.

The observer retains the original failed test fixture and emits a bounded
diagnostic containing the operation, invocation, primitive, node, receipt status,
error type and hashes. The runtime sends worker stderr to `/dev/null`; this runner
cannot recover it and records that absence. Successful fixtures retain their
existing automatic cleanup. This is credential-free FILE simulation, with no
physical device or preserved CP2 input.

The frozen semantic-context proof includes the test source. Therefore the
projection is deliberately `UNKNOWN_CONTEXT_CHANGED` for exactly that one file,
although all 15 named production identity records and SDK identity must remain
unchanged. This is diagnostic evidence, never a passing production identity gate.
The observer is formatted in the projection and its resulting bytes are recorded.

The runner invokes exactly once:

```text
cargo test --workspace --all-features --locked --test workflow_simulation -- --test-threads=2 --nocapture
```

It uses a fresh Cargo target and the same workspace/all-features/locked selection
as the failed S workspace job. The original CI command did not specify test thread
count; this diagnostic explicitly caps it at two for the two selected tests. This
is a disclosed diagnostic concurrency setting, not a byte-identical replay of the
original command. The test's original nonzero status remains nonzero.
Toolchain/executable, input, patch, command and log hashes are retained. Only
bounded original JSON facts and selected logs/proofs are eligible for publication.
A generic private-key, credential-field, authorization-header and token scan runs
before an atomic approved projection is published. A refused scan publishes only
a non-secret refusal receipt. Raw source, venv, arbitrary temporary files, private
keys and tokens are not uploaded. The scanner is not a universal secret detector.

Local unit tests use fabricated files and mocked commands. Actual compilation,
formatting and execution belong to the isolated Linux job. A successful diagnostic
trial does not establish a root cause, repair the original failure, or accept M5.
