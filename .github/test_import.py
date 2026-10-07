#!/usr/bin/env python3
"""M2 static import refusal fixtures; no old checkout, Git mutation, network or product execution."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/migration"))
sys.path.insert(0, str(ROOT / "tools/governance"))
import check_import as imp
import check_ci
import check_repository as repository


class ImportFixtures(unittest.TestCase):
    def setUp(self):
        (ROOT / ".g0-validation").mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix="m2-fixture-", dir=ROOT / ".g0-validation")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.raw = {"rx-platform/a.txt": b"P\r\n", "rx-solutions/tool": b"S\n", "rx_docs/docs/readme.md": b"D\n"}
        self.rows = []
        for name, data in self.raw.items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            mode = "100755" if name.endswith("/tool") else "100644"; path.chmod(imp.MODES[mode])
            prefix, relative = name.split("/", 1)
            source = "jack0682/" + prefix
            self.rows.append({"target_path": name, "source_repository": source,
                              "source_commit": imp.SOURCE_TUPLE[source][0], "source_tree_oid": imp.SOURCE_TUPLE[source][1],
                              "source_path": relative, "mode": mode, "bytes": len(data),
                              "sha256": imp.digest(data), "blob_oid": imp.git_oid("blob", data)})
        self.leaves = {r["target_path"]: (r["mode"], r["blob_oid"]) for r in self.rows}
        self.trees = {prefix: imp.tree_oid({p[len(prefix)+1:]: value for p, value in self.leaves.items() if p.startswith(prefix+'/')}) for prefix in imp.PREFIXES}
        self.docs = imp.tree_oid({"readme.md": self.leaves["rx_docs/docs/readme.md"]})
        self.payload = {"target_repository": "jack0682/RobotTransformation", "file_count": len(self.rows),
                        "source_bytes": sum(r["bytes"] for r in self.rows), "subtree_oids": self.trees,
                        "docs_tree_oid": self.docs, "sources": [{"repository": key, "commit": v[0], "tree_oid": v[1]} for key, v in imp.SOURCE_TUPLE.items()],
                        "files": self.rows}
        self.pin = imp.digest(imp.canonical(self.payload))
        self.value = {"schema": "rx.migration-import-manifest.v1", "payload": self.payload,
                      "payload_sha256": self.pin, "self_hash_rule": imp.SELF_HASH_RULE}
        manifest = self.root / imp.MANIFEST; manifest.parent.mkdir(parents=True); manifest.write_bytes(imp.canonical(self.value)); manifest.chmod(0o644)

    def synthetic_pin(self):
        # Small explicit fixture; production constants remain the frozen 1718-file import.
        return patch.multiple(imp, PAYLOAD_SHA256=self.pin, FILE_COUNT=3,
                              SOURCE_BYTES=self.payload["source_bytes"], SUBTREES=self.trees, DOCS_TREE=self.docs)

    def test_positive_fixture_checks_bytes_modes_and_trees(self):
        with self.synthetic_pin():
            self.assertEqual(imp.load_manifest(self.root), self.payload)
            self.assertEqual(imp.verify(self.root)["files"], 3)

    def test_altered_payload_cannot_repair_itself_by_updating_self_hash(self):
        value = copy.deepcopy(self.value); value["payload"]["files"][0]["sha256"] = "0"*64
        value["payload_sha256"] = imp.digest(imp.canonical(value["payload"]))
        with self.synthetic_pin(), self.assertRaisesRegex(ValueError, "independently pinned"):
            imp.validate_envelope(value)

    def test_changed_envelope_claim_is_refused(self):
        value = copy.deepcopy(self.value); value["self_hash_rule"] = "All product tests passed"
        with self.synthetic_pin(), self.assertRaisesRegex(ValueError, "envelope"):
            imp.validate_envelope(value)

    def test_duplicate_json_keys_and_non_finite_values_refused(self):
        for value in (b'{"payload":{},"payload":{}}', b'{"payload":NaN}', b'{"payload":Infinity}'):
            with self.subTest(value=value), self.assertRaises(ValueError): imp.decode(value)

    def test_unsafe_alias_and_colliding_paths_refused(self):
        for paths in (["../outside"], ["/absolute"], ["a\\b"], ["a/.GiT/config"], ["a", "a/b"], ["A", "a"], ["x/e\u0301", "x/\u00e9"]):
            with self.subTest(paths=paths), self.assertRaises(ValueError): imp.path_set(paths)

    def test_modified_bytes_or_line_endings_refused(self):
        file = self.root / "rx-platform/a.txt"; file.write_bytes(b"P\n")
        with self.assertRaisesRegex(ValueError, "bytes differ"): imp.read_sources(self.root, self.rows)

    def test_missing_and_extra_files_including_ignored_files_refused(self):
        file = self.root / "rx-platform/a.txt"; file.unlink()
        with self.assertRaisesRegex(ValueError, "Missing"): imp.read_sources(self.root, self.rows)
        file.write_bytes(self.raw["rx-platform/a.txt"]); file.chmod(0o644)
        extra = self.root / "rx-platform/.ignored-source"; extra.write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "Extra"): imp.read_sources(self.root, self.rows)

    def test_extra_empty_directory_refused(self):
        (self.root / "rx-platform/extra").mkdir()
        with self.assertRaisesRegex(ValueError, "directory"): imp.read_sources(self.root, self.rows)

    def test_mode_change_refused(self):
        (self.root / "rx-solutions/tool").chmod(0o644)
        with self.assertRaisesRegex(ValueError, "mode differs"): imp.read_sources(self.root, self.rows)

    def test_symlink_leaf_and_directory_refused(self):
        file = self.root / "rx-platform/a.txt"; file.unlink(); file.symlink_to(self.root / "rx-solutions/tool")
        with self.assertRaisesRegex(ValueError, "Nonregular"): imp.read_sources(self.root, self.rows)
        file.unlink(); file.write_bytes(self.raw["rx-platform/a.txt"])
        (self.root / "rx-platform/link").symlink_to(self.root / "rx_docs", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "directory"): imp.read_sources(self.root, self.rows)

    def test_hardlinked_source_refused(self):
        os.link(self.root / "rx-platform/a.txt", self.root / "another-link")
        with self.assertRaisesRegex(ValueError, "hardlinked"): imp.read_sources(self.root, self.rows)

    def test_symlinked_manifest_refused(self):
        file = self.root / imp.MANIFEST; backup = self.root / "manifest-copy"; backup.write_bytes(file.read_bytes()); file.unlink(); file.symlink_to(backup)
        with self.synthetic_pin(), self.assertRaisesRegex(ValueError, "Symlink"): imp.load_manifest(self.root)

    def test_tree_sorting_orders_directory_as_name_slash(self):
        a, b, c = (imp.git_oid("blob", x) for x in (b"a", b"b", b"c"))
        subtree = imp.git_oid("tree", b"100644 z\0" + bytes.fromhex(a))
        raw = b"100644 a.c\0" + bytes.fromhex(b) + b"40000 a\0" + bytes.fromhex(subtree) + b"100755 a0\0" + bytes.fromhex(c)
        self.assertEqual(imp.tree_oid({"a/z": ("100644", a), "a.c": ("100644", b), "a0": ("100755", c)}), imp.git_oid("tree", raw))

    def git_inventory(self, *, missing_manifest=False, wrong_mode=False, conflict=False, wrong_head=False, missing_object=False):
        manifest_oid = imp.git_oid("blob", (self.root / imp.MANIFEST).read_bytes())
        entries = {**self.leaves, imp.MANIFEST: ("100644", manifest_oid)}
        if missing_manifest: entries.pop(imp.MANIFEST)
        indexed = dict(entries)
        if wrong_mode: indexed["rx-solutions/tool"] = ("100644", indexed["rx-solutions/tool"][1])
        def git(root, *args, data=None):
            if "--show-toplevel" in args: return str(self.root).encode()
            if "--show-object-format" in args: return b"sha1"
            if args == ("rev-parse", "HEAD"): return b"a"*40
            if args[0] == "ls-files":
                return b"".join(f"{mode} {oid} {'1' if conflict else '0'}\t{name}".encode()+b"\0" for name, (mode, oid) in indexed.items())
            if args[0] == "cat-file":
                sizes = {oid: (self.root / name).stat().st_size for name, (_, oid) in entries.items()}
                return b"\n".join((oid + " missing" if missing_object else f"{oid} blob {sizes[oid]}").encode() for oid in data.decode().splitlines()) + b"\n"
            if args[0] == "ls-tree":
                values = dict(entries)
                if wrong_head: values["rx-platform/a.txt"] = ("100644", "f"*40)
                return b"".join(f"{mode} blob {oid}\t{name}".encode()+b"\0" for name, (mode, oid) in values.items())
            raise AssertionError(args)
        return git

    def test_git_inventory_checks_source_and_manifest_at_index_and_head(self):
        with patch.object(imp, "git", side_effect=self.git_inventory()):
            self.assertEqual(imp.verify_git(self.root, self.leaves), "a"*40)
        for option in ("missing_manifest", "wrong_mode", "conflict", "wrong_head", "missing_object"):
            with self.subTest(option=option), patch.object(imp, "git", side_effect=self.git_inventory(**{option: True})), self.assertRaises(ValueError):
                imp.verify_git(self.root, self.leaves)

    def test_provenance_must_match_candidate_not_only_frozen_payload(self):
        api = self.git_inventory()
        manifest = self.root / imp.MANIFEST; manifest.write_bytes(manifest.read_bytes() + b"\n")
        with patch.object(imp, "git", side_effect=api), self.assertRaisesRegex(ValueError, "provenance"):
            imp.verify_git(self.root, self.leaves)


class StageBoundaryTests(unittest.TestCase):
    def test_exact_m2_required_jobs(self):
        self.assertEqual(check_ci.IMPORT_SCOPE["required_jobs"], ["repository", "commit_policy", "import_fidelity", "sdk_parity", "static_identity"])
        good = {name: {"result": "success"} for name in check_ci.IMPORT_SCOPE["required_jobs"]}
        check_ci.check(good, check_ci.IMPORT_SCOPE)
        for name in good:
            for outcome in ("failure", "cancelled", "skipped", "neutral", None):
                changed = copy.deepcopy(good); changed[name]["result"] = outcome
                with self.subTest(name=name, outcome=outcome), self.assertRaises(ValueError): check_ci.check(changed, check_ci.IMPORT_SCOPE)
            missing = dict(good); missing.pop(name)
            with self.assertRaises(ValueError): check_ci.check(missing, check_ci.IMPORT_SCOPE)

    def test_bootstrap_scope_is_not_relabelled_product_success(self):
        good = {name: {"result": "success"} for name in check_ci.BOOTSTRAP_SCOPE["required_jobs"]}
        check_ci.check(good, check_ci.BOOTSTRAP_SCOPE)
        with self.assertRaises(ValueError): check_ci.check(good, check_ci.IMPORT_SCOPE)
        invalid = {**check_ci.IMPORT_SCOPE, "product_validation": "PASS"}
        with self.assertRaises(ValueError): check_ci.stage(invalid)

    def test_production_manifest_pin_is_exact_and_has_no_host_paths(self):
        self.assertEqual(imp.PAYLOAD_SHA256, "c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc")
        payload = imp.load_manifest(ROOT)
        self.assertEqual(payload["file_count"], 1718)
        text = (ROOT / imp.MANIFEST).read_text()
        self.assertNotIn("/Users/", text)
        self.assertNotIn("/home/", text)

    def test_current_root_policy_and_undeclared_root_rejection(self):
        try:
            git_root = Path(repository.git("rev-parse", "--show-toplevel").strip()).resolve()
        except ValueError:
            git_root = None
        if git_root == ROOT.resolve():
            paths = repository.git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
            files = sorted({ROOT / name for name in paths if name})
        else:
            # Only the deliberately Git-free staging fixture uses filesystem inventory.
            files = [p for p in ROOT.rglob("*") if (p.is_file() or p.is_symlink())
                     and p.relative_to(ROOT).parts[0] not in {".git", ".g0-validation"} and "__pycache__" not in p.parts]
        self.assertEqual(repository.check(ROOT, files), [])
        self.assertTrue(repository.check(ROOT, files + [ROOT / "arbitrary-product.py"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
