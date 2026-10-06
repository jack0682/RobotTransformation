# Repository governance

[repository-settings.json](repository-settings.json) is the reviewed target configuration for **jack0682/RobotTransformation**. The helpers resolve the repository root explicitly from `tools/governance/`, require that it is the Git root, and check the single origin fetch/push destination before administrative actions. Old repositories and nested administrative copies are refused.

## Initial bootstrap and later contributions

The one-time G0 bootstrap starts a fresh signed, signed-off history with no product source and no inherited DCO exceptions. The authorized maintainer creates main and develop atomically at the same verified G0 commit, then applies and reads back repository protection. If the target is no longer empty or those initial refs differ, stop and inspect; do not force-push a replacement.

Create and verify the bootstrap commit with explicit signing and signoff. The protected-branch pre-push hook has no bootstrap bypass: install the ordinary local hooks after the one-time initial ref creation. After that initialization, all changes use checked PRs. G0's successful checks are explicitly **BOOTSTRAP_ONLY**; they do not represent imported-product validation.

Source import is a later reviewed snapshot change with immutable source provenance. Original source histories, tags, signatures, PRs, and historical DCO incident records stay in their original repositories and verified backups. None becomes an exception to this repository's new commit audit.

## Protection layers

| Layer | Scope | Requirement |
|---|---|---|
| Signed contributions | Every branch | GitHub-verified commit signatures |
| Branch naming | Branch creation | Only main/develop and documented work/release/hotfix prefixes |
| Quality rules | main/develop | PR, up-to-date CI/DCO, verified signatures, resolved review threads; no deletion or force push; no bypass actors |
| PR-only updates | main/develop | Administrator update exception applies only through PRs and cannot bypass quality rules |
| Immutable tags | Every tag | No update or deletion; signed annotated tags checked by local hooks and release review |
| Full-head audit | Every PR and branch CI head | Every ancestor has author DCO and verified OpenPGP; zero exceptions |

CI must come from Actions app 15368 and DCO from app 1861. PR CI and push Branch CI are distinct. The DCO app has owner checks enabled and remediation-commit shortcuts disabled. The repository's audit also checks merges and bots. GitHub signature rules do not independently certify author DCO on a future merge; the merge helper adds the authenticated merger's own signoff and checks the resulting commit.

The current approval count is zero because one maintainer cannot approve their own PR. Increase it together with code-owner review when independent maintainer review becomes available. Owners retain GitHub administrative authority; these controls do not remove that authority. No workflow receives private signing keys or an administrative token.

## Configure an existing signing key locally

Use an account-verified email and an existing GitHub-registered public signing key. Keep private material on its trusted signing device.

```sh
git config --local user.name "Your Name"
git config --local user.email "your-verified-email@example.com"
git config --local user.signingkey YOUR_EXISTING_GPG_FINGERPRINT
python3 tools/governance/install_git_hooks.py
```

The installer changes only local clone configuration. It preserves unrelated custom hooks and non-OpenPGP configuration by refusing to overwrite them. Git's normal exported hook context is ignored in favor of the helper's fixed root. Hooks add only the current committer's truthful signoff; another author's missing certification is never manufactured.

Use `git commit -s -S` explicitly. Unlock the existing key through the normal GPG agent when needed. Never put passphrases, private keys, or equipment credentials into the repository or CI secrets.

## Merge an exact checked PR

```sh
python3 tools/governance/merge_pr.py PR_NUMBER
```

The helper audits live policy without changing it, validates GitFlow and repository identity, checks successful CI/DCO provider IDs for the exact head, and verifies the CI workflow path, PR identity, event, base, and successful completed run. It rereads the PR before requesting an exact-head merge commit. GitHub's strict base checks enforce a later base race. Any missing verification, API error, policy drift, or changed head/base stops the request.

The helper derives the signoff from the authenticated actor's current name and GitHub no-reply identity. It accepts no arbitrary signoff override. Confirm that account's web-merge author settings before its first merge. A resulting merge is independently read back for matching author DCO and verified OpenPGP. An uncertain response or `MERGED_BUT_VERIFICATION_FAILED` requires inspection of the same PR and original result before any retry; it is not permission to rewrite history or add an exception.

## Audit and apply settings

```sh
python3 -B .github/test_governance.py
python3 -B tools/governance/check_repository.py
python3 -B tools/governance/check_commit_policy.py --head HEAD --github-repository jack0682/RobotTransformation
python3 tools/governance/configure_github.py
```

The last command is GET-only by default and fails closed on unavailable or mismatched readback. It checks settings, security controls, Actions permissions, vulnerability-alert availability, automatic-security-fix policy, and every managed ruleset. Unmanaged or ambiguous rulesets require review; the helper never silently deletes them.

To apply a reviewed policy change after merging it under the existing rules:

```sh
python3 tools/governance/configure_github.py --apply
python3 tools/governance/configure_github.py
```

Both permanent branches must already exist. The apply command is scoped to this repository and verifies readback. It does not install GitHub Apps, upload keys, merge code, change CP2 runtime state, or grant device-operation authority. If a required service is unavailable, leave the PR open and restore the service instead of bypassing checks.

## Verification scope

The bootstrap fixture suite uses isolated files and mocked GitHub/GPG results; it runs no product builds, Docker, signing-key operations, Git commits, or pushes. Actual full-head verification is a separate command/CI job. Shallow histories, replacement refs, and grafts are refused so they cannot hide ancestors.

Later import and CI phases must preserve or strengthen existing product gates, including contract/binding hashes, SDK producer parity, invariant traceability, Engine boundaries, installed clients, and scoped runtime tests. Every scope transition needs its own checks and evidence. Wiki commits and project-status changes do not satisfy source PR checks or maintainer acceptance.

## Required next scope transition: M2

G0 deliberately rejects product roots and keeps `BOOTSTRAP_ONLY`. The source-import PR must implement an explicit **SOURCE_IMPORTED_UNVALIDATED** stage together with its checks; merely deleting the bootstrap allowlist or changing the scope string is not acceptable.

The M2 change must add a frozen source tuple and per-file repository/commit/path/blob/mode provenance, raw-import fidelity checks, static source-identity comparison, and same-commit SDK parity. The required aggregate must include those import/static jobs in addition to repository and full-head commit-policy checks, with negative controls for missing/extra files, mode or byte changes, stale SDK, and altered identity inputs. The source-import result must continue to state that product builds, runtime conformance, and acceptance are NOT_RUN until actually exercised.

M3 then adds the full union of product checks under its separately reviewed validation scope. This sequence makes the M2 import PR reviewable before M3 without treating G0 or static import validation as product success. The current G0 does not implement either later stage.
