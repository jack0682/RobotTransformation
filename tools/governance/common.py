"""Shared root and target guards for this repository's governance entrypoints."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "jack0682/RobotTransformation"
WORKFLOW = ".github/workflows/ci.yml"
CHECK_WORKFLOWS = {"CI": WORKFLOW, "M5": ".github/workflows/m5-artifact-candidate.yml"}
CHECK_PROVIDERS = {"CI": 15368, "DCO": 1861, "M5": 15368}
PROTECTED = {"refs/heads/main", "refs/heads/develop"}
WORK_PREFIXES = ("feature", "fix", "docs", "chore", "codex")
PRIVILEGED_PREFIXES = ("release", "hotfix")


def environment():
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                 "GIT_REPLACE_REF_BASE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"):
        # Git normally exports context variables to hooks. Fixed -C ROOT commands
        # must ignore inherited context, rather than rejecting normal hook invocation.
        env.pop(name, None)
    for name in list(env):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(name)
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def run(*command, input=None, cwd=None):
    result = subprocess.run(command, input=input, cwd=cwd or ROOT, env=environment(),
                            text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip()
                         or f"Command failed: {command[0]}")
    return result.stdout


def git(*args, input=None):
    return run("git", "--no-replace-objects", "-C", str(ROOT), *args, input=input)


def valid_oid(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) is not None


def settings():
    value = json.loads((ROOT / "repository-settings.json").read_text())
    if value.get("schema") != "rx.repository-settings.v1" or value.get("repository") != REPOSITORY:
        raise ValueError("Governance target must be exactly " + REPOSITORY)
    if type(value.get("historical_dco_exceptions")) is not int or value["historical_dco_exceptions"] != 0:
        raise ValueError("This new history has zero historical DCO exceptions")
    return value


def target_url(url):
    return url in {f"https://github.com/{REPOSITORY}", f"https://github.com/{REPOSITORY}.git",
                   f"git@github.com:{REPOSITORY}", f"git@github.com:{REPOSITORY}.git",
                   f"ssh://git@github.com/{REPOSITORY}", f"ssh://git@github.com/{REPOSITORY}.git"}


def require_checkout(*, origin=False):
    settings()
    actual = Path(git("rev-parse", "--show-toplevel").strip()).resolve()
    if actual != ROOT.resolve():
        raise ValueError("Run the root governance entrypoint in its own Git root; nested copies are refused")
    if origin:
        for args in (("remote", "get-url", "--all", "origin"),
                     ("remote", "get-url", "--push", "--all", "origin")):
            urls = git(*args).splitlines()
            if len(urls) != 1 or not target_url(urls[0]):
                raise ValueError("origin must have one fetch and one push URL for " + REPOSITORY)


def require_full_history():
    if git("rev-parse", "--is-shallow-repository").strip() != "false":
        raise ValueError("Full-head audit requires an unshallow repository")
    if git("for-each-ref", "--format=%(refname)", "refs/replace/").strip():
        raise ValueError("Git replacement refs are refused")
    grafts = Path(git("rev-parse", "--git-path", "info/grafts").strip())
    if not grafts.is_absolute():
        grafts = ROOT / grafts
    if grafts.exists() and grafts.read_bytes().strip():
        raise ValueError("Git history grafts are refused")


def api(method, path, payload=None):
    prefix = "repos/" + REPOSITORY
    if not (path == prefix or path.startswith(prefix + "/") or (method == "GET" and path == "user")):
        raise ValueError("GitHub API target outside " + REPOSITORY + " is refused")
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError("Unsupported API method")
    command = ["gh", "api", "--hostname", "github.com", "--method", method, path]
    if payload is not None:
        command += ["--input", "-"]
    raw = run(*command, input=json.dumps(payload) if payload is not None else None)
    return json.loads(raw) if raw.strip() else None


def require_remote_identity():
    value = api("GET", "repos/" + REPOSITORY)
    if value.get("full_name") != REPOSITORY or value.get("archived") is not False:
        raise ValueError("Remote repository identity changed or repository is archived")
    return value


def branch_error(event):
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        return "pull_request event payload is missing"
    base, head = pr.get("base", {}), pr.get("head", {})
    if (base.get("repo") or {}).get("full_name") != REPOSITORY:
        return "PR base repository is not " + REPOSITORY
    source, target = head.get("ref", ""), base.get("ref", "")
    same_repo = (head.get("repo") or {}).get("full_name") == REPOSITORY
    if not (head.get("repo") or {}).get("full_name"):
        return "PR head repository is missing"
    named = lambda prefixes: any(source.startswith(prefix + "/") and len(source) > len(prefix) + 1
                                 for prefix in prefixes)
    if target == "develop" and (named(WORK_PREFIXES)
                                or (same_repo and (source == "main" or named(PRIVILEGED_PREFIXES)))):
        return None
    if target == "main" and same_repo and (source == "develop" or named(PRIVILEGED_PREFIXES)):
        return None
    return f"Unsupported GitFlow route {source!r} -> {target!r}"
