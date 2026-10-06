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

## M2 scope: source imported, product unvalidated

The retained G0 checker still rejects product roots under `BOOTSTRAP_ONLY`, and its original regression fixtures remain active. The explicit **SOURCE_IMPORTED_UNVALIDATED** branch accepts only the independently pinned 1,718-file import plus the named root governance and provenance files. It does not broadly allow arbitrary files under product prefixes.

The M2 manifest records a frozen source tuple and per-file repository/commit/path/blob/mode provenance. The offline import checker pins its canonical payload SHA-256 to `c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc`, independently recalculates actual file SHA-256 and Git blob/tree IDs, and refuses additions, missing files, mode changes, aliases, symlinks, or altered payloads. With `--git`, both the source and provenance manifest must also match the index and candidate HEAD.

All five required jobs use the exact PR head or push SHA: `repository`, `commit_policy`, `import_fidelity`, `sdk_parity`, and `static_identity`. The aggregate rejects missing, failed, cancelled, skipped, or unlisted jobs. Static identity comparison consumes a hash-pinned baseline; unsupported required recipe evaluation is a failure. Explicit unmeasured compiled-binary and physical scope stays UNKNOWN/NOT_RUN. The unestablished workflow-execution/v2 consumed wire hash is a named limitation, not an invented digest.

The root content checker validates root English policy and root-document links. It verifies frozen import membership but does not normalize imported documents or claim their historical evidence links are resolved. The required import-fidelity job establishes their exact bytes; M4 owns link reconciliation. Product builds, runtime conformance, and acceptance remain NOT_RUN until actually exercised.

## Required next scope transition: M3

M3 adds the full union of prior product checks under a separately reviewed validation scope. It must record the exact accepted M2 import commit, verify that commit's imported blobs/modes and provenance against this unchanged frozen manifest, and separately validate the current candidate's legitimate source changes. The historical import baseline must not be recomputed from later source. Do not leave the M2 requirement that the current product tree equal the original snapshot permanently enabled, and do not simply remove it without the historical-commit audit and replacement current-source gates.

The M3 change must introduce a new explicit scope, preserve all governance/refusal checks, audit the M2 import commit's ancestry and provenance, and require the full contract/binding/SDK/invariant/Engine/client/package/runtime gate union for the current candidate. M2 itself does not run or claim those product checks. Frozen CP2 runtime state remains separate throughout.

## Recorded bootstrap checkpoint — 2026-10-07

The maintainer requested execution of the migration plan. Before creating G0,
Codex and independent agent reviewers on the maintainer's Mac verified recovery
of 319 source refs, 24 signed tags, and three dirty worktrees. Preservation also
covers the recorded PR heads, bases and actual merge commits (854 locators),
GitHub metadata, and 38 release assets. The original source refs, index and
worktree contents remained unchanged. Historical exceptions retain their original
repository identity and are not inherited here.

Cryptographic re-verification covered the three import commits and 24 tags,
plus the three available detached release-checksum signatures. This does not
claim cryptographic re-verification of every historical commit. Private backup
material stays outside this public source repository.

The local preservation gate record has SHA-256 `74b16b6bab1dfda6e538305305db97a4cd03a49b4e9cb0c9d47b0c725c5620ea`.
This is a preservation result, not user acceptance, a live CP2 backup, or a
product/runtime validation result.

G0 is `2a02ab9fb152e78ae7c948cb63fcb0924429a282`, published identically to
main and develop with verified OpenPGP and author DCO. Five active rulesets
matched the reviewed configuration. The [bootstrap CI run](https://github.com/jack0682/RobotTransformation/actions/runs/37497048372)
passed for that exact G0 head with BOOTSTRAP_ONLY scope. Product import, full
product CI, SDK qualification, cutover and legacy archival remain later gates.
