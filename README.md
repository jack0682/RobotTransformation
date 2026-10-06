# RobotTransformation

RobotTransformation is the product monorepo being prepared for RX: a vendor-neutral resident platform connecting heterogeneous robots, equipment, and services through common task, authority, state, result, and recovery contracts.

**Status: M2 / SOURCE_IMPORTED_UNVALIDATED.** Frozen source snapshots are imported under their original component layouts. Required checks cover source bytes, Git modes and tree identities, SDK producer parity, named static identities, and repository governance. Product builds, runtime conformance, qualification, deployment readiness, physical completion, and functional safety are **NOT_RUN** at this stage.

## Work and contribution

- [Delivery project](https://github.com/users/jack0682/projects/10)
- [Project wiki](https://github.com/jack0682/RobotTransformation/wiki)
- [Contribution workflow](CONTRIBUTING.md)
- [Repository governance](GOVERNANCE.md)
- [Security policy](SECURITY.md)

The new repository starts a signed, signed-off history with no inherited historical DCO exceptions. The imported source provenance is recorded in `provenance/import/M2-source-manifest.json`; its payload digest is pinned independently by the import checker. Original history, tags, signatures, releases, and URLs remain in [rx-platform](https://github.com/jack0682/rx-platform), [rx-solutions](https://github.com/jack0682/rx-solutions), and [rx_docs](https://github.com/jack0682/rx_docs).

Current product direction remains in the pinned [product definition](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/01_product_definition.md) and [core charter](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/43_core_charter.md) until the canonical-document migration gate passes. The wiki is a navigation guide, not a normative source or acceptance record.

The preserved CP2 acceptance failure remains separate from migration work. This bootstrap neither accepts it nor authorizes retry, settlement, resource release, environment changes, or physical operation.

## Validate this import stage

Python 3.10 or newer is sufficient for these static checks. No original source checkout or old-repository network access is needed:

```sh
python3 -B .github/test_governance.py
python3 -B .github/test_import.py
python3 -B tools/governance/check_repository.py
python3 -B tools/migration/check_import.py --git
python3 -B rx-platform/tools/check_host_sdk.py rx-solutions/sdk
```

The repository check requires a Git checkout whose origin is this repository. A preparatory file tree can use `--filesystem` for an explicitly uncommitted content check; this is not a commit or signature audit. The fixtures retain G0 refusals and add M2 import/CI negatives; Git index/HEAD fixtures, remote services, and cryptographic verifier results are mocked. Actual commit signatures are verified separately by the full-head audit and GitHub checks.

The validation scope is recorded in [.github/validation-scope.json](.github/validation-scope.json). The required aggregate includes governance, full-head DCO/signatures, import fidelity, same-candidate SDK parity, and static identity comparison. The source identity baseline is `provenance/import/M2-source-identities.json`; its checker refuses a different baseline hash. A source-derived identity result does not establish the identity of a compiled binary.

Only first-party root-document links are checked here. Frozen imported documents keep their original bytes; their historical relative evidence links are not declared resolved before M4. Current-document normalization is not part of M2.

M3 must add the full union of product checks through a reviewed scope transition. At that transition, immutable import fidelity is anchored to the recorded M2 import commit; it must not permanently prohibit legitimate later source changes or be weakened by regenerating the frozen manifest from a changed tree. See [governance](GOVERNANCE.md).

## License

Original project contributions use [Apache License 2.0](LICENSE). Preserve [NOTICE](NOTICE) and all applicable third-party attributions during subsequent imports.
