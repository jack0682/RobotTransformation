# Resident registration authoring — candidate extension revision 2

Status: implementation contract for new Platform-owned declarations, not a frozen
base/cell protocol, package verification, execution permission or completed RF02
migration. The shared identity values remain `rx-domain::component` from R1.
Existing base/cell protobufs and normative manifest hashes are unchanged.

## Author and authority boundary

The existing Platform application writer owns every accepted declaration and its
history. An active authenticated Engineer or AccountAdmin can create one. The
server assigns the registration ID and records the authenticated creator as its
owner. Reads and changes require the current author role and either that owner
identity or AccountAdmin. Cell membership is not required because registration
does not allocate a Cell, Host, process, resource, permit or work operation.

A catalog reference is attributed author input. This revision does not establish
that its package is installed, trusted or usable. Every response therefore reports
`content_verification=NOT_ESTABLISHED`,
`execution_ownership=NOT_ESTABLISHED_BY_REGISTRATION` and
`work_use_permission=NOT_EVALUATED`. These are closed response states, not caller
supplied flags. The existing execution gates do not consume these views as a
permission. Verified content acceptance, assignment and execution reporting remain
required parts of the full framework goal.

## Public HTTP authoring path

Use the ordinary authenticated ingress, cookie/session validation, Origin and
mutation headers. Existing loopback/TLS policies are unchanged. These routes are
non-actuating metadata operations; they do not substitute for terminal authority
on device operations.

| Method and path | Input | Result |
|---|---|---|
| POST `/api/v1/components` | `request_key`, `command.declaration` | Server-generated stable ID, declaration revision and attributed owner |
| GET `/api/v1/component` | `id`, optional `revision` | Current declaration or the named immutable historical snapshot |
| POST `/api/v1/components/update` | `request_key`, `command.id`, `command.expected_revision`, `command.declaration` | Same ID and owner, a new declaration revision |
| POST `/api/v1/components/retire` | `request_key`, `command.id`, `command.expected_revision` | Terminal RETIRED declaration; history preserved |

`declaration` has the existing `label` and `catalog` fields; `catalog` contains
`program` and `digest`. IDs are canonical UUID strings, digests are lowercase
SHA-256 strings and revisions are canonical decimal strings. Unknown input
fields, including caller-selected owner/state/permission, are rejected.

Each mutation uses the existing durable request ledger. The fingerprint includes
the authenticated principal, so two accounts sharing a client namespace cannot
recover each other's results by repeating a key. Current authentication and
ownership are checked before cached results are returned. Same request/content
returns its original snapshot, including after later edits or retirement; query
without `revision` to read the current record. Conflicting key reuse is rejected.

Expected-revision checks prevent lost updates. Mutation, immutable version,
audit event and request result commit in the same repository transaction. Failure
before commit writes none of them; a lost response after commit is resolved by
the original request. Retirement cannot reactivate or rewrite the record and does
not kill a process, release a resource or alter a legacy Supervisor registration.

## Persistence and compatibility

P stores the attributed record under its `component/` namespace with schema
`rx.internal.resident-component.v1`, and accepted cuts under `componenthistory/`
with `rx.resident-component-view.v1`. It uses the existing repository/writer and
audit event space. These are not a new public control-journal wire mapping.

The record identifies the installation, shared registration value, owner and
creation/change source and times. Restart invalidates old authenticated sessions
as before but preserves component ID and history. A response snapshot provides no
freshness or operating permission merely because it survived restart.

There is no client-selected ID or automatic legacy adoption through this authoring
endpoint. The separate registration-transfer protocol preserves existing IDs and
history through explicit source freeze, target intake and source acknowledgement.
A P declaration must not be silently installed as an independent S registration
with another ID.

Revision 2 coordinates these declarations with optional resident execution. An
issued, unresolved execution holds a logical component claim; new declaration
changes and retirement are refused until that assignment is stopped/reconciled.
Historical mutation-response recovery remains historical and cannot change the
active declaration. The execution view carries its separately attributed content
checkpoint and start/outcome records; this declaration-only view still does not
establish content, ownership or work permission.

The new operational path and Supervisor role opt into reader format 9, refusing
older writers that would ignore claims. Ordinary declaration stores stay at their
existing floor. Full live replacement, discovery/pagination, cross-author sharing,
generic content extensibility and complete RF02 remain open.

## Required checks

- Register without creating any Cell/Host/resource/permit/work record.
- Lose the committed create/update response; retry the same request and preserve ID/revision.
- Restart P; reject the old session, recover with current authentication and retain history.
- Reject wrong roles, another author's access, caller-forged authority and conflicting key reuse.
- Reject stale mutation revisions and reactivation after retirement; preserve historical cuts.
- Inject a pre-commit failure and prove no registration/history/cached success was committed.
- Exercise the HTTP routes through the real application writer, not a mocked business service.

These checks establish the declaration path only. They do not close registration
ownership migration, operating admission, physical qualification or the full
resident framework completion ledger.
