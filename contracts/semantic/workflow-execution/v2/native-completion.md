# Common native entry and finite completion boundary

Revision 2026-10-03.3, authorized through the v1.1 revision procedure. This supplements
host-input-membership.md for every execution-v2 provider. Contract version remains v2.

## Common meaning

Entry confirmation and completion are different facts. Entry confirmation means that
the original, already authorized finite invocation has crossed the profile's defined
native submission boundary. It grants no new authority and asserts neither completion
nor physical motion/success. The profile defines the admissible evidence for that
boundary; the common contract does not prescribe a Python process, marker, PID or pipe.

Host retains the same command gate through final qualification/input/permit/grant/epoch/
expiry checks, the existing durable SEND_ENTERED and permit-consumption transaction,
native submission, and validation of entry evidence. Checking under the gate and issuing
submission later outside it remains prohibited. Entry evidence must bind the original
operation, invocation, concrete Intent, device session and profile. Host retains its
bounded schema/size/digest and exact evidence bytes with the original receipt.

After profile-confirmed entry, Host may return the existing NATIVE_ACCEPTED receipt and
release the command gate while that finite invocation completes. It must retain pending
custody and prohibit replay, resource handover or another overlapping submission.
NATIVE_ACCEPTED is not RESULT_CAPTURED. Fences/revocations close future admission; they do
not certify that an already entered invocation is absent, stopped, or safe to transfer.

Completion collection is passive: it can only observe the existing invocation. It cannot
launch a command, replace inputs, approve another member, or create a new operation.
Captured results pass through the same Host writer, delivery/evidence journal, publication,
query and reconciliation path. A completion must match the saved operation/invocation and
device generation. Publication/ack failure retains the original fact for recovery.

An absent/unmatched entry acknowledgement, failed completion observation, process/transport
custody loss, or deadline expiry cannot prove non-execution or success. Preserve uncertainty
and resources under the existing UNKNOWN/reconciliation rules. A pending invocation with
retained live custody is not relabelled as completed, and an uncertain invocation is not
relabelled as merely pending. Restart does not reconstruct live custody from entry evidence.

## Profile responsibility and compatibility

Every supporting profile defines what evidence confirms its native entry, how it correlates
that evidence with the original invocation, and how passive completion preserves custody.
An external adapter can define its own such evidence without changing this common contract.
Unsupported evidence/profile fails closed. Python's evidence is specified only in
python-execution-profile.md; it is not an additional field in the common input envelope.

Existing synchronous providers may continue to return a captured result through the same
gate. Python fixed-input v1 behavior/bytes are unchanged. The Python execution-v2 adapter
opts into this boundary with a changed release/source identity; old packages are not silently
reinterpreted. Existing receipt states and execution-v2 RPC field numbers remain unchanged.
Update the affected v2 binding identity so mixed implementations fail negotiation.

No new runner, authority writer, execution loop or recovery ledger is introduced. Keep the
100ms execution snapshot boundary, existing freshness/epoch/admission/transport bounds, and
the original approved parameter set. CP1 validates normal S2 execution including its five-second
process. N-Part and injected-loss recovery acceptance remain subsequent checkpoints.
