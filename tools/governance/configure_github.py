#!/usr/bin/env python3
"""Read-only policy audit by default; --apply changes only the guarded repository."""
from __future__ import annotations

import argparse
import sys

from common import REPOSITORY, api, require_checkout, require_remote_identity, settings


def contains(actual, expected):
    if isinstance(expected, dict):
        # GitHub omits only this false default in update rules.
        if (isinstance(actual, dict) and actual.get("type") == "update"
                and "parameters" not in actual
                and expected.get("parameters") == {"update_allows_fetch_and_merge": False}):
            actual = {**actual, "parameters": {"update_allows_fetch_and_merge": False}}
        return isinstance(actual, dict) and all(k in actual and contains(actual[k], v)
                                                for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        remaining = list(actual)
        for item in expected:
            index = next((i for i, candidate in enumerate(remaining) if contains(candidate, item)), None)
            if index is None:
                return False
            remaining.pop(index)
        return True
    return type(actual) is type(expected) and actual == expected


def configure(apply=False):
    require_checkout(origin=True)
    config = settings()
    require_remote_identity()
    prefix = "repos/" + REPOSITORY
    automatic_fixes = config["dependency_updates"]["automated_security_fixes"]
    if type(automatic_fixes) is not bool:
        raise ValueError("Automatic security fixes must be a boolean")
    for branch in ("main", "develop"):
        if api("GET", f"{prefix}/branches/{branch}").get("name") != branch:
            raise ValueError("Both permanent branches must exist before policy changes")
    existing = api("GET", f"{prefix}/rulesets?per_page=100")
    if not isinstance(existing, list) or len(existing) >= 100:
        raise ValueError("Ruleset inventory is invalid or may be truncated")
    matched = {}
    for expected in config["rulesets"]:
        matches = [r for r in existing if r.get("name") == expected["name"]]
        if len(matches) > 1:
            raise ValueError("Ambiguous ruleset name: " + expected["name"])
        matched[expected["name"]] = matches[0]["id"] if matches else None
    expected_names = {r["name"] for r in config["rulesets"]}
    unmanaged = [r["name"] for r in existing if r.get("name") not in expected_names]
    if unmanaged:
        raise ValueError("Unmanaged rulesets require review; none will be deleted: " + ", ".join(unmanaged))
    if apply:
        api("PATCH", prefix, config["settings"])
        api("PUT", prefix + "/topics", {"names": config["topics"]})
        api("PUT", prefix + "/actions/permissions", config["actions"])
        api("PUT", prefix + "/actions/permissions/workflow", config["workflow_permissions"])
        api("PATCH", prefix, {"security_and_analysis": config["security"]})
        api("PUT", prefix + "/vulnerability-alerts")
        api("PUT" if automatic_fixes else "DELETE", prefix + "/automated-security-fixes")
        for expected in config["rulesets"]:
            rule_id = matched[expected["name"]]
            path = prefix + "/rulesets" + (f"/{rule_id}" if rule_id else "")
            result = api("PUT" if rule_id else "POST", path, expected)
            matched[expected["name"]] = result["id"]
    current = api("GET", prefix)
    if current.get("full_name") != REPOSITORY:
        raise ValueError("Repository identity changed during policy operation")
    observations = [
        ("repository settings", current, config["settings"]),
        ("topics", api("GET", prefix + "/topics")["names"], config["topics"]),
        ("actions", api("GET", prefix + "/actions/permissions"), config["actions"]),
        ("workflow permissions", api("GET", prefix + "/actions/permissions/workflow"), config["workflow_permissions"]),
        ("security", current.get("security_and_analysis", {}), config["security"]),
        ("automatic security fixes", api("GET", prefix + "/automated-security-fixes"), {"enabled": automatic_fixes}),
        ("vulnerability alerts", api("GET", prefix + "/vulnerability-alerts"), None),
    ]
    for expected in config["rulesets"]:
        rule_id = matched[expected["name"]]
        actual = api("GET", f"{prefix}/rulesets/{rule_id}") if rule_id else {}
        observations.append((expected["name"], actual, expected))
    failures = [label for label, actual, expected in observations if not contains(actual, expected)]
    for label in failures:
        print("DRIFT: " + label)
    if not failures:
        print("OK: " + REPOSITORY + ": reviewed settings and rulesets match readback")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply reviewed configuration; default audit is GET-only")
    return int(bool(configure(parser.parse_args().apply)))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"GitHub configuration: {exc}", file=sys.stderr)
        raise SystemExit(1)
