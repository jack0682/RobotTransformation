# Material alignment and regrasp · FILE_SIMULATION

This package supplies the six finite commands in `scenario.json` to the existing
external-process Host provider. It models a held new material, support transfer to
a rotating shelf, D405 groove detection, shelf rotation, alignment/stop check,
fixed-orientation regrasp and FT seating. Each invocation performs only one command.
The existing P/Executor owns ordering, publication, authority and recovery.

All values in the example are declared simulation inputs. This is not camera, force
sensor, robot kinematic, collision, contact-mechanics or functional-safety evidence.
A3 changes the shelf angle; the robot orientation remains fixed. The second gripper
channel is represented and never changed. A6 ends shelf occupancy only after the
same object's selected channel passes the declared FT simulation limits.

## Installation and authoring

Copy `config.example.json` to an installation-owned path, set the absolute owned
device directory and selected equipment identities, and create that directory.
Before Host startup, initialize this fresh scene explicitly on isolated Linux:

```sh
python3 adapter.py --config /config/host/m1-provider.json --initialize
```

Initialization refuses an existing state, effect journal or lock; it is not a reset.
The start condition models one material already held in the configured new-material
channel. The first authorized A1 binds the scene to the Host's immutable actual
object, Run, Part, candidate, slot and approval selection. Every later invocation
must retain those identities and the same reviewed parameters. A completed or
failed scene cannot start another material. Use separate installations/scenes for
independent acceptance cases; initial material replenishment is outside this Task.

Export the installed `rx_external_adapter.py` SDK and use the existing package CLI
`external-program`, `external-assemble`, request/seal and `external-register` path.
Pin the real Linux executable, `adapter.py`, SDK and configuration bytes as program
dependencies. Immutable program arguments are:

```text
-I -S -B /config/host/adapter.py --config /config/host/m1-provider.json --sdk /config/host/rx_external_adapter.py
```

Host appends its `execute`, `lookup` or `observe` mode and native storage path.
Do not invoke these modes manually to operate a qualified cell. Inspect/loading
does not initialize the simulation, import an SDK or issue a command.

`scenario.json` is authoring metadata, not a new runtime wire contract. Its steps
name primitive/node IDs, labels and boolean done observations. All six nodes use
the same 14 declared parameters. Strip each parameter's `default` when constructing
the existing NodeContract; retain unit, value_type and frame. Convert defaults to
ordinary concrete Workflow quantities and use existing definition references and
provenance. Fixed orientation is an unframed unitless quaternion for this simplified
simulation; it makes no claim about an installed coordinate system.
The fixed regrasp location is the selected shelf's symbolic location plus that
orientation. There are no inferred physical Cartesian positions or trajectories.

Use `implementation=rx.simulation.material-alignment`, `version=1.0.0` and
`completion_rule=m1/alignment-result`. The existing signed NativeOutcomeTable maps
status 0 to SUCCEEDED, and 10/11/12 to FAILED. These mean groove not detected,
alignment not confirmed, and FT seating not confirmed, respectively. Exceptions,
missing completion, process loss or unsupported states do not acquire a terminal
failure code and remain subject to existing UNKNOWN handling.

Declare `sim/ready` as the BOOLEAN `boolean/v1` unitless source with 1 s maximum
age and zero uncertainty, and map the installation condition to that source.
The existing delivery fixture's fact ID `ready` is also supported as a passive alias
of the same current state read; declare it separately if that fixture requests it.
Optional current file-device sources are `shelf.occupied`, `shelf.stopped`,
`gripper.part_held`, and `ft.part_seated`, with the same type/schema/unit. These are
passive current state reads; they are not fresh physical sensor readings.

## Evidence and negative cases

`state.json` and append-only `effects.jsonl` are provider-owned device records,
separate from P/Host and the SDK's native request/completion files. Every accepted
finite command records full original selection, operation/invocation, parameters,
observations, result code and chained before/after state digests. A2 failure records
the missing groove, keeps shelf occupancy, and prevents later commands. Logs include
observation commands, so six records mean six finite calls, not six physical motions.

Before recording an effect, the provider durably marks the scene pending. A crash
during state/journal persistence leaves pending state and conservative custody;
there is no automatic replay, cleanup, reset or local settlement. Stable support
does not mean an empty shelf. Failure evidence retains its actual support/occupancy.

For post-entry completion transmission loss, use the existing isolated result-link
fixture around the real Host transport. It withholds the original completion; do
not add fake success/unknown values, deadline extensions, or P journal mutations.

The focused provider tests are intended for isolated Linux only:

```sh
python3 -B tools/test_material_alignment.py
```

They check six-step behavior, typed/equipment/identity/order refusal, known misses,
FT failure, passive observations, pending-state preservation and independent
correlation. They do not establish signed package admission, registered transport,
Run custody, browser roundtrip, or owner acceptance; those require the integrated
M1 scene on the exact candidate.
