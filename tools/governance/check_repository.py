#!/usr/bin/env python3
"""Validate root governance for G0 or the frozen M2 import; no product runtime claims."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from common import ROOT, branch_error, git, require_checkout, settings
from check_ci import BOOTSTRAP_SCOPE, IMPORT_SCOPE, stage
sys.path.insert(0, str(ROOT / "tools/migration"))
import check_import

ROOT_FILES = {"README.md", "LICENSE", "NOTICE", "CONTRIBUTING.md", "GOVERNANCE.md",
              "SECURITY.md", "CODE_OF_CONDUCT.md", ".gitignore", "repository-settings.json"}
REQUIRED = ROOT_FILES | {".github/workflows/ci.yml", ".github/repository-policy.json",
                        ".github/validation-scope.json", ".github/dco.yml", ".github/CODEOWNERS",
                        ".github/test_governance.py", "tools/governance/common.py",
                        "tools/governance/check_ci.py", "tools/governance/check_commit_policy.py",
                        "tools/governance/check_repository.py", "tools/governance/configure_github.py",
                        "tools/governance/install_git_hooks.py", "tools/governance/merge_pr.py",
                        ".githooks/pre-commit", ".githooks/prepare-commit-msg",
                        ".githooks/commit-msg", ".githooks/pre-push"}
# Retained G0 contract used by the original bootstrap regression fixtures.
SCOPE = BOOTSTRAP_SCOPE
M2_REQUIRED = REQUIRED | {
    ".github/test_import.py", "tools/migration/check_import.py",
    "tools/migration/source_identities.py", "provenance/import/M2-source-manifest.json",
    "provenance/import/M2-source-identities.json",
}

KOREAN = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")


def ai_artifact(path):
    parts = [part.lower() for part in path.parts]
    names = {"agents.md", "agents.override.md", "claude.md", "claude.local.md", "codex.md",
             "gemini.md", "skill.md", ".cursorrules", ".windsurfrules", ".clinerules"}
    dirs = {".claude", ".codex", ".agents", ".cursor", ".windsurf", ".continue", ".roo",
            "my_harness", "harness"}
    return (any(part in dirs for part in parts) or (parts and (parts[-1] in names or parts[-1].startswith(".aider")))
            or any(parts[i:i+2] in [[".github", name]]
                   for i in range(len(parts)-1)
                   for name in ("copilot-instructions.md", "instructions", "prompts", "agents", "chatmodes")))


def allowed(path):
    return path.as_posix() in REQUIRED | {".github/pull_request_template.md"}


def links(root, path):
    text = path.read_text()
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", "", text)
    text = re.sub(r"`[^`\n]+`", "", text)
    targets = re.findall(r"\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)", text)
    targets += re.findall(r"(?m)^\s*\[(?!\^)[^\]\n]+\]:\s*(<[^>]+>|\S+)", text)
    errors = []
    for target in targets:
        value = urlsplit(target.strip("<>"))
        decoded = unquote(value.path)
        if value.scheme == "file" or (not value.scheme and decoded.startswith(("/Users/", "/home/"))):
            errors.append("Machine-specific link: " + target)
        elif value.scheme or value.netloc or not decoded:
            continue
        else:
            resolved = (path.parent / decoded).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                errors.append("Missing or out-of-root local link: " + target)
    return errors


def check_bootstrap(root, files):
    errors = []
    relative = {p.relative_to(root).as_posix() for p in files}
    for name in sorted(REQUIRED - relative):
        errors.append("Missing required scaffold file: " + name)
    for p in files:
        path = p.relative_to(root)
        if ai_artifact(path):
            errors.append("Local assistant/harness artifact must not be published: " + str(path))
        if not allowed(path):
            errors.append("File outside BOOTSTRAP_ONLY allowlist: " + str(path))
        if p.is_symlink() or not p.is_file():
            errors.append("Scaffold entries must be regular files: " + str(path))
            continue
        try:
            text = p.read_text()
            if KOREAN.search(str(path)) or KOREAN.search(text):
                errors.append("G0 source and governance text must be English: " + str(path))
            if p.suffix == ".json":
                json.loads(text)
            if p.suffix == ".md":
                errors.extend(str(path) + ": " + error for error in links(root, p))
        except (UnicodeError, ValueError, OSError) as exc:
            errors.append(f"{path}: {exc}")
    try:
        policy = json.loads((root / ".github/repository-policy.json").read_text())
        if policy != {"schema": "rx.repository-content-policy.v1", "language": "en", "exclude_ai_artifacts": True}:
            errors.append("Unexpected bootstrap content policy")
        if json.dumps(json.loads((root / ".github/validation-scope.json").read_text()), sort_keys=True) != json.dumps(SCOPE, sort_keys=True):
            errors.append("G0 scope must be BOOTSTRAP_ONLY with zero exceptions; scope transitions require a reviewed gate implementation")
        if "Apache License" not in (root / "LICENSE").read_text() or "Version 2.0" not in (root / "LICENSE").read_text():
            errors.append("Apache-2.0 license missing")
        workflow = (root / ".github/workflows/ci.yml").read_text()
        if "pull_request_target" in workflow:
            errors.append("Privileged contributor-code workflow trigger is forbidden")
        for action in re.findall(r"(?m)^\s*- uses:\s*(\S+)", workflow):
            if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action):
                errors.append("Action revision must be a full SHA: " + action)
        for required in ("contents: read", "fetch-depth: 0", "needs: [repository, commit_policy]",
                         "if: ${{ always() }}", "tools/governance/check_ci.py",
                         "tools/governance/check_commit_policy.py --head", "BOOTSTRAP_ONLY"):
            if required not in workflow:
                errors.append("Missing required bootstrap workflow boundary: " + required)
    except (ValueError, OSError) as exc:
        errors.append("Required configuration: " + str(exc))
    return errors


def check_import_stage(root, files):
    errors = []
    try:
        payload = check_import.load_manifest(root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return ["Pinned import manifest: " + str(exc)]
    imported = {row["target_path"] for row in payload["files"]}
    relative = {p.relative_to(root).as_posix() for p in files}
    for missing in sorted((M2_REQUIRED | imported) - relative):
        errors.append("Missing M2 file: " + missing)
    for extra in sorted(relative - M2_REQUIRED - imported - {".github/pull_request_template.md"}):
        errors.append("File outside declared root/import inventory: " + extra)
    for path in files:
        name = path.relative_to(root).as_posix()
        if name in imported:
            # Byte/mode/tree closure is mandatory in import_fidelity for this same candidate.
            # Do not run current-doc link/language normalization on frozen historical source.
            continue
        if ai_artifact(Path(name)):
            errors.append("Local assistant/harness artifact must not be published: " + name)
        if path.is_symlink() or not path.is_file():
            errors.append("Root entries must be regular files: " + name)
            continue
        try:
            text = path.read_text()
            if KOREAN.search(name) or KOREAN.search(text):
                errors.append("Root source and governance text must be English: " + name)
            if path.suffix == ".json":
                json.loads(text)
            if path.suffix == ".md":
                errors.extend(name + ": " + e for e in links(root, path))
        except (UnicodeError, ValueError, OSError) as exc:
            errors.append(f"{name}: {exc}")
    try:
        if json.loads((root / ".github/repository-policy.json").read_text()) != {"schema": "rx.repository-content-policy.v1", "language": "en", "exclude_ai_artifacts": True}:
            errors.append("Unexpected root content policy")
        if "Apache License" not in (root / "LICENSE").read_text() or "Version 2.0" not in (root / "LICENSE").read_text():
            errors.append("Apache-2.0 license missing")
        workflow = (root / ".github/workflows/ci.yml").read_text()
        if "pull_request_target" in workflow:
            errors.append("Privileged contributor-code workflow trigger is forbidden")
        for action in re.findall(r"(?m)^\s*- uses:\s*(\S+)", workflow):
            if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action):
                errors.append("Action revision must be a full SHA: " + action)
        for required in (
            "contents: read", "fetch-depth: 0", "if: ${{ always() }}",
            "needs: [repository, commit_policy, import_fidelity, sdk_parity, static_identity]",
            "tools/governance/check_ci.py", "tools/governance/check_commit_policy.py --head",
            "tools/migration/check_import.py --git", "rx-platform/tools/check_host_sdk.py rx-solutions/sdk",
            "tools/migration/source_identities.py compare --baseline-report provenance/import/M2-source-identities.json",
            "SOURCE_IMPORTED_UNVALIDATED",
        ):
            if required not in workflow:
                errors.append("Missing M2 workflow boundary: " + required)
        if workflow.count("uses: actions/checkout@") != workflow.count("ref: ${{ github.event.pull_request.head.sha || github.sha }}"):
            errors.append("Every M2 checkout must select the exact same candidate revision")
    except (ValueError, OSError) as exc:
        errors.append("Required M2 configuration: " + str(exc))
    return errors


def check(root, files):
    try:
        scope = stage(json.loads((root / ".github/validation-scope.json").read_text()))
    except (ValueError, OSError, TypeError) as exc:
        return ["Validation scope: " + str(exc)]
    return check_bootstrap(root, files) if scope == BOOTSTRAP_SCOPE else check_import_stage(root, files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--filesystem", action="store_true", help="Uncommitted scaffold review only; not a Git or signature audit")
    args = parser.parse_args()
    settings()
    if args.filesystem:
        files = [p for p in ROOT.rglob("*") if (p.is_file() or p.is_symlink())
                 and p.relative_to(ROOT).parts[0] not in {".git", ".g0-validation"}
                 and "__pycache__" not in p.parts]
    else:
        require_checkout(origin=True)
        paths = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
        files = sorted({ROOT / p for p in paths if p})
    errors = check(ROOT, files)
    if args.event:
        error = branch_error(json.loads(args.event.read_text()))
        if error:
            errors.append(error)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    mode = "UNCOMMITTED_SCAFFOLD" if args.filesystem else "GIT_CHECKOUT"
    scope = stage(json.loads((ROOT / ".github/validation-scope.json").read_text()))
    print(f"OK: {mode}; {scope['scope']}; {len(files)} files; root links checked; imported historical links NOT_VALIDATED_UNTIL_M4; product runtime NOT_RUN")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"repository check: {exc}", file=sys.stderr)
        raise SystemExit(1)
