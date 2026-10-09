#!/usr/bin/env python3
"""Require the exact job set for the declared validation stage; no implied runtime success."""
import json
import os
import sys

from common import ROOT

BOOTSTRAP_SCOPE = {'schema': 'rx.validation-scope.v1', 'scope': 'BOOTSTRAP_ONLY', 'product_source_imported': False, 'product_validation': 'NOT_RUN', 'historical_dco_exceptions': 0, 'required_jobs': ['repository', 'commit_policy']}
IMPORT_SCOPE = {'schema': 'rx.validation-scope.v1', 'scope': 'SOURCE_IMPORTED_UNVALIDATED', 'product_source_imported': True, 'product_validation': 'NOT_RUN', 'historical_dco_exceptions': 0, 'required_jobs': ['repository', 'commit_policy', 'import_fidelity', 'sdk_parity', 'static_identity'], 'import_manifest': 'provenance/import/M2-source-manifest.json', 'import_payload_sha256': 'c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc'}

FULL_SCOPE = {'schema': 'rx.validation-scope.v1', 'scope': 'CI_SCOPE_DECLARED_NOT_YET_RUN', 'product_source_imported': True, 'product_validation': 'SEE_EXACT_CI_RUN_EVIDENCE', 'historical_dco_exceptions': 0, 'required_jobs': ['repository', 'commit_policy', 'import_fidelity', 'sdk_parity', 'static_identity', 'platform_repository', 'solutions_repository', 'document_integrity', 'platform_rust', 'solutions_rust', 'clients', 'operator', 'operator_browser', 'sim_image', 'sim_scenarios', 'dynamixel', 'skills', 'skills_compatibility', 'compiled_identity'], 'import_origin_commit': '0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0', 'import_manifest': 'provenance/import/M2-source-manifest.json', 'import_payload_sha256': 'c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc'}

def stage(scope):
    for expected in (BOOTSTRAP_SCOPE, IMPORT_SCOPE, FULL_SCOPE):
        if json.dumps(scope, sort_keys=True) == json.dumps(expected, sort_keys=True):
            return expected
    raise ValueError("Unimplemented or altered validation scope")


def check(results, scope):
    expected = stage(scope)["required_jobs"]
    if not isinstance(results, dict) or set(results) != set(expected):
        raise ValueError("Required job inventory differs from the declared stage")
    failed = {name: result.get("result") if isinstance(result, dict) else "invalid"
              for name, result in results.items()
              if not isinstance(result, dict) or result.get("result") != "success"}
    if failed:
        raise ValueError("Required validation jobs did not pass: " + json.dumps(failed, sort_keys=True))


def main():
    scope = json.loads((ROOT / ".github/validation-scope.json").read_text())
    check(json.loads(os.environ["NEEDS"]), scope)
    print(scope["scope"] + ": every declared required job passed in this run; acceptance and physical qualification are separate")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"CI aggregate: {exc}", file=sys.stderr)
        raise SystemExit(1)
