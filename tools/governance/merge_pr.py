#!/usr/bin/env python3
"""Merge one current, checked PR by exact head; no administrator bypass or arbitrary signoff."""
from __future__ import annotations

import argparse
import re
import sys

from common import (CHECK_PROVIDERS, REPOSITORY, WORKFLOW, api, branch_error,
                    require_checkout, require_remote_identity, valid_oid)
from check_commit_policy import has_signoff
from configure_github import configure


def require_checks(number, head, base):
    if not valid_oid(head):
        raise ValueError("Exact PR head required")
    record = api("GET", f"repos/{REPOSITORY}/commits/{head}/check-runs?filter=latest&per_page=100")
    if record.get("total_count", 101) > 100:
        raise ValueError("Check inventory may be truncated; inspect before merging")
    for name, application in CHECK_PROVIDERS.items():
        matches = [c for c in record.get("check_runs", [])
                   if c.get("name") == name and c.get("app", {}).get("id") == application]
        latest = max(matches, key=lambda c: c.get("id", -1), default={})
        if (latest.get("head_sha") != head or latest.get("status") != "completed"
                or latest.get("conclusion") != "success"):
            raise ValueError(f"{name} from app {application} must succeed for the exact head")
        if name == "CI":
            match = re.fullmatch(r"https://github\.com/" + re.escape(REPOSITORY)
                                 + r"/actions/runs/(\d+)/job/\d+", latest.get("details_url", ""))
            if not match:
                raise ValueError("CI must identify this repository's GitHub Actions run")
            workflow = api("GET", f"repos/{REPOSITORY}/actions/runs/{match[1]}")
            if (workflow.get("event") != "pull_request" or workflow.get("head_sha") != head
                    or workflow.get("path") != WORKFLOW
                    or workflow.get("status") != "completed" or workflow.get("conclusion") != "success"
                    or workflow.get("repository", {}).get("full_name") != REPOSITORY
                    or not any(pr.get("number") == number
                               and pr.get("head", {}).get("sha") == head
                               and pr.get("base", {}).get("sha") == base["sha"]
                               and pr.get("base", {}).get("ref") == base["ref"]
                               for pr in workflow.get("pull_requests", []))):
                raise ValueError("CI must be a successful completed run for this PR, exact head and workflow")


def require_ready_pr(pr):
    error = branch_error({"pull_request": pr})
    if error:
        raise ValueError(error)
    if (pr.get("state") != "open" or pr.get("draft") is not False
            or pr.get("mergeable") is not True
            or pr.get("mergeable_state") not in ("clean", "blocked")
            or not valid_oid(pr.get("head", {}).get("sha"))
            or not valid_oid(pr.get("base", {}).get("sha"))):
        raise ValueError("PR must be open, ready, conflict-free and current with its base")


def actor_signoff(actor):
    login, name, actor_id = actor.get("login"), actor.get("name") or actor.get("login"), actor.get("id")
    if (not isinstance(login, str) or not re.fullmatch(r"[A-Za-z0-9-]+", login)
            or type(actor_id) is not int or actor_id < 1 or not isinstance(name, str)
            or any(c in name for c in "<>\r\n") or not name.strip()):
        raise ValueError("Invalid authenticated GitHub author identity")
    return f"{name} <{actor_id}+{login}@users.noreply.github.com>"


def merge(number):
    if type(number) is not int or number < 1:
        raise ValueError("Positive PR number required")
    require_checkout(origin=True)
    require_remote_identity()
    # Do not rely only on checked-in strict-check settings at this irreversible boundary.
    if configure(apply=False):
        raise ValueError("Remote policy drift prevents merge")
    prefix = "repos/" + REPOSITORY
    pr = api("GET", f"{prefix}/pulls/{number}")
    require_ready_pr(pr)
    head = pr["head"]["sha"]
    require_checks(number, head, pr["base"])
    signoff = actor_signoff(api("GET", "user"))
    current = api("GET", f"{prefix}/pulls/{number}")
    require_ready_pr(current)
    if (current["head"]["sha"] != head or current["base"]["sha"] != pr["base"]["sha"]
            or current["base"]["ref"] != pr["base"]["ref"]
            or current["head"]["ref"] != pr["head"]["ref"]
            or current["head"]["repo"]["full_name"] != pr["head"]["repo"]["full_name"]):
        raise ValueError("PR head or base changed during verification; no merge requested")
    result = api("PUT", f"{prefix}/pulls/{number}/merge", {
        "sha": head, "merge_method": "merge",
        "commit_title": f"Merge pull request #{number}: {pr['title']}",
        "commit_message": f"Signed-off-by: {signoff}\n",
    })
    if result.get("merged") is not True or not valid_oid(result.get("sha")):
        raise ValueError("GitHub did not confirm a merge; inspect the original PR before retrying")
    commit_record = api("GET", f"{prefix}/commits/{result['sha']}")
    commit = commit_record.get("commit", {})
    verification = commit.get("verification", {})
    author = f"{commit.get('author', {}).get('name')} <{commit.get('author', {}).get('email')}>"
    if (commit_record.get("sha") != result["sha"] or verification.get("verified") is not True
            or not (verification.get("signature") or "").startswith("-----BEGIN PGP SIGNATURE-----")
            or not has_signoff(commit.get("message", ""), author)):
        raise ValueError(f"MERGED_BUT_VERIFICATION_FAILED: {result['sha']}; preserve and investigate")
    print(f"Merged {REPOSITORY}#{number}: {result['sha']} (verified OpenPGP and author DCO)")
    return result["sha"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", type=int)
    merge(parser.parse_args().number)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"PR merge: {exc}", file=sys.stderr)
        raise SystemExit(1)
