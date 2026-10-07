#!/usr/bin/env python3
"""Merge an exact, checked PR head through GitHub with an explicit DCO trailer."""
import argparse
import json
from pathlib import Path
import subprocess
import os
import re
import sys

from check_commit_policy import has_signoff, run


def require_standalone_repository():
    """Refuse legacy administration from an imported subtree or redirected Git context.

    Kept self-contained so the standalone hook-installation fixture needs no
    new support files. Pure helper imports remain available for unit tests;
    every real API/Git boundary and command-line entry checks this guard.
    """
    expected = "jack0682/rx-solutions"
    context_variables = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS",
        "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_NAMESPACE", "GIT_SUPER_PREFIX",
    }
    if any(name in context_variables or name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
           for name in os.environ):
        raise ValueError("Legacy administration refuses a redirected Git context; use root tools/governance")
    root = Path(__file__).resolve().parents[1]
    marker = root / ".git"
    if (marker.is_symlink() or not (marker.is_dir() or marker.is_file())
            or any((parent / ".git").exists() for parent in root.parents)):
        raise ValueError("Legacy administration requires a standalone repository; use root tools/governance")
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                         env=environment, text=True, capture_output=True)
    if top.returncode or Path(top.stdout.strip()).resolve() != root:
        raise ValueError("Legacy administration requires its own Git root; use root tools/governance")
    identity = json.loads((root / "repository-settings.json").read_text())["repository"]
    if identity != expected:
        raise ValueError("Legacy repository identity does not match this component; use root tools/governance")
    origin = subprocess.run(["git", "-C", str(root), "config", "--local", "--get", "remote.origin.url"],
                            env=environment, text=True, capture_output=True)
    if origin.returncode not in (0, 1):
        raise ValueError("Cannot verify the standalone repository origin")
    if origin.returncode == 0:
        remote = origin.stdout.strip().rstrip("/").removesuffix(".git")
        remote = remote.replace("git@github.com:", "https://github.com/", 1)
        remote = remote.replace("ssh://git@github.com/", "https://github.com/", 1)
        if remote.casefold() != ("https://github.com/" + expected).casefold():
            raise ValueError("Standalone origin does not match this component; use root tools/governance")
    # Subsequent legacy Git reads inherit the same optional-lock discipline.
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"


def api(path, payload=None):
    require_standalone_repository()
    command = ["gh", "api", path]
    if payload is not None:
        command += ["--method", "PUT", "--input", "-"]
    return json.loads(run(*command, input=json.dumps(payload) if payload is not None else None))


def require_checks(repository, number, head):
    checks = api(f"repos/{repository}/commits/{head}/check-runs?filter=latest&per_page=100")
    if checks["total_count"] > 100:
        raise ValueError("More than 100 checks; inspect the PR on GitHub before merging")
    for name, application in (("CI", 15368), ("DCO", 1861)):
        matches = [check for check in checks["check_runs"]
                   if check["name"] == name and check.get("app", {}).get("id") == application]
        latest = max(matches, key=lambda check: check["id"], default={})
        if (latest.get("head_sha") != head or latest.get("status") != "completed"
                or latest.get("conclusion") != "success"):
            raise ValueError(f"{name} from application {application} must succeed for {head}")
        if name == "CI":
            match = re.fullmatch(r"https://github\.com/" + re.escape(repository)
                                 + r"/actions/runs/(\d+)/job/\d+", latest.get("details_url", ""))
            if not match:
                raise ValueError("CI does not identify a GitHub Actions run in this repository")
            workflow = api(f"repos/{repository}/actions/runs/{match[1]}")
            if (workflow.get("event") != "pull_request" or workflow.get("head_sha") != head
                    or workflow.get("path") != ".github/workflows/ci.yml"
                    or not any(pr.get("number") == number for pr in workflow.get("pull_requests", []))):
                raise ValueError("CI must belong to this PR, exact head and repository workflow")


def require_ready_pr(pr):
    # The PR-only update ruleset can report "blocked" even for its permitted
    # PR actor. Exact checks are required separately; GitHub makes the final
    # authorization decision without bypassing the quality ruleset.
    if (pr["state"] != "open" or pr["draft"] or pr["base"]["ref"] not in ("main", "develop")
            or pr.get("mergeable") is not True
            or pr.get("mergeable_state") not in ("clean", "blocked")):
        raise ValueError("PR must be open, ready, conflict-free and current with its base")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", type=int)
    parser.add_argument("--signoff", help="Your GitHub web commit Name <email>; defaults to your no-reply identity")
    args = parser.parse_args()
    repository = json.loads((Path(__file__).resolve().parents[1] / "repository-settings.json").read_text())["repository"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or args.number < 1:
        raise ValueError("Invalid repository or PR number")
    prefix = f"repos/{repository}"
    pr = api(f"{prefix}/pulls/{args.number}")
    require_ready_pr(pr)
    head = pr["head"]["sha"]
    require_checks(repository, args.number, head)
    actor = api("user")
    signoff = args.signoff or f"{actor['name'] or actor['login']} <{actor['id']}+{actor['login']}@users.noreply.github.com>"
    if not re.fullmatch(r"[^<>\r\n]+ <[^<>\s]+>", signoff):
        raise ValueError("Sign-off must be your GitHub web commit Name <email>")
    current = api(f"{prefix}/pulls/{args.number}")
    require_ready_pr(current)
    if (current["head"]["sha"] != head or current["base"]["ref"] != pr["base"]["ref"]
            or current["base"]["sha"] != pr["base"]["sha"]):
        raise ValueError("PR head or base changed during verification; rerun after checks finish")
    # GitHub checks the SHA atomically and enforces the live rules. This endpoint
    # has no administrator override. Strict required checks cover a later base
    # race. Merge commits preserve GitFlow ancestry.
    result = api(f"{prefix}/pulls/{args.number}/merge", {
        "sha": head, "merge_method": "merge",
        "commit_title": f"Merge pull request #{args.number}: {pr['title']}",
        "commit_message": f"Signed-off-by: {signoff}\n",
    })
    if result.get("merged") is not True:
        raise ValueError(f"GitHub did not merge the PR: {result.get('message')}")
    commit = api(f"{prefix}/commits/{result['sha']}")["commit"]
    verification = commit.get("verification", {})
    author = f"{commit['author']['name']} <{commit['author']['email']}>"
    if (verification.get("verified") is not True
            or not (verification.get("signature") or "").startswith("-----BEGIN PGP SIGNATURE-----")
            or not has_signoff(commit["message"], author)):
        raise ValueError(f"PR merged as {result['sha']}, but post-merge signature/DCO verification failed; inspect immediately")
    print(f"Merged {repository}#{args.number}: {result['sha']} (verified OpenPGP and author DCO)")
    return 0


if __name__ == "__main__":
    try:
        require_standalone_repository()
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"PR merge: {exc}", file=sys.stderr)
        raise SystemExit(1)
