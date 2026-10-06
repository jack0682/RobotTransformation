#!/usr/bin/env python3
"""Lightweight isolated governance fixtures; no Git commits, key operations, network, or product execution."""
from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/governance"))
import common
import check_ci
import check_commit_policy as policy
import check_repository as repository
import configure_github as configure
import install_git_hooks as install
import merge_pr

REPO = common.REPOSITORY
HEAD = "a" * 40
BASE = "b" * 40
MERGED = "c" * 40
AUTHOR = "Contributor <contributor@example.invalid>"
PGP = "-----BEGIN PGP SIGNATURE-----\nfixture\n-----END PGP SIGNATURE-----"


def pr(source="feature/test", target="develop", fork=False):
    return {"number": 7, "title": "A reviewed change", "state": "open", "draft": False,
            "mergeable": True, "mergeable_state": "clean",
            "head": {"ref": source, "sha": HEAD, "repo": {"full_name": "contributor/fork" if fork else REPO}},
            "base": {"ref": target, "sha": BASE, "repo": {"full_name": REPO}}}


class Files(unittest.TestCase):
    def setUp(self):
        (ROOT / ".g0-validation").mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="fixture-", dir=ROOT / ".g0-validation")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)


class TargetGuardTests(Files):
    def test_settings_refuse_old_repository_and_historical_exception(self):
        config = common.settings()
        file = self.directory / "repository-settings.json"
        with patch.object(common, "ROOT", self.directory):
            for target in ("jack0682/rx-platform", "jack0682/rx-solutions", "jack0682/rx_docs", "other/RobotTransformation"):
                file.write_text(json.dumps({**config, "repository": target}))
                with self.subTest(target=target), self.assertRaises(ValueError):
                    common.settings()
            for value in (1, [], False):
                file.write_text(json.dumps({**config, "historical_dco_exceptions": value}))
                with self.subTest(exception=value), self.assertRaises(ValueError):
                    common.settings()
            file.write_text(json.dumps(config))
            self.assertEqual(common.settings()["repository"], REPO)

    def test_nested_checkout_refused_before_remote_lookup(self):
        with patch.object(common, "git", return_value=str(self.directory)) as git:
            with self.assertRaisesRegex(ValueError, "nested"):
                common.require_checkout(origin=True)
            self.assertEqual(git.call_count, 1)

    def test_only_single_exact_origin_fetch_and_push_destinations_allowed(self):
        for fetch, push in ((f"https://github.com/{REPO}.git", f"git@github.com:{REPO}.git"),
                            ("https://github.com/jack0682/rx-platform.git", f"git@github.com:{REPO}.git"),
                            (f"https://github.com/{REPO}.git", "https://github.com/other/fork.git"),
                            (f"https://github.com/{REPO}.git\nhttps://github.com/other/fork.git", f"git@github.com:{REPO}.git")):
            def git(*args):
                return str(common.ROOT) if args[0] == "rev-parse" else push if "--push" in args else fetch
            with self.subTest(fetch=fetch, push=push), patch.object(common, "git", side_effect=git):
                if fetch == f"https://github.com/{REPO}.git" and push == f"git@github.com:{REPO}.git":
                    common.require_checkout(origin=True)
                else:
                    with self.assertRaises(ValueError):
                        common.require_checkout(origin=True)

    def test_target_urls_do_not_accept_tokens_suffixes_or_other_hosts(self):
        for url in (f"https://github.com/{REPO}.git/extra", f"https://token@github.com/{REPO}.git",
                    f"https://example.invalid/{REPO}.git", "git@github.com:jack0682/rx-solutions.git"):
            with self.subTest(url=url):
                self.assertFalse(common.target_url(url))

    def test_hook_environment_context_is_cleared_and_guards_forced(self):
        with patch.dict(os.environ, {"GIT_DIR": "/unrelated", "GIT_WORK_TREE": "/unrelated",
                                     "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                                     "GIT_CONFIG_VALUE_0": "/unrelated", "GIT_NO_REPLACE_OBJECTS": "0"}):
            env = common.environment()
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
            self.assertNotIn(name, env)
        self.assertEqual(env["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")

    def test_api_refuses_every_old_repository_before_subprocess(self):
        with patch.object(common, "run") as run:
            for method in ("GET", "PATCH", "PUT", "POST", "DELETE"):
                with self.subTest(method=method), self.assertRaises(ValueError):
                    common.api(method, "repos/jack0682/rx-platform")
            run.assert_not_called()

    def test_api_pins_hostname_and_serializes_payload_without_shell(self):
        with patch.object(common, "run", return_value='{"ok":true}') as run:
            value = common.api("PATCH", "repos/" + REPO, {"description": "literal $(example)"})
        self.assertTrue(value["ok"])
        self.assertEqual(run.call_args.args[:6], ("gh", "api", "--hostname", "github.com", "--method", "PATCH"))
        self.assertEqual(json.loads(run.call_args.kwargs["input"])["description"], "literal $(example)")

    def test_remote_identity_refuses_redirect_and_archive(self):
        for value in ({"full_name": "other/repo", "archived": False}, {"full_name": REPO, "archived": True}):
            with patch.object(common, "api", return_value=value), self.assertRaises(ValueError):
                common.require_remote_identity()


class GitFlowTests(unittest.TestCase):
    def test_work_routes_include_forks(self):
        for prefix in common.WORK_PREFIXES:
            for fork in (False, True):
                with self.subTest(prefix=prefix, fork=fork):
                    self.assertIsNone(common.branch_error({"pull_request": pr(prefix + "/work", fork=fork)}))

    def test_same_repository_release_and_backmerge_routes(self):
        for source, target in (("develop", "main"), ("main", "develop"), ("release/next", "main"),
                               ("release/next", "develop"), ("hotfix/issue", "main"), ("hotfix/issue", "develop")):
            with self.subTest(source=source, target=target):
                self.assertIsNone(common.branch_error({"pull_request": pr(source, target)}))

    def test_forks_cannot_impersonate_privileged_routes(self):
        for source, target in (("develop", "main"), ("main", "develop"), ("release/next", "main"), ("hotfix/x", "develop")):
            with self.subTest(source=source), self.assertRaises(ValueError):
                merge_pr.require_ready_pr(pr(source, target, fork=True))

    def test_invalid_and_missing_routes_fail_closed(self):
        for source, target in (("feature/", "develop"), ("feature/x", "main"), ("random", "develop"),
                               ("main", "main"), ("develop", "develop"), ("feature/x", "other")):
            self.assertIsNotNone(common.branch_error({"pull_request": pr(source, target)}))
        for event in ({}, {"pull_request": {}}, {"pull_request": None}):
            self.assertIsNotNone(common.branch_error(event))
        wrong = pr(); wrong["base"]["repo"]["full_name"] = "jack0682/rx_docs"
        self.assertIsNotNone(common.branch_error({"pull_request": wrong}))

    def test_branch_shell_text_is_data_only(self):
        self.assertIsNone(common.branch_error({"pull_request": pr("feature/$(exit-99)")}))


class CommitPolicyTests(Files):
    def test_matching_signoff_only_from_parsed_trailers(self):
        with patch.object(policy, "git", return_value="Signed-off-by: " + AUTHOR + "\n") as git:
            self.assertTrue(policy.has_signoff("message", AUTHOR))
            self.assertFalse(policy.has_signoff("message", "Other <other@example.invalid>"))
        self.assertEqual(git.call_args.args, ("interpret-trailers", "--parse"))

    def test_missing_author_dco_has_no_historical_exception(self):
        with patch.object(policy, "git", return_value=AUTHOR + "\0Unsigned certificate"), \
                patch.object(policy, "has_signoff", return_value=False), patch.object(policy, "api") as api:
            with self.assertRaisesRegex(ValueError, "no historical exception"):
                policy.check_commit(HEAD, REPO)
            api.assert_not_called()

    def test_github_signature_requires_exact_commit_verified_openpgp(self):
        good = {"sha": HEAD, "commit": {"verification": {"verified": True, "signature": PGP}}}
        cases = [good, {**good, "sha": BASE}, {"sha": HEAD, "commit": {"verification": {"verified": False, "signature": PGP}}},
                 {"sha": HEAD, "commit": {"verification": {"verified": True, "signature": "-----BEGIN SSH SIGNATURE-----"}}}]
        with patch.object(policy, "git", return_value=AUTHOR + "\0message"), patch.object(policy, "has_signoff", return_value=True):
            for index, value in enumerate(cases):
                with self.subTest(index=index), patch.object(policy, "api", return_value=value):
                    if index == 0:
                        policy.check_commit(HEAD, REPO)
                    else:
                        with self.assertRaises(ValueError):
                            policy.check_commit(HEAD, REPO)

    def test_old_signature_repository_rejected_before_commands(self):
        with patch.object(policy, "git") as git, self.assertRaises(ValueError):
            policy.check_commit(HEAD, "jack0682/rx-platform")
        git.assert_not_called()

    def test_local_openpgp_presence_and_verification_both_required(self):
        for signed, verification_ok in ((False, True), (True, False), (True, True)):
            def git(*args, **kwargs):
                if args[0] == "show": return AUTHOR + "\0message"
                if args[0] == "cat-file": return "tree t\ngpgsig " + PGP + "\n\nmessage" if signed else "tree t\n\nmessage"
                if "verify-commit" in args and not verification_ok: raise ValueError("bad cryptographic signature")
                return ""
            with self.subTest(signed=signed, verification_ok=verification_ok), patch.object(policy, "git", side_effect=git), \
                    patch.object(policy, "has_signoff", return_value=True):
                if signed and verification_ok:
                    policy.check_commit(HEAD)
                else:
                    with self.assertRaises(ValueError): policy.check_commit(HEAD)

    def test_fullhead_checks_all_ancestors_and_rejects_bad_head(self):
        def git(*args): return HEAD if args[0] == "rev-parse" else HEAD + "\n" + BASE + "\n"
        with patch.object(policy, "require_full_history") as full, patch.object(policy, "git", side_effect=git), \
                patch.object(policy, "check_commit") as check:
            self.assertEqual(policy.audit_head("HEAD"), (HEAD, 2))
            self.assertEqual([c.args[0] for c in check.call_args_list], [HEAD, BASE])
            full.assert_called_once()
            for value in ("", "--all"):
                with self.assertRaises(ValueError): policy.audit_head(value)

    def test_shallow_replace_and_grafts_are_refused(self):
        graft = self.directory / "grafts"
        for shallow, replace, grafted in ((True, False, False), (False, True, False), (False, False, True), (False, False, False)):
            graft.write_text("ancestor substitution" if grafted else "")
            def git(*args):
                if "--is-shallow-repository" in args: return "true" if shallow else "false"
                if args[0] == "for-each-ref": return "refs/replace/" + HEAD if replace else ""
                return str(graft)
            with self.subTest(shallow=shallow, replace=replace, graft=grafted), patch.object(common, "git", side_effect=git):
                if shallow or replace or grafted:
                    with self.assertRaises(ValueError): common.require_full_history()
                else: common.require_full_history()

    def test_prepare_message_adds_only_current_committer(self):
        file = self.directory / "message"; file.write_text("Change\n")
        with patch.object(policy, "identity", return_value=AUTHOR), patch.object(policy, "has_signoff", return_value=False), \
                patch.object(policy, "git") as git:
            policy.prepare_message(str(file))
            self.assertEqual(git.call_args.args[2], "--trailer")
            self.assertEqual(git.call_args.args[3], "Signed-off-by: " + AUTHOR)

    def test_push_guard_refuses_protected_refs_tag_replacement_wrong_target(self):
        for remote_ref, new, old in (("refs/heads/main", HEAD, BASE), ("refs/heads/develop", "0"*40, BASE),
                                    ("refs/tags/v1", HEAD, BASE), ("refs/heads/random", HEAD, "0"*40)):
            with self.subTest(remote_ref=remote_ref), patch.object(policy, "require_full_history"), self.assertRaises(ValueError):
                policy.pre_push([f"ref {new} {remote_ref} {old}"], "origin", f"https://github.com/{REPO}.git")
        with self.assertRaises(ValueError):
            policy.pre_push([], "origin", "https://github.com/jack0682/rx-solutions.git")

    def test_push_guard_audits_new_commits_and_annotated_tags(self):
        def git(*args):
            if args[:2] == ("cat-file", "-t"): return "tag"
            if args[:2] == ("cat-file", "tag"): return PGP
            if args[0] == "rev-list": return HEAD + "\n"
            return ""
        with patch.object(policy, "require_full_history"), patch.object(policy, "git", side_effect=git) as git, \
                patch.object(policy, "check_commit") as check:
            policy.pre_push([f"ref {HEAD} refs/tags/v1 {'0'*40}"], "origin", f"git@github.com:{REPO}.git")
            check.assert_called_once_with(HEAD)
            self.assertTrue(any("verify-tag" in c.args for c in git.call_args_list))


class MergeGateTests(unittest.TestCase):
    def setUp(self):
        self.pr = pr()
        self.checks = {"total_count": len(common.CHECK_PROVIDERS), "check_runs": [
            {"id": i, "name": name, "head_sha": HEAD, "status": "completed", "conclusion": "success",
             "app": {"id": app}, "details_url": f"https://github.com/{REPO}/actions/runs/{123 if name != 'M5' else 456}/job/{i}"}
            for i, (name, app) in enumerate(common.CHECK_PROVIDERS.items(), 1)]}
        self.workflow = {"event": "pull_request", "head_sha": HEAD, "path": common.WORKFLOW,
                         "status": "completed", "conclusion": "success", "repository": {"full_name": REPO},
                         "pull_requests": [{"number": 7, "head": {"sha": HEAD}, "base": {"sha": BASE, "ref": "develop"}}]}
        self.m5_workflow = copy.deepcopy(self.workflow)
        self.m5_workflow["path"] = common.CHECK_WORKFLOWS["M5"]

    def checks_api(self, method, path, payload=None):
        self.assertEqual(method, "GET")
        if "check-runs?" in path: return self.checks
        if path.endswith("/456"): return self.m5_workflow
        return self.workflow

    def check(self):
        with patch.object(merge_pr, "api", side_effect=self.checks_api):
            merge_pr.require_checks(7, HEAD, self.pr["base"])

    def test_current_required_checks_pass(self): self.check()

    def test_m5_cannot_reuse_ci_wrong_event_provider_head_or_base(self):
        for field,value in (("path",common.WORKFLOW),("event","push"),("head_sha",BASE),("conclusion","skipped"),("pull_requests",[])):
            original=copy.deepcopy(self.m5_workflow);self.m5_workflow[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check()
            self.m5_workflow=original
        original=copy.deepcopy(self.m5_workflow)
        self.m5_workflow["pull_requests"][0]["base"]["sha"]=MERGED
        with self.assertRaises(ValueError):self.check()
        self.m5_workflow=original
        item=next(c for c in self.checks["check_runs"] if c["name"]=="M5")
        for field,value in (("app",{"id":99}),("head_sha",BASE),("status","queued"),("conclusion","failure")):
            old=item[field];item[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check()
            item[field]=old

    def test_m5_missing_and_newer_failure_cannot_be_hidden(self):
        original=copy.deepcopy(self.checks)
        self.checks["check_runs"]=[c for c in self.checks["check_runs"] if c["name"]!="M5"]
        with self.assertRaises(ValueError):self.check()
        self.checks=original
        item=next(c for c in self.checks["check_runs"] if c["name"]=="M5")
        self.checks["check_runs"].append({**item,"id":999,"conclusion":"failure"});self.checks["total_count"]+=1
        with self.assertRaises(ValueError):self.check()

    def test_wrong_provider_or_stale_check_head_is_refused(self):
        for field, value in (("app", {"id": 99}), ("head_sha", BASE), ("status", "queued"), ("conclusion", "cancelled")):
            original = copy.deepcopy(self.checks)
            self.checks["check_runs"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
            self.checks = original

    def test_latest_failing_check_overrides_older_success(self):
        latest = {**self.checks["check_runs"][0], "id": 10, "conclusion": "failure"}
        self.checks["check_runs"].append(latest); self.checks["total_count"] += 1
        with self.assertRaises(ValueError): self.check()

    def test_missing_or_truncated_checks_refused(self):
        for count, checks in ((101, self.checks["check_runs"]), (1, self.checks["check_runs"][:1])):
            self.checks = {"total_count": count, "check_runs": checks}
            with self.assertRaises(ValueError): self.check()

    def test_wrong_workflow_event_path_repository_status_or_pr_refused(self):
        for field, value in (("event", "push"), ("path", ".github/workflows/other.yml"), ("repository", {"full_name": "other/repo"}),
                             ("status", "in_progress"), ("conclusion", "failure"), ("head_sha", BASE), ("pull_requests", [])):
            original = copy.deepcopy(self.workflow); self.workflow[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
            self.workflow = original

    def test_stale_base_or_retargeted_pr_does_not_reuse_ci(self):
        for field, value in (("sha", MERGED), ("ref", "main")):
            original = copy.deepcopy(self.workflow)
            self.workflow["pull_requests"][0]["base"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
            self.workflow = original

    def test_unrelated_run_url_is_refused(self):
        self.checks["check_runs"][0]["details_url"] = "https://github.com/other/repo/actions/runs/123/job/1"
        with self.assertRaises(ValueError): self.check()

    def merge_api(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if path.endswith("/pulls/7"):
            self.reads += 1
            return self.pr if self.reads == 1 else self.current
        if path == "user": return {"login": "maintainer", "name": "Maintainer", "id": 42}
        if path.endswith("/merge"):
            self.assertEqual(payload["sha"], HEAD)
            self.assertEqual(payload["merge_method"], "merge")
            self.assertEqual(payload["commit_message"], "Signed-off-by: Maintainer <42+maintainer@users.noreply.github.com>\n")
            return {"merged": True, "sha": MERGED}
        if "/commits/" in path:
            return {"sha": MERGED, "commit": {"author": {"name": "Maintainer", "email": "42+maintainer@users.noreply.github.com"},
                    "message": "message", "verification": {"verified": True, "signature": PGP}}}
        self.fail("Unexpected API path " + path)

    def run_merge(self, drift=False):
        self.calls = []; self.reads = 0
        with patch.object(merge_pr, "require_checkout"), patch.object(merge_pr, "require_remote_identity"), \
                patch.object(merge_pr, "configure", return_value=["drift"] if drift else []), \
                patch.object(merge_pr, "require_checks"), patch.object(merge_pr, "api", side_effect=self.merge_api), \
                patch.object(merge_pr, "has_signoff", return_value=True), redirect_stdout(io.StringIO()):
            return merge_pr.merge(7)

    def test_merge_uses_exact_head_after_second_read(self):
        self.current = copy.deepcopy(self.pr)
        self.assertEqual(self.run_merge(), MERGED)
        self.assertEqual(self.reads, 2)
        self.assertEqual(sum(method == "PUT" for method, _, _ in self.calls), 1)

    def test_head_or_base_changes_stop_before_mutation(self):
        for kind in ("head", "base"):
            self.current = copy.deepcopy(self.pr); self.current[kind]["sha"] = MERGED
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.run_merge()
            self.assertFalse(any(method != "GET" for method, _, _ in self.calls))

    def test_policy_drift_stops_before_pr_mutation(self):
        self.current = self.pr
        with self.assertRaises(ValueError): self.run_merge(drift=True)
        self.assertEqual(self.calls, [])

    def test_actor_identity_rejects_injected_or_missing_values(self):
        for actor in ({}, {"login": "actor", "name": "Injected\nSigned-off-by: Other", "id": 42},
                      {"login": "actor", "name": "Actor", "id": True}):
            with self.assertRaises(ValueError): merge_pr.actor_signoff(actor)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.config = common.settings(); self.prefix = "repos/" + REPO
        self.calls = []; self.fixes = False; self.apply_ignored = False
        self.rules = {i+1: copy.deepcopy(r) for i, r in enumerate(self.config["rulesets"])}
        self.repository = {"full_name": REPO, "archived": False, **self.config["settings"], "security_and_analysis": self.config["security"]}

    def api(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if path.endswith("/automated-security-fixes"):
            if method == "GET": return {"enabled": self.fixes}
            if not self.apply_ignored: self.fixes = method == "PUT"
            return None
        if path.endswith("/vulnerability-alerts"): return None
        if "/branches/" in path: return {"name": path.rsplit("/", 1)[1]}
        if path.endswith("/rulesets?per_page=100"): return [{"id": i, "name": r["name"]} for i, r in self.rules.items()]
        if "/rulesets/" in path:
            index = int(path.rsplit("/", 1)[1])
            if method == "GET": return self.rules[index]
            self.rules[index] = payload; return {"id": index}
        if method != "GET": return None
        if path == self.prefix: return self.repository
        for suffix, key in (("/topics", "topics"), ("/actions/permissions", "actions"), ("/actions/permissions/workflow", "workflow_permissions")):
            if path.endswith(suffix): return {"names": self.config[key]} if key == "topics" else self.config[key]
        self.fail("Unexpected API call " + path)

    def invoke(self, apply=False):
        with patch.object(configure, "require_checkout"), patch.object(configure, "require_remote_identity"), \
                patch.object(configure, "api", side_effect=self.api), redirect_stdout(io.StringIO()):
            return configure.configure(apply)

    def test_audit_is_get_only_and_apply_readback_matches(self):
        self.assertEqual(self.invoke(), [])
        self.assertTrue(all(method == "GET" for method, _, _ in self.calls))
        self.calls.clear(); self.fixes = True
        self.assertEqual(self.invoke(True), [])
        self.assertFalse(self.fixes)
        self.assertTrue(any(method == "DELETE" and path.endswith("/automated-security-fixes") for method, path, _ in self.calls))

    def test_drift_is_detected_without_changing_remote(self):
        self.fixes = True
        self.assertIn("automatic security fixes", self.invoke())
        self.assertTrue(self.fixes)
        self.assertTrue(all(method == "GET" for method, _, _ in self.calls))

    def test_apply_does_not_claim_success_when_remote_ignores_change(self):
        self.fixes = True; self.apply_ignored = True
        self.assertIn("automatic security fixes", self.invoke(True))

    def test_target_guard_fails_before_network(self):
        with patch.object(configure, "require_checkout", side_effect=ValueError("wrong origin")), \
                patch.object(configure, "api") as api, self.assertRaises(ValueError):
            configure.configure(True)
        api.assert_not_called()

    def test_api_error_is_not_success(self):
        with patch.object(configure, "require_checkout"), patch.object(configure, "require_remote_identity"), \
                patch.object(configure, "api", side_effect=ValueError("HTTP 403")), self.assertRaises(ValueError):
            configure.configure()

    def test_quality_bypass_and_provider_drift_are_rejected(self):
        quality = next(r for r in self.rules.values() if r["name"].endswith("protected branches"))
        quality["bypass_actors"] = [{"actor_id": 5}]
        self.assertTrue(self.invoke())
        self.assertFalse(configure.contains(True, 1))
        self.assertFalse(configure.contains([{"id": 1}, {"id": 2}], [{"id": 1}, {"id": 1}]))

    def test_unmanaged_rulesets_are_preserved_and_require_review(self):
        self.rules[99] = {"name": "Unmanaged policy"}
        with self.assertRaisesRegex(ValueError, "none will be deleted"): self.invoke(True)
        self.assertTrue(all(method == "GET" for method, _, _ in self.calls))

    def test_expected_protections_have_no_quality_bypass(self):
        quality = next(r for r in self.rules.values() if r["name"].endswith("protected branches"))
        self.assertEqual(quality["bypass_actors"], [])
        rules = {r["type"]: r for r in quality["rules"]}
        self.assertTrue({"pull_request", "required_signatures", "non_fast_forward", "deletion"} <= rules.keys())
        required = rules["required_status_checks"]["parameters"]
        self.assertTrue(required["strict_required_status_checks_policy"])
        self.assertEqual(required["required_status_checks"], [{"context": name, "integration_id": app} for name, app in common.CHECK_PROVIDERS.items()])
        self.assertEqual(rules["pull_request"]["parameters"]["allowed_merge_methods"], ["merge"])


class InstallerTests(Files):
    def test_existing_key_and_hooks_are_checked_before_config_mutation(self):
        with patch.object(install, "require_checkout"), patch.object(install, "optional_config", return_value="/custom/hooks"), \
                patch.object(install, "git") as git, self.assertRaises(ValueError):
            install.install()
        git.assert_not_called()

    def test_missing_key_does_not_generate_copy_or_change_config(self):
        hooks = self.directory / ".githooks"; hooks.mkdir()
        def config(name): return ".githooks" if name == "core.hooksPath" else ""
        with patch.object(install, "ROOT", self.directory), patch.object(install, "require_checkout"), \
                patch.object(install, "optional_config", side_effect=config), patch.object(install, "git") as git, self.assertRaises(ValueError):
            install.install()
        git.assert_not_called()

    def test_installer_changes_only_local_config_using_existing_key(self):
        hooks = self.directory / ".githooks"; hooks.mkdir(); (hooks / "pre-commit").write_text("#!/bin/sh\n")
        values = {"core.hooksPath": ".githooks", "user.signingkey": "EXISTING_PUBLIC_FINGERPRINT", "gpg.format": "openpgp", "user.name": "Name", "user.email": "name@example.invalid"}
        with patch.object(install, "ROOT", self.directory), patch.object(install, "require_checkout"), \
                patch.object(install, "optional_config", side_effect=lambda name: values.get(name, "")), patch.object(install, "git") as git, redirect_stdout(io.StringIO()):
            install.install()
        self.assertEqual(git.call_count, 5)
        self.assertTrue(all(c.args[:2] == ("config", "--local") for c in git.call_args_list))
        self.assertTrue(any(c.args == ("config", "--local", "user.signingkey", "EXISTING_PUBLIC_FINGERPRINT") for c in git.call_args_list))


class BootstrapContentTests(Files):
    """Keep the original G0 contract tested independently of the current M2 scope."""
    def setUp(self):
        super().setUp()
        self.root = self.directory / "scaffold"; self.root.mkdir()
        for name in repository.REQUIRED | {".github/pull_request_template.md"}:
            source = ROOT / name
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (self.root / ".github/validation-scope.json").write_text(json.dumps(repository.SCOPE))
        (self.root / ".github/repository-policy.json").write_text(json.dumps({"schema": "rx.repository-content-policy.v1", "language": "en", "exclude_ai_artifacts": True}))
        (self.root / "README.md").write_text("G0 fixture; no product source.\n")
        workflow = (self.root / ".github/workflows/ci.yml")
        workflow.write_text(workflow.read_text().replace(
            "needs: [" + ", ".join(check_ci.FULL_SCOPE["required_jobs"]) + "]",
            "needs: [repository, commit_policy]").replace("CI_SCOPE_DECLARED_NOT_YET_RUN", "BOOTSTRAP_ONLY"))

    def check(self):
        return repository.check_bootstrap(self.root, [p for p in self.root.rglob("*") if p.is_file() or p.is_symlink()])

    def test_current_scaffold_has_bootstrap_only_scope(self):
        self.assertEqual(self.check(), [])

    def test_product_source_and_historical_exception_files_are_refused(self):
        for name in ("Cargo.toml", "rx-platform/Cargo.toml", "core/runtime.rs", "tools/governance/runtime_adapter.py", ".github/ISSUE_TEMPLATE/Cargo.toml", ".github/historical-dco-incidents.json"):
            file = self.root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text("{}")
            self.assertTrue(any("allowlist" in e for e in self.check()))
            file.unlink()

    def test_assistant_and_harness_artifacts_are_refused(self):
        for name in ("AGENTS.md", ".codex/config.json", "my_harness/state.json", ".github/prompts/review.md"):
            self.assertTrue(repository.ai_artifact(Path(name)))
        self.assertFalse(repository.ai_artifact(Path("tools/governance/test_harness.py")))

    def test_missing_file_changed_scope_and_invalid_json_fail(self):
        file = self.root / ".github/validation-scope.json"
        original = file.read_bytes()
        for data in (b'{"scope":"PRODUCT_VALIDATED"}', b'{invalid', b'{}'):
            file.write_bytes(data); self.assertTrue(self.check())
        file.write_bytes(original); file.unlink(); self.assertTrue(self.check())

    def test_unpinned_action_and_privileged_trigger_fail(self):
        file = self.root / ".github/workflows/ci.yml"
        text = file.read_text()
        file.write_text(text.replace("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", "actions/checkout@main"))
        self.assertTrue(any("full SHA" in e for e in self.check()))
        file.write_text(text + "\npull_request_target:\n")
        self.assertTrue(any("Privileged" in e for e in self.check()))

    def test_links_english_and_symlinks_fail_closed(self):
        file = self.root / "README.md"
        file.write_text("[missing](absent.md)\n[private](/Users/example/private.txt)\n" + chr(0xac00))
        errors = self.check()
        self.assertTrue(any("Missing or out-of-root" in e for e in errors))
        self.assertTrue(any("Machine-specific" in e for e in errors))
        self.assertTrue(any("English" in e for e in errors))
        file.unlink(); file.symlink_to(self.root / "NOTICE")
        self.assertTrue(any("regular files" in e for e in self.check()))


class AggregateTests(unittest.TestCase):
    def test_every_required_job_must_succeed(self):
        good = {name: {"result": "success"} for name in repository.SCOPE["required_jobs"]}
        check_ci.check(good, repository.SCOPE)
        for state in ("failure", "cancelled", "skipped", "neutral", None):
            broken = copy.deepcopy(good); broken["repository"]["result"] = state
            with self.subTest(state=state), self.assertRaises(ValueError): check_ci.check(broken, repository.SCOPE)
        for value in ({}, {"repository": {"result": "success"}}, {**good, "unlisted": {"result": "success"}}, {**good, "repository": None}):
            with self.assertRaises(ValueError): check_ci.check(value, repository.SCOPE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
