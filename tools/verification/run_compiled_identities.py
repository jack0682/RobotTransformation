#!/usr/bin/env python3
"""Linux CI only: isolated source projection + real public-library identity probes.

No source changes in the candidate checkout, no new Cargo manifest/lock, no
device/runtime service startup. Actual cargo execution requires --execute.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
import tomllib

from compare_compiled import Refusal, compare_outputs, load_baseline, require, strict_json

HERE = Path(__file__).resolve().parent
EVALUATOR_SHA256 = "9c6a32bb5fe7ecb1ea6af1e94af1c56de4b6e4db202228d06df267ba3d05ca17"
PROBES = {
    "platform": ("rx-platform", "rx-application", "m3_platform_identity", "crates/rx-application/examples/m3_platform_identity.rs", "platform_identity.rs"),
    "device": ("rx-solutions", "rx-device-package", "m3_device_identity", "runtime/rx-device-package/examples/m3_device_identity.rs", "device_identity.rs"),
    "process": ("rx-solutions", "rx-process-package", "m3_process_identity", "runtime/rx-process-package/examples/m3_process_identity.rs", "process_identity.rs"),
}
GIT_ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
    GIT_ENV.pop(key, None)


def digest(data): return hashlib.sha256(data).hexdigest()


def git(root, *args, data=None):
    result = subprocess.run(["git", "-C", str(root), *args], input=data, env=GIT_ENV,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, "Git read failed: " + result.stderr.decode(errors="replace")[:1000])
    return result.stdout


def safe_relative(path):
    require(path and not path.startswith('/') and '\\' not in path and ':' not in path, "unsafe source path")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in path), "control character in path")
    require(all(p not in ('', '.', '..') and p.casefold() != '.git' for p in path.split('/')), "traversal/nested Git")
    require(str(PurePosixPath(path)) == path, "noncanonical path")


def no_symlink(path):
    require(path.is_absolute(), "absolute path required")
    require(not any(p.is_symlink() for p in [path, *path.parents]), "symlink path refused")


def exclusive(path, data, mode=0o644):
    no_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fchmod(stream.fileno(), mode); os.fsync(stream.fileno())


def raw_source_projection(repo, head):
    rows = []
    for entry in git(repo, 'ls-tree', '--full-tree', '-r', '-l', '-z', head, '--', 'rx-platform', 'rx-solutions').split(b'\0'):
        if not entry: continue
        meta, encoded = entry.split(b'\t', 1); mode, kind, blob, size = meta.decode().split()
        path = encoded.decode(); safe_relative(path)
        require(kind == 'blob' and mode in ('100644', '100755'), "nonregular source entry")
        rows.append({'path': path, 'mode': mode, 'blob_oid': blob, 'bytes': int(size)})
    require(rows and {r['path'].split('/')[0] for r in rows} == {'rx-platform', 'rx-solutions'}, "missing candidate source subtree")
    wanted = sorted({r['blob_oid'] for r in rows})
    data = git(repo, 'cat-file', '--batch', data=('\n'.join(wanted) + '\n').encode())
    values = {}; cursor = 0
    for object_id in wanted:
        end = data.find(b'\n', cursor); require(end >= 0, "truncated object header")
        fields = data[cursor:end].split(); require(len(fields) == 3 and fields[0].decode() == object_id and fields[1] == b'blob', "source object mismatch")
        size = int(fields[2]); cursor = end + 1; value = data[cursor:cursor+size]; cursor += size
        require(data[cursor:cursor+1] == b'\n' and len(value) == size, "truncated source object"); cursor += 1
        require(hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + value).hexdigest() == object_id, "raw source OID differs")
        values[object_id] = value
    require(cursor == len(data), "extra object output")
    for row in rows:
        value = values[row['blob_oid']]; require(len(value) == row['bytes'], "source size differs")
        row['sha256'] = digest(value)
    return rows, values


def verify_projection(folder, original, overlays):
    expected = {r['path']: r for r in original} | {r['path']: r for r in overlays}
    actual = set()
    for root, dirs, files in os.walk(folder, followlinks=False,
                                      onerror=lambda error: (_ for _ in ()).throw(Refusal(str(error)))):
        for name in dirs: require(not (Path(root)/name).is_symlink(), "projection symlink directory")
        for name in files:
            path = Path(root)/name; rel = path.relative_to(folder).as_posix(); safe_relative(rel)
            info = path.lstat(); require(stat.S_ISREG(info.st_mode), "projection nonregular file")
            require(rel in expected, "unexpected file in source projection: " + rel)
            row = expected[rel]; value = path.read_bytes()
            require(digest(value) == row['sha256'] and len(value) == row['bytes'], "source projection mutated: " + rel)
            require(stat.S_IMODE(info.st_mode) == (0o755 if row['mode'] == '100755' else 0o644), "source mode changed: " + rel)
            actual.add(rel)
    require(actual == set(expected), "projection source/overlay missing")


def log_command(command, cwd, env, log_prefix, timeout=1800):
    stdout = Path(str(log_prefix) + '.stdout'); stderr = Path(str(log_prefix) + '.stderr')
    started=datetime.now(timezone.utc).isoformat();timer=time.monotonic()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=out, stderr=err, timeout=timeout)
    receipt = {'command': command, 'cwd': str(cwd), 'returncode': result.returncode,
               'started_at_utc':started,'elapsed_seconds':time.monotonic()-timer,
               'stdout': str(stdout), 'stdout_sha256': digest(stdout.read_bytes()),
               'stderr': str(stderr), 'stderr_sha256': digest(stderr.read_bytes())}
    require(result.returncode == 0, f"command failed ({result.returncode}); retained logs at {log_prefix}")
    return receipt


def example_artifact(json_lines, name, manifest, target_dir):
    candidates = []
    for line in json_lines.splitlines():
        if not line.strip(): continue
        value = strict_json(line)
        if value.get('reason') != 'compiler-artifact': continue
        if value.get('target', {}).get('name') != name or 'example' not in value.get('target', {}).get('kind', []): continue
        if Path(value.get('manifest_path', '')).resolve() != manifest.resolve(): continue
        if value.get('executable'): candidates.append(value)
    require(len(candidates) == 1, "expected one exact example executable from Cargo artifact stream")
    require(candidates[0].get('features',[]) == [], "identity example package unexpectedly enables features")
    path = Path(candidates[0]['executable']).resolve(strict=True)
    require(path.is_relative_to(target_dir.resolve()) and stat.S_ISREG(path.lstat().st_mode), "Cargo executable outside isolated target")
    return path, candidates[0]


def execute(args):
    require(args.execute, "actual compiled probes require --execute")
    require(sys.platform == 'linux', "M3 compiled probes run only on an isolated Linux CI runner; no Mac build")
    root = args.repo.absolute(); no_symlink(root); root = root.resolve(strict=True)
    require(re.fullmatch('[0-9a-f]{40}', args.expected_head), "full expected candidate SHA required")
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == args.expected_head, "candidate HEAD differs")
    require(Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() == root, "candidate must be repo root")
    scratch = args.work.absolute(); no_symlink(scratch); scratch = scratch.resolve(strict=False)
    require(not scratch.exists() and not scratch.is_relative_to(root) and not root.is_relative_to(scratch), "fresh isolated work directory outside candidate required")
    baseline_raw = args.baseline.read_bytes(); baseline = load_baseline(baseline_raw)
    require(digest(args.evaluator.read_bytes()) == EVALUATOR_SHA256, "reviewed static evaluator bytes differ")
    scratch.mkdir(); sources = scratch/'sources'; sources.mkdir(); logs = scratch/'logs'; logs.mkdir()
    rows, blobs = raw_source_projection(root, args.expected_head)
    for row in rows: exclusive(sources/row['path'], blobs[row['blob_oid']], 0o755 if row['mode'] == '100755' else 0o644)
    verify_projection(sources, rows, [])
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0', CARGO_BUILD_JOBS='1', CARGO_INCREMENTAL='0')
    for variable in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_TARGET'):
        require(not environment.get(variable), 'unreviewed compile environment: '+variable)
    static = log_command([sys.executable, str(args.evaluator.resolve()), 'compare', '--baseline-report', str(args.baseline.resolve()),
                          '--target', str(sources), '--output', str(scratch/'pre-probe-static.json')], root, environment, logs/'static', timeout=60)
    overlays = []
    for role, (repo, package, example, target, fixture) in PROBES.items():
        probe = (HERE/'probes'/fixture).read_bytes(); path = repo+'/'+target
        require(path not in {r['path'] for r in rows}, "probe target collides with candidate")
        exclusive(sources/path, probe)
        overlays.append({'role':role,'path':path,'mode':'100644','bytes':len(probe),'sha256':digest(probe)})
    verify_projection(sources,rows,overlays)
    commands=[]; outputs={}; binaries=[]; toolchains={}; workspace_artifacts=[]
    for role,(repo,package,example,target,fixture) in PROBES.items():
        cwd=sources/repo; target_dir=scratch/'targets'/repo
        env=environment|{'CARGO_TARGET_DIR':str(target_dir)}
        declared=tomllib.loads((cwd/'rust-toolchain.toml').read_text())['toolchain']['channel']
        if repo not in toolchains:
            rustc=log_command(['rustc','-Vv'],cwd,env,logs/(repo+'-rustc'),timeout=120)
            cargo=log_command(['cargo','-V'],cwd,env,logs/(repo+'-cargo'),timeout=120)
            version=Path(rustc['stdout']).read_text();release=next((line.split(': ',1)[1] for line in version.splitlines() if line.startswith('release: ')),None)
            require(isinstance(release,str) and (release==declared or release.startswith(declared+'.')), 'active rustc differs from declared channel')
            toolchains[repo]={'declared':declared,'rustc':rustc,'cargo':cargo}
        command=['cargo','build','--locked','--manifest-path',str(cwd/'Cargo.toml'),'--package',package,
                 '--example',example,'--message-format=json-render-diagnostics']
        built=log_command(command,cwd,env,logs/(role+'-build'));commands.append(built)
        for line in Path(built['stdout']).read_bytes().splitlines():
            if not line.strip():continue
            item=strict_json(line)
            if item.get('reason')=='compiler-artifact' and item.get('manifest_path'):
                manifest_file=Path(item['manifest_path']).resolve()
                if manifest_file.is_relative_to(sources):
                    workspace_artifacts.append({'probe_role':role,'package_id':item.get('package_id'),
                        'manifest_path':str(manifest_file.relative_to(sources)), 'target':item.get('target'),
                        'features':item.get('features'), 'profile':item.get('profile')})
        manifest=cwd/target.split('/examples/')[0]/'Cargo.toml'
        executable,artifact=example_artifact(Path(built['stdout']).read_bytes(),example,manifest,target_dir)
        before=digest(executable.read_bytes())
        invoked=log_command([str(executable)],cwd,env,logs/(role+'-probe'),timeout=60);commands.append(invoked)
        require(digest(executable.read_bytes())==before,'probe executable changed during invocation')
        output=strict_json(Path(invoked['stdout']).read_bytes());outputs[role]=output
        binaries.append({'role':role,'executable':str(executable),'sha256':before,'cargo_package_id':artifact.get('package_id'),
                         'cargo_features':artifact.get('features'),'cargo_profile':artifact.get('profile'),'invoke':invoked})
    comparison=compare_outputs(baseline,outputs)
    verify_projection(sources,rows,overlays)
    require(git(root,'rev-parse','HEAD').decode().strip()==args.expected_head,'candidate HEAD changed during verification')
    report={'schema':'rx.m3-compiled-identity-receipt.v1','status':'COMPILED_UNIX_14_IDENTITIES_MATCH',
            'candidate_commit':args.expected_head,'candidate_source_trees':{repo:git(root,'rev-parse',args.expected_head+':'+repo).decode().strip() for repo in ('rx-platform','rx-solutions')},
            'source_projection':{'original_count':len(rows),'original_files':rows,'overlay_files':overlays,'original_bytes_modes_and_locks_unchanged_after_build':True},
            'static_precheck':static,'toolchains':toolchains,'commands':commands,'binaries':binaries,'workspace_compilation_features':workspace_artifacts,'outputs':outputs,'comparison':comparison,
            'features':'package defaults; no --all-features or test-harness requested; actual Cargo features recorded',
            'scope':'public library identity functions in compiled verification examples, not shipping daemon binary qualification',
            'not_observed':['S.device-package-validator.nonunix','actual shipping daemon artifact identities','13 non-public/unidentified binding consumer paths and transport negotiation','physical execution'],
            'baseline_sha256':digest(baseline_raw),'evaluator_sha256':EVALUATOR_SHA256,
            'execution_provenance':{'executor':'verification runner process','requested_by':os.environ.get('GITHUB_ACTOR','UNKNOWN'),
                'runner_name':os.environ.get('RUNNER_NAME','UNKNOWN'),'workflow':os.environ.get('GITHUB_WORKFLOW','UNKNOWN'),
                'run_id':os.environ.get('GITHUB_RUN_ID','UNKNOWN'),'repository':os.environ.get('GITHUB_REPOSITORY','UNKNOWN'),
                'user_acceptance':'NOT_PERFORMED; compiled identity agreement only'},
            'runner_sha256':digest(Path(__file__).read_bytes()),'comparator_sha256':digest((HERE/'compare_compiled.py').read_bytes())}
    exclusive(scratch/'compiled-identities.json',json.dumps(report,indent=2).encode()+b'\n')
    print(json.dumps({'status':report['status'],'receipt':str(scratch/'compiled-identities.json'),'observed':14,'nonunix':'NOT_COMPILED_FOR_THIS_TARGET'}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--evaluator',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    execute(parser.parse_args())


if __name__=='__main__':
    try:main()
    except (Refusal,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:
        print('M3 COMPILED IDENTITY REFUSED: '+str(error),file=sys.stderr);raise SystemExit(2)
