#!/usr/bin/env python3
"""Verify the immutable signed M2 ancestor from raw Git objects, not today's product bytes."""
import argparse
import json
import os
import subprocess
import types
from pathlib import Path
import sys


ORIGIN = "0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0"
ROOT = Path(__file__).resolve().parents[2]
PROTECTED = ("tools/migration/check_import.py", "tools/migration/source_identities.py", "provenance/import/M2-source-identities.json")


def require(condition, message):
    if not condition: raise ValueError(message)


def no_symlink_ancestors(path):
    require(not any(p.is_symlink() for p in [path, *path.parents]), "Symlink path or ancestor refused")


def raw_git(root, *args, data=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    for key in list(env):
        if key in {"GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE", "GIT_NAMESPACE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"} or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(key)
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(root), *args], input=data, capture_output=True, env=env)
    require(result.returncode == 0, "Origin Git audit failed: " + result.stderr.decode(errors="replace")[:1000])
    return result.stdout


def verify(root):
    root = root.absolute()
    no_symlink_ancestors(root)
    git = lambda *args, **kw: raw_git(root, *args, **kw)
    require(Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() == root.resolve(), "Expected Git worktree root")
    require(git("rev-parse", "--is-shallow-repository").strip() == b"false", "Origin audit needs full history")
    require(not git("for-each-ref", "--format=%(refname)", "refs/replace/").strip(), "Replacement refs refused")
    graft = Path(git("rev-parse", "--git-path", "info/grafts").decode().strip())
    if not graft.is_absolute(): graft = root / graft
    require(not graft.exists() or not graft.read_bytes().strip(), "History grafts refused")
    head = git("rev-parse", "HEAD").decode().strip()
    git("merge-base", "--is-ancestor", ORIGIN, head)
    for name in PROTECTED:
        original = git("show", ORIGIN + ":" + name)
        current = root / name; no_symlink_ancestors(current)
        require(current.read_bytes() == original and git("show", head + ":" + name) == original,
                       "Frozen import/identity proof changed: " + name)
    # Only execute the verified immutable implementation, never a candidate module
    # before checking its pin (including a candidate no-op require() mutant).
    frozen = types.ModuleType("verified_m2_import")
    frozen.__file__ = str(root / "tools/migration/check_import.py")
    exec(compile(git("show", ORIGIN + ":tools/migration/check_import.py"), frozen.__file__, "exec"), frozen.__dict__)
    raw_manifest = git("show", ORIGIN + ":" + frozen.MANIFEST)
    payload = frozen.validate_envelope(frozen.decode(raw_manifest))
    path = root / frozen.MANIFEST
    no_symlink_ancestors(path)
    require(path.read_bytes() == raw_manifest and git("show", head + ":" + frozen.MANIFEST) == raw_manifest, "The immutable M2 provenance manifest was changed")
    expected = {r["target_path"]: (r["mode"], r["blob_oid"]) for r in payload["files"]}
    manifest_blob = frozen.git_oid("blob", raw_manifest)
    full_expected = {**expected, frozen.MANIFEST: ("100644", manifest_blob)}
    actual = {}
    for record in git("ls-tree", "-r", "-z", ORIGIN, "--", *frozen.PREFIXES, frozen.MANIFEST).split(b"\0"):
        if not record: continue
        meta, name = record.split(b"\t", 1); mode, kind, oid = meta.decode().split(); name = frozen.safe_path(name.decode())
        require(kind == "blob" and name not in actual, "Unsupported origin tree entry")
        actual[name] = (mode, oid)
    require(actual == full_expected, "Origin file/mode/blob inventory differs")
    sizes = {r["blob_oid"]: r["bytes"] for r in payload["files"]}
    hashes = {r["blob_oid"]: r["sha256"] for r in payload["files"]}
    oids = sorted(sizes)
    raw = git("cat-file", "--batch", data=("\n".join(oids) + "\n").encode())
    cursor = 0
    for oid in oids:
        end = raw.find(b"\n", cursor); require(end >= 0, "Truncated origin blob header")
        header = raw[cursor:end].decode(); cursor = end + 1
        require(header == f"{oid} blob {sizes[oid]}", "Origin blob is missing or has wrong type/size")
        data = raw[cursor:cursor+sizes[oid]]; cursor += sizes[oid]
        require(raw[cursor:cursor+1] == b"\n", "Truncated origin blob")
        cursor += 1
        require(frozen.git_oid("blob", data) == oid and frozen.digest(data) == hashes[oid], "Origin blob content differs")
    require(cursor == len(raw), "Unexpected origin blob data")
    frozen.verify_trees(expected, payload)
    return {"status": "PASS_IMMUTABLE_ORIGIN", "origin_commit": ORIGIN, "candidate_head": head,
            "origin_is_ancestor": True, "source_files": len(expected), "source_bytes": payload["source_bytes"],
            "manifest_payload_sha256": frozen.PAYLOAD_SHA256,
            "scope": "Original import objects only; current source is checked by the full CI union",
            "signature_scope": "The required full-head OpenPGP/DCO job covers this ancestor; this command does not replace it"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--root", type=Path, default=ROOT); args = p.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        p.exit(1, "Origin audit refused: " + str(exc) + "\n")
