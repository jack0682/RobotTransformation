#!/usr/bin/env python3
"""Audit every ancestor for truthful author DCO and verified OpenPGP; no exceptions."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from common import (PROTECTED, REPOSITORY, WORKFLOW, PRIVILEGED_PREFIXES, WORK_PREFIXES, api, git,
                    require_checkout, require_full_history, target_url, valid_oid)


def identity(kind):
    value = git("var", f"GIT_{kind}_IDENT").strip()
    match = re.fullmatch(r"(.+ <[^<>\s]+>) \d+ [+-]\d{4}", value)
    if not match:
        raise ValueError("Invalid Git identity")
    return match[1]


def has_signoff(message, author):
    trailers = git("interpret-trailers", "--parse", input=message)
    return any(line.partition(":")[0].lower() == "signed-off-by"
               and line.partition(":")[2].strip().casefold() == author.casefold()
               for line in trailers.splitlines())


def prepare_message(path):
    committer = identity("COMMITTER")
    if not has_signoff(Path(path).read_text(), committer):
        git("interpret-trailers", "--in-place", "--trailer", f"Signed-off-by: {committer}", path)


def check_message(path):
    if not has_signoff(Path(path).read_text(), identity("AUTHOR")):
        raise ValueError("Missing author-matching Signed-off-by trailer")


def check_signing_config():
    if git("config", "--get", "commit.gpgsign").strip().lower() != "true":
        raise ValueError("Enable commit.gpgsign with the root hook installer")
    if git("config", "--get", "gpg.format").strip() != "openpgp":
        raise ValueError("OpenPGP signing is required")
    if not git("config", "--get", "user.signingkey").strip():
        raise ValueError("Configure an existing OpenPGP signing key locally")


def check_commit(sha, github_repository=None):
    if not valid_oid(sha):
        raise ValueError("Full commit object ID required")
    if github_repository is not None and github_repository != REPOSITORY:
        raise ValueError("Signature repository must be " + REPOSITORY)
    author, message = git("show", "-s", "--format=%an <%ae>%x00%B", sha).split("\0", 1)
    if not has_signoff(message, author):
        raise ValueError(f"{sha}: missing author Signed-off-by: {author}; no historical exception")
    if github_repository:
        record = api("GET", f"repos/{REPOSITORY}/commits/{sha}")
        verification = record.get("commit", {}).get("verification", {})
        if record.get("sha") != sha or verification.get("verified") is not True:
            raise ValueError(f"{sha}: GitHub signature verification failed")
        if not (verification.get("signature") or "").startswith("-----BEGIN PGP SIGNATURE-----"):
            raise ValueError(f"{sha}: verified OpenPGP signature required")
    else:
        headers = git("cat-file", "commit", sha).split("\n\n", 1)[0]
        if "\ngpgsig -----BEGIN PGP SIGNATURE-----\n" not in "\n" + headers:
            raise ValueError(f"{sha}: OpenPGP commit signature required")
        git("-c", "gpg.format=openpgp", "verify-commit", sha)


def audit_head(head, github_repository=None):
    if not head or head.startswith("-"):
        raise ValueError("One explicit commit-ish is required")
    require_full_history()
    revision = git("rev-parse", "--verify", "--end-of-options", head + "^{commit}").strip()
    if not valid_oid(revision):
        raise ValueError("Head did not resolve to one full commit ID")
    commits = git("rev-list", "--end-of-options", revision, "--").splitlines()
    if not commits or revision not in commits:
        raise ValueError("Empty or inconsistent full-head history")
    for sha in commits:
        check_commit(sha, github_repository)
    return revision, len(commits)


def require_release_candidate(sha):
    """Read-only release gate: never create a tag or infer readiness from PR CI."""
    if not valid_oid(sha):
        raise ValueError("Release candidate must be a full commit ID")
    prefix = f"repos/{REPOSITORY}"

    def main_head():
        return api("GET", prefix + "/git/ref/heads/main").get("object", {}).get("sha")

    if main_head() != sha:
        raise ValueError("Release candidate must equal current remote main")
    record = api("GET", prefix + f"/actions/workflows/ci.yml/runs?branch=main&event=push&head_sha={sha}&per_page=100")
    runs = record.get("workflow_runs")
    count = record.get("total_count")
    if (not isinstance(runs, list) or type(count) is not int
            or count != len(runs) or not 1 <= count <= 100):
        raise ValueError("Main CI inventory is missing or truncated")
    if any(type(run.get("id")) is not int for run in runs):
        raise ValueError("Main CI run identity is invalid")
    latest = max(runs, key=lambda run: run["id"])
    # Re-read: a rerun can have invalidated an earlier successful attempt.
    current = api("GET", prefix + f"/actions/runs/{latest['id']}")
    if (current.get("id") != latest["id"] or current.get("head_sha") != sha
            or current.get("head_branch") != "main" or current.get("event") != "push"
            or current.get("path") != WORKFLOW
            or current.get("repository", {}).get("full_name") != REPOSITORY
            or current.get("status") != "completed" or current.get("conclusion") != "success"):
        raise ValueError("Latest push CI on this exact main commit must complete successfully")
    if main_head() != sha:
        raise ValueError("Remote main changed during release verification")
    print(f"Release candidate {sha}: main push CI {current['id']} passed; no tag or release created")
    return current["id"]


def pre_push(lines, remote_name, remote_url):
    if remote_name != "origin" or not target_url(remote_url):
        raise ValueError("Push destination must be the guarded origin repository")
    require_full_history()
    updates = []
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            raise ValueError("Invalid pre-push input")
        _, new, remote_ref, old = fields
        if remote_ref in PROTECTED:
            raise ValueError("Direct protected-branch updates or deletion are forbidden")
        if not valid_oid(new) or not valid_oid(old):
            raise ValueError("Invalid push object ID")
        if remote_ref.startswith("refs/tags/"):
            if set(old) != {"0"}:
                raise ValueError("Existing tags are immutable")
        elif remote_ref.startswith("refs/heads/"):
            name = remote_ref.removeprefix("refs/heads/")
            if not any(name.startswith(p + "/") and len(name) > len(p) + 1
                       for p in WORK_PREFIXES + PRIVILEGED_PREFIXES):
                raise ValueError("Unsupported branch name")
        else:
            raise ValueError("Unsupported public reference")
        updates.append((new, remote_ref))
    checked = set()
    for new, remote_ref in updates:
        if set(new) == {"0"}:
            continue
        if remote_ref.startswith("refs/tags/"):
            if git("cat-file", "-t", new).strip() != "tag":
                raise ValueError("Annotated signed tag required")
            if "-----BEGIN PGP SIGNATURE-----" not in git("cat-file", "tag", new):
                raise ValueError("OpenPGP tag signature required")
            git("-c", "gpg.format=openpgp", "verify-tag", new)
            commit = git("rev-parse", "--verify", new + "^{commit}").strip()
            require_release_candidate(commit)
        for sha in git("rev-list", new, "--not", "--remotes").splitlines():
            if sha not in checked:
                check_commit(sha)
                checked.add(sha)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--head", help="Audit the complete ancestry of this head")
    modes.add_argument("--prepare-message")
    modes.add_argument("--check-message")
    modes.add_argument("--check-config", action="store_true")
    modes.add_argument("--pre-push", action="store_true")
    modes.add_argument("--release-candidate", help="Check exact remote main and its latest push CI; no writes")
    parser.add_argument("--github-repository", choices=[REPOSITORY])
    parser.add_argument("--remote-name")
    parser.add_argument("--remote-url")
    args = parser.parse_args()
    require_checkout(origin=True)
    if args.prepare_message:
        prepare_message(args.prepare_message)
    elif args.check_message:
        check_message(args.check_message)
    elif args.check_config:
        check_signing_config()
    elif args.pre_push:
        pre_push(sys.stdin, args.remote_name, args.remote_url)
    elif args.release_candidate:
        require_release_candidate(args.release_candidate)
    else:
        revision, count = audit_head(args.head, args.github_repository)
        print(f"OK: {revision}: {count} ancestors; author DCO and OpenPGP verified; exceptions=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"commit policy: {exc}", file=sys.stderr)
        raise SystemExit(1)
