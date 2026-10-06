#!/usr/bin/env python3
"""Check current copied documents and pinned origin records, without fetching URLs.

The origin index was verified against frozen original Git objects when prepared.
Its pin authenticates that reviewed record; this check is not a live URL probe.
Only --run-tables executes the three existing embedded document-table checks.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import subprocess
import sys
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = "rx_docs/docs"
ORIGINS = "provenance/import/M3-document-origins.json"
ORIGIN_INDEX_SHA256 = "245f00ebc384de5cb4836eb9ecad761b9ddae4926490232e2fd674c3fc51aff2"
SOURCE_REPOSITORY = "jack0682/rx_docs"
SOURCE_COMMIT = "4384ed49e384c53e645f71757ce597292b928eb6"
SOURCE_TREE = "fc044058911df75964c2debf57afc59af812eb31"
IMPORT_MANIFEST = "provenance/import/M2-source-manifest.json"
IMPORT_PAYLOAD_SHA256 = "c154b96c9bfb63d70d837dfefc2c41cc37e586bf26c754a9f6291e2e538be5fc"
ORIGIN_COUNTS = (94, 120, 42, 18)
TABLE_DOCUMENTS = ("21_declaration_reuse_measurement.md", "22_open_items_boundary.md",
                   "23_handover_counterexamples.md")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))


def relative(value):
    require(isinstance(value, str) and value and not value.startswith("/"), "Invalid relative document path")
    require("\\" not in value and ":" not in value and not any(ord(c) < 32 for c in value), "Unsafe document path")
    require(all(p not in ("", ".", "..") and p.casefold().rstrip(" .") != ".git"
                for p in value.split("/")), "Document path traversal or Git metadata")
    require(str(PurePosixPath(value)) == value, "Noncanonical document path")
    return value


def current_path(root, name):
    """M3 path lookup. Later layout transitions must supply reviewed path evidence."""
    path = root / relative(name)
    for parent in [path, *path.parents]:
        require(not parent.is_symlink(), "Symlink document path: " + name)
    return path


def read(root, name):
    path = current_path(root, name)
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), "Missing regular document file: " + name)
    return path.read_bytes()


def document_paths(root):
    folder = current_path(root, DOCS)
    require(folder.is_dir(), "Current document directory is missing")
    paths = []
    def failed(error):
        raise ValueError("Unreadable document directory: " + str(error))
    for directory, dirs, files in os.walk(folder, followlinks=False, onerror=failed):
        for name in dirs + files:
            path = Path(directory) / name
            require(not path.is_symlink(), "Symlink in current documents: " + str(path))
        for name in files:
            path = Path(directory) / name
            require(stat.S_ISREG(path.stat().st_mode), "Nonregular current document: " + str(path))
            paths.append(path.relative_to(root).as_posix())
    return sorted(paths)


def rendered_mask(text):
    # Preserve offsets for provenance occurrence/line checks.
    chars = list(text)
    def blank(start, end):
        for i in range(start, end):
            if chars[i] not in "\r\n":
                chars[i] = " "
    for match in re.finditer(r"<!--.*?-->", text, re.S):
        blank(match.start(), match.end())
    offset, fence = 0, None
    for line in text.splitlines(keepends=True):
        if fence:
            blank(offset, offset + len(line))
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}[ \t]*\r?\n?$", line):
                fence = None
        else:
            match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if match:
                fence = (match[1][0], len(match[1]))
                blank(offset, offset + len(line))
            elif re.match(r"^(?: {4}|\t)", line):
                blank(offset, offset + len(line))
        offset += len(line)
    masked = "".join(chars)
    at = 0
    while at < len(masked):
        if masked[at] != "`" or (at and masked[at - 1] == "\\"):
            at += 1
            continue
        end = at + 1
        while end < len(masked) and masked[end] == "`":
            end += 1
        close = re.search(r"(?<!`)" + re.escape(masked[at:end]) + r"(?!`)", masked[end:])
        if close:
            stop = end + close.end()
            blank(at, stop)
            at = stop
        else:
            at = end
    return "".join(chars)


def destination(mask, at):
    while at < len(mask) and mask[at].isspace():
        at += 1
    if at == len(mask):
        return None
    if mask[at] == "<":
        end = mask.find(">", at + 1)
        return None if end < 0 else (at + 1, end)
    start, depth = at, 0
    while at < len(mask):
        char = mask[at]
        if char == "\\" and at + 1 < len(mask):
            at += 2
            continue
        if char.isspace() or (char == ")" and depth == 0):
            break
        depth += (char == "(") - (char == ")")
        at += 1
    return (start, at) if at > start else None


def link_spans(text):
    mask, spans = rendered_mask(text), {}
    for match in re.finditer(r"(?<!\\)\]\(", mask):
        found = destination(mask, match.end())
        if found:
            spans[found] = "inline_or_image"
    for match in re.finditer(r"(?m)^ {0,3}\[(?!\^)[^\]\n]+\]:[ \t]*", mask):
        found = destination(mask, match.end())
        if found:
            spans[found] = "reference_definition"
    for match in re.finditer(r'''\b(?:href|src)\s*=\s*(["'])(.*?)\1''', mask, re.I | re.S):
        spans[(match.start(2), match.end(2))] = "html_attribute"
    return [{"href": text[a:b], "line": text.count("\n", 0, a) + 1, "syntax": kind}
            for (a, b), kind in sorted(spans.items())]


def local_target(document, href):
    parsed = urlsplit(html.unescape(href))
    require(parsed.scheme != "file", "Machine-specific file URL: " + href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    decoded = unquote(parsed.path)
    require(not decoded.startswith("/") and "\\" not in decoded and "\0" not in decoded,
            "Invalid local document target: " + href)
    target = posixpath.normpath(posixpath.join(posixpath.dirname(document), decoded))
    return relative(target)


def check_local_links(root, document, text):
    count = 0
    for link in link_spans(text):
        target = local_target(document, link["href"])
        if target is not None:
            path = current_path(root, target)
            require(path.exists(), f"{document}:{link['line']}: missing local target {link['href']}")
            count += 1
    return count


def check_contracts(root):
    protected = {}
    for family, integrity_key in (("contracts/v1.0", "schema_hash_sha256"),
                                  ("cell_operations/v1.0", "cell_manifest_sha256")):
        folder = DOCS + "/" + family
        manifest_path = folder + "/protocol_manifest.json"
        raw = read(root, manifest_path)
        manifest = decode(raw)
        integrity = decode(read(root, folder + "/manifest_integrity.json"))
        require(integrity.get("manifest_file") == "protocol_manifest.json"
                and integrity.get(integrity_key) == sha256(raw), "Protocol manifest integrity differs: " + family)
        documents = manifest.get("normative_document_sha256")
        require(isinstance(documents, dict) and len(documents) == 4, "Expected four normative documents: " + family)
        for name, expected in documents.items():
            path = folder + "/" + relative(name)
            require(sha256(read(root, path)) == expected, "Normative document hash differs: " + path)
            protected[path] = (expected, manifest_path, sha256(raw), "normative_document_sha256")
    manifest_path = DOCS + "/contracts/workflow-execution/v2/manifest.json"
    raw = read(root, manifest_path)
    manifest = decode(raw)
    require(manifest.get("schema") == "rx.contract-revision.v1", "Unexpected workflow manifest schema")
    documents = manifest.get("files")
    require(isinstance(documents, dict) and len(documents) == 10, "Expected ten workflow contract files")
    for name, expected in documents.items():
        path = str(PurePosixPath(manifest_path).parent / relative(name))
        require(sha256(read(root, path)) == expected, "Workflow contract hash differs: " + path)
        protected[path] = (expected, manifest_path, sha256(raw), "files")
    require(len(protected) == 18, "Normative document inventory differs")
    return protected


def import_rows(root):
    manifest = decode(read(root, IMPORT_MANIFEST))
    payload = manifest.get("payload")
    require(manifest.get("payload_sha256") == IMPORT_PAYLOAD_SHA256
            and sha256(canonical(payload)) == IMPORT_PAYLOAD_SHA256, "Frozen import payload differs")
    return {row["target_path"]: row for row in payload["files"]}


def load_origins(root):
    raw = read(root, ORIGINS)
    require(sha256(raw) == ORIGIN_INDEX_SHA256, "Reviewed M3 document-origin index bytes differ")
    return decode(raw)


def check_origins(root, index, protected, documents):
    require(index.get("schema") == "rx.document-origin-index.v1"
            and index.get("source_repository") == SOURCE_REPOSITORY
            and index.get("source_commit") == SOURCE_COMMIT
            and index.get("source_tree_oid") == SOURCE_TREE, "Document origin authority differs")
    groups = [index.get(name) for name in ("origins", "occurrences", "changed_documents", "hash_bound_documents")]
    require(all(isinstance(group, list) for group in groups)
            and tuple(map(len, groups)) == ORIGIN_COUNTS, "Document-origin inventory differs")
    origins, occurrences, changed, bound = groups
    by_url = {}
    for record in origins:
        path = relative(record["path"])
        url = "https://github.com/" + SOURCE_REPOSITORY + "/blob/" + SOURCE_COMMIT + "/" + quote(path, safe="/-._~")
        require(record.get("url") == url and record.get("repository") == SOURCE_REPOSITORY
                and record.get("commit") == SOURCE_COMMIT and record.get("kind") == "blob"
                and record.get("mode") in ("100644", "100755"), "Origin URL/path/object authority differs")
        require(not record.get("fragment") and not record.get("query")
                and record.get("fragment_proof") == {"status": "NO_FRAGMENT", "fragment": ""}, "Unsupported converted origin fragment/query")
        require(re.fullmatch(r"[0-9a-f]{40}", record.get("git_object_oid", ""))
                and re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", ""))
                and type(record.get("bytes")) is int and record["bytes"] >= 0, "Invalid recorded origin object proof")
        require(url not in by_url, "Duplicate origin URL")
        by_url[url] = record
    frozen = import_rows(root)
    changed_by_path = {}
    for item in changed:
        path = relative(item["path"])
        require(path.startswith(DOCS + "/") and path not in changed_by_path and path not in protected,
                "Invalid, duplicate or normative changed document")
        before = frozen.get(path, {})
        require((item.get("before_sha256"), item.get("before_bytes"), item.get("mode"))
                == (before.get("sha256"), before.get("bytes"), before.get("mode")), "Changed document preimage differs: " + path)
        raw = read(root, path)
        require((sha256(raw), len(raw)) == (item.get("after_sha256"), item.get("after_bytes")),
                "M3 changed document bytes differ: " + path)
        require(stat.S_IMODE(current_path(root, path).stat().st_mode) == int(item["mode"], 8) & 0o777,
                "M3 changed document mode differs: " + path)
        changed_by_path[path] = item
    expected = Counter()
    used_origins = set()
    for item in occurrences:
        document, href = item["document"], item["new_href"]
        require(document in changed_by_path and href in by_url, "Occurrence lacks changed document or origin")
        record = by_url[href]
        old_target = local_target(document.removeprefix("rx_docs/"), item["old_href"])
        require(old_target == item.get("old_destination") == record["path"]
                and item.get("origin_git_object_oid") == record["git_object_oid"], "Occurrence origin proof differs")
        require(type(item.get("line")) is int and item["line"] > 0, "Invalid occurrence line")
        expected[(document, item["line"], item["syntax"], href)] += 1
        used_origins.add(href)
    actual = Counter((path, item["line"], item["syntax"], item["href"])
                     for path, text in documents.items() for item in link_spans(text) if item["href"] in by_url)
    require(actual == expected and used_origins == set(by_url), "Converted href occurrence inventory differs")
    recorded = {}
    for item in bound:
        path = item["path"]
        require(path not in recorded, "Duplicate hash-bound origin record")
        recorded[path] = (item["sha256"], item["owner_manifest"], item["manifest_sha256"], item["manifest_field"])
    require(recorded == protected, "Frozen normative document or owner-manifest proof differs")
    projections = index.get("unchanged_local_evidence_projections")
    require(isinstance(projections, list) and len(projections) == 2, "Expected two local evidence projections")
    for item in projections:
        require(local_target(item["document"], item["href"]) == item["target"], "Projection path mapping differs")
        row = frozen.get(item["target"], {})
        raw = read(root, item["target"])
        require((sha256(raw), len(raw)) == (row.get("sha256"), row.get("bytes")), "Frozen local evidence projection differs")
        decode(raw)
        require(any(link["line"] == item["line"] and link["href"] == item["href"]
                    for link in link_spans(documents[item["document"]])), "Projection href missing from normative document")
    return {"recorded_origins": len(origins), "converted_occurrences": len(occurrences), "changed_documents": len(changed)}


def table_blocks(root):
    blocks = []
    for name in TABLE_DOCUMENTS:
        text = read(root, DOCS + "/" + name).decode("utf-8")
        openings = re.findall(r"^```python[^\S\n]*$", text, re.MULTILINE)
        found = re.findall(r"^```python[^\S\n]*\n(.*?)^```[^\S\n]*$", text, re.MULTILINE | re.DOTALL)
        require(len(openings) == len(found) == 1, name + ": expected exactly one complete Python fence")
        blocks.append((name, found[0]))
    return blocks


def check(root, run_tables=False):
    root = Path(root).absolute()
    paths = document_paths(root)
    documents, json_count, links = {}, 0, 0
    for name in paths:
        if name.endswith(".json"):
            decode(read(root, name))
            json_count += 1
        elif name.endswith(".md"):
            text = read(root, name).decode("utf-8")
            documents[name] = text
            links += check_local_links(root, name, text)
    protected = check_contracts(root)
    origins = check_origins(root, load_origins(root), protected, documents)
    blocks = table_blocks(root)
    if run_tables:
        for name, block in blocks:
            print("Checking embedded table: " + name, flush=True)
            result = subprocess.run([sys.executable, "-B", "-c", block], cwd=root / "rx_docs",
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0"))
            require(result.returncode == 0, name + ": embedded table check failed")
    return {"status": "DOCUMENT_CHECKS_OK", "scope": "CURRENT_DOCUMENTS_AND_PINNED_ORIGIN_RECORDS",
            "json_files": json_count, "markdown_files": len(documents), "local_targets": links,
            "hash_bound_documents": len(protected), **origins,
            "embedded_tables": len(blocks) if run_tables else "NOT_RUN",
            "external_network_and_anchor_checks": "NOT_RUN",
            "origin_proof_scope": "Pinned records verified from frozen original Git objects during preparation",
            "product_builds_and_runtime": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--run-tables", action="store_true")
    args = parser.parse_args()
    print(json.dumps(check(args.root, args.run_tables), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("Document checks refused: " + str(error), file=sys.stderr)
        raise SystemExit(1)
