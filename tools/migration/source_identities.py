#!/usr/bin/env python3
"""V07 bounded, named source-identity calculator. No Rust build or product CLI.

A calculated source digest is not a measured compiled-binary identity. Recipes
are specific to the frozen P/S commits; algorithm-source changes yield UNKNOWN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys


class Refusal(RuntimeError):
    pass


class Support:
    """Small stdlib-only support; offline CI does not import the local importer."""
    Refusal = Refusal

    @staticmethod
    def sha256(value):
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def safe_relative(value):
        if not value or value.startswith('/') or '\\' in value or ':' in value or any(ord(c)<32 or ord(c)==127 for c in value):
            raise Refusal('unsafe relative path')
        if any(p in ('','.','..') or p.casefold().rstrip(' .')=='.git' for p in value.split('/')):
            raise Refusal('relative traversal/alias')
        if str(PurePosixPath(value))!=value:raise Refusal('noncanonical relative path')

    @staticmethod
    def reject_symlink_ancestors(path):
        if not path.is_absolute():raise Refusal('absolute filesystem path required')
        if any(p.is_symlink() for p in [path,*path.parents]):raise Refusal('symlink ancestor refused')

    @staticmethod
    def exclusive_write(parent,name,payload,mode):
        Support.safe_relative(name)
        if '/' in name:raise Refusal('output name must be a leaf')
        fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            leaf=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
            try:
                with os.fdopen(leaf,'wb',closefd=False) as stream:stream.write(payload);stream.flush()
                os.fchmod(leaf,mode);os.fsync(leaf)
            finally:os.close(leaf)
            os.fsync(fd)
        finally:os.close(fd)


raw=Support()
FROZEN_BASELINE_REPORT_SHA256 = "e2016d2af1bdb63cdef079738ffba5ebaf47a66f78ae0391b8ed02e85a0334f5"

P = "rx-platform/"
S = "rx-solutions/"
HOST = S + "runtime/rx-host/"
SERVICE = HOST + "src/service/"
BINDINGS = [
    "executor/v1", "executor-plan/v1", "production/v1", "assignment/v1", "host-read/v1",
    "host-configuration/v1", "host-configuration/v2", "host-qualification/v1",
    "host-qualification/v2", "resident-reporting/v1", "resident-execution/v1",
    "workflow-execution/v2", "executor-execution/v2", "host-execution/v2",
]


class Unknown(RuntimeError):
    pass


def strict_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise Unknown("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Unknown("nonfinite JSON number")))


def jcs(value) -> bytes:
    """Exact JCS subset used here: UTF-8 strings, arrays, objects, bool/null,
    and safe integers. Float/unsafe-integer inputs are refused, not approximated.
    Object keys sort by UTF-16 code units, not Python's Unicode codepoint order.
    """
    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if isinstance(value, int):
        if abs(value) > 2**53 - 1:
            raise Unknown("JCS integer outside implemented exact-safe subset")
        return str(value).encode()
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise Unknown("unpaired Unicode surrogate") from error
        return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    if isinstance(value, list):
        return b"[" + b",".join(jcs(item) for item in value) + b"]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise Unknown("non-string JCS object key")
        return b"{" + b",".join(jcs(key) + b":" + jcs(value[key])
                                  for key in sorted(value, key=lambda key: key.encode("utf-16-be"))) + b"}"
    raise Unknown("JCS type outside supported subset: " + type(value).__name__)


def domain_hash(domain, value):
    if not domain or "\n" in domain or "\r" in domain:
        raise Unknown("invalid canonical digest domain")
    return raw.sha256(domain.encode() + b"\n" + jcs(value))


class MemoryView:
    def __init__(self, blobs):
        self.blobs = blobs

    def read(self, path):
        raw.safe_relative(path)
        if path not in self.blobs:
            raise Unknown("missing input: " + path)
        return self.blobs[path]

    def paths_under(self, prefix):
        return sorted(path for path in self.blobs if path.startswith(prefix + "/"))

    def proof_hash(self,path,function=None,kind='whole'):
        return raw.sha256(proof_fragment(self.read(path),function,kind))

    def binding_source_set(self,family):
        return set(strict_json(self.read(P+'spec/'+family+'/binding.json'))['source_sha256'])

    def context_records(self):
        return [{'path':p,'sha256':raw.sha256(self.read(p))} for p in context_paths(self)]


class FilesystemView:
    def __init__(self, target):
        raw.reject_symlink_ancestors(target)
        self.root = target.resolve(strict=True)

    def read(self, path):
        raw.safe_relative(path)
        candidate = self.root / path
        raw.reject_symlink_ancestors(candidate)
        info = candidate.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise Unknown("nonregular source input: " + path)
        return candidate.read_bytes()

    def paths_under(self, prefix):
        raw.safe_relative(prefix)
        folder = self.root / prefix
        raw.reject_symlink_ancestors(folder)
        if not folder.is_dir():
            raise Unknown("missing source directory: " + prefix)
        result = []
        def failed(error):raise Unknown('source inventory unreadable directory: '+str(error))
        for current, dirs, files in os.walk(folder, followlinks=False,onerror=failed):
            for name in dirs:
                if (Path(current) / name).is_symlink():
                    raise Unknown("source inventory symlink")
            for name in files:
                path = Path(current) / name
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise Unknown("source inventory nonregular file")
                result.append(path.relative_to(self.root).as_posix())
        return sorted(result)


def function_text(data, name):
    """Extract one reviewed Rust function, ignoring quoted strings and comments.
    This is a guard, not a Rust interpreter. Unsupported raw strings are UNKNOWN.
    """
    text = data.decode("utf-8")
    matches = list(re.finditer(r"\bfn\s+" + re.escape(name) + r"(?:\s*<|\s*\()", text))
    if len(matches) != 1:
        raise Unknown("function proof anchor is ambiguous: " + name)
    start = matches[0].start(); begin = text.find("{", matches[0].end())
    if begin < 0:
        raise Unknown("function proof body missing")
    depth = 0; i = begin; string = False; escaped = False; comment = False; block = 0
    while i < len(text):
        char = text[i]; pair = text[i:i+2]
        if comment:
            if char == "\n": comment = False
        elif block:
            if pair == "/*": block += 1; i += 1
            elif pair == "*/": block -= 1; i += 1
        elif string:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': string = False
        elif pair == "//": comment = True; i += 1
        elif pair == "/*": block = 1; i += 1
        elif char == '"':
            if i and text[i-1] in ('r', '#'):
                raise Unknown("raw string in proof function unsupported")
            string = True
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0: return text[start:i+1].encode()
        i += 1
    raise Unknown("unterminated function proof")


def proof_fragment(data,function=None,kind='whole'):
    if function:return function_text(data,function)
    if kind=='resolver-expression':
        source=data.decode();begin=source.index('let resolver_digest = canonical::digest(');end=source.index('.map_err',begin)
        return source[begin:end].encode()
    if kind=='driver-struct':
        pattern=r'(#\[derive\(Clone, Debug, Serialize, Deserialize, PartialEq, Eq\)\]\s*#\[serde\(deny_unknown_fields\)\]\s*pub struct Driver\s*\{[^}]+\})'
        result=re.search(pattern,data.decode())
        if not result:raise Unknown('Driver serde descriptor shape not recognized')
        return result.group().encode()
    if kind!='whole':raise Unknown('unsupported proof fragment kind')
    return data


class ReportReference:
    """Frozen proof hashes/source sets; no source checkout needed in offline CI."""
    def __init__(self,baseline):
        self.baseline=baseline;self.hashes={}
        proofs=[p for r in baseline['named_identities'].values() for p in r['algorithm_proofs']]
        proofs += [r['wire_algorithm_proof'] for r in baseline['bindings'].values() if 'wire_algorithm_proof' in r]
        proofs += [r['wire_file_proof'] for r in baseline['bindings'].values() if 'wire_file_proof' in r]
        proofs += [p for r in baseline['bindings'].values() for p in r.get('wire_call_site_proofs',[])]
        proofs += [baseline['binding_inventory_algorithm_proof']]
        for p in proofs:
            key=(p['path'],p.get('function'),p.get('kind','whole'));value=p['baseline_fragment_sha256']
            if key in self.hashes and self.hashes[key]!=value:raise Unknown('conflicting frozen proof hashes')
            self.hashes[key]=value

    def proof_hash(self,path,function=None,kind='whole'):
        try:return self.hashes[(path,function,kind)]
        except KeyError as error:raise Unknown('unrecorded frozen algorithm proof: '+path) from error

    def binding_source_set(self,family):
        return {p['path'][len(P):] for p in self.baseline['bindings'][family]['source_inputs']}

    def context_records(self):
        return self.baseline['semantic_context']['inputs']


def context_paths(view):
    roots=[P+'crates',P+'tools',S+'runtime',S+'drivers',S+'sdk/crates']
    paths={p for root in roots for p in view.paths_under(root)
           if p.endswith('.rs') or p.split('/')[-1] in ('Cargo.toml','Cargo.lock','rust-toolchain.toml')}
    paths.update(prefix+name for prefix in (P,S) for name in ('Cargo.toml','Cargo.lock','rust-toolchain.toml'))
    paths.add(S+'sdk/Cargo.toml')
    return sorted(paths)


def semantic_context(view,baseline):
    """Conservative Rust/module/dependency context guard, separate from digest inputs."""
    expected=baseline.context_records();wanted={p['path']:p['sha256'] for p in expected}
    try:
        paths=context_paths(view);changes=[{'path':p,'expected_sha256':wanted.get(p),'actual_sha256':raw.sha256(view.read(p))}
                                         for p in paths if p not in wanted or raw.sha256(view.read(p))!=wanted[p]]
        missing=sorted(set(wanted)-set(paths))
        return {'status':'PASS' if not changes and not missing else 'UNKNOWN_CONTEXT_CHANGED','inputs':expected,
                'changed':changes,'missing':missing,'scope':'conservative Rust source/module routing plus Cargo manifests/locks/toolchain; not the semantic named-hash preimage'}
    except (Unknown,raw.Refusal,OSError,UnicodeError,ValueError) as error:
        return {'status':'UNKNOWN','inputs':expected,'reason':str(error)}


class Calculator:
    def __init__(self, view, baseline):
        self.view = view; self.baseline = baseline; self.results = {}; self.reads = {}; self.proofs = []

    def read(self, path):
        value = self.view.read(path); self.reads[path] = {"path": path, "bytes": len(value), "sha256": raw.sha256(value)}
        return value

    def text(self, path):
        value = self.read(path)
        if value.startswith(b"\xef\xbb\xbf") or b"\r\n" in value:
            raise Unknown("include_str BOM/CRLF semantics outside verified baseline subset: " + path)
        return value.decode("utf-8")

    def proof(self, path, function=None,kind='whole'):
        before = self.baseline.proof_hash(path,function,kind)
        after = raw.sha256(proof_fragment(self.read(path),function,kind))
        self.proofs.append({"path": path, "function": function,"kind":kind, "baseline_fragment_sha256": before, "target_fragment_sha256": after})
        if before != after:
            raise Unknown("algorithm/serialization proof changed: " + path + ("::" + function if function else ""))

    def canonical_proof(self, solution=False):
        prefix = S + "sdk/" if solution else P
        self.proof(prefix + "crates/rx-domain/src/canonical.rs")
        self.proof(prefix + "crates/rx-domain/src/types.rs")
        self.proof(prefix + "crates/rx-domain/Cargo.toml")
        self.proof(prefix + "crates/rx-domain/src/lib.rs")
        self.proof(prefix + "Cargo.toml")
        self.proof((S if solution else P) + "Cargo.lock")

    def content_proof(self, solution=False):
        prefix = S + "sdk/" if solution else P
        self.proof(prefix + "crates/rx-package/src/verify.rs", "content_digest")

    def dependency(self, name):
        result = self.results[name]
        for item in result["inputs"]: self.reads[item["path"]] = item
        if result["calculation_status"] != "CALCULATED_SOURCE_ONLY":
            raise Unknown("dependency identity unknown: " + name)
        return result["value"]

    def add(self, name, algorithm, evidence, recipe):
        self.reads = {}; self.proofs = []
        result = {"name": name, "algorithm": algorithm, "evidence": evidence, "runtime_compiled_observation": "NOT_RUN"}
        try:
            result.update(calculation_status="CALCULATED_SOURCE_ONLY", value=recipe())
        except (Unknown, raw.Refusal, OSError, UnicodeError, ValueError, KeyError) as error:
            result.update(calculation_status="UNKNOWN", value=None, reason=str(error))
        result["inputs"] = [self.reads[path] for path in sorted(self.reads)]
        result["algorithm_proofs"] = self.proofs
        self.results[name] = result

    def host(self, kind):
        self.proof(HOST + "build.rs")
        base = set(self.view.paths_under(HOST + "src")) | set(self.view.paths_under(S + "drivers/rx-melsec-mc/src"))
        base |= {S + p for p in ["Cargo.lock", "runtime/rx-host/Cargo.toml", "runtime/rx-host/build.rs", "drivers/rx-melsec-mc/Cargo.toml", "sdk/source-lock.json"]}
        domains = {"MELSEC": "RX-HOST-MELSEC-SOURCE-v1", "JTC": "RX-HOST-ROS-JTC-SOURCE-v1", "DYNAMIXEL": "RX-DYNAMIXEL-SOURCE-v1"}
        if kind == "JTC":
            base |= set(self.view.paths_under(S + "native/ros-jtc")) | set(self.view.paths_under(S + "runtime/rx-solution-catalog/src"))
            base |= {S+p for p in ["catalogs/device-support.v1.json", "catalogs/fixtures/controllers.v1.json", "runtime/rx-solution-catalog/Cargo.toml", "dependencies/native-stack.lock.json", "dependencies/native.repos"]}
        if kind == "DYNAMIXEL":
            base = set(self.view.paths_under(S + "native/dynamixel")) | set(self.view.paths_under(HOST + "src"))
            base |= {S+p for p in ["Cargo.lock", "runtime/rx-host/build.rs", "runtime/rx-host/Cargo.toml", "sdk/source-lock.json"]}
        digest = hashlib.sha256(domains[kind].encode() + b"\0")
        for path in sorted(base):
            relative = path[len(S):].encode(); value = self.read(path)
            digest.update(struct.pack("<Q", len(relative)) + relative + struct.pack("<Q", len(value)) + value)
        return digest.hexdigest()

    def tuple_identity(self, path, proof_function, domain, includes, *, solution=False):
        self.canonical_proof(solution)
        if proof_function: self.proof(path, proof_function)
        else:self.proof(path,kind='resolver-expression')
        return domain_hash(domain, [self.text(p) for p in includes])

    def descriptor(self, kind):
        file, implementation, dependency = {
            "MELSEC": ("device_package.rs", "rx.melsec.ensure-state.v1", "host.MELSEC"),
            "JTC": ("jtc_package.rs", "rx.ros.position-jtc.v1", "host.JTC"),
        }[kind]
        self.proof(SERVICE + file, "driver"); self.proof(SERVICE + "device_package.rs", "driver")
        self.proof(SERVICE+'device_package.rs',kind='driver-struct');self.canonical_proof(True)
        return {"schema": "rx.native-driver-reference.v1", "implementation": implementation, "source_digest": self.dependency(dependency)}

    def python_driver(self, kind):
        self.canonical_proof(True)
        self.content_proof(True)
        self.proof(SERVICE + {"sdk": "python_package.rs", "library": "python_library.rs", "execution": "python_execution_package.rs"}[kind], "driver")
        if kind == "sdk":
            value = domain_hash("RX-PYTHON-SDK-DRIVER-v1", [self.dependency("host.MELSEC"),
                raw.sha256(self.read(S+"deployment/local-skills/host_runner.py")), raw.sha256(self.read(S+"deployment/local-skills/python_environment.py"))])
        elif kind == "library":
            value = domain_hash("RX-PYTHON-LIBRARY-DRIVER-v1", [self.dependency("driver.python-sdk")["source_digest"], raw.sha256(self.read(SERVICE+"python_library.rs"))])
        else:
            value = domain_hash("RX-PYTHON-EXECUTION-DRIVER-v2", [self.dependency("driver.python-sdk")["source_digest"], self.text(SERVICE+"python_execution_package.rs"), self.text(HOST+"src/python_execution.rs")])
        return {"schema": "rx.native-driver-reference.v1", "implementation": {"sdk":"rx.python.sdk.v1", "library":"rx.python.sdk-library.v1", "execution":"rx.python.execution.v2"}[kind], "source_digest":value}

    def external(self):
        includes = [SERVICE+"external_package.rs", HOST+"src/external_process/profile.rs", HOST+"src/external_process/mod.rs", HOST+"src/external_process/wire.rs", HOST+"src/external_process/owned.rs", S+"deployment/external-adapters/rx_external_adapter.py"]
        value = self.tuple_identity(SERVICE+"external_package.rs", "driver", "RX-EXTERNAL-PROCESS-DRIVER-v1", includes, solution=True)
        return {"schema":"rx.native-driver-reference.v1", "implementation":"rx.external-process.v1", "source_digest":value}

    def process_validator(self):
        path=S+"runtime/rx-process-package/src/review.rs"; self.proof(path,"validator_digest"); self.content_proof(True)
        includes=[path,S+"Cargo.lock",S+"sdk/source-lock.json",S+"runtime/rx-process-package/src/candidate.rs",S+"runtime/rx-process/src/compile.rs",S+"runtime/rx-process/src/lib.rs"]
        includes += [S+"sdk/crates/rx-process-contract/src/"+f for f in ("model.rs","source_validation.rs","validation.rs","package_review.rs")]
        return raw.sha256(b"RX-PROCESS-VERIFIER-v1\0" + "".join(self.text(p) for p in includes).encode())

    def device_validator(self, unix):
        path=S+"runtime/rx-device-package/src/review.rs"; self.proof(path,"validator_digest"); self.canonical_proof(True); self.content_proof(True)
        # The descriptor's serde layout is guarded explicitly, not inferred from dict key ordering.
        self.proof(SERVICE+'device_package.rs',kind='driver-struct')
        includes=[S+"runtime/rx-device-package/src/"+f for f in ("review.rs","lib.rs","jtc.rs","python.rs","external.rs")]+[S+"Cargo.lock",S+"sdk/source-lock.json"]
        source=raw.sha256(b"RX-DEVICE-VERIFIER-SOURCE-v1\0"+"".join(self.text(p) for p in includes).encode())
        drivers=["driver.MELSEC","driver.JTC"] + (["driver.python-sdk","driver.python-library","driver.python-execution","driver.external-process"] if unix else [])
        return domain_hash("RX-DEVICE-VERIFIER-v1",[source]+[self.dependency(d) for d in drivers])

    def run(self):
        for name in ("MELSEC","JTC","DYNAMIXEL"):
            self.add("host."+name,"SHA256(domain NUL + sorted path/u64LE length/bytes inventory)","S:runtime/rx-host/build.rs:61-145",lambda n=name:self.host(n))
        for name in ("MELSEC","JTC"):
            self.add("driver."+name,"Driver serde descriptor with build source digest","S:runtime/rx-host/src/service/{device_package,jtc_package}.rs",lambda n=name:self.descriptor(n))
        for name in ("sdk","library","execution"):
            self.add("driver.python-"+name,"Driver descriptor; source_digest=SHA256(domain LF JCS(tuple))","S:runtime/rx-host/src/service/python_*.rs::driver",lambda n=name:self.python_driver(n))
        self.add("driver.external-process","Driver descriptor; source_digest=SHA256(domain LF JCS(ordered UTF8 sources))","S:runtime/rx-host/src/service/external_package.rs:70-86",self.external)
        recipes=[
            ("P.workflow-resolver",P+"crates/rx-domain/src/workflow/resolve.rs",None,"RX-WORKFLOW-RESOLVER-v1",[P+"crates/rx-domain/src/workflow/"+f for f in ("model.rs","math.rs","resolve.rs")]+[P+"crates/rx-domain/src/definition/pattern.rs"]),
            ("P.workflow-materializer",P+"crates/rx-process-contract/src/execution_v2/materialize.rs","compiler_digest","RX-WORKFLOW-MATERIALIZER-v2",[P+"crates/rx-process-contract/src/execution_v2/materialize.rs",P+"crates/rx-process-contract/src/execution_v2.rs",P+"crates/rx-domain/src/canonical.rs",P+"crates/rx-domain/src/types.rs"]),
            ("P.process-source-validator",P+"crates/rx-process-contract/src/source_validation.rs","empty","RX-PROCESS-SOURCE-VALIDATOR-v1",[P+"crates/rx-process-contract/src/source_validation.rs",P+"crates/rx-process-contract/src/model.rs"]),
        ]
        for name,path,fn,domain,includes in recipes:
            self.add(name,"SHA256(domain LF JCS(ordered source string tuple))",path,lambda p=path,f=fn,d=domain,i=includes:self.tuple_identity(p,f,d,i))
        self.add("S.process-package-validator","SHA256(domain NUL + ordered raw UTF8 source concatenation)","S:runtime/rx-process-package/src/review.rs:7-25",self.process_validator)
        for unix in (True,False):
            self.add("S.device-package-validator."+("unix" if unix else "nonunix"),"SHA256(domain LF JCS([source hash, ordered Driver descriptors]))","S:runtime/rx-device-package/src/review.rs:8-38",lambda u=unix:self.device_validator(u))
        return self.results


WIRE_RECIPES = {
    **{family:("jcs-sha256", None, P+"crates/rx-api/src/grpc/mod.rs", "manifest_hash") for family in ("executor/v1","executor-plan/v1","production/v1","assignment/v1")},
    "host-read/v1":("jcs-sha256",None,P+"crates/rx-host-client/src/bootstrap.rs","host_read_binding_hash"),
    "host-configuration/v1":("domain-jcs","RX-HOST-CONFIGURATION-BINDING-v1",P+"crates/rx-host-client/src/configuration.rs","binding_hash"),
    "host-qualification/v1":("domain-jcs","RX-HOST-CONFIGURATION-BINDING-v1",P+"crates/rx-host-client/src/qualification.rs","binding_hash"),
    "host-configuration/v2":("domain-jcs","RX-HOST-EXECUTION-CONFIGURATION-BINDING-v2",P+"crates/rx-host-client/src/configuration_v2.rs","binding_hash"),
    "host-qualification/v2":("domain-jcs","RX-HOST-EXECUTION-QUALIFICATION-BINDING-v2",P+"crates/rx-host-client/src/qualification_v2.rs","binding_hash"),
    "host-execution/v2":("domain-jcs","RX-HOST-EXECUTION-BINDING-v2",P+"crates/rx-host-client/src/execution_v2.rs","protocol"),
    "executor-execution/v2":("domain-jcs","RX-EXECUTOR-EXECUTION-BINDING-v2",P+"crates/rx-process-contract/src/execution_v2/executor.rs","binding_hash"),
    "resident-reporting/v1":("raw-sha256",None,P+"crates/rx-api/src/grpc/resident_reporting.rs","binding"),
    "resident-execution/v1":("raw-sha256",None,P+"crates/rx-api/src/grpc/resident_execution.rs","binding"),
}
WIRE_CALLERS={family:P+'crates/rx-api/src/grpc/'+file for family,file in {
    'executor/v1':'execution_read.rs','executor-plan/v1':'executor_plan.rs',
    'production/v1':'production.rs','assignment/v1':'assignment.rs'}.items()}


def binding_report(view, baseline):
    result = {}
    if raw.sha256(view.read(P+'crates/rx-protocol/build.rs'))!=baseline.proof_hash(P+'crates/rx-protocol/build.rs'):
        raise Unknown('binding source-inventory build algorithm changed')
    actual_paths = {p for p in view.paths_under(P+"spec") if p.endswith('/binding.json')}
    expected_paths = {P+"spec/"+family+"/binding.json" for family in BINDINGS}
    if actual_paths != expected_paths:
        raise Unknown("binding family inventory is not the frozen 14")
    for family in BINDINGS:
        path=P+"spec/"+family+"/binding.json"
        row={"path":path,"runtime_compiled_observation":"NOT_RUN"}
        try:
            data=view.read(path); value=strict_json(data)
            if not isinstance(value,dict):raise Unknown('binding manifest is not an object')
            sources=value["source_sha256"]
            if not isinstance(sources,dict) or not sources: raise Unknown("empty/non-object source_sha256")
            closure=[]
            for rel,expected in sorted(sources.items()):
                if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise Unknown('source_sha256 entry is not a SHA256 hex string')
                raw.safe_relative(rel)
                current=raw.sha256(view.read(P+rel)); closure.append({"path":P+rel,"expected_sha256":expected,"actual_sha256":current,"matches":current==expected})
            expected_source_set=baseline.binding_source_set(family)
            row.update(raw_manifest_sha256=raw.sha256(data),canonical_manifest_sha256=raw.sha256(jcs(value)),source_inputs=closure,
                       source_closure_valid=all(x['matches'] for x in closure),source_path_set_matches_baseline=set(sources)==expected_source_set,canonical_calculation_status="CALCULATED_SOURCE_ONLY")
            if family in WIRE_RECIPES:
                kind,domain,proof,fn=WIRE_RECIPES[family]
                expected_file=baseline.proof_hash(proof);actual_file=raw.sha256(view.read(proof))
                row['wire_file_proof']={'path':proof,'function':None,'kind':'whole','baseline_fragment_sha256':expected_file,'target_fragment_sha256':actual_file}
                if expected_file!=actual_file:raise Unknown('wire consumer module/import scope changed')
                if family in WIRE_CALLERS:
                    caller=WIRE_CALLERS[family];expected_caller=baseline.proof_hash(caller);actual_caller=raw.sha256(view.read(caller))
                    row['wire_call_site_proofs']=[{'path':caller,'function':None,'kind':'whole','baseline_fragment_sha256':expected_caller,'target_fragment_sha256':actual_caller}]
                    if expected_caller!=actual_caller:raise Unknown('binding include/call-site implementation changed')
                actual_proof=raw.sha256(function_text(view.read(proof),fn));expected_proof=baseline.proof_hash(proof,fn)
                row['wire_algorithm_proof']={'path':proof,'function':fn,'kind':'whole','baseline_fragment_sha256':expected_proof,'target_fragment_sha256':actual_proof}
                if actual_proof!=expected_proof: raise Unknown("wire consumer hash function changed")
                if kind!='raw-sha256' and raw.sha256(view.read(P+"crates/rx-domain/src/canonical.rs"))!=baseline.proof_hash(P+"crates/rx-domain/src/canonical.rs"): raise Unknown("wire canonical implementation changed")
                digest=raw.sha256(data) if kind=='raw-sha256' else raw.sha256(jcs(value)) if kind=='jcs-sha256' else domain_hash(domain,value)
                row.update(consumed_wire_identity_status="CALCULATED_SOURCE_ONLY",consumed_wire_digest=digest,wire_algorithm=kind,wire_domain=domain,wire_evidence=proof+"::"+fn)
            else:
                row.update(consumed_wire_identity_status="UNKNOWN",consumed_wire_digest=None,wire_reason="No production consumed wire hash expression identified for workflow-execution/v2; canonical hash is diagnostic, not a claimed wire digest")
        except (Unknown,raw.Refusal,OSError,UnicodeError,ValueError,KeyError) as error:
            row.update(consumed_wire_identity_status="UNKNOWN",reason=str(error))
            row.setdefault('canonical_calculation_status','UNKNOWN')
        result[family]=row
    return result


def sdk_integrity(view):
    try:
        prefix=S+'sdk/'; lock=strict_json(view.read(prefix+'source-lock.json'))
        if not isinstance(lock,dict) or not isinstance(lock.get('files'),dict):raise Unknown('SDK lock/files must be objects')
        paths=view.paths_under(prefix.rstrip('/')); actual={p[len(prefix):]:raw.sha256(view.read(p)) for p in paths if p!=prefix+'source-lock.json'}
        return {"status":"PASS" if lock.get('schema')=='rx.host-sdk.v1' and lock.get('files')==actual and len(actual)==162 else "FAIL","files":len(actual),"scope":"SDK inventory/source SHA closure, not compiler output"}
    except (Unknown,raw.Refusal,OSError,ValueError,KeyError) as error:return {"status":"UNKNOWN","reason":str(error)}


def calculate(view, baseline):
    try: bindings=binding_report(view,baseline)
    except (Unknown,raw.Refusal,OSError,ValueError) as error: bindings={"inventory":{"canonical_calculation_status":"UNKNOWN","reason":str(error)}}
    path=P+'crates/rx-protocol/build.rs'
    context=semantic_context(view,baseline)
    if context['status']!='PASS':
        for row in bindings.values():
            if row.get('consumed_wire_identity_status')=='CALCULATED_SOURCE_ONLY':
                row['formula_wire_digest']=row.pop('consumed_wire_digest')
                row['consumed_wire_identity_status']='UNKNOWN_CONTEXT_CHANGED'
                row['wire_reason']='Formula value calculated, but module/import/dependency context is no longer the frozen context'
    return {"named_identities":Calculator(view,baseline).run(),"bindings":bindings,"sdk_integrity":sdk_integrity(view),"semantic_context":context,
            "binding_inventory_algorithm_proof":{"path":path,"function":None,"kind":"whole","baseline_fragment_sha256":baseline.proof_hash(path)}}


def compare(before, after):
    identities={}
    context_valid=before['semantic_context']['status']=='PASS' and after['semantic_context']['status']=='PASS'
    for name,old in before['named_identities'].items():
        new=after['named_identities'][name]
        status='UNKNOWN' if old['calculation_status']!='CALCULATED_SOURCE_ONLY' or new['calculation_status']!='CALCULATED_SOURCE_ONLY' else ('PASS' if context_valid else 'UNKNOWN') if old['value']==new['value'] else 'FAIL'
        identities[name]={"status":status,"baseline":old['value'],"target":new['value'],"reason":new.get('reason')}
    bindings={}
    for name,old in before['bindings'].items():
        new=after['bindings'].get(name,{})
        if old.get('canonical_calculation_status')!='CALCULATED_SOURCE_ONLY' or new.get('canonical_calculation_status')!='CALCULATED_SOURCE_ONLY':status='UNKNOWN'
        else:
            manifest_same=all(old.get(k)==new.get(k) for k in ('raw_manifest_sha256','canonical_manifest_sha256'))
            if not manifest_same or not new.get('source_closure_valid') or not new.get('source_path_set_matches_baseline'):status='FAIL'
            elif not context_valid:status='UNKNOWN'
            elif name in WIRE_RECIPES and new.get('consumed_wire_identity_status')!='CALCULATED_SOURCE_ONLY':status='UNKNOWN'
            else:status='PASS' if old.get('consumed_wire_digest')==new.get('consumed_wire_digest') else 'FAIL'
        bindings[name]={"source_identity_comparison":status,"wire_identity_scope":new.get('consumed_wire_identity_status','UNKNOWN'),"reason":new.get('reason',new.get('wire_reason'))}
    results=[i['status'] for i in identities.values()]+[b['source_identity_comparison'] for b in bindings.values()]+[after['sdk_integrity']['status']]+([] if context_valid else ['UNKNOWN'])
    status='FAIL' if 'FAIL' in results else 'UNKNOWN' if 'UNKNOWN' in results else 'PASS_BOUNDED_STATIC_SOURCE_IDENTITIES'
    return {"status":status,"named":identities,"bindings":bindings,"semantic_context_status":after['semantic_context']['status'],
            "compiled_binary_identity":"UNKNOWN_NOT_BUILT_OR_QUERIED","physical_acceptance":"NOT_PERFORMED",
            "remaining_gate":"M3 isolated CI must build exact candidate and query/cross-check emitted driver/validator/binding identities against these calculated values; no source-only claim replaces that gate"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('baseline','compare'))
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--plan-dir',type=Path)
    source.add_argument('--baseline-report',type=Path)
    parser.add_argument('--target',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    source_paths=[]
    if args.baseline_report:
        if args.command!='compare':raise Unknown('offline baseline report only supports compare')
        baseline_bytes=args.baseline_report.read_bytes()
        if raw.sha256(baseline_bytes)!=FROZEN_BASELINE_REPORT_SHA256:raise Unknown('frozen baseline report SHA256 differs')
        baseline_report=strict_json(baseline_bytes);old=baseline_report['baseline'];baseline=ReportReference(old)
        source_digest=baseline_report['baseline_source_manifest_payload_sha256']
    else:
        from m2_import import prepare
        prepared=prepare(args.plan_dir);source_paths=prepared.source_paths;baseline=MemoryView(prepared.blobs)
        old=calculate(baseline,baseline);source_digest=prepared.digest
    report={"schema":"rx.migration-named-source-identities.v1","scope":"15 reviewed named source recipes, 14 binding manifests/source closures, Unix and non-Unix device-validator variants; compiled/runtime verification not run","baseline_source_manifest_payload_sha256":source_digest,"baseline":old}
    if args.command=='compare':
        if args.target is None:raise Unknown('--target required')
        target=args.target.absolute();raw.reject_symlink_ancestors(target);target=target.resolve(strict=True)
        for source in source_paths:
            if target==source or target.is_relative_to(source) or source.is_relative_to(target):raise Unknown('source/target overlap')
        new=calculate(FilesystemView(target),baseline);report.update(target=new,comparison=compare(old,new))
    else: report['status']='CALCULATED_BASELINE_ONLY_TARGET_NOT_CHECKED'
    payload=json.dumps(report,ensure_ascii=False,indent=2).encode()+b'\n'
    if args.output:
        output=args.output.absolute();raw.reject_symlink_ancestors(output);output=output.resolve(strict=False)
        for source in source_paths:
            if output.is_relative_to(source):raise Unknown('output inside original source repository')
        if args.target and output.is_relative_to(args.target.resolve()):raise Unknown('read-only comparator output inside target refused')
        raw.exclusive_write(output.parent,output.name,payload,0o644)
    print(json.dumps({"output":str(args.output) if args.output else None,"status":report.get('comparison',{}).get('status',report.get('status')),"named_count":len(old['named_identities']),"bindings":len(old['bindings']),"baseline_unknown_names":[n for n,r in old['named_identities'].items() if r['calculation_status']=='UNKNOWN'],"wire_unknown_families":[n for n,r in old['bindings'].items() if r.get('consumed_wire_identity_status')=='UNKNOWN']}))
    if args.command=='baseline':
        complete=all(r['calculation_status']=='CALCULATED_SOURCE_ONLY' for r in old['named_identities'].values()) and len(old['bindings'])==14 and all(r.get('canonical_calculation_status')=='CALCULATED_SOURCE_ONLY' and r.get('source_closure_valid') for r in old['bindings'].values()) and old['sdk_integrity']['status']=='PASS' and old['semantic_context']['status']=='PASS'
        complete=complete and all(r.get('consumed_wire_identity_status')=='CALCULATED_SOURCE_ONLY' for n,r in old['bindings'].items() if n!='workflow-execution/v2')
        return 0 if complete else 2
    return 0 if report['comparison']['status']=='PASS_BOUNDED_STATIC_SOURCE_IDENTITIES' else 2


if __name__=='__main__':
    try:raise SystemExit(main())
    except (Unknown,raw.Refusal,OSError,ValueError,KeyError) as error:
        print('V07 REFUSED: '+str(error),file=sys.stderr);raise SystemExit(2)
