#!/usr/bin/env python3
"""Validate stage-specific root ownership, source governance and canonical documentation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from common import ROOT, branch_error, git, require_checkout, settings
from check_ci import BOOTSTRAP_SCOPE, IMPORT_SCOPE, FULL_SCOPE, stage
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


SOURCE_COMPONENTS = ("rx-platform", "rx-solutions")
FULL_CONTENT_POLICY = {'schema': 'rx.repository-content-policy.v2', 'language': 'en', 'canonical_document_language': 'preserve-source', 'canonical_document_inventory': '.github/root-file-inventory.json#canonical_documents', 'exclude_ai_artifacts': True}


def root_inventory(root):
    value = json.loads((root / ".github/root-file-inventory.json").read_text())
    if (value.get("schema") != "rx.current-root-file-inventory.v2"
            or set(value) != {"schema", "scope", "files", "canonical_documents"}
            or not isinstance(value.get("files"), list)
            or not isinstance(value.get("canonical_documents"), list)):
        raise ValueError("Invalid typed root file inventory")
    check_import.path_set(value["files"])
    check_import.path_set(value["canonical_documents"])
    files, documents = set(value["files"]), set(value["canonical_documents"])
    if any(name.split("/")[0] in check_import.PREFIXES for name in files):
        raise ValueError("Component source must not masquerade as root governance")
    expected = {name for name in files if name.split("/")[0] in {"docs", "contracts", "references"}}
    if documents != expected:
        raise ValueError("Canonical document ownership differs from exact root inventory")
    if any(Path(name).suffix not in {".md", ".json"} for name in documents):
        raise ValueError("Canonical language scope admits only declared Markdown and JSON documents")
    return files


def canonical_documents(root):
    # root_inventory validates the exact typed set before this accessor is used.
    return set(json.loads((root / ".github/root-file-inventory.json").read_text())["canonical_documents"])


def job_env_runner_errors(workflow):
    """Reject runner references at job.env in the repository's block-style workflow.

    GitHub allows runner in step.env/with/run, but not jobs.<job_id>.env.
    This focused regression guard is not a complete GitHub expression validator.
    """
    errors = []
    body = workflow.partition("jobs:\n")[2]
    for match in re.finditer(r"(?ms)^  ([A-Za-z_][A-Za-z0-9_-]*):\n(.*?)(?=^  [A-Za-z_][A-Za-z0-9_-]*:|\Z)", body):
        job, block = match.groups()
        for env in re.finditer(r"(?ms)^    [\"']?env[\"']?:\s*\n(.*?)(?=^    \S|\Z)", block):
            for expression in re.findall(r"\$\{\{(.*?)\}\}", env.group(1), re.DOTALL):
                if re.search(r"\brunner\s*(?:\.|\[)", expression):
                    errors.append("runner context is unavailable in jobs." + job + ".env; use step.env")
    return errors


def check_full_ci_stage(root, files):
    errors = []
    try:
        required = root_inventory(root)
        check_import.load_manifest(root)
        document_names = canonical_documents(root)
        sys.path.insert(0, str(root / "tools/docs"))
        import check_canonical_layout
        import check_documents
        check_canonical_layout.check(root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return ["Root/import declaration: " + str(exc)]
    if json.loads((root / ".github/repository-policy.json").read_text()) != FULL_CONTENT_POLICY:
        errors.append("Unexpected root content policy")
    if "Apache License" not in (root / "LICENSE").read_text() or "Version 2.0" not in (root / "LICENSE").read_text():
        errors.append("Apache-2.0 license missing")
    relative = {p.relative_to(root).as_posix() for p in files}
    actual_root = {name for name in relative if name.split("/")[0] not in SOURCE_COMPONENTS}
    for missing in sorted(required - actual_root): errors.append("Missing declared root file: " + missing)
    for extra in sorted(actual_root - required): errors.append("Undeclared root file: " + extra)
    for prefix in SOURCE_COMPONENTS:
        if not any(name.startswith(prefix + "/") for name in relative): errors.append("Missing source component: " + prefix)
    for path in files:
        name = path.relative_to(root).as_posix()
        if ai_artifact(Path(name)): errors.append("Local assistant/harness artifact must not be published: " + name)
        if path.is_symlink() or not path.is_file():
            errors.append("Source entries must be regular files: " + name); continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            if name in actual_root: errors.append("Root governance must be UTF-8 text: " + name)
            continue
        if name not in document_names and (KOREAN.search(name) or KOREAN.search(text)):
            errors.append("Code and governance text must be English: " + name)
        try:
            if path.suffix == ".json":
                check_documents.decode(text) if name in document_names else json.loads(text)
            if name in document_names and path.suffix == ".md":
                check_documents.check_local_links(root, name, text)
            elif name in actual_root and path.suffix == ".md":
                errors.extend(name + ": " + e for e in links(root, path))
        except (ValueError, OSError) as exc: errors.append(f"{name}: {exc}")
    workflow = (root / ".github/workflows/ci.yml").read_text()
    errors.extend(job_env_runner_errors(workflow))
    if "pull_request_target" in workflow or re.search(r"(?m)^\s*(?:-\s*)?[\"']?continue-on-error[\"']?\s*:", workflow):
        errors.append("Privileged trigger or tolerated child failure is forbidden")
    for action in re.findall(r"(?m)^\s*- uses:\s*(\S+)", workflow):
        if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action): errors.append("Action must be SHA-pinned: " + action)
    expected_needs = "needs: [" + ", ".join(FULL_SCOPE["required_jobs"]) + "]"
    for token in (expected_needs, "if: ${{ always() }}", "contents: read", "CARGO_BUILD_JOBS: '2'",
                  "tools/migration/check_origin.py", "tools/governance/check_ci.py",
                  "tools/docs/check_documents.py --run-tables", "python3 -B .github/test_documents.py",
                  "python3 -B .github/test_canonical_layout.py", "python3 -B .github/test_canonical_root.py",
                  "python3 -B .github/test_root_signing.py",
                  "source/rx-solutions/apps/operator/package-lock.json", "path: compat-platform",
                  "ref: e08fd1a45e2782d10f222d00ef1962a675463609"):
        if token not in workflow: errors.append("Missing M3 workflow boundary: " + token)
    # The only conditional steps are PR routing and diagnostic artifact upload.
    allowed_conditions = {"${{ always() }}", "always()", "github.event_name == 'pull_request'"}
    for line in workflow.splitlines():
        condition = re.match(r"^\s*(?:-\s*)?[\"']?if[\"']?\s*:\s*(.+)$", line)
        if condition and condition.group(1).strip() not in allowed_conditions:
            errors.append("Unapproved workflow condition can skip a required check")
    for job in ("skills", "skills_compatibility"):
        match = re.search(r"(?ms)^  " + job + r":\n(.*?)(?=^  [a-z_]+:|\Z)", workflow)
        if not match or match.group(1).count("arch: amd64") != 1 or match.group(1).count("arch: arm64") != 1:
            errors.append("Installed-skills matrix must retain amd64 and arm64: " + job)
    job_names = set(re.findall(r"(?m)^  ([a-z_]+):$", workflow[workflow.index("jobs:"):]))
    if job_names != set(FULL_SCOPE["required_jobs"]) | {"ci"}: errors.append("Workflow job set differs from declaration")
    candidate_checkouts = workflow.count("ref: ${{ github.event.pull_request.head.sha || github.sha }}")
    if candidate_checkouts != len(FULL_SCOPE["required_jobs"]) + 1 or workflow.count("uses: actions/checkout@") != candidate_checkouts + 1:
        errors.append("Same-candidate checkouts or sole frozen compatibility checkout differ")
    return errors


def check(root, files):
    try:
        scope = stage(json.loads((root / ".github/validation-scope.json").read_text()))
    except (ValueError, OSError, TypeError) as exc:
        return ["Validation scope: " + str(exc)]
    if scope == BOOTSTRAP_SCOPE: return check_bootstrap(root, files)
    if scope == IMPORT_SCOPE: return check_import_stage(root, files)
    return check_full_ci_stage(root, files)


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
    print(f"OK: {mode}; {scope['scope']}; {len(files)} files; declared scope checked; document integrity and actual product results have separate required jobs")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"repository check: {exc}", file=sys.stderr)
        raise SystemExit(1)
