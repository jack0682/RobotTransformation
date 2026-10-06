# RobotTransformation

RobotTransformation is the product monorepo being prepared for RX: a vendor-neutral resident platform connecting heterogeneous robots, equipment, and services through common task, authority, state, result, and recovery contracts.

**Status: M3 / CI_SCOPE_DECLARED_NOT_YET_RUN.** This change declares the full required CI union. Local staging checks do not establish a successful hosted run. The exact candidate CI run is the evidence for executed checks; product acceptance, shipping-binary identity, and physical qualification remain separate.

The immutable M2 import is audited at signed ancestor `0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0`. Current source is validated by the full Platform/Solutions gate union, same-candidate SDK and installed-skills checks, frozen compatibility tests, current-document integrity, and bounded compiled identity probes.

## Work and contribution

- [Delivery project](https://github.com/users/jack0682/projects/10)
- [Project wiki](https://github.com/jack0682/RobotTransformation/wiki)
- [Contribution workflow](CONTRIBUTING.md)
- [Repository governance](GOVERNANCE.md)
- [Security policy](SECURITY.md)

The new repository starts a signed, signed-off history with no inherited historical DCO exceptions. The imported source provenance is recorded in `provenance/import/M2-source-manifest.json`; its payload digest is pinned independently by the import checker. Original history, tags, signatures, releases, and URLs remain in [rx-platform](https://github.com/jack0682/rx-platform), [rx-solutions](https://github.com/jack0682/rx-solutions), and [rx_docs](https://github.com/jack0682/rx_docs).

Current product direction remains in the pinned [product definition](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/01_product_definition.md) and [core charter](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/43_core_charter.md) until the canonical-document migration gate passes. The wiki is a navigation guide, not a normative source or acceptance record.

The preserved CP2 acceptance failure remains separate from migration work. This bootstrap neither accepts it nor authorizes retry, settlement, resource release, environment changes, or physical operation.

## Validate this CI declaration

Python 3.10 or newer is sufficient for these root fixtures. Full Rust, native, installed-client, and simulation checks run on isolated GitHub-hosted Linux runners:

```sh
python3 -B .github/test_governance.py
python3 -B .github/test_import.py
python3 -B .github/test_full_ci.py
python3 -B .github/test_documents.py
python3 -B tools/governance/check_repository.py
python3 -B tools/migration/check_origin.py
python3 -B rx-platform/tools/check_host_sdk.py rx-solutions/sdk
```

The repository check requires a Git checkout whose origin is this repository. A preparatory file tree can use `--filesystem` for an explicitly uncommitted content check; this is not a commit or signature audit. The fixtures retain G0 refusals and add M2 import/CI negatives; Git index/HEAD fixtures, remote services, and cryptographic verifier results are mocked. Actual commit signatures are verified separately by the full-head audit and GitHub checks.

The validation scope and exact required job set are recorded in [.github/validation-scope.json](.github/validation-scope.json). Missing, failed, cancelled, or skipped jobs cannot yield a successful aggregate. Full-head signing/DCO, the immutable origin, SDK parity, and static identity jobs remain required.

The origin audit reads original Git objects and verifies ancestry; it does not force current product bytes to remain equal to the original import. The source-identity baseline and its evaluator remain pinned while this migration changes governance and documentation rather than the protected Rust/Cargo context.

Current copied-document links are resolved before this gate can merge. Immutable evidence URLs are checked against a pinned index verified from the original source objects; live remote availability is not inferred. Canonical document relocation remains the separate M4 phase.

The compiled probe invokes applicable public identity functions from existing packages in isolated raw candidate source copies. It records inputs, compilation and output identity. Private transport consumers, shipping daemons, the non-Unix validator variant, and physical effects are outside that probe's observation scope. Source-only calculations and previous CI results are not substituted for a current run.

## License

Original project contributions use [Apache License 2.0](LICENSE). Preserve [NOTICE](NOTICE) and all applicable third-party attributions during subsequent imports.
