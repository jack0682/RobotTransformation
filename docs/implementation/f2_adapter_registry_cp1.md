# F2′ CP1 — external adapter package contract proposal

2026-10-04 · Docs only · **ACCEPTED WITH CONDITIONS on 2026-10-05; NOT IMPLEMENTED**.

The user accepted CP1 with three conditions: prove one Run across two existing Hosts by
product CLI before CP2 authoring, without code changes; express support before unclamp only
through existing observations/guards and robot primitives; and add a separate CP3 kill
after entry but before durable completion that remains UNKNOWN without reissue/advancement.
CP3 must also show Host A does not advance while Host B's clamp is UNKNOWN. If the first
   two prerequisites need changes or new semantics, stop and ask; multi-Host changes cannot
be charged to registry cost. [Current prerequisite finding](f2_cp2_prerequisites.md).

Support scope decision, 2026-10-05: the S2 example may split unload into acquire-support and
withdraw in a separate scenario-authoring commit. Python Host observation code stays unchanged.
For this SIM only, unclamp waits for the same Part's acquire-support to be SETTLED/SUCCEEDED;
there is **no fresh support observation**. This ordering is weaker than a real cell requires
and must be stated in docs/receipts. Registry-declared gripper observation and an unclamp guard
are a parked follow-up. This supersedes sensor/support-observation requirements in the original
CP1 proposal, not the two-Host prerequisite or the CP3 pre-completion negative case.

The purpose is to add the S1 simulated pneumatic chuck through an installed package to
the same released `rx-hostd`, without S1-specific platform or solutions source changes.
The general registry is framework work; its cost is measured separately. CP1 fixes the
design and measurement boundary. It does not establish that registration or recovery works.
That conditional acceptance permits CP2 prerequisite checks, not bypass of a failed prerequisite. Review steps are in
[RUN_CP1.md](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-04-f2-checkpoint1/RUN_CP1.md).

## 1. Existing meaning and ownership remain fixed

This proposal uses the extension point in [common native completion](../../contracts/semantic/workflow-execution/v2/native-completion.md)
and [Host input membership](../../contracts/semantic/workflow-execution/v2/host-input-membership.md).
It does not revise execution-v2, NativeAdapter/AdapterFactory, or
[Python execution profile v2](../../contracts/semantic/workflow-execution/v2/python-execution-profile.md).
The external provider specifies its own process pins and native evidence; it does not
pretend a restarted daemon is the finite Python runner or reinterpret Python return facts.
The existing Python profile continues to run the other S2 finite skills unchanged.

The new package/protocol description below is a **provider-binding proposal**, not an
amendment to a published common contract. Its serialization/schema identifiers must be
pinned with the implementation's package identity before CP2 registration; unsupported
bindings fail closed. No existing manifest/hash is changed by CP1. If implementing this
binding requires changing an existing contract, trait, authority, ledger, state machine,
or increasing seams, stop and request one concrete revision recommendation.

| Owner | Responsibility |
|---|---|
| P | Existing publication, Run/Part/slot, authority, UNKNOWN and reconciliation decisions |
| Host | Verify package/materials and locally approved parameter membership; own gate, process/channel, original operation/invocation, observation validation, completion classification and handover |
| External adapter | Implement declared device commands; report correlated entry, completion and current native facts; never issue approval, settle an operation or release a resource |
| Existing Executor | Follow the published workflow and existing Run path; no adapter-owned workflow loop |

Use the existing `begin_with_context` → `Entered`/`Captured`, passive `completed`/`lookup_with_input`,
and post-commit `acknowledge_completion` methods. Use existing observation, guard,
LocalProtection and handover/shutdown ports. The registry's factory remains release-owned;
site data selects a verified installed identity, never an arbitrary executable path.
Validation and opening are passive; no device effect is permitted during inspect/open.

One generic external-process registration path is allowed. No pneumatic, vendor or Task
variant is allowed in core. Existing builtins retain their configuration and behavior.
Host gate/journal/package interpretation counts as core under [K-a..K-d](../43_core_charter.md),
even if its implementation lives in solutions or a distributed SDK. The P seam budget
remains **18 pairs / 31 references**; changing the allowlist is not a solution.

## 2. Package identity, admission and declared interface

The package uses the existing signed DEVICE_REFERENCE ownership, verification and installation
boundary. Registration records availability; it does not confer qualification or permission.
The installed registry entry pins the verified package and binding to the Host configuration.
The existing software review, configuration and v2 qualification remain prerequisites for I/O.
Host compares each Prepare's exact parameter bytes with its own acknowledged approved domain.
The adapter cannot replace this check with a received digest or an assertion from P.

| Package material | Required meaning |
|---|---|
| Identity | Package name/version plus exact content identity; name/version alone never selects mutable bytes |
| Closure and signature | Canonical manifest and referenced files pinned by schema/size/SHA-256, including command/observation declarations, executable/environment, protocol binding and native outcome mapping; existing trusted signer and verification boundary |
| Execution | Installed program/environment ArtifactRefs, supported OS/architecture and SIMULATION scope; no input-selected command, import, path or interpreter |
| Commands | Unique names, exact template/primitive association and typed parameter contracts, units and bounds; undeclared or ill-typed commands fail before submission |
| Observations | Unique source identities, value types, units where applicable, freshness requirements and device binding; absence is unknown, never synthesized readiness |
| Native evidence | Entry/completion schema and reviewed NativeOutcomeTable association; no package field may authoritatively claim SETTLED, SUCCEEDED, RELEASED or grant authority |
| Lifecycle | Passive lookup, process ownership, protection and handover capabilities; unsupported lifecycle proof is a refusal, not a permissive default |

All dependency bytes in the executable closure must be verified at installation and checked
against the pinned installation before launch. Symlink/path aliases or a matching label
cannot replace exact content identity. Unknown mandatory fields, incompatible protocol,
missing files or conflicting command/source declarations are rejected. Package self-signing
with an untrusted key is not admission. A valid signature does not by itself authorize execution.
Old package bytes remain available while their operations/evidence still reference them.

S1's package data declares `clamp` and `unclamp`; `clamp` consumes the resolved force in N
through the existing typed common envelope and its declared bounds. `unclamp` has no
package-supplied workflow/authority parameter. Both retain the original binding and selected
common input bytes. The observation `chuck.clamped` is boolean, with source/device identity
and freshness; it is not proof of robot support or past command completion. Extra S1 values
must be declared data, not parser branches. Mixed ECC_51/ECC_99/ECC_51 selection stays in
the existing object/resource resolution rules and publication.

| Refusal | Required result |
|---|---|
| Unregistered identity | `rx-hostd inspect` fails, no process/native I/O fallback |
| Unsigned or untrusted candidate | Inspect/admission fails; candidate assembly is not activation |
| Tampered executable, manifest, declaration or dependency | Digest/signature/closure mismatch fails before effects |
| Undeclared command or observation | Dispatch/source validation refuses it; no dynamic discovery that enlarges authority |
| Approved input, operation or device mismatch | Existing Host membership/binding refusal; adapter never receives an executable request |
| Unsupported protocol or entry proof | Closed refusal; no conversion to Python v1 or a direct skill-run path |

These are the requested CP1/CP2 refusal categories, not additional milestone gates.
Exact diagnostic spellings and installed CLI flags are CP2 deliverables; they are not
advertised as commands available in today's binary.

## 3. Host-owned process protocol

Use a private, bounded, versioned request/reply channel created by the Host for its owned
child/process group. No public adapter listener or request-selected endpoint is needed.
Host pins the program/environment and associates the channel with its current child handle
and a fresh session challenge. Saved PID, pathname, marker or old acknowledgement is not
proof of current custody. A replacement channel cannot inherit an old live-process claim.
Inspection and passive startup cannot submit device commands or replay a pending request.

Every operation exchange carries the original operation/invocation, concrete Intent digest,
device generation, package/program/protocol identity and exact request digest. Execute also
carries the common bound input and original expiry from Host's admitted dispatch. Run, Part,
ordinal, object, slot and selection remain the existing execution binding; they are not new
adapter authority fields. The Host compares responses with its saved dispatch, not with a
package-created alternative. Messages have closed schemas and checked lengths before allocation;
parameter and evidence limits reuse the existing contract limits. No deadline, freshness,
ticket or 100ms execution snapshot boundary is extended.

| Logical exchange (not a new P RPC) | Mapping and required behavior |
|---|---|
| Open / identity challenge | Passive process startup, verified pins and fresh channel ownership; no device command |
| Execute / Entry | Existing Host gate through final checks, durable SEND_ENTERED and permit consumption; entry proof returned on the owned channel after durable acceptance of the original finite request and before device effect |
| Completion poll | Nonblocking `completed`; observes only entered requests while ordinary source observation remains available |
| Lookup(original IDs) | `lookup_with_input`; retrieves retained evidence only, never invokes Execute, imports a skill or substitutes another call |
| Capture acknowledged | `acknowledge_completion` only after the same Host writer commits the original capture; failed publication/ack leaves evidence retrievable |
| Observe / current-state query | `observe_sources`/guard; declared typed samples correlated with device and fresh channel; stale/missing/malformed values fail closed |
| Protection / shutdown / handover query | Existing LocalProtection and shutdown/handover ports; no new abort authority or settle RPC |

For this binding, native entry means the verified adapter has durably accepted the exact
finite request on that owned channel. Entry is neither I/O completion nor physical success.
It must satisfy common NativeEntry correlation and retention. Only Execute can initiate the
declared command, and only once for the original identity; duplicate original requests are
looked up, while changed bytes under the same identity are rejected. The adapter cannot run
N parts, choose the next node or resubmit after a communication error.

The Host classifies a native capture with the existing reviewed outcome mapping and writes
the existing receipt/evidence path. A transient adapter/channel loss is not encoded as a
terminal FAILED result and later overwritten with success; use existing UNKNOWN/reconciliation.
The package never writes P/Host authority tables. Killing a process or receiving an abort
acknowledgement cannot prove absence of a prior effect or permit resource release.
Protection must remain independent of the command gate and a successful database transaction.

## 4. Completion evidence and restart: two independent requirements

**An adapter restart alone never clears UNKNOWN. The Host requires both original completion
evidence and current custody evidence.** Completion answers what happened to the original call;
custody answers whether the Host now has sufficient control/support to continue or hand over.
Neither replaces the other, and a currently clamped sensor cannot establish past completion.

The provider's native completion journal is an evidence source within the existing
Host-owned installation/native storage boundary, not a second recovery/authority ledger.
It retains exact original request identity and immutable correlated native completion bytes.
Use the existing native storage/SDK mechanism and Host evidence writer; do not create a
second settle state machine. The package may supply native facts through its assigned interface,
but cannot edit qualification, receipts, ownership or reconciliation records. Evidence must
survive adapter process failure and failed Host acknowledgement. Retention cannot discard an
unacknowledged completion or a record still needed for original-operation lookup.

| Situation | Required behavior |
|---|---|
| Entry accepted, channel lost or adapter hung/killed | UNKNOWN/QUARANTINED; original operation remains holder; no next Part or overlapping command |
| Restarted process, completion record absent/incomplete/mismatched | Remain UNKNOWN; no replay and no fabricated success |
| Original completion exists, current custody missing | Preserve completion fact, keep resources held; do not authorize continuation |
| Current custody exists, original completion missing | Preserve current observation, remain UNKNOWN about the past command |
| Both independently verified | Use original operation/invocation query/reconciliation and existing handover path; no reissue |

CP3 keeps the Host alive. It can use its owned old-child/process-group handle to establish
exit/reaping (or terminate/reap the owned hung group), verify the same package/device/journal
identity, then establish a fresh owned channel to a passive restarted adapter. A stored PID
is insufficient. Current custody evidence additionally covers no residual native work,
current device control and required support/handover facts under the existing profile rules.
Process restart alone is not device reset. Changed device generation or unresolved residual
work refuses settlement/continuation. Cold Host restart and migration are outside this CP.

For the positive CP3 demonstration, select the loss boundary after Part 2 clamp's native
entry and durable SIM completion fact, before Host/P accepts the completion. The adapter is
actually killed or hung; a relay-only fault does not satisfy F2′ CP3. This permits retrieval
of the original fact after restart, with the fresh custody checks above. Record this exact
window in RUN_CP3 and the receipt. A kill before sufficient durable completion evidence can
remain UNKNOWN; arbitrary post-entry crashes are not promised recoverable without reissue.
If this window cannot be exposed using existing native evidence storage, stop and ask rather
than introduce a new ledger or quietly weaken the requested fault.

## 5. Scope decisions for CP2/CP3

| Decision | In scope / parked | Consequence |
|---|---|---|
| Standalone unclamp | **IN** | Separate published node, operation/invocation and effect row; no `unload` → unclamp alias that claims robot unloading |
| Ordering around unclamp | **IN**, scenario package | Split unload into acquire-support → unclamp → withdraw. Unclamp waits for same-Part acquire-support SETTLED/SUCCEEDED through the existing Run path. No fresh support observation; weaker than a real cell |
| Replacement while held | **DENY** | Refuse activation/rebinding/removal/GC of the selected package or executable/dependency/protocol identity while any affected operation is pending, UNKNOWN, quarantined or otherwise held |
| Same-package passive restart | **IN** | Same pinned identity and journal; satisfies §4 only, never bypasses the replacement refusal |
| Hot replacement/migration of held work | **PARKED** | New unselected bytes may be stored as candidates; selection waits for ordinary release and reconfiguration/qualification |

The resulting SIM sequence is pick → load → rotate-align → clamp → close-door → process →
open-door → acquire-support → unclamp → withdraw → place: **11 nodes**, within
the existing 16-node ceiling. N=3 remains ECC_51/ECC_99/ECC_51. Expect 33 node operations,
including six S1 clamp/unclamp effects. This deliberate scenario split is charged to external
authoring cost. It does not revise the accepted historical F1 nine-step receipts.

Use two Host instances of the **same installed rx-hostd binary** if needed: the unchanged
Python builtin for remaining finite S2 skills and the generic registry for S1. Existing
published host/template bindings select the destination; do not add a composite runner.
The old builtin cannot issue hidden clamp/unclamp effects in the split scenario. CP2 must
demonstrate the same-Part settled-operation order and explicitly record the absence of a
fresh support observation. New common semantics or a new seam still require a stop and approval.

## 6. Measurement plan and baseline

[F0 §§1–4](framework_extension_cost.md) recorded an unsuccessful independent adapter probe
plus a Python alternative: **6 files / 63 physical lines / 12 commands**. That total is
3 files/26 lines for the backend probe plus 3/37 for the finite-skill alternative; commands
are 7 product/helper + 3 fixture + 2 mistaken calls. F0 did not prove adapter registration.
Compare like categories, and keep this unsuccessful baseline visible.

| Cost boundary | Measurement | Current value |
|---|---|---|
| B0: before registry | P `4fd1c16631d819b9eb776de92d7fc366af4439f3`; S `45dc6eac4befbffd38615575477152baa5361411` | Source baseline, clean worktrees; seams 18/31 |
| B0 → B1: general registry | P/S changed files and added/deleted LOC by file, including contracts, SDK copies, tests, CLI and Host separately; K-a..K-d classification | Not implemented / not measured |
| B1 freeze | Merged registry heads, installed SDK identity, rx-hostd SHA-256, image ID and OS/arch before S1 authoring | To record in CP2 |
| B1 → B2: S1 extension | All P/S source changes and binary identity comparison during external-only package authoring | Required **0 files / +0 −0 LOC**, same Host binary; not yet measured |
| External original files | Package code, declarations, schema/template data, scenario composition and hand-written helpers: physical UTF-8 lines including blanks | To measure per file; no estimate presented as zero |
| Generated/copied material | Generated manifests/SDK/environment/workflow/receipts and reused baseline data listed separately with sizes | Do not hide hand-written helper cost here |
| Commands and time | Ordered command log with rc, wall time and product/helper/fixture/mistake category, including retries; setup/build separately | CP2 authoring uses installed artifacts/product CLI only; core-source fixture cost must be zero |

Capture `git diff --numstat B0 B1` per repo and a changed-file inventory; identify generated
SDK lines separately rather than subtracting them invisibly. Freeze B1 before S1 authoring.
Use an external directory without P/S source mounts or imports. Record available installed
tools, dependency origins, SDK/package artifacts and invocation log. A missing installed
packaging/signing/commission command is an authoring blocker, not permission to call a Cargo
fixture or source-tree helper. If generic work must resume, end that attempt, account for its
cost, freeze a new B1 and repeat the external-only attempt with prior failure retained.
Record authoring pain for F3′; do not start F3′ tooling.

CP2 reports registration/refusals, mixed-model selected values, the six S1 effect IDs matched
to the Run and `chuck.clamped` reaching Host observation. CP3 reports the two-evidence restart,
same operation/invocation, retained resources/slot, no advancement while UNKNOWN, completion
and no duplicate target effect, and the held-replacement refusal. These are later checkpoint
evidence, not claims established by this document.

## 7. Source basis, validation and checkpoint boundary

The current seams were checked with `tools/check_engine_boundaries.py`: 63 modules, 79 files,
18 pairs/31 references. It is a static boundary check, not type resolution or runtime proof.
Existing implementation anchors at the S baseline:
[NativeAdapter](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/native.rs),
[AdapterFactory](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/service/mod.rs),
[closed backend](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/service/config.rs),
[builtin factory](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/service/factory.rs).
The common/Python documents linked in §1 define the allowed reuse; this design is not runtime proof.

CP1 changes only Docs: provenance corrections, this proposal, its review commands and baseline
receipt, framework status and one parking entry. P/S code, existing normative contracts and
manifests remain unchanged. Documentation/link/hash checks and exact-head CI/DCO are prechecks.
After Docs develop merge, hand back RUN_CP1 and stop for user acceptance. No registry code,
S1 authoring, CP2 run or CP3 fault injection starts before that acceptance.
