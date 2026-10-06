# Execution v2: one explicit no-effect retry

This fixes the implementation boundary of the already approved same-Part/slot
retry rule. It does not introduce automatic retry, a new physical authority role,
rework, cold Host recovery, or a new Run budget. The contract version remains v2;
the change uses the existing v1.1 revision procedure.

## Evidence and current pre-state

The original Work must be v2, finite, settled `NOT_EXECUTED`, and integrity-valid.
Its immutable evidence must include the original enrolled Host's durable
`VOIDED_BEFORE_SEND` receipt, correlated to operation, Intent digest, invocation,
Host boot and delivery journal. A timeout, missing receipt, operator description,
`NATIVE_REJECTED`, failed/partial native result, idle state, or locally inferred
`NOT_EXECUTED` is insufficient. An invocation must be known; absence is not filled
in. Any stored receipt/evidence of native send/acceptance or conflicting invocation
blocks this proof even if a later receipt says voided. Query/reconcile the original
operation until sufficient, non-conflicting evidence exists.

Current pre-state means the reviewed StepBinding's declared conditions evaluate
true with their normal typed, fresh, registered-source evidence, and the assigned
Host freshly confirms all three existing handover predicates: no residual native
work, control custody, and support custody. A retryable package must declare the
preconditions needed by that step; an empty precondition set is unsupported for
retry. A generic `ready` label cannot substitute for missing package/device state
requirements. This is an operating-profile claim, not functional-safety assurance.
P evaluates the configured conditions; neither an operator nor the Executor may
submit their own PASS or choose a weaker predicate set.

For this slice the Host boot, journal, current enrollment/session and resource
fences must remain those of the original admission. The fresh handover observations
must match the original operation/invocation/profile and each other on device
session, and match the current Host boot. They use the existing three handover
source paths and schema. Host authenticates/reads that current device session;
P does not fabricate native evidence to fill the gap left by an unsent operation.
All three observations must be captured after the retry approval and remain within
the step's existing age/uncertainty limit. Conflicting observation identities fail.
Host restart or a cell requiring unrelated recovery is
not resolved by this path; retain custody and use the existing recovery boundary.
If the device profile cannot establish the registered current device identity and
required pre-state, the Host must refuse proof. This cannot be inferred from
three self-consistent observation IDs alone.

## Explicit approval, proof, and consumption

1. A current ReleaseManager with an authorized operator terminal explicitly requests
   one retry, naming the original operation and expected operation/Cell revisions,
   with a recorded justification. P requires the original no-effect receipt above,
   the current qualified v2 configuration, current actual object/definitions and
   pool ownership, an Executing Run with an incomplete Part, and no prior committed
   retry for that activation. Normal current Step conditions must hold. Approval
   records actor/session/terminal, runtime boot, configuration, cell epoch/scopes,
   original operation/revision/selection, Host identity and resource fences. Its
   30-second expiry bounds approval, not the original receipt's historical validity.
2. The currently enrolled assigned Host supplies the fresh handover observations.
   P revalidates the approval actor, deadline, revisions, configuration, current
   instance, Step conditions, Host/fences, and original receipt. In one transaction
   it releases only the original Work's operation resources and marks the retry
   authorization ready. It does not consume/replenish the slot, complete the Part,
   change its object or parameter artifacts, or emit a new effect. The original
   operation remains settled `NOT_EXECUTED`, now with release evidence. Repeated or
   lost replies recover the same proof/authorization; they never clear another owner.
3. The negotiated Executor explicitly names that retry authorization when requesting
   the same compiled node on the same Run/Part. P uses the ordinary private
   computation/currentness/admission path, compares the saved Part and approved index,
   and rechecks the ready authorization and its still-current actor/deadline/facts.
   The transaction creates one new operation/permit, atomically consumes the retry
   authorization, acquires resources normally, and links new and original operation
   IDs. It keeps the original actual object, slot, candidate, report, parameters and
   Intent; a fresh permit carries current authority. Part budget is not consumed again.

The Executor cannot name another Run, Part, node, original operation or selection.
An ordinary SubmitNode without a retry authorization recovers the original occupied
operation. The original request key always returns its original operation, including
after retry approval. The retry key recovers only the new linked operation. A changed
key cannot mint a second attempt; at most one retry operation is committed per
activation. An expired unused approval may be superseded only by a new explicit
human approval, preserving its history and without resetting a consumed retry count.

## Frontier, restart and failure

The persistent activation record retains both operation identities through a retry
link. A ready proof may make this one node eligible for explicit retry; it never
marks the node successful. The frontier may exclude the original `NOT_EXECUTED`
operation only after checking that immutable retry link/proof and the original
settled, integrity-valid, released state. Once admitted, the new linked operation is
the sole current operation for that node. Unlinked duplicate operations are integrity
errors, not ignored history. Successful original work can never enter this path.

Full completion still requires the new operation's actual success/release and every
remaining required node. UNKNOWN/conflict/partial failure in either attempt blocks
progression and keeps applicable resource and slot custody. A second retry is refused;
there is no automatic next-slot fallback. Restart preserves the original/retry link,
consumption and histories. A new runtime boot invalidates unused approval but does
not erase it or replay a committed effect. Revision drift blocks a fresh retry while
historical receipt/query and original-key recovery remain available.

Required controls: no receipt; timeout-only and operator-only claims; missing/false/
stale preconditions or handover facts; wrong Host/boot/journal/device session; wrong
Run/Part/node; revised actual object or definitions; approval expiry/revocation;
rollback and committed-lost-reply at proof and operation admission; concurrent/double
approval/submit; restart; original-success refusal; second retry refusal; UNKNOWN
custody; and successful retry followed by remaining same-Part nodes before next slot.
P protocol fixtures are prechecks. Native Host proof and case 10 follow the first
P/Executor gate; they do not authorize implementing the new Host/UI before it.
