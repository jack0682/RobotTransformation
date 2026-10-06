"""Fabricated metadata/facts and mocked commands only; no product process."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner


class Fixtures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_source_bytes_and_executable_mode_must_match_git(self):
        source = self.root / "source"; source.mkdir(); path = source / "a.rs"; path.write_bytes(b"source"); path.chmod(0o644)
        oid = hashlib.sha1(b"blob 6\0source").hexdigest(); expected = "a" * 40
        def git(root, *args):
            if args == ("rev-parse", "--show-toplevel"): return str(source).encode()
            if args == ("rev-parse", "HEAD"): return expected.encode()
            if args[0] in ("status", "for-each-ref"): return b""
            if args[0] == "ls-tree": return f"100644 blob {oid}\ta.rs\0".encode()
            raise AssertionError(args)
        with patch.object(runner, "git", side_effect=git):
            self.assertEqual(runner.source_rows(source, expected)["a.rs"]["sha256"], runner.digest(b"source"))
            path.write_bytes(b"tamper")
            with self.assertRaisesRegex(ValueError, "bytes differ"): runner.source_rows(source, expected)
            path.write_bytes(b"source"); path.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "mode differs"): runner.source_rows(source, expected)
            with self.assertRaisesRegex(ValueError, "head differs"): runner.source_rows(source, "b" * 40)

    def test_projection_changes_are_exact_and_source_is_untouched(self):
        source = self.root / "source"; source.mkdir(); (source / "a.rs").write_bytes(b"one")
        row = {"a.rs": {"sha256": runner.digest(b"one"), "bytes": 3, "mode": "100644"}}
        projection = self.root / "projection"; runner.copy_projection(source, row, projection)
        self.assertEqual(runner.changed_paths(row, projection), [])
        (projection / "a.rs").write_bytes(b"two"); (projection / "unexpected").write_text("extra")
        self.assertEqual(runner.changed_paths(row, projection), ["a.rs", "unexpected"])
        self.assertEqual((source / "a.rs").read_bytes(), b"one")
        with self.assertRaises(FileExistsError): runner.copy_projection(source, row, projection)

    def test_paths_and_symlinks_cannot_escape(self):
        for name in ("../outside", "/absolute", "a//b", "a\\b", "a/../b"):
            with self.subTest(name=name), self.assertRaises(ValueError): runner.relative(name)
        alias = self.root / "alias"; alias.symlink_to(self.root)
        with self.assertRaises(ValueError): runner.clean_path(alias / "new")

    def test_credential_markers_refuse_all_payload_without_disclosing_value(self):
        cases = [b"-----BEGIN PRIVATE KEY-----\nFABRICATED", b"Authorization: Bearer invented-token-value",
                 b"Cookie: session=fictional-session", b"ghp_" + b"X" * 40,
                 b'{"private_seed_hex":"' + b"ab" * 32 + b'"}', b'{"password":"fabricated-password"}',
                 b'compiler: {"worker_token":"fabricated-token"}']
        for index, value in enumerate(cases):
            scope = self.root / str(index); scope.mkdir(); selected = scope / "selected"; selected.mkdir()
            (selected / "log.stderr").write_bytes(value); public = scope / "public"
            self.assertFalse(runner.publish(selected, public))
            self.assertEqual({p.name for p in public.iterdir()}, {"PUBLICATION.json"})
            self.assertNotIn(value, (public / "PUBLICATION.json").read_bytes())

    def test_clean_evidence_is_exact_and_manifested(self):
        selected = self.root / "selected"; selected.mkdir(); raw = b'{"status":"UNKNOWN","error_type":"TimeoutError"}\n'
        (selected / "receipt.json").write_bytes(raw); public = self.root / "public"
        self.assertTrue(runner.publish(selected, public))
        self.assertEqual((public / "evidence/receipt.json").read_bytes(), raw)
        self.assertEqual(json.loads((public / "CHECKSUMS.json").read_text())["receipt.json"], runner.digest(raw))

    def test_incomplete_publication_never_exposes_a_partial_approved_tree(self):
        selected = self.root / "selected"; selected.mkdir(); (selected / "x").write_text("safe"); public = self.root / "public"
        with patch.object(runner.os, "rename", side_effect=OSError("fabricated disk error")), self.assertRaises(OSError):
            runner.publish(selected, public)
        self.assertFalse(public.exists())

    def test_only_original_bounded_facts_are_selected_and_unknown_is_unchanged(self):
        fixtures = self.root / "fixtures"; fixture = fixtures / "case-a"; operation = fixture / "python-journal/op-a"; operation.mkdir(parents=True)
        original = {"schema": "rx.python-host-request.v1", "operation": "op-a", "invocation": "inv-a", "intent_digest": "a", "environment_digest": "b", "device_session": "c", "input": {"primitive": "pick", "node": "pick"}}
        result = {k: original[k] for k in ("operation", "invocation", "intent_digest", "environment_digest", "device_session")}
        result.update(schema="rx.python-host-receipt.v1", status="UNKNOWN", error_type="TimeoutError")
        for name, value in [("request.json", original), ("receipt.json", result)]: (operation / name).write_text(json.dumps(value))
        device = fixture / "device"; device.mkdir(); (device / "state.json").write_text('{"phase":"SUPPLY"}')
        (device / "unselected-private.json").write_text('{"password":"not-for-upload"}')
        (fixture / "venv").mkdir(); (fixture / "venv/unselected").write_text("not a fact")
        destination = self.root / "facts"; facts = runner.fact_files(fixtures, destination)
        self.assertEqual(len(facts), 3); self.assertFalse((destination / "case-a/device/unselected-private.json").exists())
        observed = runner.fact_correlations(destination)[0]
        self.assertTrue(observed["correlation_matches"]); self.assertEqual(observed["receipt_status"], "UNKNOWN")
        self.assertEqual(observed["error_type"], "TimeoutError"); self.assertFalse(observed["uncertainty_promoted"])
        self.assertEqual(json.loads((operation / "receipt.json").read_text()), result)
        copied = destination / "case-a/python-journal/op-a/receipt.json"
        malformed = dict(result); del malformed["invocation"]; copied.write_text(json.dumps(malformed))
        self.assertFalse(runner.fact_correlations(destination)[0]["correlation_matches"])

    def test_fact_symlinks_and_oversize_are_refused(self):
        fixture = self.root / "fixtures/case"; journal = fixture / "python-journal/op"; journal.mkdir(parents=True)
        target = self.root / "outside"; target.write_text("{}"); (journal / "request.json").symlink_to(target)
        with self.assertRaises(ValueError): runner.fact_files(fixture.parent, self.root / "facts")
        (journal / "request.json").unlink(); (journal / "request.json").write_bytes(b" " * (runner.MAX_FACT + 1))
        with self.assertRaisesRegex(ValueError, "bound"): runner.fact_files(fixture.parent, self.root / "facts")

    def test_both_missing_null_empty_or_nonstring_tuple_never_claims_correlation(self):
        destination = self.root / "facts"; operation = destination / "case/python-journal/op"; operation.mkdir(parents=True)
        fields = ("operation", "invocation", "intent_digest", "environment_digest", "device_session")
        original = {"schema": "rx.python-host-request.v1", **{key: "original-" + key for key in fields}}
        result = {"schema": "rx.python-host-receipt.v1", "status": "UNKNOWN", "error_type": "TimeoutError",
                  **{key: original[key] for key in fields}}
        for field in fields:
            for mutation in ("missing", "null", "empty", "number", "boolean"):
                request, receipt = dict(original), dict(result)
                if mutation == "missing":
                    del request[field]; del receipt[field]
                else:
                    value = {"null": None, "empty": "", "number": 0, "boolean": False}[mutation]
                    request[field] = value; receipt[field] = value
                request_raw = json.dumps(request).encode(); receipt_raw = json.dumps(receipt).encode()
                (operation / "request.json").write_bytes(request_raw); (operation / "receipt.json").write_bytes(receipt_raw)
                with self.subTest(field=field, mutation=mutation):
                    observed = runner.fact_correlations(destination)[0]
                    self.assertFalse(observed["correlation_matches"])
                    self.assertEqual(observed["receipt_status"], "UNKNOWN")
                    self.assertFalse(observed["uncertainty_promoted"])
                    self.assertEqual((operation / "request.json").read_bytes(), request_raw)
                    self.assertEqual((operation / "receipt.json").read_bytes(), receipt_raw)

    def test_command_runs_once_and_preserves_nonzero_and_stream_hashes(self):
        selected = self.root / "selected"; selected.mkdir()
        def fake(args, **kwargs):
            kwargs["stdout"].write(b"original stdout"); kwargs["stderr"].write(b"original failure")
            return SimpleNamespace(returncode=101)
        with patch.object(runner.subprocess, "run", side_effect=fake) as launch:
            code = runner.command(["cargo", "test"], self.root, {}, selected, "trial")
            self.assertEqual(launch.call_count, 1)
        record = json.loads((selected / "trial.command.json").read_text())
        self.assertEqual(code, 101); self.assertEqual(record["returncode"], 101); self.assertEqual(record["retry_count"], 0)
        self.assertEqual(record["stderr_sha256"], runner.digest(b"original failure"))

    def test_redirected_context_is_refused_before_git_or_build(self):
        for name in ("GIT_DIR", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "RUSTFLAGS", "RUSTC", "RUSTC_WRAPPER",
                     "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTC", "CARGO_BUILD_RUSTC_WRAPPER",
                     "CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTFLAGS",
                     "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS"):
            with patch.dict(os.environ, {name: "fabricated"}), patch.object(runner.subprocess, "run") as call:
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Redirected"): runner.environment()
                call.assert_not_called()

    def test_old_python_is_refused_before_filesystem_or_process_work(self):
        with patch.object(runner.sys, "version_info", (3, 10, 0)), patch.object(runner.subprocess, "run") as call:
            with self.assertRaisesRegex(ValueError, "Python 3.11"):
                runner.execute(SimpleNamespace())
            call.assert_not_called()


if __name__ == "__main__": unittest.main(verbosity=2)
