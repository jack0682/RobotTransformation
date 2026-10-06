# Contributing

RobotTransformation is a public Apache-2.0 personal project. M2 imports frozen source with static integrity and identity checks. Product builds/runtime validation, contract changes, releases, and acceptance retain their separate gates.

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

### External fork contributors

The origin-guarded helper commands above are for a maintainer clone whose origin is `jack0682/RobotTransformation`. Administrative helpers never manage a fork or another repository. Fork contributors use their own local Git signing configuration, make explicit `git commit -s -S` commits, and inspect them with `git verify-commit HEAD`; they do not install this canonical-origin hook set in a fork clone. Run `.github/test_governance.py` and `tools/governance/check_repository.py --filesystem` for the current root content checks, then push the work branch to the fork and open a PR to develop. The target repository's CI audits the complete PR-head ancestry, including matching author DCO. The same contribution requirements apply.

## Review and checks

Describe the concrete problem, resulting behavior, source and artifact identity, tests actually run, failures, unverified scope, dependencies, and rollback. Changes to authority, UNKNOWN, stopping, handover, or recovery need counterexamples and compatibility impact. A structural edit may change a source-based compiler, validator, or driver identity even when intended behavior stays the same.

For the M2 static stage:

```sh
python3 -B .github/test_governance.py
python3 -B .github/test_import.py
python3 -B tools/governance/check_repository.py
python3 -B tools/migration/check_import.py --git
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
