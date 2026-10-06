#!/usr/bin/env python3
"""Linux-only root hook/OpenPGP integration in disposable local repositories.

Fixture repositories stay below ROOT/.g0-validation. The disposable keyring uses
a short RUNNER_TEMP directory to stay within Unix socket limits. The canonical
origin is configuration only: no clone, fetch, pull, push, gh, or network command
is executed. Pre-push is exercised through its executable/stdin interface.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://github.com/jack0682/RobotTransformation.git"
AUTHOR = "Root Signing Fixture <root-signing@example.invalid>"
GOVERNANCE_FILES = (
    "common.py", "check_ci.py", "check_commit_policy.py", "check_repository.py",
    "configure_github.py", "install_git_hooks.py", "merge_pr.py",
)


class RootSigningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform != "linux":
            raise RuntimeError("This real Git/GPG fixture must run on the isolated Linux CI runner")
        cls.gpg = shutil.which("gpg")
        cls.gpgconf = shutil.which("gpgconf")
        if not cls.gpg or not cls.gpgconf or not shutil.which("git"):
            raise RuntimeError("Git, GnuPG, and gpgconf are required; crypto checks cannot be skipped")
        parent = ROOT / ".g0-validation"
        if parent.is_symlink():
            raise RuntimeError("Fixture parent must not be a symlink")
        parent.mkdir(exist_ok=True)
        # Short names also keep GnuPG's Unix socket path within Linux's limit.
        cls.temporary = tempfile.TemporaryDirectory(prefix="s-", dir=parent)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.workspace = Path(cls.temporary.name)
        key_parent = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())).resolve()
        cls.key_temporary = tempfile.TemporaryDirectory(prefix="rx-gpg-", dir=key_parent)
        cls.addClassCleanup(cls.key_temporary.cleanup)
        cls.keyring = Path(cls.key_temporary.name)
        cls.keyring.chmod(0o700)
        if len(os.fsencode(str(cls.keyring / "S.gpg-agent.browser"))) >= 104:
            raise RuntimeError("Disposable GPG socket path is too long")
        cls.env = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_") and key not in
                   {"GNUPGHOME", "GPG_AGENT_INFO", "GPG_TTY", "GH_TOKEN", "GITHUB_TOKEN"}}
        cls.env.update(
            GNUPGHOME=str(cls.keyring), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
            GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0",
            GIT_ALLOW_PROTOCOL="", PYTHONDONTWRITEBYTECODE="1", LC_ALL="C",
        )
        cls.addClassCleanup(cls.stop_fixture_agent)
        result = subprocess.run(
            [cls.gpg, "--batch", "--pinentry-mode", "loopback", "--passphrase", "",
             "--quick-generate-key", AUTHOR, "ed25519", "sign", "1d"],
            cwd=cls.workspace, env=cls.env, text=True, capture_output=True, timeout=60,
        )
        if result.returncode:
            raise RuntimeError("Ephemeral fixture key generation failed: " + result.stderr)
        result = subprocess.run(
            [cls.gpg, "--batch", "--with-colons", "--list-secret-keys", "root-signing@example.invalid"],
            cwd=cls.workspace, env=cls.env, text=True, capture_output=True, check=True, timeout=30,
        )
        fingerprints = [line.split(":")[9] for line in result.stdout.splitlines()
                        if line.startswith("fpr:")]
        if len(fingerprints) != 1:
            raise RuntimeError("Expected one disposable signing key fingerprint")
        cls.fingerprint = fingerprints[0]

    @classmethod
    def stop_fixture_agent(cls):
        # This homedir identifies only the freshly generated fixture agent.
        subprocess.run([cls.gpgconf, "--homedir", str(cls.keyring), "--kill", "gpg-agent"],
                       cwd=cls.workspace, env=cls.env, capture_output=True, timeout=30)

    def setUp(self):
        self.repo = self.workspace / self._testMethodName
        self.repo.mkdir()
        self.command("git", "init", "-b", "feature/root-signing-fixture")
        self.command("git", "remote", "add", "origin", ORIGIN)
        for name, value in (("user.name", "Root Signing Fixture"),
                            ("user.email", "root-signing@example.invalid"),
                            ("user.signingkey", self.fingerprint),
                            ("gpg.program", self.gpg), ("protocol.allow", "never")):
            self.command("git", "config", "--local", name, value)
        tools = self.repo / "tools/governance"
        tools.mkdir(parents=True)
        for name in GOVERNANCE_FILES:
            shutil.copy2(ROOT / "tools/governance" / name, tools / name)
        shutil.copy2(ROOT / "repository-settings.json", self.repo / "repository-settings.json")
        shutil.copytree(ROOT / ".githooks", self.repo / ".githooks")
        self.command(sys.executable, "-B", "tools/governance/install_git_hooks.py")

    def command(self, *args, input=None, ok=True):
        if args[0] == "git" and any(arg in {"push", "fetch", "pull", "clone", "ls-remote"} for arg in args[1:]):
            self.fail("Network Git commands are prohibited in the signing fixture")
        result = subprocess.run(args, cwd=self.repo, env=self.env, input=input,
                                text=True, capture_output=True, timeout=60)
        message = result.stdout + result.stderr
        if ok:
            self.assertEqual(result.returncode, 0, message)
        else:
            self.assertNotEqual(result.returncode, 0, message)
        return result

    def signed_commit(self, message="A real signed fixture contribution"):
        # No explicit -s: the real prepare-commit-msg hook must add our trailer.
        self.command("git", "commit", "--allow-empty", "-m", message)
        return self.command("git", "rev-parse", "HEAD").stdout.strip()

    def audit(self, head="HEAD", *, ok=True):
        return self.command(sys.executable, "-B", "tools/governance/check_commit_policy.py",
                            "--head", head, ok=ok)

    def test_real_hooks_sign_commit_add_one_trailer_and_verify_full_head(self):
        self.signed_commit()
        self.command("git", "-c", "gpg.format=openpgp", "verify-commit", "HEAD")
        self.assertIn("exceptions=0", self.audit().stdout)
        self.command("git", "commit", "--amend", "--allow-empty", "--no-edit")
        message = self.command("git", "show", "-s", "--format=%B", "HEAD").stdout
        self.assertEqual(message.count("Signed-off-by: " + AUTHOR), 1)
        self.audit()
        rejected = self.command("git", "commit", "--allow-empty", "--author",
                                "Other Author <other@example.invalid>", "-m", "Another author's work", ok=False)
        self.assertIn("Missing author-matching", rejected.stderr)
        edited = (self.repo / ".git/COMMIT_EDITMSG").read_text()
        self.assertNotIn("Signed-off-by: Other Author", edited)

    def test_unsigned_and_cryptographically_tampered_commits_are_rejected(self):
        signed = self.signed_commit("Signed original fixture payload")
        raw = self.command("git", "cat-file", "commit", signed).stdout
        self.assertIn("gpgsig -----BEGIN PGP SIGNATURE-----", raw)
        tampered = self.command("git", "hash-object", "-t", "commit", "-w", "--stdin",
                                input=raw.replace("Signed original fixture payload", "Tampered fixture payload")).stdout.strip()
        self.audit(tampered, ok=False)
        # This explicit bypass creates test evidence only inside the disposable repo.
        self.command("git", "-c", "core.hooksPath=/dev/null", "commit", "--allow-empty",
                     "--no-gpg-sign", "-s", "-m", "Unsigned fixture")
        self.assertIn("OpenPGP commit signature required", self.audit(ok=False).stderr)

    def test_missing_author_dco_is_rejected_even_below_a_compliant_head(self):
        self.signed_commit()
        self.command("git", "-c", "core.hooksPath=/dev/null", "commit", "--allow-empty",
                     "-S", "-m", "Intentionally missing author DCO in fixture")
        bad = self.command("git", "rev-parse", "HEAD").stdout.strip()
        self.command("git", "verify-commit", bad)
        self.assertIn("missing author Signed-off-by", self.audit(ok=False).stderr)
        self.signed_commit("Compliant descendant of the rejected fixture")
        failure = self.audit(ok=False).stderr
        self.assertIn(bad, failure)
        self.assertIn("missing author Signed-off-by", failure)

    def test_real_pre_push_executable_checks_feature_and_protected_refs_without_network(self):
        head = self.signed_commit()
        zero = "0" * 40
        hook = str(self.repo / ".githooks/pre-push")
        self.command(hook, "origin", ORIGIN,
                     input=f"refs/heads/feature/root-signing-fixture {head} refs/heads/feature/root-signing-fixture {zero}\n")
        for branch in ("main", "develop"):
            for new, old in ((head, zero), (zero, head)):
                with self.subTest(branch=branch, deletion=new == zero):
                    result = self.command(hook, "origin", ORIGIN,
                                          input=f"refs/heads/feature/root-signing-fixture {new} refs/heads/{branch} {old}\n", ok=False)
                    self.assertIn("Direct protected-branch", result.stderr)

    def test_installer_preserves_custom_hooks_and_global_configuration(self):
        self.command("git", "config", "--local", "--unset", "core.hooksPath")
        hook = self.repo / ".git/hooks/pre-commit"
        original = b"#!/bin/sh\nexit 0\n"
        hook.write_bytes(original)
        hook.chmod(0o755)
        rejected = self.command(sys.executable, "-B", "tools/governance/install_git_hooks.py", ok=False)
        self.assertIn("custom hooks are preserved", rejected.stderr)
        self.assertEqual(hook.read_bytes(), original)
        self.command("git", "config", "--local", "core.hooksPath", "../custom-hooks")
        before = self.command("git", "config", "--local", "--list").stdout
        rejected = self.command(sys.executable, "-B", "tools/governance/install_git_hooks.py", ok=False)
        self.assertIn("custom hooks path is preserved", rejected.stderr)
        self.assertEqual(self.command("git", "config", "--local", "--list").stdout, before)
        self.assertEqual(self.command("git", "config", "--global", "--list").stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
