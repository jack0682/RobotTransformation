#!/usr/bin/env python3
"""Document-gate negatives in task-scoped fixtures; no network or product execution."""
from __future__ import annotations

import copy
import json
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

    def write(self, name, raw):
        path = self.root / name
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
        return {p: gate.read(self.root, p).decode() for p in gate.document_paths(self.root) if p.endswith(".md")}

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
        self.write(self.projections[0]["target"], b'{"changed":true}\n')
        with self.assertRaisesRegex(ValueError, "evidence projection differs"):
            gate.check(self.root)

    def test_reviewed_index_and_current_after_bytes_are_bound(self):
        path = self.root / gate.ORIGINS
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "index bytes differ"):
            gate.check(self.root)
        self.write(gate.ORIGINS, gate.canonical(self.index))
        path = self.root / self.document
        path.write_bytes(path.read_bytes() + b"Changed prose\n")
        with self.assertRaisesRegex(ValueError, "changed document bytes differ"):
            gate.check(self.root)

    def test_origin_ref_and_occurrence_line_are_cross_checked(self):
        for kind in ("ref", "line"):
            value = copy.deepcopy(self.index)
            if kind == "ref": value["origins"][0]["url"] = self.url.replace(gate.SOURCE_COMMIT, "main")
            else: value["occurrences"][0]["line"] = 999
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                gate.check_origins(self.root, value, gate.check_contracts(self.root), self.documents())

    def test_symlink_target_is_not_a_valid_local_document(self):
        link = self.root / gate.DOCS / "alias.md"
        link.symlink_to(self.root / self.document)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            gate.check(self.root)

    def test_table_fence_must_be_unique_and_complete(self):
        path = self.root / gate.DOCS / gate.TABLE_DOCUMENTS[1]
        path.write_bytes(path.read_bytes() + b"```python\nmissing close\n")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            gate.check(self.root)

    def test_tables_execute_only_explicitly_in_copied_docs_context(self):
        with patch.object(gate.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            result = gate.check(self.root, run_tables=True)
        self.assertEqual(run.call_count, 3)
        self.assertTrue(all(call.kwargs["cwd"] == self.root / "rx_docs" for call in run.call_args_list))
        self.assertEqual(result["embedded_tables"], 3)
        with patch.object(gate.subprocess, "run", return_value=SimpleNamespace(returncode=7)), self.assertRaisesRegex(ValueError, "table check failed"):
            gate.check(self.root, run_tables=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
