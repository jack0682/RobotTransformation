#!/usr/bin/env python3
"""One advisory Linux diagnostic projection; never replaces required CI or M5.

The source checkout stays unchanged. Only an observer test is changed in an
exported projection. Original UNKNOWN and nonzero test results remain failures.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True

SOURCE_SHA = "314c9f323a7dd8865a3f9e2b1347325684858c8e"
SOURCE_TREE = "21d007574b121652f8bf403115868b8a5d33a69c"
TEST = "rx-solutions/runtime/rx-host/tests/workflow_simulation.rs"
TEST_SHA = "9b20489e064c0e07f7a1c57ca9b5e22406cfee151ff517765bfae8e45fa79b24"
OBSERVER_SHA = "fe8925362e3be05d4ccbdf6a61debdfc210de1e0db36c207b34908e5f4b86700"
CALCULATOR = "tools/migration/source_identities.py"
CALCULATOR_SHA = "9c6a32bb5fe7ecb1ea6af1e94af1c56de4b6e4db202228d06df267ba3d05ca17"
BASELINE = "provenance/import/M2-source-identities.json"
BASELINE_SHA = "e2016d2af1bdb63cdef079738ffba5ebaf47a66f78ae0391b8ed02e85a0334f5"
PREFIX = "tools/diagnostics/workflow_simulation/"
MAX_LOG = 16 * 1024 * 1024
MAX_FACT = 131072
KEY_MARKER = re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
AUTH_MARKER = re.compile(rb"(?i)(?:authorization\s*:\s*(?:bearer|basic)\s+\S+|(?:set-cookie|cookie)\s*:\s*\S+)")
TOKEN_MARKER = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")
SECRET_FIELDS = {"private_key", "private_seed", "private_seed_hex", "client_token", "worker_token",
                 "access_token", "refresh_token", "session_token", "password", "password_hash"}


class DiagnosticRefusal(ValueError):
    pass


def require(value, message):
    if not value:
        raise DiagnosticRefusal(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def clean_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts and not any(p.is_symlink() for p in [path, *path.parents]), "Unsafe path")
    return path.resolve()


def relative(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name
            and not any(ord(c) < 32 for c in name), "Unsafe source name")
    parts = PurePosixPath(name)
    require(not parts.is_absolute() and str(parts) == name and all(p not in ("", ".", "..") for p in name.split("/")), "Unsafe source name")
    return name


def environment():
    forbidden = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_NAMESPACE",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_COUNT",
                 "GIT_CONFIG_PARAMETERS", "GIT_REPLACE_REF_BASE", "GIT_CONFIG", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS",
                 "RUSTC", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTFLAGS"}
    require(not any(k in forbidden or k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_", "CARGO_BUILD_RUSTC"))
                    or (k.startswith("CARGO_TARGET_") and k.endswith("_RUSTFLAGS")) for k in os.environ), "Redirected build or Git context")
    return dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
                GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1", CARGO_BUILD_JOBS="2",
                RUSTUP_TOOLCHAIN="1.98.1", RUST_BACKTRACE="1", CARGO_TERM_COLOR="never")


def git(root, *args):
    command = ["git", "--no-replace-objects", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
               "-c", "core.fsmonitor=false", "-C", str(root), *args]
    result = subprocess.run(command, capture_output=True, env=environment())
    require(result.returncode == 0, "Read-only Git operation failed")
    return result.stdout


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Symlink in projection")
        if path.is_dir():
            continue
        require(path.is_file(), "Nonregular projection leaf")
        raw = path.read_bytes()
        result[path.relative_to(root).as_posix()] = {"sha256": digest(raw), "bytes": len(raw),
                                                   "mode": "100755" if path.stat().st_mode & 0o111 else "100644"}
    return result


def source_rows(root, expected_head):
    require(re.fullmatch(r"[0-9a-f]{40}", expected_head), "Exact control SHA required")
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root, "Expected Git root")
    require(git(root, "rev-parse", "HEAD").decode().strip() == expected_head, "Checkout head differs")
    require(not git(root, "status", "--porcelain=v1", "--untracked-files=all").strip(), "Checkout is not clean")
    require(not git(root, "for-each-ref", "--format=%(refname)", "refs/replace/").strip(), "Replace refs refused")
    rows = {}
    for record in git(root, "ls-tree", "-r", "-z", expected_head).split(b"\0"):
        if not record:
            continue
        header, name = record.split(b"\t", 1); mode, kind, oid = header.decode().split(); name = relative(name.decode())
        require(kind == "blob" and mode in ("100644", "100755") and name not in rows, "Unexpected Git leaf")
        path = clean_path(root / name)
        require(path.is_relative_to(root) and path.is_file(), "Source leaf missing")
        raw = path.read_bytes()
        require(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == oid, "Source bytes differ from Git")
        actual_mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        require(actual_mode == mode, "Source executable mode differs")
        rows[name] = {"blob_oid": oid, "sha256": digest(raw), "bytes": len(raw), "mode": mode}
    return rows


def copy_projection(source, rows, destination):
    destination.mkdir(exist_ok=False)
    for name, row in rows.items():
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True)
        raw = (source / name).read_bytes()
        require(digest(raw) == row["sha256"], "Source changed while copying")
        target.write_bytes(raw); target.chmod(int(row["mode"], 8) & 0o777)


def changed_paths(rows, projection):
    actual = inventory(projection)
    expected = {name: {k: row[k] for k in ("sha256", "bytes", "mode")} for name, row in rows.items()}
    return sorted(name for name in set(expected) | set(actual) if expected.get(name) != actual.get(name))


def load_calculator(source):
    require(digest((source / CALCULATOR).read_bytes()) == CALCULATOR_SHA, "Frozen calculator differs")
    raw = (source / BASELINE).read_bytes(); require(digest(raw) == BASELINE_SHA, "Frozen identity baseline differs")
    spec = importlib.util.spec_from_file_location("frozen_diagnostic_source_identity", source / CALCULATOR)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    baseline = json.loads(raw)["baseline"]
    return module, baseline, module.ReportReference(baseline)


def verify_observer_identities(before, after):
    require(after["named_identities"] == before["named_identities"]
            and after["sdk_integrity"] == before["sdk_integrity"], "Observer changed named production identities")
    context = after["semantic_context"]
    require(context["status"] == "UNKNOWN_CONTEXT_CHANGED"
            and [row["path"] for row in context["changed"]] == [TEST]
            and context["missing"] == [], "Unexpected diagnostic semantic context")


def secret_fields(value):
    if isinstance(value, dict):
        return any((k.lower().replace("-", "_") in SECRET_FIELDS and v not in (None, "", False)) or secret_fields(v) for k, v in value.items())
    if isinstance(value, list):
        return any(secret_fields(v) for v in value)
    return False


def suspicious(raw):
    if KEY_MARKER.search(raw) or AUTH_MARKER.search(raw) or TOKEN_MARKER.search(raw):
        return True
    for candidate in [raw, *raw.splitlines()]:
        try:
            if secret_fields(json.loads(candidate)):
                return True
        except (ValueError, UnicodeError):
            pass
    # Catch credential fields even when surrounded by a compiler/log prefix.
    return bool(re.search(rb'(?i)["\'](?:private_seed_hex|client_token|worker_token|access_token|refresh_token|session_token|password|private_key)["\']\s*[:=]\s*["\'][^"\']+', raw))


def publish(selected, public):
    require(not public.exists(), "Public output must be fresh")
    files = []; total = 0
    for path in sorted(selected.rglob("*")):
        require(not path.is_symlink(), "Publication symlink refused")
        if path.is_dir():
            continue
        require(path.is_file() and path.stat().st_size <= MAX_LOG, "Publication file bound exceeded")
        raw = path.read_bytes(); total += len(raw)
        require(total <= 64 * 1024 * 1024, "Publication total bound exceeded")
        files.append((path.relative_to(selected), raw))
    findings = [index for index, (name, raw) in enumerate(files) if suspicious(str(name).encode()) or suspicious(raw)]
    stage = selected.parent / "publication-stage"
    require(not stage.exists(), "Publication stage must be fresh")
    stage.mkdir()
    audit = {"schema": "rx.workflow-diagnostic-publication.v1", "status": "REFUSED" if findings else "APPROVED",
             "scope": "Generic private-key, credential-field and authorization-token scan; not an arbitrary-secret detector",
             "credential_fixture": "NONE_FILE_SIMULATION_ONLY", "files": len(files), "bytes": total,
             "finding_file_indices": findings, "secret_values_disclosed": False}
    if not findings:
        for name, raw in files:
            target = stage / "evidence" / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        write_json(stage / "CHECKSUMS.json", {str(name): digest(raw) for name, raw in files})
    write_json(stage / "PUBLICATION.json", audit)
    public.parent.mkdir(parents=True, exist_ok=True)
    os.rename(stage, public)
    return not findings


def fact_files(fixtures, destination):
    """Copy only bounded synthetic JSON facts from retained failure fixtures."""
    records = []
    if not fixtures.exists():
        return records
    for fixture in sorted(fixtures.iterdir()):
        require(fixture.is_dir() and not fixture.is_symlink(), "Unexpected fixture root")
        # Successful TempDir instances disappear; retained directories are failures.
        if not (fixture / "python-journal").is_dir():
            continue
        paths = list((fixture / "device").glob("state.json")) + list((fixture / "device").glob("effects.jsonl"))
        paths += list((fixture / "python-journal").glob("*/request.json"))
        paths += list((fixture / "python-journal").glob("*/receipt.json"))
        paths += list((fixture / "python-journal").glob("*/entry.json"))
        paths += list((fixture / "python-journal/captures").glob("*/capture.json"))
        for source in sorted(set(paths)):
            path = clean_path(source); require(path.is_relative_to(fixture) and path.is_file(), "Unsafe fact leaf")
            require(path.stat().st_size <= MAX_FACT, "Fact exceeds byte bound")
            raw = path.read_bytes(); require(len(raw) <= MAX_FACT, "Fact grew beyond bound")
            if source.suffix == ".jsonl":
                values = [json.loads(line) for line in raw.splitlines() if line.strip()]
            else:
                values = [json.loads(raw)]
            require(all(isinstance(value, dict) for value in values), "Expected JSON object facts")
            name = Path(fixture.name) / source.relative_to(fixture)
            target = destination / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            records.append({"path": name.as_posix(), "sha256": digest(raw), "bytes": len(raw)})
    return records


def fact_correlations(destination):
    result = []
    if not destination.exists():
        return result
    fields = ("operation", "invocation", "intent_digest", "environment_digest", "device_session")
    for path in sorted(destination.glob("*/python-journal/*/request.json")):
        request = json.loads(path.read_bytes()); receipt_path = path.with_name("receipt.json")
        receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else None
        result.append({"request": path.relative_to(destination).as_posix(), "request_sha256": digest(path.read_bytes()),
                       "operation": request.get("operation"), "invocation": request.get("invocation"),
                       "primitive": request.get("input", {}).get("primitive"), "node": request.get("input", {}).get("node"),
                       "receipt_present": receipt is not None,
                       "receipt_sha256": digest(receipt_path.read_bytes()) if receipt is not None else None,
                       "receipt_status": receipt.get("status") if receipt is not None else None,
                       "error_type": receipt.get("error_type") if receipt is not None else None,
                       "correlation_matches": (request.get("schema") == "rx.python-host-request.v1"
                                               and receipt.get("schema") == "rx.python-host-receipt.v1"
                                               and all(isinstance(request.get(key), str) and request[key]
                                                       and isinstance(receipt.get(key), str) and receipt[key]
                                                       and receipt[key] == request[key] for key in fields)) if receipt is not None else None,
                       "uncertainty_promoted": False})
    return result


def command(args, cwd, env, selected, label):
    started = time.time_ns()
    with (selected / (label + ".stdout")).open("wb") as stdout, (selected / (label + ".stderr")).open("wb") as stderr:
        result = subprocess.run(list(map(str, args)), cwd=cwd, env=env, stdout=stdout, stderr=stderr)
    record = {"argv": list(map(str, args)), "cwd": str(cwd), "returncode": result.returncode,
              "started_ns": started, "finished_ns": time.time_ns(), "retry_count": 0}
    for stream in ("stdout", "stderr"):
        path = selected / (label + "." + stream)
        with path.open("rb") as handle: record[stream + "_sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
        record[stream + "_bytes"] = path.stat().st_size
    write_json(selected / (label + ".command.json"), record)
    return result.returncode


def execute(args):
    require(sys.version_info >= (3, 11), "Python 3.11 or newer is required")
    require(sys.platform == "linux" and platform.machine() == "x86_64" and os.environ.get("CI") == "true" and args.execute_isolated_linux, "Explicit fresh Linux CI execution required")
    control, source, work, public = map(clean_path, (args.control, args.source, args.work, args.public))
    require(len({control, source, work, public}) == 4 and all(not a.is_relative_to(b) for a in (work, public) for b in (control, source))
            and not public.is_relative_to(work) and not work.is_relative_to(public), "Input/output roots must be disjoint")
    require(not work.exists() and not public.exists(), "Preserve previous diagnostic output")
    work.mkdir(parents=True); selected = work / "selected"; selected.mkdir()
    env = environment(); env["TMPDIR"] = str(work / "fixtures"); Path(env["TMPDIR"]).mkdir()
    env["CARGO_TARGET_DIR"] = str(work / "cargo-target")
    code = 1; receipt = {"schema": "rx.workflow-simulation-advisory.v1", "source_commit": SOURCE_SHA,
                        "control_commit": args.expected_control, "required_ci_or_m5_replacement": False,
                        "original_failed_run": 37522256416, "original_failure_reclassified": False,
                        "worker_stderr": "NOT_CAPTURED_BY_UNCHANGED_RUNTIME", "credential_fixture": "NONE_FILE_SIMULATION_ONLY",
                        "cargo_test_invocations": 0, "automatic_retry": False, "acceptance_claim": False,
                        "original_test_threads": "NOT_EXPLICIT_IN_ORIGINAL_CI",
                        "diagnostic_test_threads": 2,
                        "concurrency_scope": "Explicit diagnostic cap; not a claim that the original command selected this flag"}
    try:
        control_rows = source_rows(control, args.expected_control)
        source_before = source_rows(source, SOURCE_SHA)
        require(git(source, "rev-parse", "HEAD^{tree}").decode().strip() == SOURCE_TREE, "Pinned source tree differs")
        require(source_before[TEST]["sha256"] == TEST_SHA, "Original test preimage differs")
        observer = control / PREFIX / "observer.rs"
        require(digest(observer.read_bytes()) == OBSERVER_SHA, "Reviewed observer bytes differ")
        write_json(selected / "source-inventory.json", source_before)
        write_json(selected / "control-tools.json", {name: row for name, row in control_rows.items()
                   if name.startswith(PREFIX) or name == ".github/workflows/workflow-simulation-diagnostic.yml"})
        module, baseline, reference = load_calculator(source)
        before = module.calculate(module.FilesystemView(source), reference)
        require(module.compare(baseline, before)["status"] == "PASS_BOUNDED_STATIC_SOURCE_IDENTITIES", "Original source identity proof failed")
        write_json(selected / "original-source-identities.json", before)
        projection = work / "projection"; copy_projection(source, source_before, projection)
        require(changed_paths(source_before, projection) == [], "Raw projection differs")
        (projection / TEST).write_bytes(observer.read_bytes())
        require(changed_paths(source_before, projection) == [TEST], "Observer must be the sole source change")
        require(command(["rustfmt", "--edition", "2024", projection / TEST], projection, env, selected, "observer-format") == 0, "Observer formatting failed")
        require(changed_paths(source_before, projection) == [TEST], "Formatter changed unexpected source")
        projected = inventory(projection)
        after = module.calculate(module.FilesystemView(projection), reference)
        verify_observer_identities(before, after)
        write_json(selected / "diagnostic-source-identities.json", after)
        write_json(selected / "observer-change.json", {"path": TEST, "original_sha256": TEST_SHA,
                   "reviewed_observer_sha256": OBSERVER_SHA, "formatted_observer_sha256": projected[TEST]["sha256"],
                   "source_gate_status": "EXPECTED_UNKNOWN_DIAGNOSTIC_ONLY", "required_source_gate_weakened": False})
        shutil.copyfile(projection / TEST, selected / "formatted-observer.rs")
        import difflib
        (selected / "observer.patch").write_text("".join(difflib.unified_diff((source / TEST).read_text().splitlines(True),
                                                  (projection / TEST).read_text().splitlines(True), fromfile=TEST, tofile=TEST)))
        for label, invocation in [("rustc", ["rustc", "--version", "--verbose"]), ("cargo", ["cargo", "--version"]),
                                  ("rustup-active", ["rustup", "show", "active-toolchain"]), ("python", ["python3", "-VV"])]:
            require(command(invocation, projection, env, selected, label) == 0, "Toolchain observation failed")
        require((selected / "rustc.stdout").read_text().startswith("rustc 1.98.1 "), "Pinned Rust version differs")
        tool_hashes = {}
        for tool in ("cargo", "rustc", "rustfmt"):
            label = "path-" + tool
            require(command(["rustup", "which", "--toolchain", "1.98.1", tool], projection, env, selected, label) == 0, "Tool executable observation failed")
            path = clean_path((selected / (label + ".stdout")).read_text().strip())
            require(path.is_file(), "Tool executable unavailable")
            with path.open("rb") as stream: tool_hashes[tool] = {"path": str(path), "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}
        executable = Path(sys.executable).resolve()
        python_command = Path(shutil.which("python3")).resolve()
        write_json(selected / "environment.json", {"platform": platform.platform(), "machine": platform.machine(),
                   "python_executable": str(executable), "python_executable_sha256": digest(executable.read_bytes()),
                   "python_command": str(python_command), "python_command_sha256": digest(python_command.read_bytes()),
                   "rust_tool_binaries": tool_hashes, "python_version": sys.version, "cpu_count": os.cpu_count(), "disk_free_bytes": shutil.disk_usage(work).free,
                   "runner_os": os.environ.get("RUNNER_OS"), "runner_arch": os.environ.get("RUNNER_ARCH"),
                   "image_os": os.environ.get("ImageOS"), "image_version": os.environ.get("ImageVersion"),
                   "fresh_target": env["CARGO_TARGET_DIR"], "cargo_build_jobs": 2, "test_threads": 2,
                   "physical_device_input": False, "no_environment_secret_dump": True})
        require(not Path(env["CARGO_TARGET_DIR"]).exists(), "Diagnostic target was not fresh")
        receipt["cargo_test_invocations"] = 1
        code = command(["cargo", "test", "--workspace", "--all-features", "--locked", "--test", "workflow_simulation", "--", "--test-threads=2", "--nocapture"],
                       projection / "rx-solutions", env, selected, "workflow-simulation")
        receipt["cargo_returncode"] = code
        receipt["retained_facts"] = fact_files(work / "fixtures", selected / "facts")
        receipt["original_operation_correlations"] = fact_correlations(selected / "facts")
        require(inventory(projection) == projected, "Diagnostic execution changed the source projection")
        require(source_rows(source, SOURCE_SHA) == source_before, "Original immutable checkout changed")
        require(source_rows(control, args.expected_control) == control_rows, "Control tools changed")
        receipt["status"] = "DIAGNOSTIC_TEST_PASSED" if code == 0 else "DIAGNOSTIC_TEST_FAILED"
        receipt["successful_fixture_facts"] = "NOT_RETAINED_BY_UNCHANGED_SUCCESS_CLEANUP"
    except Exception as error:
        receipt.update(status="DIAGNOSTIC_SETUP_OR_EVIDENCE_FAILURE", failure_class=type(error).__name__,
                       failure_code=str(error) if isinstance(error, DiagnosticRefusal) else "UNEXPECTED_DIAGNOSTIC_ERROR")
        code = code if code else 1
    write_json(selected / "receipt.json", receipt)
    try:
        approved = publish(selected, public)
    except Exception:
        if not public.exists():
            public.mkdir(parents=True)
            write_json(public / "PUBLICATION.json", {"status": "REFUSED", "reason": "PUBLICATION_INCOMPLETE", "secret_values_disclosed": False})
        approved = False
    print(json.dumps({"status": receipt["status"], "publication_approved": approved,
                      "required_ci_or_m5_replacement": False, "cargo_test_invocations": receipt["cargo_test_invocations"]}))
    return code if code else (0 if approved else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("control", "source", "work", "public"): parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--expected-control", required=True)
    parser.add_argument("--execute-isolated-linux", action="store_true")
    return execute(parser.parse_args())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit("Diagnostic preflight refused; no product acceptance or automatic retry") from None
