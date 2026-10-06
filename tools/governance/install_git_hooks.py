#!/usr/bin/env python3
"""Configure this clone with an existing signing key; never generate or copy keys."""
import sys
from pathlib import Path
import subprocess

from common import ROOT, environment, git, require_checkout


def optional_config(name):
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(ROOT), "config", "--get", name],
                            text=True, capture_output=True, env=environment())
    if result.returncode not in (0, 1):
        raise ValueError(result.stderr.strip())
    return result.stdout.strip()


def install():
    require_checkout(origin=True)
    hooks = ROOT / ".githooks"
    configured = optional_config("core.hooksPath")
    if configured and (ROOT / configured).resolve() != hooks.resolve():
        raise ValueError("Existing custom hooks path is preserved; integrate it explicitly")
    if not configured:
        previous = Path(git("rev-parse", "--git-path", "hooks").strip())
        if not previous.is_absolute():
            previous = ROOT / previous
        if any(p.is_file() and not p.name.endswith(".sample") for p in previous.glob("*")):
            raise ValueError("Existing custom hooks are preserved; integrate them explicitly")
    key = optional_config("user.signingkey")
    if not key:
        raise ValueError("Configure your existing GitHub-registered OpenPGP key first")
    if optional_config("gpg.format") not in ("", "openpgp"):
        raise ValueError("Existing non-OpenPGP signing configuration is preserved")
    for name in ("user.name", "user.email"):
        if not optional_config(name):
            raise ValueError("Configure " + name + " before installing hooks")
    for path in hooks.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError("Hook entries must be regular files")
        path.chmod(path.stat().st_mode | 0o111)
    for name, value in (("core.hooksPath", ".githooks"), ("gpg.format", "openpgp"),
                        ("user.signingkey", key), ("commit.gpgsign", "true"), ("tag.gpgsign", "true")):
        git("config", "--local", name, value)
    print("Configured only this clone; existing signing key retained; no key material copied")


if __name__ == "__main__":
    try:
        install()
    except (ValueError, OSError) as exc:
        print(f"hook installation: {exc}", file=sys.stderr)
        raise SystemExit(1)
