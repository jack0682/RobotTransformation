# Registered external counter verification

Run only on a fresh Linux CI runner with explicit `--execute-fresh-linux-ci`. The installed developer P image supplies the fixture exporter; the selected S image supplies Host, Executor, authoring CLIs and the Python interpreter. The same S image ID is used for Host and author. The verification kit and publisher/package signer private keys are not author mounts.

The provisioner creates fresh TLS and fixture Ed25519 keys, pins a fresh external-only initial cell before first Host initialization, compiles through public package CLIs, and exercises public review, stage, Host acknowledgement, apply, six measured qualification areas and activation. No FILE Host is hot-replaced. The report remains software simulation evidence, not physical qualification or cold recovery certification.

The required `--historical-bundle` is the prepared `historical-runtime-client/` artifact with exact original files, lock, probe and origin record. The old published four-file runtime facade is mounted read-only and tested before the selected cell has Runs/work. It performs catalog/steps/compose/recover with the same UUID and explicit non-execution result. Its source bytes, old image/layer lineage, draft revisions and refusal observations are recorded. It is not an Execution-v2 compatibility claim.

| Case | Observation required |
|---|---|
| normal | One matching actual entry, effect and durable completion; the original Run/Part/operation is completed/settled/succeeded/released with no resource holder |
| consumer_response_loss | Installed CLI stdout is discarded; a new consumer queries the original Run and finds the same completion and one effect |
| cold_after_entry | Entry callback observed, no effect; after cold Host restart the original UNKNOWN/held Run/Part/resources and native immutable facts remain, with no replay |
| cold_drop_completion | Durable completion callback and one effect observed before response loss; cold Host restart does not fabricate release/success or repeat the effect |

The helpers compare the P-bound operation/invocation/selection, native profile/program/session, exact dispatch and parameter bytes, immutable request/completion records, and independent simulator markers. `SEND_ENTERED` is not used as native-entry proof. Normal cases wait for the complete final-state predicate. Cold cases do not require a service-ready Host; unsupported startup refusal is retained alongside UNKNOWN. If the fault precondition is not observed, the case fails.

Every case uses fresh output and owned resources. `--keep-resources` retains them for the duration of the CI job. Mutating Docker targets must all belong to the exact fresh harness resource list. No preserved CP2 resource name, Run, key, DB or volume is accepted as an input.

Raw `private/` includes fixture keys/TLS/passwords. Only an approved private-value-audited evidence projection may be published. A leak or incomplete audit fails the case and emits a redacted refusal receipt. A summary is written only after all selected scenarios and their publication gates succeed. Pure Python tests exercise oracle mutations and boundaries; actual product execution is still required for acceptance.
