#!/usr/bin/env python3
"""Exercise legacy admin routing in disposable repositories, without network/key use."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get("RX_ADMIN_TEST_SOURCE_ROOT", Path(__file__).resolve().parents[2]))
GIT = shutil.which("git")
COMPONENTS = ("rx-platform", "rx-solutions")
SCRIPTS = ("merge_pr.py", "configure_github.py", "install_git_hooks.py")


class LegacyAdminGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("RX_ADMIN_TEST_TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
        self.empty = self.base / "empty-hooks"
        self.empty.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.call_log = self.base / "gh-called.txt"
        fake = self.bin / "gh"
        fake.write_text("#!/bin/sh\nprintf 'called\\n' >> \"$RX_ADMIN_GH_CALL_LOG\"\n"
                        "printf 'fixture denies every network operation\\n' >&2\nexit 97\n")
        fake.chmod(0o755)
        self.env.update(PATH=str(self.bin) + os.pathsep + self.env.get("PATH", ""),
                        RX_ADMIN_GH_CALL_LOG=str(self.call_log))

    def git(self, root, *args):
        result = subprocess.run([GIT, "-c", "core.hooksPath=" + str(self.empty), "-C", str(root), *args],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def repository(self, path):
        path.mkdir(parents=True)
        self.git(path, "init", "-b", "feature/fixture")
        return path

    def component(self, path, component):
        (path / "tools").mkdir(parents=True, exist_ok=True)
        for name in (*SCRIPTS, "check_commit_policy.py"):
            shutil.copy2(ROOT / component / "tools" / name, path / "tools" / name)
        shutil.copy2(ROOT / component / "repository-settings.json", path / "repository-settings.json")
        (path / ".githooks").mkdir(exist_ok=True)
        (path / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
        return path

    def invoke(self, component, name, overrides=None, help_only=False, imported=False):
        env = dict(self.env, **(overrides or {}))
        if imported:
            module = name.removesuffix(".py")
            call = {"merge_pr": "api('repos/owner/repository')",
                    "configure_github": "api('PATCH', 'repos/owner/repository', {})",
                    "install_git_hooks": "git('config', '--local', 'guard.mustNotWrite', 'true')"}[module]
            code = "import sys; sys.path.insert(0, " + repr(str(component / "tools")) + "); "
            code += "import " + module + "; " + module + "." + call
            args = [sys.executable, "-c", code]
        else:
            args = [sys.executable, str(component / "tools" / name)]
            args += ["--help"] if help_only else ({"merge_pr.py": ["1"], "configure_github.py": ["--apply"],
                                                 "install_git_hooks.py": []}[name])
        return subprocess.run(args, cwd=self.base, env=env, text=True, capture_output=True)

    def state(self, repo, component):
        config = repo / ".git" / "config"
        return (hashlib.sha256(config.read_bytes()).hexdigest(),
                [(str(p.relative_to(component)), p.stat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in sorted((component / ".githooks").iterdir())])

    def assert_refused(self, repo, component, name, overrides=None, imported=False):
        before = self.state(repo, component)
        result = self.invoke(component, name, overrides, imported=imported)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("root tools/governance", result.stderr)
        self.assertEqual(self.state(repo, component), before)
        self.assertFalse(self.call_log.exists(), "Legacy helper reached gh before refusing")

    def test_nested_cli_refuses_before_network_config_or_chmod(self):
        for component in COMPONENTS:
            repo = self.repository(self.base / component / "mono")
            child = self.component(repo / component, component)
            for script in SCRIPTS:
                with self.subTest(component=component, script=script):
                    self.assert_refused(repo, child, script)

    def test_imported_real_io_entry_points_cannot_bypass_the_guard(self):
        for component in COMPONENTS:
            repo = self.repository(self.base / component / "mono")
            child = self.component(repo / component, component)
            for script in SCRIPTS:
                with self.subTest(component=component, script=script):
                    self.assert_refused(repo, child, script, imported=True)

    def test_git_environment_cannot_redirect_standalone_or_nested_context(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "standalone"), component)
            other = self.repository(self.base / component / "other")
            variants = [{"GIT_DIR": str(other / ".git")}, {"GIT_WORK_TREE": str(other)},
                        {"GIT_COMMON_DIR": str(other / ".git")}, {"GIT_INDEX_FILE": str(other / "index")},
                        {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.worktree", "GIT_CONFIG_VALUE_0": str(other)},
                        {"GIT_CONFIG_PARAMETERS": "'core.worktree=" + str(other) + "'"},
                        {"GIT_CONFIG_KEY_0": "core.worktree"}, {"GIT_CONFIG_VALUE_0": str(other)},
                        {"GIT_DIR": ""}]
            for override in variants:
                for script in SCRIPTS:
                    with self.subTest(component=component, script=script, variables=sorted(override)):
                        self.assert_refused(repo, repo, script, override)

    def test_nested_dotgit_does_not_turn_import_into_standalone_authority(self):
        for component in COMPONENTS:
            repo = self.repository(self.base / component / "mono")
            child = self.component(self.repository(repo / component), component)
            for script in SCRIPTS:
                with self.subTest(component=component, script=script):
                    self.assert_refused(repo, child, script)

    def test_wrong_repository_identity_and_origin_refuse_without_io(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "repo"), component)
            settings = repo / "repository-settings.json"
            original = settings.read_text()
            data = json.loads(original)
            data["repository"] = "jack0682/RobotTransformation"
            settings.write_text(json.dumps(data))
            for script in SCRIPTS:
                self.assert_refused(repo, repo, script)
            settings.write_text(original)
            self.git(repo, "remote", "add", "origin", "https://github.com/jack0682/RobotTransformation.git")
            for script in SCRIPTS:
                self.assert_refused(repo, repo, script)

    def test_standalone_cli_help_preserves_existing_configure_and_merge_entry(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "repo"), component)
            for remote in [None, "https://github.com/jack0682/" + component + ".git",
                           "git@github.com:jack0682/" + component + ".git",
                           "ssh://git@github.com/jack0682/" + component + ".git"]:
                if remote:
                    self.git(repo, "config", "remote.origin.url", remote)
                for script in ("merge_pr.py", "configure_github.py"):
                    with self.subTest(component=component, script=script, remote=remote):
                        result = self.invoke(repo, script, help_only=True)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(self.call_log.exists())

    def test_standalone_real_api_reaches_only_the_fixture_network_stub(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "repo"), component)
            for script in ("merge_pr.py", "configure_github.py"):
                result = self.invoke(repo, script)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fixture denies every network operation", result.stderr)
                self.assertTrue(self.call_log.exists())
                self.call_log.unlink()

    def test_standalone_hook_fixture_needs_no_support_file_or_user_key(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "repo"), component)
            for key, value in [("user.name", "Disposable Fixture"), ("user.email", "fixture@example.invalid"),
                               ("user.signingkey", "TEST-PLACEHOLDER-NO-SIGNING")]:
                self.git(repo, "config", key, value)
            for _ in range(2):
                result = self.invoke(repo, "install_git_hooks.py")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.git(repo, "config", "--local", "--get", "core.hooksPath"), ".githooks")
            self.assertEqual(self.git(repo, "config", "--local", "--get", "commit.gpgsign"), "true")
            self.assertTrue((repo / ".githooks" / "pre-commit").stat().st_mode & 0o111)
            self.git(repo, "config", "core.hooksPath", "custom-preserved-hooks")
            before = self.state(repo, repo)
            result = self.invoke(repo, "install_git_hooks.py")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Preserving custom", result.stderr)
            self.assertEqual(self.state(repo, repo), before)
            self.assertFalse(self.call_log.exists())

    def test_standalone_linked_worktree_is_accepted_without_real_key_use(self):
        for component in COMPONENTS:
            repo = self.component(self.repository(self.base / component / "repo"), component)
            self.git(repo, "add", ".")
            self.git(repo, "-c", "user.name=Disposable Fixture", "-c", "user.email=fixture@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-m", "Disposable test tree")
            linked = self.base / component / "linked"
            self.git(repo, "worktree", "add", "--detach", str(linked), "HEAD")
            self.assertTrue((linked / ".git").is_file())
            for script in ("merge_pr.py", "configure_github.py"):
                result = self.invoke(linked, script, help_only=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.invoke(linked, "install_git_hooks.py")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Configure user.signingkey", result.stderr)
            self.assertFalse(self.call_log.exists())

    def test_symlinked_dotgit_cannot_borrow_another_repository(self):
        for component in COMPONENTS:
            real = self.repository(self.base / component / "real")
            pretender = self.component(self.base / component / "pretender", component)
            (pretender / ".git").symlink_to(real / ".git", target_is_directory=True)
            for script in SCRIPTS:
                self.assert_refused(pretender, pretender, script)

    def test_legacy_guard_copies_have_one_behavior_except_component_identity(self):
        guards = []
        for component in COMPONENTS:
            for name in SCRIPTS:
                text = (ROOT / component / "tools" / name).read_text()
                block = text.split("def require_standalone_repository():", 1)[1].split("\n\ndef ", 1)[0]
                guards.append(block.replace("jack0682/" + component, "EXPECTED_COMPONENT"))
        self.assertEqual(len(set(guards)), 1)


if __name__ == "__main__":
    unittest.main()
