# Execution v2 operation admission and Host delivery

This is the operation boundary of the authorized execution-v2 revision. Part admission,
protocol declaration and parameter content do not independently authorize a node effect.
Existing lifecycle, qualification, conditions, mandate, budget, resource, fence, permit,
Host receipt and UNKNOWN rules remain mandatory.

## P-owned selection and admission

A current registered, explicitly negotiated Executor requests a node for a Run/Part
under its mandate and optimistic revisions. The request contains no slot, Intent,
parameter artifact, report digest or caller-authored approval. P finds the current
eligible compiled node, its published workflow-node mapping and the immutable Part
binding. It rechecks the actual instance and reserved slot/pool generation.

P snapshots the pinned domain and materializes the candidate/slot outside the writer.
The report must match both the already approved index and that Part's immutable report;
parameter bytes/reference must match the saved Part parameter for that node. On commit,
P rechecks current definitions, instance, qualification, Executor session/mandate,
Run/Part/frontier and reservation at the same serialized admission boundary. A racing
change blocks new admission; it cannot rewrite a committed operation or its original
selection. The computation ticket is private P state, not a deserializable authority.

The existing admission path receives this checked selection. All non-parameter Intent
fields equal the signed template, including target, program, profile/site/calibration,
resources, timeout and completion/cancel rules. Only the parameter reference varies.
The transaction creates the ordinary operation/permit, acquires the same resources,
records activation ownership, and persists an explicit v2 operation binding. It links
operation ID, mandate, full publication/policy identity, selection/digest and report.
Selection retains Run/Part, actual instance/revision/value digest, candidate/slot,
compiled/workflow node link, parameter/Intent digests and current authority generation.
A different Run's approval cannot be reused even if parameter bytes match.

For process eligibility/completion, P uses a per-Part instantiation of the immutable
v2 template graph with only the verified parameter references substituted. The cell's
published template is not overwritten and no v1 execution plan is installed as a
fallback. Existing frontier logic still requires actual operation evidence; stored
parameter bytes do not mark a node complete. The v2 snapshot must identify the original
plan and this Part-specific view explicitly.

Original-key replay and an already occupied activation recover the same operation,
selection and permit rather than charge/acquire again. Expired or revoked authority
cannot be renewed by replay. A new node always requires a fresh currentness decision.

## Delivery and Host boundary

Work with a v2 operation binding must use the separate `rx.host.execution.v2`
HostExecutionService for Prepare, Authorize, receipt query and reconciliation; no
fallback to v1 is permitted. Existing authenticated base/cell context, Intent,
grant, permit, receipt and evidence facts retain their meanings. V2 Prepare includes
the exact operation-binding artifact and canonical parameter bytes/reference. V2
Authorize pins the same binding digest as the durable prepared operation.

Host authenticates the enrolled P identity and scope, validates the accepted v2
configuration/qualification policy, all operation/Run/Part/node/parameter links,
canonical bytes/schema/size/digest and template invariants, and retains the binding
atomically with its ordinary prepare receipt. Caller-supplied hash equality without
this P/Host authority boundary is not approval. Any unsupported version or missing
binding fails before native work. Host authorization still performs the existing
permit/grant/epoch/expiry/condition checks and journals SendEntered before the native
call. P first-emission checks use the same original binding and current instance;
retries/query retain the original operation and invocation identities.

The P outbox may retain its existing prepare/authorize lifecycle since Work carries
an explicit immutable protocol binding. Every transport decision must branch on that
binding. Bare v1 prepare/authorize cannot execute such Work. Lost/unsupported responses
are unknown outcomes, never fabricated NOT_EXECUTED or successful completion.

## Evidence, completion and recovery

Receipt and evidence must correlate the original operation/invocation/Intent digest;
v2 also retains the operation binding through preparation/authorization/query. The
existing resource-release evidence remains required. Completion uses the per-Part
verified graph and real operation outcomes. Only full required completion can consume
the slot reservation and allow the next Part. UNKNOWN/dispute/partial failure retains
custody and blocks progression.

The approved recovery contract remains: applied/done evidence continues remaining
nodes; proved no effect and safe pre-state can authorize at most one explicit retry
of the same node/Part/slot, linked to the settled original. Neither a new request key,
new Run nor an operator's label resets this state. The original receipt stays queryable
after revision changes; new retry/new-node admission still checks current references.

Required controls include changed non-parameter fields/parameter bytes, wrong Run/Part/
node/instance/slot, stale state after CPU verification, cross-Run approval reuse,
idempotent lost replies, v1-only transport refusal, preserved resources on UNKNOWN,
and no frontier/completion advancement from parameter materialization alone. Protocol
fixtures are not deployed Host effects; frozen-v1 and final M3 evidence stay separate.


## Local membership before native input handoff — revision 2026-10-03.2

[Host input membership](host-input-membership.md) requires Host to regenerate the
selected report from its qualification-linked local domain and compare Prepare bytes
to the locally derived node input before using the existing gate/runner lifecycle.
The common envelope and binding are shared by Python and future external adapters.
