# RobotTransformation

RobotTransformation is the development home for RX: a vendor-neutral resident platform connecting heterogeneous robots, equipment, and services through common task, authority, state, result, and recovery contracts.

**Status: Development source of truth, before the first RobotTransformation release.** Use this repository for new product work, current documentation and semantic contracts. Repository migration is separate from SDK/distribution acceptance, resolution of the preserved CP2 failure and physical qualification. Required CI and DCO verify each contribution; no release or runtime acceptance is implied by this status.

The immutable M2 import is audited at signed ancestor `0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0`. Current source is validated by the full Platform/Solutions gate union, same-candidate SDK and installed-skills checks, frozen compatibility tests, current-document integrity, and bounded compiled identity probes.

## Product goal and progress

The product goal is an operable, installable RX software draft: a solo SI developer/operator can configure, verify, simulate, change and recover supported heat-treatment workflows in the action graph with almost no manual code. This is a software-draft goal, not a claim of physical qualification or functional safety.

| Find | Open |
|---|---|
| Final goal and capability epics | [Goal #25](https://github.com/jack0682/RobotTransformation/issues/25) / [Goals and epics](https://github.com/users/jack0682/projects/10/views/7) |
| Current execution | [Current sprint](https://github.com/users/jack0682/projects/10/views/1) |
| Planned tasks and unscheduled work | [Sprint planning](https://github.com/users/jack0682/projects/10/views/5) / [Product backlog](https://github.com/users/jack0682/projects/10/views/4) |
| Acceptance checkpoints | [Milestones](https://github.com/jack0682/RobotTransformation/milestones) / [Acceptance queue](https://github.com/users/jack0682/projects/10/views/3) |
| Delivery direction and cadence | [Product roadmap](https://github.com/jack0682/RobotTransformation/wiki/Product-Roadmap) / [Sprint plan](https://github.com/jack0682/RobotTransformation/wiki/Sprint-Plan) |

The linked [RobotTransformation — Sprints project](https://github.com/users/jack0682/projects/10) is also available from this repository's **Projects** tab. Goal → Epic → Task is the work hierarchy; milestones are acceptance checkpoints and sprints are planning windows. The project mirrors actual issue/PR evidence, not assumed progress. Keep it current as part of every task, following [the synchronization rules](CONTRIBUTING.md#project-synchronization).

## Work and contribution

- [Sprint project](https://github.com/users/jack0682/projects/10)
- [Project wiki and operating guide](https://github.com/jack0682/RobotTransformation/wiki)
- [Contribution workflow](CONTRIBUTING.md)
- [Repository governance](GOVERNANCE.md)
- [Security policy](SECURITY.md)

The new repository starts a signed, signed-off history with no inherited historical DCO exceptions. The imported source provenance is recorded in `provenance/import/M2-source-manifest.json`; its payload digest is pinned independently by the import checker. Original history, tags, signatures, releases, and URLs remain in [rx-platform](https://github.com/jack0682/rx-platform), [rx-solutions](https://github.com/jack0682/rx-solutions), and [rx_docs](https://github.com/jack0682/rx_docs).

Current product direction is owned by the [product documentation](docs/README.md), [product definition](docs/01_product_definition.md), [core charter](docs/43_core_charter.md), and [canonical contracts](contracts/README.md). Original rx_docs documents and evidence remain preserved at their original paths and revisions. The wiki is a navigation guide, not a normative source or acceptance record.

The preserved CP2 acceptance failure remains separate from migration work. This migration neither accepts it nor authorizes retry, settlement, resource release, environment changes, or physical operation.

## Validate the current document and product gates

Python 3.10 or newer is sufficient for these root fixtures. Full Rust, native, installed-client, and simulation checks run on isolated GitHub-hosted Linux runners:

```sh
python3 -B .github/test_governance.py
python3 -B .github/test_import.py
python3 -B .github/test_full_ci.py
python3 -B .github/test_documents.py
python3 -B .github/test_canonical_layout.py
python3 -B tools/docs/check_documents.py --run-tables
python3 -B tools/governance/check_repository.py
python3 -B tools/migration/check_origin.py
python3 -B rx-platform/tools/check_host_sdk.py rx-solutions/sdk
```

The repository check requires a Git checkout whose origin is this repository. A preparatory file tree can use `--filesystem` for an explicitly uncommitted content check; this is not a commit or signature audit. The fixtures retain G0 refusals and add M2 import/CI negatives; Git index/HEAD fixtures, remote services, and cryptographic verifier results are mocked. Actual commit signatures are verified separately by the full-head audit and GitHub checks.

The validation scope and exact required job set are recorded in [.github/validation-scope.json](.github/validation-scope.json). Missing, failed, cancelled, or skipped jobs cannot yield a successful aggregate. Full-head signing/DCO, the immutable origin, SDK parity, and static identity jobs remain required.

The origin audit reads original Git objects and verifies ancestry; it does not force current product bytes to remain equal to the original import. The source-identity baseline and its evaluator remain pinned while this migration changes governance and documentation rather than the protected Rust/Cargo context.

Current canonical links, JSON, contracts, and finite compatibility routes are checked together. Exact M3 link-transition proof is verified separately against its pinned ancestor commit; its recorded line numbers and whole-file hashes do not freeze later ordinary prose. The M4 map records complete initial relocation and the three embedded-table path adaptations. Original evidence URL availability is not inferred from local checks.

The compiled probe invokes applicable public identity functions from existing packages in isolated raw candidate source copies. It records inputs, compilation and output identity. Private transport consumers, shipping daemons, the non-Unix validator variant, and physical effects are outside that probe's observation scope. Source-only calculations and previous CI results are not substituted for a current run.

## License

Original project contributions use [Apache License 2.0](LICENSE). Preserve [NOTICE](NOTICE) and all applicable third-party attributions during subsequent imports.
