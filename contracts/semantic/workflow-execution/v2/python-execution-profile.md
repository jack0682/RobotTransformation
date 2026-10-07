# Python execution profile v2

Revision 2026-10-03.2. This explicitly opts a signed Python package into the existing
execution-v2 contract. It does not change the fixed-input meaning of Python registration
or library v1. Approval membership, input envelopes, binding and recovery semantics are
specified only by host-input-membership.md and the common execution-v2 contracts.

## Python-specific declaration

The closed profile schema is `rx.python-execution-profile.v2`. It contains only:

- `schema`;
- the prepared absolute Python environment path and its exact environment digest;
- the exact `rx.python-environment.v1` program ArtifactRef consumed by the existing runner.

The program artifact must identify the actual canonical environment manifest bytes and
its embedded environment identity/path. Interpreter, runner and verifier remain pinned by
the Host release using the existing Python release mechanism. Runtime parameters cannot
choose paths, interpreters, modules or executables. Existing environment validation and
size limits remain, and loading/inspection does not import or execute the skill.

Scope, SIMULATION, templates, NodeContracts, parameter contracts, input membership and
operation bindings are not duplicated inside this Python profile. They come from the signed
common execution-template catalog and Host's accepted common configuration/qualification.
The package retains family/profile/adapter source documents with the existing signed
DEVICE_REFERENCE ownership/verification boundary; the explicit adapter/assembly identity
must distinguish this profile from fixed-input Python v1. Every local template's program
pin must match the Python environment program pin. Original/profile disagreement fails
verification even under a valid signature.

## Existing runner integration

After the common Host membership check, the existing Python runner receives the exact
verified common envelope as its `main(inputs)` argument. The signed scenario package
interprets its declared primitive and values. It must not contain an N-Part workflow
or bypass Host admission. Existing environment verification, original invocation facts,
unknown-process handling, receipt query and resource custody remain in use.

A passive operation-bound Program can reuse the existing executable/environment/runner
machinery. It must preserve the Host's immutable operation binding rather than overwrite
a global fixed input or treat identical parameter bytes as another Run's authority.

This profile is SIMULATION-only in checkpoint 1. It does not implement an external adapter
registry, a new Task type system, physical device support or cold Host recovery. A future
external adapter uses the common envelope/membership/binding contract and supplies its own
provider-specific pins; it does not inherit Python fields or revise common approval meaning.

## Compatibility

Existing Python v1 packages, fixed inputs and historical records retain exact matching.
They cannot implicitly opt into this profile. Unsupported profile/adapter identity is a
closed refusal; there is no fallback that strips v2 fields into a v1 invocation. The existing
package ABI and execution-v2 wire services are retained; binding identities track the
common semantic revision before coordinated deployment.

## Python-specific native entry evidence

Revision 2026-10-03.3 uses the common native-completion.md meaning. Python defines entry
as the pinned runner's acceptance of this finite invocation after verifying the pinned
environment, interpreter and skill source, checking the dispatch deadline, and durably
recording the original request before any skill import or main call.

The existing runner's explicit execution-v2 entry mode sends a bounded
rx.python-native-entry.v2 acknowledgement on the private, freshly owned process channel.
It identifies operation, invocation, Intent digest, environment digest and device session,
and hashes the exact request bytes received on that channel. Host must compare all fields
with its dispatched request while retaining the gate. The runner syncs the request and
entry record before sending this acknowledgement; then it continues that same invocation.
This is Python submission acceptance, not a claim of physical device entry or completion.

Only the acknowledgement from the currently owned, release-pinned runner is entry evidence.
Spawn success, PID existence, a directory/marker, or a stored acknowledgement by itself is
insufficient. Reopening these files never restores live process custody. An existing
request is looked up without re-importing or re-executing the skill.

The Host retains the owned process group and original request until its bounded reply,
process exit and group reaping are established. Completion waiting must not hold the Host
command gate or prevent ordinary source observations. Passive collection writes the same
correlated native capture and Host evidence as the existing Python runner. Failure or
residual process-group custody retains UNKNOWN/held resources; it does not permit replay.
The existing synchronous execute/lookup behavior remains for Python v1. All interpreter,
runner and verifier files remain pinned by the release; no request selects another program.
