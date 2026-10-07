# Contributing

RobotTransformation is a public Apache-2.0 personal project. M3 declares the full isolated CI union. Use exact run evidence for executed checks; releases and acceptance retain their separate gates.

## Branches

| Branch | Purpose | PR destination |
|---|---|---|
| `main` | Stable or release baseline | Updated through checked PRs after bootstrap |
| `develop` | Integration | `main` for promotion |
| `feature/*`, `fix/*`, `docs/*`, `chore/*`, `codex/*` | Focused work from develop | `develop` |
| `release/*` | Release preparation from develop | `main`, then carry fixes to `develop` |
| `hotfix/*` | Urgent work from main | `main`, then carry fixes to `develop` |

A main-to-develop backmerge uses a PR. Only same-repository branches can use the main, develop, release, or hotfix promotion routes. External contributors submit a work branch to develop. Fork workflows receive read-only tokens and no signing keys or repository secrets.

Use merge commits. Squash, rebase, and automatic merge are disabled. Reviewed commit identity is preserved. Do not rewrite published history or replace a published tag.

## Project synchronization

All contributors, including agents, keep the [linked delivery project](https://github.com/users/jack0682/projects/10) synchronized with the work they actually perform. Updating tracking is part of the task handoff, not a separate optional cleanup. The issue owns scope, dependencies and evidence; the PR owns the proposed source change; Project fields summarize their current state. Product contracts and exact execution evidence remain authoritative.

| Checkpoint | Required update |
|---|---|
| Before starting | Find the existing task before creating another. Link its parent Epic and relevant goal, set one `level:*` label plus appropriate work-type/area labels, record the accountable owner, primary milestone where applicable, and planned Sprint for leaf tasks only. Confirm scope and dependency readiness. |
| Work starts | Set the task In progress and record the executing agent, host and branch separately from the human owner. Do not mark an entire Epic complete because one child starts or merges. |
| Meaningful progress or scope change | Record the new user-visible behavior, source/PR, checks actually executed, failures, limits and next action. Adjust dependencies and estimates when evidence changes; do not overwrite earlier failures. |
| Blocked | Set Blocked only for a concrete dependency/decision, with the owner and unblock condition. If an in-scope fix can proceed, keep In progress and preserve the failure evidence. |
| PR or technical handoff | Link the task from the PR and the PR/evidence from the task. Move to Review only when a reviewable result and verification record exist. Keep owner acceptance Pending until explicitly decided. |
| Acceptance, completion or carryover | Record the exact accepted artifact/revision and decision before setting Accepted/Done when required. Otherwise document why separate acceptance is Not required. Preserve original IDs/evidence and record why and where unfinished work moves. Update the parent Epic and milestone only from their own criteria. |

Use `Refs #<task>` for contributions whose issue still requires owner acceptance; do not use auto-closing keywords to bypass that gate. A merge, closed PR, green CI run or elapsed Sprint is not acceptance. M1 technical handoff remains `USER_ACCEPTANCE_PENDING` until the owner accepts it. Failed and UNKNOWN execution results remain visible with original custody; board edits never settle or replay a Run.

Milestone and Sprint are separate from the Goal → Epic → Task hierarchy. Keep priority, status, acceptance, size and Sprint in their Project fields; do not create duplicate issues or labels to represent another view. Do not double-count parent/child delivery. Repository automation may add issues to Backlog, but it does not choose their scope, Sprint, evidence or acceptance.

At the end of an active work session, reconcile the task's actual state, PR links, evidence and next action before reporting to the user. Do not change another active task's state without checking its latest evidence. If Project access is unavailable, update the accessible issue/PR with the exact pending field changes, report the synchronization gap, and do not claim it was applied. Use the authorized GitHub UI when a connector lacks Project permissions; do not broaden credentials silently.

Current cadence, WIP and carryover rules are maintained in the [Project workflow](https://github.com/jack0682/RobotTransformation/wiki/Project-Workflow) and [Sprint plan](https://github.com/jack0682/RobotTransformation/wiki/Sprint-Plan). Changing planning dates does not authorize later milestones, releases, physical operation or semantic changes.

## Signing and author certification

Every new commit, including merges, requires both its author's matching `Signed-off-by` trailer and a verified OpenPGP signature. Read the [Developer Certificate of Origin](https://developercertificate.org/) before signing off. DCO attests contribution rights; the signature authenticates the commit. Neither substitutes for the other. The new history has **zero historical DCO exceptions**, including for the maintainer, bots, merges, and imported snapshots.

Use an existing key on your trusted signing device. The hook installer configures only this clone; it does not generate, copy, export, upload, or install key material. See [GOVERNANCE.md](GOVERNANCE.md) for setup and initial-bootstrap boundaries.

```sh
python3 tools/governance/install_git_hooks.py
git switch develop
git switch -c feature/your-change
# Make the change and run the relevant checks.
git add <changed-paths>
git commit -s -S -m "Describe the resulting behavior"
git push -u origin feature/your-change
# Open a PR to develop, then wait for current CI and DCO.
python3 tools/governance/merge_pr.py PR_NUMBER
```

Local hooks and the root helpers refuse direct protected-branch pushes and old-repository targets. Do not run administrative helpers copied into component subtrees.

### External fork contributors

The origin-guarded helper commands above are for a maintainer clone whose origin is `jack0682/RobotTransformation`. Administrative helpers never manage a fork or another repository. Fork contributors use their own local Git signing configuration, make explicit `git commit -s -S` commits, and inspect them with `git verify-commit HEAD`; they do not install this canonical-origin hook set in a fork clone. Run `.github/test_governance.py` and `tools/governance/check_repository.py --filesystem` for the current root content checks, then push the work branch to the fork and open a PR to develop. The target repository's CI audits the complete PR-head ancestry, including matching author DCO. The same contribution requirements apply.

## Review and checks

Describe the concrete problem, resulting behavior, source and artifact identity, tests actually run, failures, unverified scope, dependencies, and rollback. Changes to authority, UNKNOWN, stopping, handover, or recovery need counterexamples and compatibility impact. A structural edit may change a source-based compiler, validator, or driver identity even when intended behavior stays the same.

For root/M3 fixtures:

```sh
python3 -B .github/test_governance.py
python3 -B .github/test_import.py
python3 -B .github/test_full_ci.py
python3 -B .github/test_documents.py
python3 -B tools/governance/check_repository.py
python3 -B tools/migration/check_origin.py
python3 -B rx-platform/tools/check_host_sdk.py rx-solutions/sdk
python3 -B tools/governance/check_commit_policy.py --head HEAD
```

The last command uses trusted public keys in the local GPG keyring. GitHub-backed CI uses the same full-head scope and GitHub's recorded OpenPGP verification. The fixture tests do not themselves establish real signature validity.

Required CI is the exact PR-head `CI` from GitHub Actions (app 15368), plus `DCO` from the DCO app (app 1861). A Branch CI result, stale head, other provider, cancelled child, or local test result does not substitute. Required review conversations must be resolved. Zero external approvals are required while the project has one maintainer; the maintainer still reviews the output and evidence.

M2 has a fixed snapshot-only contract: the manifest, file bytes/modes, SDK producer parity, and named static identities must match the reviewed baseline. Product-source work after import requires the documented M3 scope transition, anchoring frozen import evidence to its original commit while enforcing current-source gates. Unified product CI must retain all prior required contract, SDK, invariant, boundary, language, package, and runtime checks. Do not relabel static import verification as product conformance.

## Scope and publication

Use English for source, comments, UI, contribution material, and governance. The later documentation policy may allow Korean general product documentation by path. Keep local assistant instructions, harnesses, credentials, equipment addresses, runtime data, and machine-specific state untracked.

Preserve source provenance, licenses, notices, history, and historical evidence. A snapshot commit certifies the contributor's actual work and rights; it does not fabricate the original authors' signoffs. Package verification, review, qualification, activation, execution, and maintainer acceptance remain distinct. CI or a PR merge never accepts the preserved CP2 Run.

Dependency updates are manual, focused, signed PRs. Vulnerability alerts remain enabled; automatic security-fix proposals are disabled. An unverified dependency upgrade is not bundled into repository migration.

The full required workflow runs original Platform and Solutions Rust, client, native, operator, and installed-skills checks on separate Linux runners. Do not run heavy migration builds on the preserved CP2 host. The origin audit anchors the original import to its immutable commit; current code is validated through current-source gates. A changed compiler, validator, or driver identity requires explicit impact review instead of reusing historical approval.
