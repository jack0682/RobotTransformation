# Non-actuating settlement — candidate extension v1

Status: candidate revision 1. Not a published normative document, not part of the
`contracts/v1.0` or `cell_operations/v1.0` manifests, and not a physical qualification. It
changes no base or cell protobuf, wire or manifest hash; it describes an operator API and a
Host application path of the platform. Ported from the research framework-validation work
(retained-Host scope only); the implementation lives in rx-platform
(`docs/recovery-settlement-proposal.md`, `crates/rx-application/src/engine/settlement.rs`).

`POST /api/v1/recovery-settlements` accepts an idempotent request key and operation, expected
operation/cell revisions and a justification. It requires a current terminal-authenticated
ReleaseManager. The request carries no observations or execution permission.

The first supported scope is a successful, settled, valid finite operation whose run is
RecoveryRequired, whose resource disposition is Quarantined, and whose original Host
boot/journal and configuration are retained. Only authority-loss/runtime-restart restrictions
are eligible; other restrictions remain outside this path. The old mandate must be inactive and
the original permit consumed. A delivered, current, matching Host fence acknowledgment is
required.

The authorization binds the current runtime, cell epoch/scopes/configuration, operation
revision/intent, Host session/boot/journal and exact resource fences. It expires after
30 seconds and is superseded by a newer authorization for the operation. The approver's current
role/session/terminal is rechecked at application.

P's existing pinned Host communication obtains fresh correlated no-pending/control/support
observations. A current authenticated Host may apply this authorization only when every bound
context and resource holder/fence still matches. The ordinary release path retains its
readiness and original-permit continuity checks; it is not loosened by this extension.

Resource/work settlement and eligible part/run completion occur in one transaction. Revoked
mandates remain revoked. Cell qualification, restrictions and native actuation permissions are
not restored or cleared. An applied authorization is read-only on retry. Partial
multi-operation progress does not imply whole-job completion.

UNKNOWN, missing lookup, changed native lineage, a changed Host boot, arbitrary outcome
correction, and next-production authorization are not supported by this first settlement
scope. These remain obligations of the wider final goal, not implied successes. Settlement of
work on a Host that restarted (known result on a replaced boot) is a separate, later scope
(rx_docs `implementation/host_readmission_delta.md`, "settlement v2").
