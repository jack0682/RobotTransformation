#!/usr/bin/env python3
"""Install repository-local signing defaults and hooks, preserving existing custom hooks."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


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


def git(*args, optional=False):
    require_standalone_repository()
    result = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True)
    if result.returncode and not (optional and result.returncode == 1):
        raise ValueError(result.stderr.strip() or "Git configuration failed")
    return result.stdout.strip()


def main():
    hooks = ROOT / ".githooks"
    configured = git("config", "--get", "core.hooksPath", optional=True)
    if configured and (ROOT / configured).resolve() != hooks.resolve():
        raise ValueError(f"Preserving custom core.hooksPath={configured}; integrate hooks manually")
    if not configured:
        previous = Path(git("rev-parse", "--git-path", "hooks"))
        if not previous.is_absolute():
            previous = ROOT / previous
        custom = [path.name for path in previous.glob("*")
                  if path.is_file() and not path.name.endswith(".sample")]
        if custom:
            raise ValueError(f"Preserving custom hooks: {', '.join(sorted(custom))}; integrate manually")
    key = git("config", "--get", "user.signingkey", optional=True)
    if not key:
        raise ValueError("Configure user.signingkey with your existing GitHub-registered OpenPGP key first")
    if git("config", "--get", "gpg.format", optional=True) not in ("", "openpgp"):
        raise ValueError("Existing signing format is not OpenPGP; select your OpenPGP key first")
    for name in ("user.name", "user.email"):
        if not git("config", "--get", name, optional=True):
            raise ValueError(f"Configure {name} before installing DCO hooks")
    for path in hooks.iterdir():
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o111)
    for name, value in (("core.hooksPath", ".githooks"), ("gpg.format", "openpgp"),
                        ("user.signingkey", key), ("commit.gpgsign", "true"), ("tag.gpgsign", "true")):
        git("config", "--local", name, value)
    print("Installed local DCO hooks, OpenPGP commit/tag signing and main/develop push guard")
    print("Commits attest your DCO contribution automatically; GitHub remains the enforcement boundary")
    return 0


if __name__ == "__main__":
    try:
        require_standalone_repository()
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"hook installation: {exc}", file=sys.stderr)
        raise SystemExit(1)
