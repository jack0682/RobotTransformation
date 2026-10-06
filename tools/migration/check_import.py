#!/usr/bin/env python3
"""Offline verification of the frozen M2 import; no original checkout or regeneration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "provenance/import/M2-source-manifest.json"
PAYLOAD_SHA256 = "c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc"
PREFIXES = ("rx-platform", "rx-solutions", "rx_docs")
SOURCE_TUPLE = {
    "jack0682/rx-platform": ("22d8b18dc9770d552608d2c2cf48c93f4b2cbf59", "8ce3a467c453b3605f43d49a9120daea3437f202"),
    "jack0682/rx-solutions": ("0fed87b5f7e4bee0925613af9db4d515769a61ea", "c7716bdbc393797bc3cd8d3c40cb4a73ed01a4e9"),
    "jack0682/rx_docs": ("4384ed49e384c53e645f71757ce597292b928eb6", "fc044058911df75964c2debf57afc59af812eb31"),
}
SUBTREES = {"rx-platform": "8ce3a467c453b3605f43d49a9120daea3437f202",
            "rx-solutions": "c7716bdbc393797bc3cd8d3c40cb4a73ed01a4e9",
            "rx_docs": "dfef0c01f746dc8d28b29df50b710fbe361b201b"}
DOCS_TREE = "4eb56fb68816cda3a69f99b3e34ca7ffb0e072e7"
SELF_HASH_RULE = "SHA256(canonical payload); envelope and this manifest file excluded from 1718 source leaves"
FILE_COUNT = 1718
SOURCE_BYTES = 14799312
MODES = {"100644": 0o644, "100755": 0o755}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git_oid(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "Duplicate JSON key")
        value[key] = item
    return value


def decode(raw):
    require(len(raw) <= 4 * 1024 * 1024, "Import manifest is too large")
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))


def safe_path(value):
    require(isinstance(value, str) and value and not value.startswith("/") and not value.endswith("/"), "Invalid relative path")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value) and "\\" not in value and ":" not in value,
            "Control byte or non-POSIX path")
    parts = value.split("/")
    require(all(p not in ("", ".", "..") and p.casefold().rstrip(" .") != ".git" for p in parts), "Path traversal or nested Git path")
    require(str(PurePosixPath(value)) == value, "Noncanonical path")
    return value


def path_set(values):
    names = {}
    for value in values:
        safe_path(value)
        key = unicodedata.normalize("NFC", value).casefold()
        require(key not in names, "Duplicate/case/Unicode path alias")
        names[key] = value
    for key in names:
        parts = key.split("/")
        require(not any("/".join(parts[:i]) in names for i in range(1, len(parts))), "File/directory path collision")


def no_symlink_ancestors(path):
    for part in [path, *path.parents]:
        require(not part.is_symlink(), "Symlink path or ancestor refused")


def tree_oid(leaves):
    path_set(list(leaves))
    tree = {}
    for path, entry in leaves.items():
        node = tree
        parts = path.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = entry
    def encode(node):
        raw = bytearray()
        for name, value in sorted(node.items(), key=lambda p: p[0].encode() + (b"/" if isinstance(p[1], dict) else b"")):
            mode, oid = ("40000", encode(value)) if isinstance(value, dict) else value
            raw.extend(mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(oid))
        return git_oid("tree", bytes(raw))
    return encode(tree)


def validate_envelope(value):
    require(isinstance(value, dict) and value.get("schema") == "rx.migration-import-manifest.v1", "Wrong manifest schema")
    require(set(value) == {"schema", "payload", "payload_sha256", "self_hash_rule"} and value.get("self_hash_rule") == SELF_HASH_RULE, "Unexpected manifest envelope")
    payload = value.get("payload")
    require(isinstance(payload, dict), "Missing payload")
    require(value.get("payload_sha256") == PAYLOAD_SHA256 and digest(canonical(payload)) == PAYLOAD_SHA256,
            "Manifest differs from the independently pinned M2 payload")
    require(payload.get("target_repository") == "jack0682/RobotTransformation", "Wrong target repository")
    require(type(payload.get("file_count")) is int and payload["file_count"] == FILE_COUNT, "Wrong import count")
    require(type(payload.get("source_bytes")) is int and payload["source_bytes"] == SOURCE_BYTES, "Wrong source byte count")
    require(payload.get("subtree_oids") == SUBTREES and payload.get("docs_tree_oid") == DOCS_TREE, "Wrong frozen tree identities")
    sources = payload.get("sources")
    require(isinstance(sources, list) and len(sources) == len(SOURCE_TUPLE), "Wrong source tuple")
    require({r.get("repository"): (r.get("commit"), r.get("tree_oid")) for r in sources} == SOURCE_TUPLE, "Wrong source tuple")
    rows = payload.get("files")
    require(isinstance(rows, list) and len(rows) == FILE_COUNT, "Wrong file inventory")
    path_set([row["target_path"] for row in rows])
    for row in rows:
        source = row.get("source_repository")
        require(source in SOURCE_TUPLE and (row.get("source_commit"), row.get("source_tree_oid")) == SOURCE_TUPLE[source], "Source row identity differs")
        source_path, target = safe_path(row.get("source_path")), safe_path(row.get("target_path"))
        require(target == source.rsplit("/", 1)[1] + "/" + source_path, "Import path mapping differs")
        require(row.get("mode") in MODES and type(row.get("bytes")) is int and row["bytes"] >= 0, "Invalid source mode or size")
        require(re.fullmatch("[0-9a-f]{40}", row.get("blob_oid", "")) and re.fullmatch("[0-9a-f]{64}", row.get("sha256", "")), "Invalid source object hash")
    return payload


def load_manifest(root):
    path = root / MANIFEST
    no_symlink_ancestors(path)
    require(path.is_file(), "Import manifest is missing")
    return validate_envelope(decode(path.read_bytes()))


def read_sources(root, rows):
    expected = {r["target_path"]: r for r in rows}
    allowed_dirs = {str(p) for name in expected for p in PurePosixPath(name).parents if str(p) != "."}
    found = {}
    no_symlink_ancestors(root)
    for prefix in PREFIXES:
        folder = root / prefix
        require(folder.is_dir() and not folder.is_symlink(), "Imported component directory missing or symlinked")
        for current, dirs, files in os.walk(folder, followlinks=False):
            for name in dirs:
                path = Path(current) / name
                relative = path.relative_to(root).as_posix()
                require(not path.is_symlink() and relative in allowed_dirs, "Unexpected or symlinked imported directory")
            for name in files:
                path = Path(current) / name
                relative = path.relative_to(root).as_posix()
                safe_path(relative)
                require(relative in expected, "Extra imported file: " + relative)
                info = path.lstat()
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "Nonregular or hardlinked imported file")
                row = expected[relative]
                require(stat.S_IMODE(info.st_mode) == MODES[row["mode"]], "Imported file mode differs: " + relative)
                raw = path.read_bytes()
                require((len(raw), digest(raw), git_oid("blob", raw)) == (row["bytes"], row["sha256"], row["blob_oid"]),
                        "Imported file bytes differ: " + relative)
                found[relative] = (row["mode"], row["blob_oid"])
    require(set(found) == set(expected), "Missing imported source files")
    return found


def verify_trees(leaves, payload):
    actual = {prefix: tree_oid({p[len(prefix)+1:]: value for p, value in leaves.items() if p.startswith(prefix + "/")})
              for prefix in PREFIXES}
    require(actual == payload["subtree_oids"], "Imported component tree OID differs")
    docs = tree_oid({p[len('rx_docs/docs/'):]: value for p, value in leaves.items() if p.startswith('rx_docs/docs/')})
    require(docs == payload["docs_tree_oid"], "Imported docs tree OID differs")
    return actual


def git(root, *args, data=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    for key in list(env):
        if key in {"GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                   "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE", "GIT_NAMESPACE",
                   "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"} or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(key)
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(root), *args], env=env, input=data, capture_output=True)
    require(result.returncode == 0, "Read-only Git inventory failed: " + result.stderr.decode(errors="replace")[:1000])
    return result.stdout


def verify_git(root, expected):
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root.resolve(), "Target must be a Git worktree root")
    require(git(root, "rev-parse", "--show-object-format").strip() == b"sha1", "Expected SHA-1 Git object format")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    require(re.fullmatch("[0-9a-f]{40}", head), "Exact candidate HEAD missing")
    manifest_path = root / MANIFEST
    info = manifest_path.lstat()
    require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o644 and info.st_nlink == 1,
            "Manifest must be a regular 100644 file")
    expected = {**expected, MANIFEST: ("100644", git_oid("blob", manifest_path.read_bytes()))}
    entries = {}
    for item in git(root, "ls-files", "--stage", "-z", "--", *PREFIXES, MANIFEST).split(b"\0"):
        if not item: continue
        metadata, name = item.split(b"\t", 1)
        mode, oid, stage = metadata.decode().split()
        path = safe_path(name.decode())
        require(stage == "0" and path not in entries, "Conflicted or duplicate imported index entry")
        entries[path] = (mode, oid)
    require(entries == expected, "Imported source or provenance index set/mode/blob differs")
    committed = {}
    for item in git(root, "ls-tree", "-r", "-z", head, "--", *PREFIXES, MANIFEST).split(b"\0"):
        if not item: continue
        metadata, name = item.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        path = safe_path(name.decode())
        require(kind == "blob" and path not in committed, "Unsupported committed entry")
        committed[path] = (mode, oid)
    require(committed == expected, "Candidate HEAD source or provenance set/mode/blob differs")
    # Matching an index/tree reference is insufficient if its blob is unavailable.
    sizes = {oid: (root / path).stat().st_size for path, (_, oid) in expected.items()}
    oids = sorted(sizes)
    records = git(root, "cat-file", "--batch-check", data=("\n".join(oids) + "\n").encode()).splitlines()
    require(len(records) == len(oids), "Missing candidate Git blob availability record")
    for oid, record in zip(oids, records):
        require(record == f"{oid} blob {sizes[oid]}".encode(), "Candidate Git blob missing or size/type differs")
    return head


def verify(root, with_git=False):
    root = root.absolute()
    payload = load_manifest(root)
    leaves = read_sources(root, payload["files"])
    trees = verify_trees(leaves, payload)
    head = verify_git(root, leaves) if with_git else None
    return {"status": "PASS", "scope": "SOURCE_IMPORTED_UNVALIDATED",
            "checked": "filesystem+index+HEAD" if with_git else "filesystem only; uncommitted preflight",
            "candidate_head": head, "manifest_payload_sha256": PAYLOAD_SHA256,
            "files": len(leaves), "bytes": payload["source_bytes"], "subtree_oids": trees,
            "product_builds_and_runtime": "NOT_RUN", "historical_document_links": "NOT_VALIDATED_UNTIL_M4"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--git", action="store_true", help="Also require exact imported entries in index and candidate HEAD")
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.git), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Import verification refused: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
