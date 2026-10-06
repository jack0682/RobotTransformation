# Execution v2: Host-owned approval membership and bound inputs

Revision 2026-10-03.2, authorized after F0. These semantics are common to every
execution-v2 native provider. Python and future external adapters consume the same
approved envelope and binding without redefining approval or adding execution paths.
This supplements host-qualification.md and operation-admission.md under the existing
v1.1 revision procedure. Execution remains contract version v2.

## Approval material and ownership

The approved set remains the pinned Policy, exhaustive ReportIndex and InputClosure
from the original v2 contract. Do not replace it with an unbounded scalar range, a
caller-selected hash, or a pre-enumeration of every concrete parameter artifact.

Before acknowledging qualification, Host must possess and validate the complete
canonical index and input closure against the policy references, and the local signed
template packages against the configuration. Material acquisition is not approval.
Use the existing trusted installation/material ownership boundary to supply immutable
artifacts before configuration/qualification; no request-selected executable or arbitrary
filesystem lookup is allowed. A generic owned material directory may contain bounded
chunks for large artifacts; assembled bytes must satisfy the existing artifact's full
schema/size/digest and v2 limits. A transport or local file name is never the identity.
No new RPC is required for this installation-backed acquisition.

Host verifies canonical bytes, complete Cartesian coverage, pinned resolver/compiler
identities and deterministic report regeneration for every candidate/slot. Verification
may be prepared outside the journal transaction, but committing acceptance must recheck
its original Host incarnation, configuration, package/verification identities and policy.
Incomplete/failed material verification cannot produce an accepted domain. Existing
freshness, epoch, qualification and admission limits must not be extended by this work.

Host's existing durable store retains the material and verification identity. The v2
qualification acknowledgement atomically associates that locally verified domain with
the exact configuration receipt, publication, policy, qualification ID/revision and
acceptance sequence. Reopening an acknowledgement without its matching material is not
sufficient to accept new Prepare calls. Original-operation records remain queryable;
missing current approval cannot create new rights. Old readers must refuse stores whose
v2 obligations they cannot interpret, through the existing reader/installation guard.

## Prepare checks against the Host's own approved set

Prepare is admitted only through the already defined HostExecutionService and the
authenticated, enrolled P/cell boundary. After ordinary shape/scope validation, Host:

1. Loads its durable accepted qualification and corresponding configured policy/domain.
   It does not obtain approval by copying the incoming operation binding or trusting P's
   assertion that its supplied parameter hash is acceptable.
2. Matches publication/policy/configuration and local template identity to that record.
   Validates operation, mandate, Run, Part, ordinal, actual-object identity, slot and node
   correlations already required by execution-v2. P remains owner of current actual-object
   and Run admission decisions; that does not replace Host's parameter membership check.
3. Uses the received candidate/slot only as coordinates into the locally approved domain.
   Recomputes that report from the Host's saved input closure and signed templates and
   compares its digest to the Host's saved ReportIndex entry. Missing coordinates, a
   different report or a node not local to this Host fail closed.
4. Extracts that node's canonical parameter bytes from the recomputation. Requires exact
   byte equality with Prepare's bytes and equality of schema/size/digest and report/selection
   links. Checks the concrete Intent against the approved template with only the already
   authorized parameter reference substituted. Matching two caller-supplied hashes is not
   a substitute for this comparison.
5. Atomically retains the immutable execution binding and verified input with the existing
   operation preparation receipt. No native command occurs during verification/preparation.

An original-key replay returns the original prepared identity; a changed binding or bytes
cannot replace it. Authorize requires that same saved binding and uses the existing
permit/grant/epoch/expiry/conditions checks and SendEntered boundary. A legacy Prepare or
Authorize cannot consume a v2 operation. Unsupported provider/version fails before effects.

## One common envelope, one existing execution lifecycle

`rx.workflow-parameters.v2` is the common canonical input envelope. Its inputs reference,
templates digest, candidate/slot/node/task/primitive, typed values with units/frames, done,
failure and UNKNOWN declarations keep their existing materializer meaning. They are not
Python profile fields. `rx.execution-operation.v2` and its selection keep their current
operation/Run/Part/publication/parameter/authority meaning across all adapters.

A native provider receives only the verified, operation-bound input from the existing Host
gate. Provider preparation/binding is passive. It may decode its declared primitive/value
contract, but cannot enlarge the approved set, grant authority, replace the original
operation, reinterpret UNKNOWN or launch a workflow loop. The native provider's input
handoff is common; a future external adapter reuses it with no change to these semantics.

Use the existing Host journal/receipt/evidence/query/reconcile/handover lifecycle. Do not
create a second approval writer, native execution engine or independent recovery ledger.
Return facts correlated to the original invocation; a Python return or simulated device
record is not physical completion. CLI acceptance receipts and status views must explicitly
identify the S2 nine-step published workflow and SIMULATION target from saved authority data.

## Compatibility and existing checks

V1 fixed inputs/Intent matching, bytes and identities remain unchanged. Template substitution
requires explicit execution-v2 profile, configuration and qualification acceptance. Bump the
affected v2 binding/source identities to require a compatible P/SDK/Executor/Host combination;
do not silently accept an older v2 peer whose acknowledgement lacks Host-owned membership.
No global package ABI change, new RPC, registry or higher limits is introduced here.

Retain the already approved controls: tampered bytes/non-parameter fields; wrong Run/Part/
slot/node; foreign approval reuse; unavailable or mismatched locally accepted domain;
original-request replay/lost response; retained UNKNOWN custody; and no effects before
permission. Host membership checks must exercise the Host's own saved approval material,
not use an assertion from a P fixture as the expected answer. These are applications of
existing approval/compatibility obligations, not additional milestone gates.

The authorized native-completion.md revision defines common entry/completion separation.
Profile-specific entry evidence does not replace any Host-owned input membership check.
