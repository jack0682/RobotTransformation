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

CI runs for PRs to `main` or `develop` and for pushes to those two branches. A work-branch push alone does not start CI; open a draft PR to get CI early. Editing a PR title or description does not rerun CI. After changing a PR's base branch, close and reopen the PR so CI runs against the new base; `merge_pr.py` refuses a CI run recorded for another base.

The manual base-change procedure depends on using the root merge helper; do not
replace it with a GitHub UI merge that omits its exact-base check. A ready-for-review
transition and a post-merge main/develop push can still trigger separate runs.

## Release preparation

Promote through a checked PR, then wait for the **latest main push CI on the exact
release commit**. Before creating a signed annotated tag, run:

```sh
python3 tools/governance/check_commit_policy.py --release-candidate FULL_MAIN_SHA
```

This command is read-only. The pre-push hook also refuses a new tag without that
same current-main/CI evidence. A passing PR does not qualify the merged main commit.
Recheck immediately before publishing, retain immutable tags and use an existing
remote tag with `gh release create --verify-tag`. Follow [release eligibility](GOVERNANCE.md#release-eligibility)
for scope, artifact evidence, known limitations and the hook/API boundary.

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

The current M1 admission optimization has a bounded impact review in
`provenance/verification/m1-admission-context-review.json`. The existing identity
runner pins that review, its exact parent/change commits and the two old/new file
hashes. It retains the frozen evaluator's original `UNKNOWN_CONTEXT_CHANGED`
report, then separately checks that only the reviewed context differs and that
all named values, binding/source proofs and SDK inventory remain unchanged.
Actual public identity probes still compare against the original frozen baseline;
all required product and runtime checks remain mandatory. This review is not
maintainer acceptance or a general exemption for future Rust changes.
