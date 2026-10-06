# RobotTransformation

RobotTransformation is the product monorepo being prepared for RX: a vendor-neutral resident platform connecting heterogeneous robots, equipment, and services through common task, authority, state, result, and recovery contracts.

**Status: G0 / BOOTSTRAP_ONLY.** This scaffold contains repository governance and its tests. Product source has not been imported. A successful G0 CI result does not establish contract implementation, SDK compatibility, runtime behavior, deployment readiness, physical completion, or functional safety.

## Work and contribution

- [Delivery project](https://github.com/users/jack0682/projects/10)
- [Project wiki](https://github.com/jack0682/RobotTransformation/wiki)
- [Contribution workflow](CONTRIBUTING.md)
- [Repository governance](GOVERNANCE.md)
- [Security policy](SECURITY.md)

The new repository starts a signed, signed-off history with no inherited historical DCO exceptions. Approved source snapshots will be imported with immutable provenance in a separate reviewed change. Original history, tags, signatures, releases, and URLs remain in [rx-platform](https://github.com/jack0682/rx-platform), [rx-solutions](https://github.com/jack0682/rx-solutions), and [rx_docs](https://github.com/jack0682/rx_docs).

Current product direction remains in the pinned [product definition](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/01_product_definition.md) and [core charter](https://github.com/jack0682/rx_docs/blob/4384ed49e384c53e645f71757ce597292b928eb6/docs/43_core_charter.md) until the canonical-document migration gate passes. The wiki is a navigation guide, not a normative source or acceptance record.

The preserved CP2 acceptance failure remains separate from migration work. This bootstrap neither accepts it nor authorizes retry, settlement, resource release, environment changes, or physical operation.

## Validate this scaffold

Python 3.10 or newer is sufficient for the local governance fixtures:

```sh
python3 -B .github/test_governance.py
python3 -B tools/governance/check_repository.py
```

The repository check requires a Git checkout whose origin is this repository. A preparatory file tree can use `--filesystem` for an explicitly uncommitted content check; this is not a commit or signature audit. The fixture suite mocks remote services and cryptographic verifier results. Actual commit signatures are verified separately by the full-head audit and GitHub checks.

The validation scope is recorded in [.github/validation-scope.json](.github/validation-scope.json). Import and unified product CI must arrive with their own required integrity and verification gates. G0 is not a route for bypassing those gates.

## License

Original project contributions use [Apache License 2.0](LICENSE). Preserve [NOTICE](NOTICE) and all applicable third-party attributions during subsequent imports.
