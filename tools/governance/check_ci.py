#!/usr/bin/env python3
"""Fail closed for every required child job; G0 success has BOOTSTRAP_ONLY scope."""
import json
import os
import sys

from common import ROOT


def check(results, scope):
    expected = scope.get("required_jobs")
    if (scope.get("scope") != "BOOTSTRAP_ONLY" or expected != ["repository", "commit_policy"]
            or not isinstance(results, dict) or set(results) != set(expected)):
        raise ValueError("Required job inventory or validation scope changed")
    failed = {name: result.get("result") if isinstance(result, dict) else "invalid" for name, result in results.items()
              if not isinstance(result, dict) or result.get("result") != "success"}
    if failed:
        raise ValueError("Required validation jobs did not pass: " + json.dumps(failed, sort_keys=True))


def main():
    check(json.loads(os.environ["NEEDS"]), json.loads((ROOT / ".github/validation-scope.json").read_text()))
    print("BOOTSTRAP_ONLY: governance checks passed; product validation NOT_RUN")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"CI aggregate: {exc}", file=sys.stderr)
        raise SystemExit(1)
