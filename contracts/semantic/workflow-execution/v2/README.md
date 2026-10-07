# Explicit workflow execution v2 — pre-implementation contract decision

Status: revision authorized by the user on 2026-10-02; decisions below fixed before
implementation. No v2 runtime, compatibility PASS or M3 acceptance is claimed.
This is the original semantic contract for the implementation sequence below.
The [cell model](../../../implementation/laser_cell_model.md) remains the single
domain-model document; this contract contains no laser-specific dispatch branches.

**v2 means the execution contract version.** **v1.1 revision procedure** means
the existing change procedure in the [master plan](../../../42_framework_master_plan.md):
document the revision, impact cases, compatibility/migration and hashes first,
then synchronize P and the generated S SDK. It is not a second name for v2 or a
requirement to label the new execution schema v1.1. Existing frozen v1 bytes and
exact-Intent behavior remain unchanged. This revision adds explicit v2 bindings;
it must not reinterpret a stored v1 record or accept unknown v2 fields as v1.

## 1. Approval representation and bounds

The selected representation is **approval of pinned template/rule/input closure
and an exhaustive report-digest index, with deterministic server recomputation**.
It is not a list of every concrete parameter ArtifactRef and not approval of a
resolver alone. The existing pure `rx.program-input-policy.v1` 64-choice helper
is not the v2 authority mechanism; its limits and v1 meaning are unchanged.

A publication pins the workflow, complete definition closure (including models,
instance configuration, properties, tasks, resolution/constraint rules and
overrides), ordered candidate variants, ordered slot domain, Intent templates,
resolver/compiler/canonicalization implementation identities, report index and
compiled process. A candidate variant pins a part model and complete value-bearing
context. There are no unbounded runtime scalar overrides or arbitrary expressions.
If an actual object has value-bearing overrides different from a candidate,
it requires a new resolve/Preview/publication before use. An object instance ID
is an identity binding, never a back door to change approved model values.

The index has schema `rx.execution-report-index.v2` and `entries`, ordered by
variant index then slot index. Each entry is `[variant_index, slot_index,
report_sha256]`. Indices are nonnegative JSON integers; the digest is 64 lowercase
hex characters. Every pair in the approved Cartesian domain occurs exactly once.
No duplicates, holes, implicit defaults or runtime append are permitted. Entries
refer to the publication's pinned ordered variant/slot tables. Its canonical
bytes are an immutable artifact whose digest is included in the approved policy.
Changing any table, entry, template or input changes the publication identity.

The deterministic v2 execution report commits to the complete pinned input
closure, variant/slot identity, status, values, units/frames, provenance,
constraints and every node's concrete parameter bytes/hash/size and invariant
Intent fields. Report content excludes receipt UUID, creation clock, Run/Part IDs,
runtime object-instance identity and operation IDs. Those are stored in separate
linked records. Runtime object identity/revision and the checked value-bearing
projection are retained in the selection record; their exclusion from reusable
report bytes does not exclude them from authorization or currentness checks.
Generated
parameters refer to deterministic report *inputs* and selection identity, not
to their containing report digest (no circular hash). Existing v1 report and
parameter formats are not silently rewritten. Numeric representation, map
ordering and digest domains must be pinned in P's v2 canonical DTO/binding
manifest, with cross-consumer golden vectors, before P/Executor gate completion.
Floating locale formatting or iteration order cannot enter a digest.

Publication checks every candidate with the pinned resolver and compiler, checks
concrete values and constraints, streams each report into this index, and retains
the immutable input closure and index. A BLOCKED or bounded candidate blocks the
whole publication; no silent dropping of slots. Preview reads/reconstructs these
same committed reports and must match the index. Runtime P rereads the selected
inputs, revalidates types/constraints/currentness, regenerates the report and
compares its digest to the already approved entry. It persists the selected
report and concrete parameters before any operation can be admitted. The digest
comparison is to the prior approval, not a new digest supplied by the caller.

| Boundary | v2 limit / action |
|---|---|
| Candidate variants | 1–8 per publication |
| Ordered slots | 1–2400 per publication; one Run uses the first N jointly unused slots in published order |
| Report pairs | At most 19,200; full Cartesian coverage required |
| Action nodes | At most 16, one bounded Skill per Task in this profile |
| Index canonical artifact | At most 2 MiB, checked before parsing/allocation |
| Deterministic report | At most 900,000 bytes per candidate |
| Concrete node parameter | At most 64 KiB; at most 1 MiB across 16 nodes per candidate |
| Policy envelope | At most 128 KiB; large index/closure are referenced artifacts |
| Definition closure | At most 512 distinct definitions and 16 MiB total canonical bytes |
| Qualification closure | At most 1024 distinct dependency identities, including definition and runtime/package dependencies; existing per-artifact bounds still apply |
| Run / retry | At most 2400 parts; at most one explicitly approved no-effect retry per node per part; no automatic retry |

Limits are enforced at publication and all readers. Exceeding a limit returns a
located error, never truncates data or weakens a check. These are v2 limits, not
global increases to legacy package assets or configuration bounds.

### Dense 2400 cost and qualification consequences

[Reproducible sizing](../../../../references/execution_v2_design_2026-10-02/sizing.json)
uses current A/B M2 reports and v1 compiler payload sizes plus exact serialization
of the proposed index. It is **representation sizing, not a 2400-slot resolution,
latency benchmark or qualification result**. The supplied dense geometry remains
BLOCKED; no fixture numbers were changed to make this estimate executable.

For two variants and eight nodes, literal enumeration requires 38,400 concrete
parameter artifacts (19,200 per variant). A single compact reference array alone
is 5,284,801 bytes, before policy wrappers. Current payload-size extrapolation is
48,499,200 bytes of parameters and 929,577,600 bytes of reports. Slot-digit/pose
changes and the new report format can alter payload sizes; these are not measured
v2 storage totals. A report index is exactly 362,633 bytes at 2 × 2400 and
1,450,373 bytes at the 8 × 2400 maximum with the stated encoding.

This saves stored approval references, **not semantic verification work**:
publication and qualification verification each require 4800 candidate
resolutions/constraint checks and up to 38,400 parameter generations for A/B.
Work is streamed with one report/parameter group in memory. At the maximum,
19,200 reports can represent 17,280,000,000 transient report bytes; bounded memory
does not imply cheap processing. Publication remains non-executable until the
complete job commits; cancellation/incomplete index grants nothing. Runtime
recomputes one selected candidate before new effects, including after a freshness
boundary; no 38,400-way linear search is required. Wall time is unmeasured until
the real v2 implementation exists and must be reported before release.

Qualification's dependency closure contains every pinned definition, template,
rule, compiler/resolver/canonicalizer, program/environment, device/profile/site
configuration, ordered domain and index. Current A/B receipts share 82 distinct
definition digests; these are inspected once per closure, not repeated 4800 times.
The new index is one artifact dependency, but it does not erase its transitive
input dependencies. Generated outputs are a versioned *derived* dependency class:
qualification verifies the complete index by recomputation and records that
verification against this exact configuration and input closure. It does not
rubber-stamp a hash list, inherit qualification from a similarly named model, or
require 38,400 independently reviewed static device inputs. The v2 implementation
must add this explicit dependency meaning; it cannot omit dependencies under an
existing v1 package/schema or raise the legacy 32-asset Python package limit.
Missing dependency, implementation identity or full-domain evidence fails closed.
Existing reviewer/operator separation, permit/fence and resource rules still apply.

## 2. Who selects the slot and actual part

The published order rule selects slots. In this slice it is the data-declared
zero-based row-major order (row then column), with the exact generated order
committed in publication. P reserves the next unused slot and commits its ordinal
with Run/Part binding before dispatch. N selects the first N jointly unused entries in published order, not arbitrary indices.
Executor, UI, barcode input and operator cannot override or skip the slot.
The server owns concurrent reservation/consumption for a tray instance across
Runs; a new Run cannot reset occupancy or reuse a consumed slot by changing its
Run ID. Replenishment needs explicit recorded state change, not a retry flag.

Operator or enrolled simulated barcode/MES input supplies the actual object
instance. P records authenticated actor/source, original request, Run, Part,
ordinal, object reference/revision, candidate variant and reserved slot. It checks
the object's type/model and value-bearing data against an approved candidate.
Missing or ambiguous binding blocks. This is not approval of operator-selected
slots. Arbitrary slot selection is outside this revision; adding it would require
an explicit publication selection rule and separately authorized, recorded choice.

P issues a run-scoped selection record binding publication/policy/index,
configuration, Run, Part, actual object, slot, node, parameter digest, Intent
digest and current authority generation. It is accessed under the existing
authenticated P/Executor/Host boundary; caller-provided equality is not authority.
Host validates exact selected bytes/schema/size and invariant template fields
under that selection. Identical content bytes may be deduplicated across Runs,
but a selection/approval record from Run A can never authorize Run B. Operation
identity, Host preparation, permit and journal retain these selection links.

## 3. Pinned publication versus current references

**Conflict policy: BLOCK new effects.** At Run binding and before each new node
operation/retry admission, P checks that every reference in the publication's
value/authority dependency closure is still current and usable. An updated,
deleted, retired or superseded definition revision blocks even if its numeric
value is equal. Updates to unrelated definitions do not block. Run/Part's actual
object revision is checked too. Warning-only or silently continuing on old
values is not supported. Nor may a new revision be substituted into an old report.
The diagnostic includes definition key/label, pinned revision/digest and current
revision/digest (or missing status), and identifies the affected node/property.

Currentness validation and durable operation admission have one serialized
decision boundary: a racing update either precedes admission and blocks it, or
follows a committed admission and blocks subsequent effects. Already admitted
operations keep their original immutable selection; an update does not rewrite,
reissue or claim cancellation of an operation that may have acted. Existing
permits, expiry, stopping and resource custody still govern that operation.
Original-operation query/reconciliation remains available after a revision change.

Resume requires a new resolve → Preview → publish and qualification of the changed
closure, then a new Run after old obligations are settled. The current Run cannot
be silently migrated. Reopening an old Preview/report stays possible and visibly
identifies its pinned snapshot; viewing is not execution admission.

## 4. Frozen v1 consumers, not rebuilt legacy branches

Counterexample 2 must run the **existing installed v1 P, Executor, Host and built
UI bytes** recorded in [legacy-freeze.json](../../../../references/execution_v2_design_2026-10-02/legacy-freeze.json).
These are the installed Linux v0.4.0-rc.1 images, currently stopped, copied without
rebuilding on 2026-10-02. M2's live macOS authoring API/Vite server is a separate
development surface, not this complete runtime distribution. No running Host or
Executor is claimed. Binary hashes, image content IDs, source provenance and the
complete UI tree digest are frozen before any v2 code change. The image IDs and
retained byte copies, not mutable tags or a fresh build of old source, are the
oracle. If an artifact is unavailable or mismatched, this test is NOT RUN.

In an isolated installation, first execute a valid v1 positive control using those
same consumers. Inject the same pinned v2 plan into each old consumer's real
ingress (P publication/configuration, Executor plan fetch, Host configuration/
Prepare and UI plan read/operate). Use a test transport only to deliver bytes;
it must not parse/reject on behalf of the old consumer. Record returned errors,
network calls, journals and an independent device-effect counter. Include a valid
v2 candidate control on the new P/Executor pair so rejection cannot be attributed
only to broken fixtures. Exercise new-schema, v1-envelope-with-extra-policy and
mixed-version negotiation cases. An old UI must not present/submit a stripped v1
plan as executable. A parser/error/page failure alone is insufficient: establish
no admission/permit/effect, no silent downgrade and no lost unresolved custody.
If the old consumer ignores fields or exposes unsafe execution, fail the gate;
do not patch/rebuild the frozen oracle to manufacture a pass. Installation isolation
or protocol-level enforcement must be reviewed explicitly before moving forward.

## 5. Precommitted counterexamples and release gates

| Case | Required evidence |
|---|---|
| 1 | v1 golden bytes, stored-record reads and existing positive/negative corpus unchanged; exact-Intent matching retained |
| 2 | Frozen deployed v1 P/Executor/Host/UI injection above; explicit incompatible/mixed-version rejection before effects |
| 3 | An approved set member for another part, slot, model or node rejected; wrong type, unit or frame rejected |
| 4 | Non-parameter Intent mutation, absent/tampered bytes, wrong template/rule/index/report/implementation digest, missing/duplicate index entry and over-limit domain rejected |
| 5 | Overrides use the same constraints; invalid force/geometry/unit blocked; bounded non-concrete values never executable |
| 6 | Lost response/restart/query recovers the original Run/Part/slot/selection/operation; no new selection or duplicate effect |
| 7 | Saved Preview, publication, Run and independent native effects agree on pinned definitions/rules/reports/values/order |
| 9 (added a) | Reuse Run A selection/approval/parameter witness in Run B rejected even when publication, slot and content hash coincide; fresh Run B authority is the positive control |
| 10 (added b) | UNKNOWN settlement cannot silently choose retry or next slot; the disposition table below is enforced, including concurrent/repeated settlement |

Former case **8 is an M3 human acceptance item**, separate from the v2 contract
gate: real registered P↔Host response loss → UNKNOWN shown to operator → resource
held → original operation reconciled → next part completes. Simulation integration
tests prepare this acceptance but do not replace it or authorize an M3 PASS.

| Original operation settlement | Permitted same-slot behavior | Next slot |
|---|---|---|
| Unresolved / conflicting / insufficient evidence | Query/reconcile original only; no new operation; resources retained | Blocked |
| Applied and done proven | Resume remaining nodes of the same Part using the original selection; never repeat the applied node | Only after all required nodes/done conditions complete and resource release is evidenced |
| Proven no effect and safe known pre-state | Recovery-authorized explicit retry of this node on the same Part/slot, new operation ID linked to the settled original, unchanged selection, fresh currentness/constraints/permit; maximum one retry | Blocked while Part incomplete |
| Failed/partial effect or actual state incompatible with remaining steps | Stop progression and retain applicable obligations; manual recovery/abort through existing authorized path | No automatic skip; abort ends the Run |

Settlement alone is not evidence of no effect or of successful Part completion.
An operator label without the existing authorized evidence path grants no retry.
Retry after a definition revision change is blocked by section 3. Consumed or
ambiguous slot state cannot be reset by declaring no effect. A second retry is
outside this bounded profile and stops the Run. Restart preserves the retry count,
slot reservation, completion and reconciliation links transactionally.

Implement and integrate in this order: **contract → P and Executor (cases 1–5) →
Host → UI**. Case 2 tests the frozen old Host/UI during the first gate; that does
not authorize implementing the new Host/UI early. P/Executor tests can use protocol
fixtures but cannot claim actual new Host effects. Host then establishes the same
selection/byte checks and cases 6, 9, 10; UI finally consumes the saved API records,
followed by full case 7 and M3 case 8. Required tests for earlier cases are repeated
on the final bundle where cross-component behavior is affected.

Publish **one compatible release bundle** of P, generated SDK, Executor, Host,
compiler/packages, CLI and UI. Intermediate develop PRs are not partial releases
or upgrades to the live M2 installation. The bundle manifest pins all binaries,
bindings, schema/canonicalization versions and UI assets; unsupported mixed
installations refuse new v2 runs. No automatic v1 store migration or main release
is included. Separate new execution records/read-version guards prevent an old
reader from ignoring v2 obligations. v1 unresolved work must be settled under its
original authority before an installation switches; rollback while v2 obligations
exist is refused. Changing any decision here requires a documented revision and
impact cases before the corresponding implementation change.


The [Host qualification acknowledgement contract](host-qualification.md) fixes how
the reviewed derived domain binds to the accepted v2 configuration, while preserving
legacy receipts, explicit activation and new-operation permits.

The [runtime binding and slot custody contract](runtime-binding.md) distinguishes
actual ObjectInstance values, Run-local ordinals, publication slot ordinals and
resource identity across Runs, including explicit quiet replenishment.

The [Executor session and Part admission contract](executor-admission.md) preserves
the existing start/mandate/budget path while explicitly negotiating v2 and atomically
binding current actual objects, reserved slots and approved materialized artifacts.

The [operation admission and delivery contract](operation-admission.md) binds the
selected values to ordinary operation/resource/permit semantics and explicit Host-v2
transport, while keeping the original operation recoverable under UNKNOWN.

The bounded no-effect retry implementation is specified in [retry-admission.md](retry-admission.md).


The [Host-owned input membership contract](host-input-membership.md) specifies
provider-independent checks against the Host's qualification-linked approval material.
The [Python execution profile](python-execution-profile.md) contains only Python
environment/program pins and reuses those common semantics and the existing runner.

## Native entry and completion revision

Revision 2026-10-03.3 separates common entry/completion meaning in native-completion.md
from each provider profile's accepted entry evidence. Python evidence is defined in
python-execution-profile.md. Existing freshness limits and execution-v2 wire states remain.
