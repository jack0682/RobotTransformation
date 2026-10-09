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

## M3 CI declaration and current source

### CI action runtime and shared setup

The active root workflow pins these upstream releases to full commit IDs. Each
release's action metadata declares Node 24; `setup-node`'s `node-version` input
separately selects the Node version used by the operator build.

| Action | Release | Commit |
|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| actions/setup-node | v7.1.0 | 949feb2413d6458794dcd2491c4babbbce0c15c1 |
| actions/cache | v6.1.0 | 55cc8345863c7cc4c66a329aec7e433d2d1c52a9 |
| actions/upload-artifact | v7.0.2 | cf430e030ddbb5b0abf93d22962f4752f3646cd9 |
| actions/download-artifact | v8.0.2 | 9000827ccba6bdab643e8b6fd33ac0654aef8333 |

Upstream release notes and the pinned `action.yml` are the update inputs:
[checkout](https://github.com/actions/checkout/releases/tag/v7.0.1),
[setup-node](https://github.com/actions/setup-node/releases/tag/v7.1.0),
[cache](https://github.com/actions/cache/releases/tag/v6.1.0),
[upload](https://github.com/actions/upload-artifact/releases/tag/v7.0.2),
[download](https://github.com/actions/download-artifact/releases/tag/v8.0.2).
The current GitHub-hosted Ubuntu runners support Node 24. Any future self-hosted
runner must meet the selected action releases' runner requirements before use.
Preserved component workflows and frozen import proofs are not rewritten.

The Ubuntu mirror adjustment lives in `tools/ci/use_ubuntu_archive.sh`. It replaces
only the known Azure HTTP mirror URL with the official HTTPS archive and preserves
suites and signing keys. Callers still own package installation.

Operator checks and API browser authoring run once. One image build feeds the five
required M1 scenarios in the same run; archive SHA-256 and loaded image ID must match.
The image and public scenario evidence are retained for 14 days. An expired image
requires rebuilding the producer, not accepting missing evidence or disabling ID
checks. Failed-job reruns and full reruns retain their distinct run attempts.

### Release eligibility

New tags may point only to the **current remote main commit** whose latest
`push` run of this repository's root CI workflow completed successfully. A green
PR check, develop run, workflow_dispatch run, older green attempt, skipped check
or source-tree equality is not sufficient. The release check re-reads the chosen
run and remote main; unavailable or truncated API data refuses publication.

Use `python3 tools/governance/check_commit_policy.py --release-candidate FULL_SHA`
as a read-only preflight before tag creation and again immediately before publishing.
The existing pre-push hook repeats the same gate for every new signed annotated tag,
using its peeled commit rather than its tag object ID. Existing tags stay immutable.
If main advances, re-evaluate the intended release rather than silently retargeting.

Publication is a separate maintainer action: explicitly choose the version and
scope, verify the annotated OpenPGP tag, push only that tag, verify the remote tag
object, and publish using the already existing tag (`gh release create --verify-tag`).
Record the commit, successful main CI URL, source/build identities, supported
platforms, known limitations and checksums/signatures for any distributed assets.
A prerelease must be labelled as such. Do not infer runtime/distribution or physical
qualification from source CI, and do not publish credentials or private test state.

These helpers and local hooks enforce the normal Git path; they cannot prevent an
administrator from bypassing hooks or creating a tag/release through a separate API.
Remote immutable-tag and protected-branch rules remain in force. This change creates
no tag, release, signing key, remote bypass or automatic publishing workflow.

The declared stage is `CI_SCOPE_DECLARED_NOT_YET_RUN`; this source label is not a claim that hosted execution succeeded. The aggregate evaluates the exact nineteen required job results for each run. GitHub Actions run identity and artifacts establish what executed. CI success does not accept CP2 or authorize physical equipment.

The import-fidelity job now verifies immutable ancestor `0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0`, its complete source objects and provenance, and the unchanged identity baseline/evaluator. It verifies protected bytes using its own standard-library Git reader before executing the verified historical checker. Current product source is checked separately; the import manifest is never regenerated from evolved source.

Platform and Solutions retain their original full required checks, including actual disposable Git/GPG hook tests on Linux. Current copied-document JSON, normative hashes, unique embedded table checks, and local links are required. An earlier set of missing evidence links was repaired in the copied ordinary documents before this gate; hash-bound documents and the original documentation repository were preserved.

Every candidate job checks out the same head. Installed skills use current P by default and also test the frozen old-P compatibility pin on both amd64 and arm64. The compatibility checkout is a sibling of the product checkout. Cargo jobs are limited to two, including inside the skills Docker build, with component/architecture cache and target separation. Release records include repository, commit, component path and tree identity. CI artifacts with finite retention are not permanent acceptance evidence.

M4 changes canonical documentation paths only through a further reviewed scope/path-map update. M5 establishes the declared distribution and consumer release scope. M7 handles changed implementation identities and fresh review/qualification explicitly; this M3 declaration does not assert those later gates passed.
