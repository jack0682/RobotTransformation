# F2′ CP2 prerequisite finding — support observation is not connected

2026-10-05. **SCOPE DECIDED: PACKAGE SPLIT AND ORDERING ONLY; CP2 NOT DELIVERED**.

The user superseded the support stop below: allow a separately committed S2 example-package
split into `acquire-support` and `withdraw`, charged separately from registry cost. Do not
connect gripper state to `python_skill.rs`/`simulation.rs`. For this SIM scenario, unclamp
follows the same Part's SETTLED/SUCCEEDED acquire-support operation through the existing Run
path. **There is no fresh support observation; ordering alone is weaker than a real cell
requires.** Docs and receipts must state that limitation. A registry-declared gripper
observation and unclamp guard are parked until the registry works. Conditions 1 and 3 remain
unchanged: first prove the code-free two-Host Run before S1 authoring; stop and ask if it fails.
The old observation-path recommendation below is historical and was explicitly NOT approved.

**Two-Host prerequisite passed later on 2026-10-05.** Codex ran the installed product CLI
against a new isolated SIM installation with unchanged F1 P/Host/Executor binaries. One
published nine-step S2 Run completed across Python Host A (8 nodes) and Python Host B (clamp).
The earlier NOT_PERFORMED statements below preserve the original support-stop finding.
[Product receipt, exact commands and limitations](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-two-host/RUN.md).
This is not registry/S1 or CP2 acceptance evidence. S1 authoring may proceed only on the later
frozen registry baseline; the two-Host prerequisite itself required zero runtime source changes.
CP1 was accepted by the user with three conditions. Codex performed the checks below;
there is no claim that the user executed these commands or accepted CP2.

## Accepted conditions

1. Before S1 authoring, use the product CLI to prove one Run across two Host instances
   using existing Executor/P without changes. A necessary change requires a stop and
   permission; it is not registry cost. CP3 must show Host A does not advance while
   Host B's clamp is UNKNOWN.
2. Support before unclamp uses existing observations/guards and existing robot primitives
   only. Insufficient support is a stop, not authorization to introduce new semantics.
3. In addition to the recoverable CP3 window, a separate kill after entry and before durable
   completion must retain UNKNOWN, with no reissue and no Run advancement. It need not finish.

## What was actually checked

The existing detached F1 environment was preserved. An ephemeral container used its mounted
configuration/package/environment read-only, with networking disabled. A Python data-copy
helper invoked the installed product CLI; it was not a replacement implementation of Host.
It added only the existing observation name `gripper.part_held` to a temporary binding's
condition IDs and updated that file's digest in a temporary startup file.
No device effect, service restart, qualification mutation or Run was performed.

| Product CLI input | Result |
|---|---|
| Original Python execution startup, condition IDs `[sim/ready]` | rc=0; inspection reports `native_processes_started=0` |
| Temporary copy with additional `gripper.part_held` condition | rc=1; `Python execution template bindings differ` |

Host binary SHA-256: `f0e2792bf2e3511b93889a0e27f6dfc3d53c2856bbdb308533333c1857fa8993`.
P baseline: `4fd1c16631d819b9eb776de92d7fc366af4439f3`.
S baseline: `45dc6eac4befbffd38615575477152baa5361411`.
[Recorded result](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-prerequisites/support-inspect.json) and
[reproduction helper](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/references/2026-10-05-f2-prerequisites/inspect_support.py).

This check establishes the current Python binding restriction. It does not prove that
every possible external package design is impossible, or that multi-Host dispatch fails.

## Why the current S2 path is insufficient

At the S baseline, [Python binding validation](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/service/python_execution_package.rs#L85)
requires exactly `sim/ready`. [Python source observation](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/python_skill.rs#L333)
delegates to the support adapter, and [FileDevice](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/runtime/rx-host/src/simulation.rs#L112)
accepts only `ready`/`sim/ready`. Its unconditional SIM support observation does not observe
the S2 device state's gripper and cannot stand in for same-Part support before unclamp.

The existing [S2 finite skill](https://github.com/jack0682/rx-solutions/blob/45dc6eac4befbffd38615575477152baa5361411/examples/process/laser-heat-treatment/rotation/skill.py#L158)
establishes holding, unclamps and withdraws inside one `unload` branch. The `pick` branch
requires SUPPLY, while this point in the workflow is OPEN with the part clamped.
The skill's `gripper.part_held` result/effect data is not a fresh Host native source.
The separate material-flow acquire example explicitly describes logical state simulation,
not a device adapter. Reusing its boolean return would not supply the required observation.

Thus the CP1 proposal's support → unclamp → withdrawal split is not an already available
S2 primitive/Host observation path. Renaming unload to acquire, treating `sim/ready` as
gripper support, or moving a fabricated support assertion into S1 would conceal this gap.

## Status and one recommendation

**The two-Host product Run has not been performed.** Source inspection found per-node Host
selection and local Host policy filtering, but those are not runtime evidence. The support
prerequisite was checked during preparation and triggered condition 2's explicit stop.
Do not count the multi-Host prerequisite as passed, failed, or as registry development.
Registry implementation and S1 external authoring remain unstarted. P/S diff is zero.

Recommendation for user approval: permit a separate, bounded support prerequisite before
registry implementation: extract S2's existing unload support/withdrawal behavior into
separately callable package actions, and connect the gripper's actual SIM state to the
existing typed boolean observation/guard path for the Python Host. Account for that work
separately from registry cost; retain the existing authority, UNKNOWN and handover meanings.
This would relax the requirement to use only already callable robot primitives and the
goal's unchanged-builtin boundary, so it is **not authorized or implemented by this record**.
Any common/Python contract or NativeAdapter revision discovered during that design still
requires separate approval. After approval, keep the code-free multi-Host Run check ahead
of any S1 authoring; a failure there must again stop and ask.

The original stop added no parking item. The subsequent scope decision adds one follow-up:
registry-declared gripper support observation and unclamp guard. The accepted CP3 pre-completion
negative case remains required and is not parked. Next: code-free two-Host Run prerequisite.

## Reproduce this limited inspection

With the preserved F1 image and Host container available, from rx_docs:

```sh
docker run --rm -i --network none --volumes-from rx-f1-cp3r3-h:ro \
  --entrypoint python3 rx-f1-solutions:cp3-merged - \
  < references/2026-10-05-f2-prerequisites/inspect_support.py
```

Expected results are the two return codes above. Temporary files live only in the disposable
container. This is an inspection reproduction, not a completed CP2 Run acceptance command.
