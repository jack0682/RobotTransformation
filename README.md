# RobotTransformation

RobotTransformation is the product monorepo being prepared for RX: a vendor-neutral resident platform connecting heterogeneous robots, equipment, and services through common task, authority, state, result, and recovery contracts.

**Status: M4 / CANONICAL_DOCUMENTS_TRANSITION.** Product documentation and semantic contracts now use their canonical paths. The exact candidate CI run is the evidence for executed checks; this routing change does not declare runtime acceptance, a released bundle, or physical qualification.

The immutable M2 import is audited at signed ancestor `0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0`. Current source is validated by the full Platform/Solutions gate union, same-candidate SDK and installed-skills checks, frozen compatibility tests, current-document integrity, and bounded compiled identity probes.

## Work and contribution

- [Delivery project](https://github.com/users/jack0682/projects/10)
- [Project wiki](https://github.com/jack0682/RobotTransformation/wiki)
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
