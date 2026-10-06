#!/usr/bin/env python3
"""Document-gate negatives in task-scoped fixtures; no network or product execution."""
from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/docs"))
import check_documents as gate


class ParserTests(unittest.TestCase):
    def test_rendered_destinations_include_images_references_and_html(self):
        text = '[a](relative(a).md "title") ![b](<b.png>)\n[r]: c.md\n<a href="d.md">d</a>'
        self.assertEqual([item["href"] for item in gate.link_spans(text)],
                         ["relative(a).md", "b.png", "c.md", "d.md"])

    def test_code_and_comments_do_not_become_document_targets(self):
        text = '`[x](inline.md)`\n````md\n[x](fenced.md)\n```\n````\n<!-- [x](comment.md) -->\n[x](real.md)'
        self.assertEqual([item["href"] for item in gate.link_spans(text)], ["real.md"])

    def test_unsafe_local_paths_and_ambiguous_json_are_refused(self):
        for href in ("../../../outside", "/Users/private", "file:///private", "bad\\path", "%00"):
            with self.subTest(href=href), self.assertRaises(ValueError):
                gate.local_target("docs/a.md", href)
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                gate.decode(data)


class DocumentFixtures(unittest.TestCase):
    def setUp(self):
        folder = ROOT / ".g0-validation"
        folder.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="documents-", dir=folder)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.initial_material = {}
        self.bound = []
        for family, key in (("contracts/v1.0", "schema_hash_sha256"),
                            ("cell_operations/v1.0", "cell_manifest_sha256")):
            owner = gate.DOCS + "/" + family + "/protocol_manifest.json"
            files = {}
            for number in range(4):
                name = f"norm-{number}.md"
                raw = ("# Normative " + str(number) + "\n").encode()
                self.write(str(Path(owner).parent / name), raw)
                files[name] = gate.sha256(raw)
            manifest = gate.canonical({"normative_document_sha256": files})
            self.write(owner, manifest)
            self.write(str(Path(owner).parent / "manifest_integrity.json"), gate.canonical({
                key: gate.sha256(manifest), "manifest_file": "protocol_manifest.json"}))
            self.add_bound(owner, files, manifest, "normative_document_sha256")
        owner = gate.DOCS + "/contracts/workflow-execution/v2/manifest.json"
        files = {}
        projection_dir = "rx_docs/references/execution_v2_design_2026-10-02/"
        self.projections = []
        readme = "# Workflow\n"
        self.source_rows = []
        for number, name in enumerate(("sizing.json", "legacy-freeze.json"), 2):
            target = projection_dir + name
            self.write(target, b"{}\n")
            self.source_rows.append(self.row(target, b"{}\n"))
            href = "../../../../references/execution_v2_design_2026-10-02/" + name
            readme += "[projection](" + href + ")\n"
            self.projections.append({"document": str(Path(owner).parent / "README.md"),
                                     "line": number, "href": href, "target": target})
        for number, name in enumerate(["README.md"] + [f"contract-{i}.md" for i in range(9)]):
            raw = readme.encode() if number == 0 else b"# Contract\n"
            self.write(str(Path(owner).parent / name), raw)
            files[name] = gate.sha256(raw)
        manifest = gate.canonical({"schema": "rx.contract-revision.v1", "files": files})
        self.write(owner, manifest)
        self.add_bound(owner, files, manifest, "files")
        for name in gate.TABLE_DOCUMENTS:
            self.write(gate.DOCS + "/" + name, b"# Table\n```python\nprint('table fixture')\n```\n")
        self.url = "https://github.com/" + gate.SOURCE_REPOSITORY + "/blob/" + gate.SOURCE_COMMIT + "/references/proof.md"
        self.document = gate.DOCS + "/ordinary.md"
        before = b"# Ordinary\n[proof](../references/proof.md)\n"
        after = ("# Ordinary\n[proof](" + self.url + ")\n").encode()
        self.write(self.document, after)
        self.source_rows.append(self.row(self.document, before))
        payload = {"files": self.source_rows}
        payload_hash = gate.sha256(gate.canonical(payload))
        self.write(gate.IMPORT_MANIFEST, gate.canonical({"payload": payload, "payload_sha256": payload_hash}))
        self.index = {"schema": "rx.document-origin-index.v1", "source_repository": gate.SOURCE_REPOSITORY,
                      "source_commit": gate.SOURCE_COMMIT, "source_tree_oid": gate.SOURCE_TREE,
                      "origins": [{"url": self.url, "repository": gate.SOURCE_REPOSITORY,
                                   "commit": gate.SOURCE_COMMIT, "path": "references/proof.md",
                                   "mode": "100644", "kind": "blob", "git_object_oid": "a" * 40,
                                   "bytes": 10, "sha256": "b" * 64, "fragment": "", "query": "",
                                   "fragment_proof": {"status": "NO_FRAGMENT", "fragment": ""}}],
                      "occurrences": [{"document": self.document, "line": 2, "syntax": "inline_or_image",
                                       "old_href": "../references/proof.md", "new_href": self.url,
                                       "old_destination": "references/proof.md", "origin_git_object_oid": "a" * 40}],
                      "changed_documents": [{"path": self.document, "before_sha256": gate.sha256(before),
                                             "after_sha256": gate.sha256(after), "before_bytes": len(before),
                                             "after_bytes": len(after), "mode": "100644"}],
                      "hash_bound_documents": self.bound, "unchanged_local_evidence_projections": self.projections}
        raw = gate.canonical(self.index)
        self.write(gate.ORIGINS, raw)
        # Synthetic small origin set; production pins/counts are not regenerated.
        pins = patch.multiple(gate, ORIGIN_INDEX_SHA256=gate.sha256(raw),
                              IMPORT_PAYLOAD_SHA256=payload_hash, ORIGIN_COUNTS=(1, 1, 1, 18))
        pins.start()
        self.addCleanup(pins.stop)
        self.source_material = copy.deepcopy(self.initial_material)
        historical = patch.object(gate, "historical_material", return_value=self.source_material)
        historical.start(); self.addCleanup(historical.stop)
        layout = patch.object(gate, "check_canonical_layout", return_value={"synthetic_fixture": True})
        layout.start(); self.addCleanup(layout.stop)
        # check_canonical_layout's independent full corpus fixtures exercise the actual layout.

    def write(self, name, raw):
        self.initial_material[name] = {"raw": raw, "mode": "100644"}
        path = gate.current_path(self.root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o644)

    def row(self, name, raw):
        return {"target_path": name, "sha256": gate.sha256(raw), "bytes": len(raw), "mode": "100644"}

    def add_bound(self, owner, files, raw, field):
        for name, expected in files.items():
            self.bound.append({"path": str(Path(owner).parent / name), "sha256": expected,
                               "owner_manifest": owner, "manifest_sha256": gate.sha256(raw), "manifest_field": field})

    def documents(self):
        return {p: item["raw"].decode() for p, item in self.source_material.items() if p.endswith(".md")}

    def test_valid_fixture_does_not_execute_table_code_by_default(self):
        with patch.object(gate.subprocess, "run") as run:
            result = gate.check(self.root)
        run.assert_not_called()
        self.assertEqual(result["hash_bound_documents"], 18)
        self.assertEqual(result["embedded_tables"], "NOT_RUN")
        self.assertEqual(result["product_builds_and_runtime"], "NOT_RUN")

    def test_new_missing_local_target_fails_without_allowlist(self):
        self.write(gate.DOCS + "/new.md", b"[new](missing.md)\n")
        with self.assertRaisesRegex(ValueError, "missing local target"):
            gate.check(self.root)

    def test_old_physical_href_is_not_resolved_by_historical_alias(self):
        self.write(gate.DOCS + "/legacy-link.md", b"[old](../rx_docs/docs/ordinary.md)\n")
        with self.assertRaisesRegex(ValueError, "missing local target"):
            gate.check(self.root)

    def test_current_document_json_is_checked(self):
        self.write(gate.DOCS + "/bad.json", b'{"x":1,"x":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            gate.check(self.root)

    def test_contract_bytes_and_repaired_manifest_do_not_bypass_frozen_proof(self):
        folder = gate.DOCS + "/contracts/v1.0/"
        self.write(folder + "norm-0.md", b"Changed normative bytes\n")
        with self.assertRaisesRegex(ValueError, "Normative document hash"):
            gate.check(self.root)
        manifest = gate.decode(gate.read(self.root, folder + "protocol_manifest.json"))
        manifest["normative_document_sha256"]["norm-0.md"] = gate.sha256(b"Changed normative bytes\n")
        raw = gate.canonical(manifest)
        self.write(folder + "protocol_manifest.json", raw)
        self.write(folder + "manifest_integrity.json", gate.canonical({"manifest_file": "protocol_manifest.json", "schema_hash_sha256": gate.sha256(raw)}))
        with self.assertRaisesRegex(ValueError, "Frozen normative"):
            gate.check(self.root)

    def test_workflow_contract_and_local_projection_are_checked(self):
        self.write(gate.DOCS + "/contracts/workflow-execution/v2/contract-0.md", b"changed\n")
        with self.assertRaisesRegex(ValueError, "Workflow contract hash"):
            gate.check(self.root)

    def test_projection_bytes_are_frozen_separately(self):
        self.source_material[self.projections[0]["target"]]["raw"] = b'{"changed":true}\n'
        with self.assertRaisesRegex(ValueError, "evidence projection differs"):
            gate.check(self.root)

    def test_historical_index_is_bound_while_current_prose_can_evolve(self):
        path = self.root / gate.ORIGINS
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "index bytes differ"):
            gate.check(self.root)
        self.write(gate.ORIGINS, gate.canonical(self.index))
        path = gate.current_path(self.root, self.document)
        path.write_bytes(b"A later introduction.\n" + path.read_bytes() + b"Changed prose\n")
        self.assertEqual(gate.check(self.root)["converted_occurrences"], 1)
        self.source_material[self.document]["raw"] += b"Tampered historical prose\n"
        with self.assertRaisesRegex(ValueError, "changed document bytes differ"):
            gate.check(self.root)

    def test_origin_ref_and_occurrence_line_are_cross_checked(self):
        for kind in ("ref", "line"):
            value = copy.deepcopy(self.index)
            if kind == "ref": value["origins"][0]["url"] = self.url.replace(gate.SOURCE_COMMIT, "main")
            else: value["occurrences"][0]["line"] = 999
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                gate.check_origins(self.root, value, gate.check_contracts(self.root), self.documents(), source_material=self.source_material)

    def test_symlink_target_is_not_a_valid_local_document(self):
        link = gate.current_path(self.root, gate.DOCS + "/alias.md")
        link.symlink_to(gate.current_path(self.root, self.document))
        with self.assertRaisesRegex(ValueError, "Symlink"):
            gate.check(self.root)

    def test_table_fence_must_be_unique_and_complete(self):
        path = gate.current_path(self.root, gate.DOCS + "/" + gate.TABLE_DOCUMENTS[1])
        path.write_bytes(path.read_bytes() + b"```python\nmissing close\n")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            gate.check(self.root)

    def test_tables_execute_only_explicitly_in_copied_docs_context(self):
        with patch.object(gate.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            result = gate.check(self.root, run_tables=True)
        self.assertEqual(run.call_count, 3)
        self.assertTrue(all(call.kwargs["cwd"] == self.root for call in run.call_args_list))
        self.assertEqual(result["embedded_tables"], 3)
        with patch.object(gate.subprocess, "run", return_value=SimpleNamespace(returncode=7)), self.assertRaisesRegex(ValueError, "table check failed"):
            gate.check(self.root, run_tables=True)


class HistoricalReaderTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / ".g0-validation"; folder.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="historical-docs-", dir=folder)
        self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
        self.git("init", "-q", "-b", "fixture")
        self.git("config", "user.name", "Disposable migration fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", os.devnull)
        self.paths = {"rx_docs/docs/fixture-%03d.md" % n for n in range(121)}
        for path in self.paths:
            p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("# Original\n")
        p = self.root / gate.ORIGINS; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("{}\n")
        self.git("add", "."); self.git("commit", "-q", "-m", "Disposable origin")
        self.anchor = self.git("rev-parse", "HEAD").strip()
        self.pins = patch.multiple(gate, M3_ANCHOR=self.anchor)
        self.pins.start(); self.addCleanup(self.pins.stop)
        rows = patch.object(gate, "import_rows", return_value={p: {} for p in self.paths})
        rows.start(); self.addCleanup(rows.stop)
    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout
    def test_reads_exact_ancestor_without_writing_checkout(self):
        before = (self.root / ".git/index").read_bytes()
        material = gate.historical_material(self.root)
        self.assertEqual(set(material), self.paths)
        self.assertTrue(all(v["raw"] == b"# Original\n" and v["mode"] == "100644" for v in material.values()))
        self.assertEqual((self.root / ".git/index").read_bytes(), before)
    def test_wrong_commit_and_nonancestor_are_rejected(self):
        with patch.object(gate, "M3_ANCHOR", "0" * 40), self.assertRaisesRegex(ValueError, "Historical Git read refused"):
            gate.historical_material(self.root)
        tree = self.git("rev-parse", "HEAD^{tree}").strip()
        other = self.git("commit-tree", tree, "-m", "Disconnected disposable root").strip()
        with patch.object(gate, "M3_ANCHOR", other), self.assertRaisesRegex(ValueError, "Historical Git read refused"):
            gate.historical_material(self.root)
    def test_unfinalized_anchor_and_redirected_context_are_rejected(self):
        with patch.object(gate, "M3_ANCHOR", "UNSET"), self.assertRaisesRegex(ValueError, "not finalized"):
            gate.historical_material(self.root)
        with patch.dict(os.environ, {"GIT_DIR": str(self.root / ".git")}), self.assertRaisesRegex(ValueError, "redirected"):
            gate.historical_material(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
