# Execution v2 actual objects and slot custody

This fixes the runtime binding details of the already authorized execution-v2
contract. It is not an execution result or a new permission to bypass existing
Run, resource, recovery or qualification checks.

## Actual object identity and values

The generic definition model adds `OBJECT_INSTANCE`, with an immutable versioned
reference, one `base` ObjectModel reference and instance `values`. A type is not a
model and a model is not an actual instance. Instances cannot inherit from another
instance or a resource. Normal field/type/unit/required-value checks apply and
resolved values retain the actual declaring reference. Known v1 definition kinds
keep their meanings; old consumers must reject the unknown kind. Persisting this
kind opts the store into reader barrier10, even before a v2 Preview exists.

The operator supplies an actual instance reference at runtime, not an arbitrary
parameter artifact or slot. Ordinary definition authoring remains under its
existing catalog permissions. An instance may be authored as data before the Run;
operator binding does not confer general catalog write permission. No unrestricted
instance override is introduced at the execution boundary.

P loads the instance and its complete current ancestry. Its direct ObjectModel
reference must select exactly one approved candidate and satisfy the workflow's
object type contract. Missing or ambiguous candidates are refused. P compares the
complete effective value-bearing projection (field/property contract and values)
to the approved model. A different value, including a limit or an unused declared
field, needs a new approved variant/publication. Equal-value instance overrides
may retain their own provenance; they do not expand the approved value domain.
Label and instance identity are recorded separately from that semantic projection.

Run/Part binding records authenticated actor/source and original request, instance
reference/revision, model, checked value digest and reservation. A new instance
revision blocks new work even when its numeric values match. The actual-instance
identity and provenance stay in binding/selection records; reusable report/parameter
bytes still use the approved candidate's semantic inputs. Equality of values does
not erase the instance from authorization. A reference to an ObjectModel alone is
not accepted as a runtime instance.

Instance custody is keyed by installation plus catalog/definition identity, not
revision, policy or Run ID. One instance cannot be allocated to another Run/Part
by revising it or copying another Run's approval. Explicit same-Part recovery can
retain its original instance. Rework/object-identity reassignment is outside this
slice; replenishing a slot pool does not reset object custody.

## Deriving resource slot pools

P derives slot resources from `Source::Pattern` declarations in active workflow
Task properties, using the saved input closure, never hardcoded context names such
as supply/output. It deduplicates position/orientation/frame references to the
same resource/pattern. Every candidate must bind each such context to the same
single ResourceInstance and pattern revision. Multiple/ambiguous subjects, models
used instead of actual resource instances, or competing patterns for one instance
are refused for execution. Pattern fields/type compatibility and current references
are checked using the existing point-pattern resolver.

At least one slot resource is required by this tending profile. Every bound pool
has 1–2400 physical slots. A publication may approve a prefix of that capacity,
but an unapproved slot cannot become executable. All pattern-driven resources,
including a destination resource, participate in the same reservation transaction.
A resource occurring in multiple contexts is one pool, not duplicate capacity.

Pool identity is installation plus ResourceInstance catalog/ID. It excludes Run,
publication, policy and resource revision, so any of those changes cannot reset
consumption. The first explicit initialization records the owning cell, resource
and pattern revisions, layout/count, actor/source and generation. This single-cell
profile refuses another cell's use of that pool; multi-cell material handoff is
not added. Geometry/revision changes require an explicit quiet reinitialization.

## Order, reservation and completion

"Prefix" means the first N jointly unused entries encountered in the immutable
published row-major order, after excluding entries already reserved/consumed in
any participating pool. It does not mean reusing indices0..N-1 on each new Run.
The server picks that list; clients cannot submit indices, skip an available entry
or shorten N silently. If fewer than N entries are available, creation fails
atomically. Concurrent Run creation serializes against the same pool records.

P reserves the selected entries for the new Run atomically with its immutable
configuration/publication binding. Part admission assigns the next reserved entry
to the actual instance/Part atomically with normal budget consumption. It cannot
advance while the previous Part has unfinished nodes or unresolved obligations.
Run-local Part `ordinal` remains one-based1..N. Selection additionally records
one-based `slot_ordinal`, the rank in the publication's complete slot order;
`slot` remains its zero-based physical index. These counters are distinct when
prior Runs have already used slots. All are in the authoritative selection digest.

Reservation makes a slot unavailable before any effect. UNKNOWN, timeout, conflict,
abort or a declaration of no effect never makes it unused again. Same-Part retry
retains the instance and reservation, requires the existing proved-no-effect/safe
pre-state recovery path, and is limited to one explicit retry. Proven applied work
continues only remaining nodes; no repeat of an applied node. Completion of every
required node/done condition and resource-release evidence consumes the reservation.
An aborted Run cannot automatically advance or free its remaining reservations.

## Explicit initialization and replenishment

Pool initialization/replenishment is a separate idempotent recorded command under
operator terminal authority for the owning cell, restricted to SIMULATION
in this profile. It must identify the current resource/pattern revisions and the
expected pool generation, and record a reason/source. Replenishment increments the
generation; it never rewrites reservation/consumption history.

It is refused while a nonterminal Run references the pool, an operation is unresolved
or disputed, resources are held/quarantined, or an intervention case remains open.
It cannot clear resource custody, settle UNKNOWN, change a Run's selection, or mint
a new operation permit. A caller's empty/free boolean is not evidence of settlement.
The initial state is uninitialized until this command succeeds; no physical inventory
is inferred from geometry. Native inventory evidence/automatic replenishment and
multi-area inventory are outside the simulation slice.

## Admission and recovery boundary

Current definitions, actual-instance revision, qualification, pool generation and
ownership must be checked in the same serialized boundary as each new admission.
P materializes the selected candidate/slot from pinned inputs, verifies the already
approved report index, and persists report/parameter bytes before dispatch. Existing
permission, mandate, budget, fence, resource and transport gates still apply.

Original request replay and operation query/reconciliation retain their original
immutable selection even after a dependency revision changes. They cannot refresh
an expired permission or approve new effects. Legacy Run/Part/operation entry points
must not consume v2 reservations or create unbound Parts. The explicit v2 path must
use the same established lifecycle, with negotiated Executor/Host support.

Required controls include actual-instance inheritance/provenance and mismatched
values; ambiguous candidates; concurrent allocation; cross-Run reuse; a second Run
starting at the next unused slot; revision changes without inventory reset; quiet,
authorized replenishment and rejection during UNKNOWN; distinct Part/slot ordinals;
idempotent loss/restart recovery; and the approved same-slot retry/next-slot rules.
