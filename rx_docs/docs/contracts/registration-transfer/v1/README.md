# Registration transfer boundary, revision 4

Status: source preparation, target intake and explicit Supervisor acceptance
reconciliation are integrated with scoped validation evidence. Content acceptance
and Platform-directed execution remain required; this is not full RF02 closure.

## Source preparation

A legacy Supervisor registry may be frozen for one explicit request ID and target
Platform installation. The source retains every original registration UUID and
revision. Its current declarations and optional resident-selection index are
hashed together, and the original control-history head is recorded. The source
freeze marker, history event and persistent storage fences commit atomically.
Retrying the exact request returns the original cut; changing its target or ID
is refused. An empty or inconsistent registration/index source is refused.

The SQLite adapter seals these key prefixes in both entity and control-projection
tables: `components/registration/`, `components/resident-selections`, and
`components/registry-freeze`. Insert, update and delete are refused. The seal list
itself cannot be updated or deleted through ordinary SQL DML. There is no unseal
method. Ordinary databases remain at schema 6. A source seal promotes schema 6
to 7; a schema-8 store stays at 8. Schema-6 binaries refuse sealed databases.
Reopening verifies the expected guard definitions and seal list.

Source declaration/retirement writes, new local assignments, resume permits and
new work commits are blocked while frozen. Existing execution observations,
investigation/disposition records and historical result queries remain separate
and may continue. Original history export stops at the frozen cursor, so later
observations do not silently change the import cut.

The local freeze result says PERMANENTLY_FROZEN / NOT_ESTABLISHED /
NOT_TRANSFERRED for local declaration writer, P acceptance and process ownership.
A serialized export is not remote attestation. A target receiver verifies the
configured source boundary itself; an uploaded JSON `sealed` claim is refused.

## Target intake and publication

P's trusted startup configuration maps source names to absolute normalized paths
and owner principals. The wire request supplies only the source name, source
freeze ID and expected configuration-binding digest, inside the existing
request-key envelope. The original freeze ID identifies the transfer; the HTTP
request key identifies the importing author's idempotent request. Paths, authority
booleans and serialized proof objects are not accepted as caller inputs.

P authorizes the current Engineer or AccountAdmin and source owner before source
I/O. A service around the existing ApplicationPort opens the actual sealed source
under its exclusive writer lock, verifies the fence definitions, target
installation, source cut, declarations digest and selection identities, and
streams bounded chunks to the existing authoritative application writer. No
second authority writer or process manager is introduced. Source absence does
not prevent P startup. Missing, final-symlink, hard-linked, empty and unsealed
sources are refused. The existing-source opener never creates a missing source
or upgrades an unsealed database. Within one service lifetime, a changed resolved
path/device/inode is refused after its first successful source verification.
The configuration binding remains the configured path and owner across boots;
this is not an anti-rollback identity for privileged filesystem replacement.

Each stage rechecks the current actor, active owner role, installation boot and
source binding. Original UUIDs, positive declaration revisions, declarations,
retirement and every original event through the frozen cut are retained. Source
creation/change/retirement history must be contiguous for each declaration and
end at the frozen current declaration. Source timestamps are not invented: P's
materialized records carry target intake time and actor, while raw source events
retain their original documents and event IDs. Raw events that resemble P control
entities remain opaque archive data and do not become live control state.
The original resident-selection index is retained as provenance, not as a new
execution assignment.

Intake begins by promoting the target store to at least reader schema 8 in the same
transaction as its Receiving record. Schema-7 and older readers refuse the target.
Chunked staged component rows are inaccessible through normal component
read/write/report-scope paths until final acceptance. An existing P UUID is never
overwritten. Active reporting scopes that map the original S ID to a different P
component must be explicitly revoked before that component is staged; new aliases
cannot be issued or continued after staging. Historical diagnostic records remain.
This does not merge a former diagnostic alias's history into the canonical ID.

Only after all declarations and original history have passed validation does P
commit Accepted, the receipt, audit event and original request result together.
The receipt explicitly retains NOT_ESTABLISHED content verification,
NOT_ESTABLISHED_BY_REGISTRATION execution ownership and NOT_EVALUATED work use.
The imported component can then be changed through P's existing versioned API;
its next revision follows the original revision. The source writer remains sealed.

After an interrupted chunk or P restart, a currently authorized caller with the
same original request and unchanged binding resumes the stored cursor. Old-boot
tickets are refused. Exact request recovery after acceptance returns the original
receipt without reopening an offline source, and remains subject to current
caller authorization. Removing source configuration does not erase historical
receipts. A collision or inconsistent history leaves a Receiving transfer that
cannot publish usable components; this revision has no abort, unseal or arbitrary
rebind endpoint. Preserve that record for explicit investigation.

## HTTP surface

All routes use the existing authenticated browser/CSRF boundary:

- `GET /api/v1/registration-source?source=NAME`: authorized configuration context.
- `POST /api/v1/registration-transfers`: import or recover the original request.
- `GET /api/v1/registration-transfer?id=FREEZE_ID`: progress.
- `GET /api/v1/registration-transfer/receipt?id=FREEZE_ID`: accepted receipt.
- `GET /api/v1/registration-transfer/history?id=FREEZE_ID&after=CURSOR`: original
  event archive, eight events per page and an optional next cursor. During Receiving,
  this exposes only staged provenance, not accepted execution state.

## Compatibility and remaining obligations

The shared FreezeRequest/FreezeRecord DTOs move to rx-domain and the generated SDK;
Supervisor re-exports retain the old import path and serialized shape. Ordinary
stores stay at schema 6, source-only sealing uses 7 and target intake explicitly requires at least 8.
Revision 4 preserves the optional resident-execution floor of 9; readers refuse
10+. Source guard definitions are still checked on sealed format-9 stores. No frozen base/cell protobuf or manifest changes.
The new development CLI is not automatically invoked or installed by the existing
installer. The optional P source configuration defaults to empty.

The source lock and receipt do not acquire a process by PID, revoke physical
authority, validate package content or prove functional safety. Arbitrary
privileged schema edits, copying an older database over the source, hostile
parent-directory replacement and whole-installation rollback are outside this
local source boundary and require the separate upgrade/restore contract.
S acknowledgement is provided by the revision-3 addition below. The general P
execution-assignment path, content acceptance, registration discovery, installation
integration and full RF01–RF14 verification remain open.


## Source reconciliation addition (revision 3, integrated with scoped validation)

After P intake, the source owner may authorize an Observer-only reporter scope
for an imported canonical component. The optional reporting service's
ReadAcceptance returns the target's immutable original transfer decision only
within that current scope. S must authenticate that result, match its complete
local FreezeRecord and component membership, and persist the first matching
evidence atomically with a local history event. An arbitrary serialized receipt
or local boolean is not accepted by the public source reconciliation API.

Source inspect may report RECORDED_FROM_AUTHENTICATED_PLATFORM with the preserved
first evidence. This is historical acknowledgement only. Local declarations and
assignments remain refused, the original frozen history cut stays unchanged, and
current execution/content/work authority remains unestablished. On changed or
missing target acceptance, keep historical evidence and require investigation;
do not replay an operation or silently reset either side.

Source acknowledgement adds an optional `acceptance` field to the source inspect
view and a separately keyed history record; it does not upgrade the SQLite reader
format or alter the original frozen cut. Older source readers can ignore this
historical acknowledgement and still refuse local declaration/assignment writes.
The CLI's new process boot replaces an earlier reporting session for the same
principal under the existing single-current-peer rule; use the installation's
reviewed reporter identity and explicitly approve the new scope.


Revision 4 does not change the source freeze or target acceptance wire values.
It makes reader promotions monotonic when the execution extension is enabled.
P assignments retain the imported component's original registry binding and
frozen cut. An enrolled Supervisor must match them before preparation; another
empty registry cannot replace unresolved legacy execution history. Managed
snapshots stay outside the permanently sealed legacy author namespaces.
