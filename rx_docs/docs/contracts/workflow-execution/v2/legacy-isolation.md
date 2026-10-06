# Frozen-v1 failure and approved installation isolation

Revision: 2026-10-03.1, explicitly approved by the user after the frozen-UI failure.
This completes the existing case 2 isolation decision; it adds no new gate case.

## Observed failure and evidence boundary

Unmodified installed v0.4.0-rc.1 P/Executor/Host/UI passed the valid-v1 control. A
transport fixture replaced only the overview/start-context recipe ArtifactRef and
matching displayed Run recipe digest with the pinned, positive-control Plan2
reference. It did not change P's stored configuration, Run authority, Start request
or device outcomes. The UI displayed the v2 digest as the reviewed workflow and
submitted the legacy Start request, which has no recipe digest. The existing v1
workflow completed and the independent simulated-device counter increased by two.

This is a controlled misleading-read/mixed-version test, not proof that an honest
v2 P serves such a context, accepts a v2 configuration as v1, or ran v2 parameters.
The frozen UI does not satisfy the required unsupported-plan refusal. Preserve this
FAIL and the original frozen bytes; never relabel the old consumer as conformant.

## Approved enforcement

- A v2-capable P serves only a digest-pinned `rx.operator-ui-bundle.v2` manifest.
  The file inventory format and `api_schema: rx.operator-api.v1` stay unchanged.
  A v1 manifest fails configured startup even with its correct original digest.
  API-only startup remains available; omission does not authorize an old UI.
- Bundle v2 identifies the reviewed UI build with explicit unsupported-execution
  refusal. Its current legacy Start reader accepts only `rx.resolved-process.v1`
  and a closed StartContext envelope; v2 or extra policy cannot be stripped into
  a legacy Start. This adds no v2 operating UI. A manifest declaration alone is
  not behavior evidence: replay the same injection against the built new bundle.
- P independently rejects legacy create/start/read/dispatch against a configured
  v2 workflow. Do not rely on client checks or translate v2 to v1. P's separate
  execution-v2 services and exact negotiated bindings remain mandatory.
- Frozen v1 P/Executor/Host negative probes and mixed service/binding refusals
  remain required. Record each surface actually exercised. A new-version test
  does not retroactively establish frozen-v1 behavior.

## Compatibility and deployment

Ship compatible P/S/UI as one pinned combination. New P with an old UI bundle and
old P with a new bundle fail schema validation; neither automatically downgrades.
Previously installed v1 combinations keep their own bytes and stored semantics.
Trusted installer pins, local read-only bundle storage and authenticated direct
terminal HTTPS remain assumptions. No protection against an attacker rewriting
the trusted installer or server is claimed. New P refusing legacy commands is
required even if a cached/external old browser attempts them.

The first gate can pass only with the frozen failure reported and these approved
isolation checks passing. M3b/M3c operation and installer delivery are transferred
to the subsequent framework work, not accepted by this gate.
