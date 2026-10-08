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

The BOOLEAN sources `vision.result_available` and `vision.groove_detected` expose
the current file-device groove result through the same observation plane. Before
A2 both are false. A completed simulated detection has available=true and
detected=true; a completed simulated miss has available=true and detected=false.
Detected=false alone does not establish a completed miss. Read availability and
detection together with the original A2 operation outcome and material identity;
these observations do not settle an operation or replace its completion evidence.

## Native passive observer candidate

`observer.cpp` is a package-owned alternative to starting Python for each passive
observation. It reads the same initialized file-device state and returns the
existing `rx.external-native-snapshot.v1` message. It does not change Host/P code,
observation bounds, the fixed admission snapshot deadline, native outcome mapping,
or qualification. Earlier freshness failures remain failures of their original
candidates; this changed provider needs its own measured Linux verification.

Build on isolated Linux with nlohmann-json3-dev and libssl-dev available:

```sh
g++ -std=c++17 -O2 -Wall -Wextra -Werror observer.cpp -o m1-observer -lcrypto
```

The runtime needs the matching libcrypto shared library. Declare the observer as
the external Program executable and retain the exact Python executable, adapter,
SDK and configuration as pinned dependencies. Immutable Program arguments are:

```text
--python /opt/rx/python/python --adapter /config/host/adapter.py --config /config/host/m1-provider.json --sdk /config/host/rx_external_adapter.py
```

Host appends `observe|execute|lookup` and its native storage directory. In observe
mode, the program validates the exact request shape, original challenge/session,
kernel boot clock, configuration digest, and requested source names. Files are
bounded, owned and regular; symlink path components are refused. Samples carry the
actual file-read CLOCK_BOOTTIME timestamp. The native `owner.lock` inspection is
the same passive custody check used by the SDK. There is no cached observation,
retimestamped camera data, state rewrite, provider command or generated completion.

For execute and lookup, the program does not read stdin. It uses `execv` to replace
itself with the same pinned Python adapter using `-I -S -B`, preserving the original
PID, process group, channel bytes and file descriptors. The SDK retains entry,
completion, lookup and no-replay behavior; the observer does not interpret these
requests. Initialization still uses the explicit Python `--initialize` command.

From `rx-solutions/`, run the Linux-only process-equivalence checks:

```sh
RX_M1_OBSERVER_BINARY=/absolute/m1-observer \
RX_M1_OBSERVER_DIAGNOSTICS=/absolute/new-observer-latency.json \
python3 -B tools/test_material_alignment_observer.py
```

Without `RX_M1_OBSERVER_BINARY`, the tests compile the candidate using the command
above in a temporary Linux directory. The diagnostic output path must be new and
its parent must already exist. Tests compare actual Python SDK and C++ snapshots
over initialized state, all six commands, completed miss, pending writes and live
native ownership. They also check exact exec delegation, original passive lookup,
malformed-input refusal and unchanged device/native files. Five process-latency
samples for each implementation are recorded without a timing pass threshold or
selecting successful retries. These timings are diagnostics; actual Host admission
and the UI/runtime roundtrip remain separate acceptance evidence.

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

Python and native passive observers hold a shared `state.lock` while reading the
device snapshot. Execute holds the exclusive lock across pending-marker, effect
journal and final-state persistence, so an in-flight write-ahead marker cannot be
published as a stable not-ready observation. The native timestamp is taken after
the lock is acquired and the state bytes are read. A crashed writer releases its
kernel lock; its persisted pending marker still produces ready=false and
no_pending_commands=false. A hung writer can still cause the unchanged Host
deadline to expire. This synchronization changes neither readiness meaning nor
the existing admission/observation timing limits.

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
