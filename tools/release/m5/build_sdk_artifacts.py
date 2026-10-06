#!/usr/bin/env python3
"""Build unsigned M5 SDK artifacts on a fresh Linux CI runner, never on this Mac.

Reuses the exact tracked client package test from the selected monorepo commit.
All generated source/build/lock changes are confined to --work. A Rust failure
retains partial metadata and logs, exits 2, and never writes final CHECKSUMS.sha256.
Run --help for required inputs. Root signs CHECKSUMS.sha256 offline in a separate step.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tomllib
import uuid
import zipfile
import traceback
from build_diagnostics import vocabulary,save_failure

from full_run.historical_bundle import validate_historical_bundle
from artifacts import archive, checksums, inventory, safe_name, verify_checksums, sha_file

REPOSITORY = 'jack0682/RobotTransformation'
PINS = {'grpcio':'1.84.0','protobuf':'7.36.2','setuptools':'84.0.0','wheel':'0.48.0','build':'1.6.1'}
RUST_MEMBERS = ['crates/rx-domain','crates/rx-process-contract']
RUST_CRATES = {'rx-domain','rx-process-contract'}
RUNTIME_HARNESS = ['run_registered_counter.py','infrastructure.py','fixtures.py','counter_commission.py',
                   'README.md','SOURCE_INPUTS.md','leak_audit.py','historical_bundle.py']


def encoded(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()


def digest(path): return sha_file(Path(path))


def publish(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(encoded(value)+b'\n')


def native_architecture(machine):
    try:return {'x86_64':'amd64','amd64':'amd64','aarch64':'arm64','arm64':'arm64'}[machine.lower()]
    except KeyError:raise ValueError('Unsupported Linux builder architecture: '+machine) from None


def validate_paths(repo,work,output):
    values=[Path(p).absolute() for p in [repo,work,output]]
    for path in values:
        if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('Symlinked source/work/output paths are refused')
    repo,work,output=[p.resolve() for p in values]
    if not repo.is_dir() or not (repo/'rx-platform/Cargo.toml').is_file() or not (repo/'rx-solutions/Cargo.toml').is_file():
        raise ValueError('The new monorepo root with both product components is required')
    if work.exists() or output.exists():raise ValueError('Fresh --work and --output paths are required')
    for path in [work,output]:
        if path.is_relative_to(repo) or repo.is_relative_to(path):raise ValueError('Artifacts/work may not overlap the source repository')
    if work.is_relative_to(output) or output.is_relative_to(work):raise ValueError('Producer logs/work and public output must be separate trees')
    return repo,work,output


def normalize_origin(value):
    patterns=[r'https://github\.com/([^/]+/[^/]+?)(?:\.git)?',r'git@github\.com:([^/]+/[^/]+?)(?:\.git)?',
              r'ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?']
    for pattern in patterns:
        found=re.fullmatch(pattern,value.strip().rstrip('/'))
        if found:return found[1]
    raise ValueError('Expected a canonical GitHub repository origin')


class Runner:
    def __init__(self,work):
        self.work=work;self.logs=work/'logs';self.logs.mkdir()
        self.serial=0;self.commands=[]
        self.environment=dict(os.environ,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',
            PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CACHE_DIR=str(work/'pip-cache'),
            XDG_CACHE_HOME=str(work/'cache'),TMPDIR=str(work/'tmp'),
            CARGO_BUILD_JOBS='1',CARGO_INCREMENTAL='0',CARGO_TARGET_DIR=str(work/'rust-target'),
            CARGO_HOME=str(work/'cargo-home'),CMAKE_BUILD_PARALLEL_LEVEL='2')
        (work/'tmp').mkdir()

    def run(self,label,args,*,cwd=None,extra_env=None,check=True):
        self.serial+=1
        stem=self.logs/(f'{self.serial:04d}-'+label)
        env=dict(self.environment,**(extra_env or {}))
        result=subprocess.run(list(map(str,args)),cwd=cwd or self.work,env=env,capture_output=True)
        stem.with_suffix('.stdout').write_bytes(result.stdout);stem.with_suffix('.stderr').write_bytes(result.stderr)
        record={'label':label,'argv':list(map(str,args)),'cwd':str(cwd or self.work),'returncode':result.returncode,
                'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
        self.commands.append(record)
        (self.work/'commands.json').write_bytes(encoded(self.commands)+b'\n')
        if check and result.returncode:raise RuntimeError(label+' failed; producer logs retained under --work/logs')
        return result

    def text(self,label,args,**kwargs):return self.run(label,args,**kwargs).stdout.decode().strip()


def git(runner,repo,*args):
    return runner.text('git-'+args[0],['git','-C',repo,*args],extra_env={'GIT_OPTIONAL_LOCKS':'0'})


def source_snapshot(runner,repo,expected):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',expected):raise ValueError('Full expected Git commit hash required')
    if Path(git(runner,repo,'rev-parse','--show-toplevel')).resolve()!=repo:raise ValueError('--repo is not the Git root')
    head=git(runner,repo,'rev-parse','HEAD')
    if head!=expected:raise ValueError('Source HEAD differs from --expected-head')
    dirty=git(runner,repo,'status','--porcelain=v1','--untracked-files=all','--ignore-submodules=none')
    if dirty:raise ValueError('Source working tree is not clean; no SDK build was authorized from local changes')
    origin=git(runner,repo,'remote','get-url','origin')
    if normalize_origin(origin)!=REPOSITORY:raise ValueError('Wrong repository origin')
    object_format=git(runner,repo,'rev-parse','--show-object-format')
    if object_format not in ('sha1','sha256'):raise ValueError('Unsupported Git object format')
    components={name:{'component_path':name,'tree_oid':git(runner,repo,'rev-parse',head+':'+name)}
                for name in ['rx-platform','rx-solutions']}
    return {'repository':REPOSITORY,'commit':head,'tree_oid':git(runner,repo,'rev-parse',head+'^{tree}'),
            'object_format':object_format,'clean':True,'components':components}


def parse_tree(raw):
    entries=[]
    for record in raw.split(b'\0'):
        if not record:continue
        header,path=record.split(b'\t',1)
        mode,kind,oid=header.decode('ascii').split(' ')
        name=path.decode('utf-8');safe_name(name)
        if kind!='blob' or mode not in ('100644','100755'):raise ValueError('Only tracked regular source files are supported: '+name)
        entries.append({'path':name,'blob':oid,'mode':mode})
    if len({e['path'] for e in entries})!=len(entries):raise ValueError('Duplicate tracked input path')
    return entries


def copy_tracked(runner,repo,snapshot,prefixes,destination,strip_prefix):
    destination.mkdir(parents=True,exist_ok=False)
    result=runner.run('source-files',['git','-C',repo,'ls-tree','-r','-z','--full-tree',snapshot['commit'],'--',*prefixes])
    entries=parse_tree(result.stdout)
    if not entries:raise ValueError('Empty tracked source selection')
    copied={}
    for entry in entries:
        source=repo/entry['path']
        if source.is_symlink() or not source.is_file():raise ValueError('Tracked source is no longer regular')
        raw=source.read_bytes()
        blob=hashlib.new(snapshot['object_format'],b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=entry['blob']:raise ValueError('Source bytes differ from expected commit: '+entry['path'])
        expected_mode='100755' if source.stat().st_mode & 0o111 else '100644'
        if expected_mode!=entry['mode']:raise ValueError('Source mode differs from expected commit')
        relative=Path(entry['path']).relative_to(strip_prefix)
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw);target.chmod(0o755 if entry['mode']=='100755' else 0o644)
        copied[relative.as_posix()]={'original_path':entry['path'],'blob':blob,'mode':entry['mode'],
                                  'sha256':hashlib.sha256(raw).hexdigest()}
    return copied


def minimal_workspace(raw):
    text=raw.decode('utf-8');value=tomllib.loads(text)
    members=value.get('workspace',{}).get('members')
    if not isinstance(members,list) or not set(RUST_MEMBERS)<=set(members):raise ValueError('Original workspace lacks selected public crates')
    if 'package' in value:raise ValueError('Expected a virtual workspace manifest')
    if 'default-members' in value['workspace']:raise ValueError('Review default-members before exporting')
    match=re.search(r'(?ms)^\[workspace\]\s*\n(.*?)(?=^\[|\Z)',text)
    if not match:raise ValueError('Workspace section unavailable')
    section=match.group(1)
    replaced,count=re.subn(r'(?ms)^members\s*=\s*\[.*?\]',
        'members = ["crates/rx-domain", "crates/rx-process-contract"]',section,count=1)
    if count!=1:raise ValueError('Cannot replace exactly the workspace members')
    generated=text[:match.start(1)]+replaced+text[match.end(1):]
    wanted=tomllib.loads(text);wanted['workspace']['members']=RUST_MEMBERS
    if tomllib.loads(generated)!=wanted:raise ValueError('Generated workspace changed more than members')
    return generated.encode()


def packages_by_identity(document):
    result={}
    for package in document.get('package',[]):
        identity=(package['name'],package['version'],package.get('source'))
        if identity in result:raise ValueError('Ambiguous duplicate package in Cargo.lock')
        result[identity]=package
    return result


def validate_lock_subset(original_raw,generated_raw):
    old_doc=tomllib.loads(original_raw.decode());new_doc=tomllib.loads(generated_raw.decode())
    if old_doc.get('version')!=new_doc.get('version'):raise ValueError('Cargo lock format changed')
    old,new=packages_by_identity(old_doc),packages_by_identity(new_doc)
    if not new:raise ValueError('Empty generated Cargo.lock')
    local=set();third_party=[]
    for identity,package in new.items():
        if identity not in old:raise ValueError('New dependency version/source introduced: '+str(identity))
        if package.get('checksum')!=old[identity].get('checksum'):raise ValueError('Dependency checksum changed: '+str(identity))
        if package.get('source') is None:
            local.add(package['name'])
        else:
            third_party.append({k:package[k] for k in ['name','version','source','checksum'] if k in package})
    if local!=RUST_CRATES:raise ValueError('Generated lock contains nonpublic or missing local crates')
    return {'status':'LOCK_SUBSET_VERIFIED','original_packages':len(old),'generated_packages':len(new),
            'removed_packages':len(set(old)-set(new)),'local_crates':sorted(local),
            'third_party':sorted(third_party,key=lambda p:(p['name'],p['version'],p['source']))}


def validate_rust_metadata(value,root):
    root=root.resolve();members=set(value['workspace_members']);selected=[]
    for package in value['packages']:
        if package['id'] in members:selected.append(package['name'])
        if package['source'] is None:
            path=Path(package['manifest_path']).resolve()
            if not path.is_relative_to(root) or package['name'] not in RUST_CRATES:
                raise ValueError('Rust source bundle escapes the two public crates')
    if set(selected)!=RUST_CRATES or len(members)!=2:raise ValueError('Rust metadata workspace differs')


def wheel_metadata(path):
    with zipfile.ZipFile(path) as stream:
        names=stream.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate wheel member')
        for name in names:safe_name(name.rstrip('/'))
        # Vendored distributions may carry nested dist-info data (setuptools
        # does). Only this wheel's root dist-info identifies the distribution.
        metadata=[n for n in names if n.count('/')==1 and n.endswith('.dist-info/METADATA')]
        wheel=[n for n in names if n.count('/')==1 and n.endswith('.dist-info/WHEEL')]
        if (len(metadata)!=1 or len(wheel)!=1
                or metadata[0].rsplit('/',1)[0]!=wheel[0].rsplit('/',1)[0]):
            raise ValueError('Wheel root metadata is ambiguous or inconsistent')
        info=BytesParser().parsebytes(stream.read(metadata[0]));tags=BytesParser().parsebytes(stream.read(wheel[0]))
        if not info.get('Name') or not info.get('Version'):raise ValueError('Wheel name/version absent')
        return {'filename':Path(path).name,'name':info['Name'],'version':info['Version'],
            'requires_dist':info.get_all('Requires-Dist',[]),'requires_python':info.get('Requires-Python'),
            'tags':tags.get_all('Tag',[]),'sha256':digest(path),'bytes':Path(path).stat().st_size}


def dependency_versions(wheels):
    records=[wheel_metadata(p) for p in sorted(Path(wheels).glob('*.whl'))]
    by_name={re.sub(r'[-_.]+','-',r['name']).lower():r for r in records}
    if len(by_name)!=len(records):raise ValueError('Multiple versions of the same Python package in wheelhouse')
    for name,version in PINS.items():
        if name not in by_name or by_name[name]['version']!=version:raise ValueError('Pinned Python dependency absent/different: '+name)
    if 'rxclpy' not in by_name:raise ValueError('Offline wheelhouse lacks built rxclpy')
    return records


def validate_python_closure(records,environment):
    normalize=lambda name:re.sub(r'[-_.]+','-',name).lower()
    expected={normalize(item['name']):item['version'] for item in environment if normalize(item['name'])!='pip'}
    actual={normalize(item['name']):item['version'] for item in records}
    if actual!=expected:raise ValueError('Offline wheelhouse differs from the environment used for conformance')
    return expected


def toolchain(runner,source):
    commands={'python':[sys.executable,'--version'],'git':['git','--version'],'cmake':['cmake','--version'],
        'cxx':['c++','--version'],'protoc':['protoc','--version'],'patchelf':['patchelf','--version'],
        'pkg-config':['pkg-config','--version'],'readelf':['readelf','--version'],'ldd':['ldd','--version']}
    result={'system':platform.system(),'machine':platform.machine(),'python_implementation':platform.python_implementation(),
        'python_target':{'version':platform.python_version(),'cache_tag':sys.implementation.cache_tag,
                         'soabi':sysconfig.get_config_var('SOABI')}}
    for name,args in commands.items():
        executable=shutil.which(str(args[0]))
        if executable is None:raise RuntimeError('Required CI tool is missing: '+name)
        response=runner.run('version-'+name,args,cwd=source)
        path=Path(executable).resolve()
        result[name]={'version':(response.stdout+response.stderr).decode(errors='replace').strip(),
            'executable_sha256':digest(path)}
    packages={}
    for name in ['protobuf','grpc++','openssl']:
        packages[name]=runner.text('pkg-config-'+name,['pkg-config','--modversion',name],cwd=source)
    result['cpp_dependencies']=packages
    return result


def dynamic_dependencies(text,install):
    result=[]
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        if 'not found' in line:raise ValueError('C++ runtime shared dependency is missing')
        if '=>' in line:
            name,right=line.split('=>',1);path=right.strip().split(' (',1)[0]
        elif line.startswith('/'):
            path=line.split(' (',1)[0];name=Path(path).name
        else:
            result.append({'name':line.split(' (',1)[0],'origin':'kernel'});continue
        source=Path(path).resolve()
        if not source.is_file():raise ValueError('ldd did not identify a regular dependency')
        local=source.is_relative_to(install.resolve())
        result.append({'name':name.strip(),'resolved_file':source.name,'origin':'sdk' if local else 'system',
            'artifact_path':source.relative_to(install.resolve()).as_posix() if local else None,'sha256':digest(source)})
    return result


def build_clients(runner,repo,snapshot,output):
    source=runner.work/'client-source'
    prefixes=['rx-platform/'+name for name in ['clients','proto','spec','LICENSE','NOTICE',
        'tools/test_client_packages.py','tools/prepare_clients.py','tools/export_protocol.py']]
    lineage=copy_tracked(runner,repo,snapshot,prefixes,source,'rx-platform')
    venv=runner.work/'client-build-venv'
    runner.run('fresh-venv',[sys.executable,'-m','venv',venv])
    python=venv/'bin/python'
    runner.run('install-pinned-build-dependencies',[python,'-m','pip','install','--only-binary=:all:',
        *[name+'=='+version for name,version in PINS.items()]])
    build=runner.work/'client-packages'
    runner.run('existing-client-package-tests',[python,source/'tools/test_client_packages.py','--work',build],cwd=source)
    result=json.loads((build/'result.json').read_bytes())
    if result.get('status')!='CLIENT_PACKAGES_PASS' or not result.get('same_expanded_bytes_statuses_roundtrips') or result.get('cases',0)<=0:
        raise ValueError('Existing client package test did not produce valid PASS evidence')
    wheels=list((build/'wheels').glob('*.whl'))
    if len(wheels)!=1:raise ValueError('Exactly one built rxclpy wheel required')
    metadata=wheel_metadata(wheels[0])
    project=tomllib.loads((source/'clients/rxclpy/pyproject.toml').read_text())['project']
    if metadata['name']!='rxclpy' or metadata['version']!=project['version']:
        raise ValueError('Built Python package name/version differs from selected source')
    shutil.copyfile(wheels[0],output/wheels[0].name)
    python_artifact={'path':wheels[0].name,'sha256':digest(output/wheels[0].name),
        'bytes':(output/wheels[0].name).stat().st_size,'wheel':metadata,'scope':'installed Python client library; no runtime core'}
    versions=json.loads(runner.text('python-installed-metadata',[python,'-c',
        'import importlib.metadata,json; print(json.dumps(sorted([{"name":d.metadata["Name"],"version":d.version} for d in importlib.metadata.distributions()],key=lambda d:d["name"].lower())))']))
    frozen=[v['name']+'=='+v['version'] for v in versions if re.sub(r'[-_.]+','-',v['name']).lower() not in ('pip','rxclpy')]
    (runner.work/'python-build-requirements.txt').write_text('\n'.join(sorted(frozen))+'\n')
    wheelhouse=runner.work/'python-wheelhouse';wheelhouse.mkdir()
    runner.run('download-offline-wheelhouse',[python,'-m','pip','download','--only-binary=:all:','--dest',wheelhouse,
        wheels[0],'-r',runner.work/'python-build-requirements.txt'])
    dependencies=dependency_versions(wheelhouse)
    validate_python_closure(dependencies,versions)
    python_dependencies=archive(wheelhouse,output/'python-wheelhouse.tar.gz','python-wheelhouse')
    python_dependencies['scope']='offline same-Python-ABI/native-architecture client installation and build dependencies'
    install=runner.work/'rxclcpp';shutil.copytree(build/'install',install,symlinks=True)
    (install/'bin').mkdir(exist_ok=True)
    shutil.copyfile(build/'cpp-build/rxclcpp-conformance',install/'bin/rxclcpp-conformance')
    (install/'bin/rxclcpp-conformance').chmod(0o755)
    runner.run('strip-generated-conformance-rpath',['patchelf','--remove-rpath',install/'bin/rxclcpp-conformance'])
    dynamic=runner.text('conformance-elf-dynamic',['readelf','-d',install/'bin/rxclcpp-conformance'])
    if '(RPATH)' in dynamic or '(RUNPATH)' in dynamic:raise ValueError('Exported conformance binary retains build RPATH')
    licenses=install/'share/licenses/rxclcpp';licenses.mkdir(parents=True)
    for name in ['LICENSE','NOTICE']:shutil.copyfile(source/name,licenses/name)
    libdirs=sorted({str(p.parent) for p in install.rglob('librxclcpp.so*')})
    if not libdirs:raise ValueError('Installed rxclcpp shared library absent')
    libs=runner.text('cpp-runtime-dependencies',['ldd',install/'bin/rxclcpp-conformance'],extra_env={'LD_LIBRARY_PATH':':'.join(libdirs)})
    if 'not found' in libs:raise ValueError('C++ runtime shared dependency is missing')
    runner.run('relocated-cpp-conformance',[install/'bin/rxclcpp-conformance',install/'share/rxclcpp/protocol/strict-wire-v1/vectors.json'],
        extra_env={'LD_LIBRARY_PATH':':'.join(libdirs)})
    cpp=archive(install,output/'rxclcpp.tar.gz','rxclcpp');cpp['scope']='native Linux installed CMake package; system protobuf/gRPC/OpenSSL dependencies required'
    prepared=runner.work/'client-sources'
    shutil.copytree(build/'prepared',prepared,ignore=shutil.ignore_patterns('build','__pycache__','*.pyc','*.egg-info'))
    shutil.copytree(source/'clients/examples',prepared/'examples')
    sources=archive(prepared,output/'client-sources.tar.gz','client-sources')
    sources['scope']='prepared public client sources, generated protocol closure, examples; no core services'
    return {'artifacts':{'rxclpy':python_artifact,'python_wheelhouse':python_dependencies,'rxclcpp':cpp,'client_sources':sources},
        'status':'BUILT_AND_EXISTING_CLIENT_TESTS_PASSED','producer_test':result,
        'protocol_build':json.loads((build/'prepared/build.json').read_bytes()),'python_environment':versions,
        'python_wheels':dependencies,'cpp_dynamic_dependencies':dynamic_dependencies(libs,install),'source_input_inventory':lineage,
        'build_resource_budget':{'cargo_jobs':1,'cmake_jobs':2,'cmake_scope':'two original client test --build invocations explicitly use -j2; distribution recipe CMake jobs1 is separate'}}


def build_adapter(runner,repo,snapshot,image,assets,output):
    # Compare selected tracked bytes, not an ignored local lookalike.
    reference=runner.work/'adapter-reference'
    copy_tracked(runner,repo,snapshot,['rx-solutions/deployment/external-adapters/rx_external_adapter.py'],
        reference,'rx-solutions/deployment/external-adapters')
    root=runner.work/'adapter-extraction';root.mkdir()
    result=runner.run('installed-external-sdk',['docker','run','--rm','--network','none','--read-only',
        '--memory=512m','--cpus=1','--pids-limit=32','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--user',f'{os.getuid()}:{os.getgid()}','-v',str(root)+':/out:rw','--entrypoint','/opt/rx/bin/rx-device-package',
        image,'external-sdk','/out/external-adapter-sdk'])
    receipt=json.loads(result.stdout)
    if receipt.get('status')!='EXTERNAL_ADAPTER_SDK_EXPORTED' or receipt.get('activation_authorized') is not False:
        raise ValueError('Installed SDK export receipt differs')
    sdk=root/'external-adapter-sdk';helper=sdk/'rx_external_adapter.py'
    if digest(helper)!=digest(reference/'rx_external_adapter.py'):raise ValueError('Installed helper differs from selected S source')
    required=['counter.py','make_package_inputs.py','conformance.py','README.md','schema-reference.json']
    for name in required:
        source=assets/name
        if source.is_symlink() or not source.is_file():raise ValueError('Required parent-owned public adapter fixture absent: '+name)
        shutil.copyfile(source,sdk/name)
    for name in ['LICENSE','NOTICE']:shutil.copyfile(repo/'rx-solutions'/name,sdk/name)
    artifact=archive(sdk,output/'external-adapter-sdk.tar.gz','external-adapter-sdk')
    artifact['scope']='installed external adapter helper and public simulation/conformance examples; no qualification authority'
    return {'status':'INSTALLED_EXPORT_MATCHES_SELECTED_SOURCE','artifact':artifact,'export_receipt':receipt,
        'image':image,'helper_sha256':digest(helper),'producer_examples':{n:digest(assets/n) for n in required}}


def build_verification_kit(runner,repo,snapshot,harness,output):
    kit=runner.work/'verification-kit'
    lineage=copy_tracked(runner,repo,snapshot,['rx-platform/tools/cell_delivery'],kit/'cell_delivery','rx-platform/tools/cell_delivery')
    for name in ['LICENSE','NOTICE']:shutil.copyfile(repo/'rx-platform'/name,kit/name)
    (kit/'full_run').mkdir()
    for name in RUNTIME_HARNESS:
        source=harness/name
        if source.is_symlink() or not source.is_file():raise ValueError('Full Run verification helper absent: '+name)
        shutil.copyfile(source,kit/'full_run'/name)
    artifact=archive(kit,output/'verification-kit.tar.gz','verification-kit')
    artifact['scope']='trusted CI provisioner/verifier only; never mounted in external-author containers'
    return {'status':'PACKAGED_NOT_EXECUTED','artifact':artifact,'source_input_inventory':lineage,
            'registered_run_executed':False}


def build_historical(runner,bundle,output):
    pins=validate_historical_bundle(bundle)
    snapshot=runner.work/'historical-runtime-client'
    shutil.copytree(bundle,snapshot)
    if validate_historical_bundle(snapshot)!=pins:raise ValueError('Historical copy changed the selected bytes')
    artifact=archive(snapshot,output/'historical-runtime-client.tar.gz','historical-runtime-client')
    artifact['scope']='exact published old Python runtime facade; live compatibility is a separate required gate'
    return {'status':'PINNED_PUBLISHED_BYTES_NOT_EXECUTED','artifact':artifact,'pins':pins}


def build_rust(runner,repo,snapshot,output):
    root=runner.work/'public-rust-contracts'
    prefixes=['rx-platform/'+name for name in [*RUST_MEMBERS,'proto','spec','LICENSE','NOTICE','Cargo.toml','Cargo.lock','rust-toolchain.toml']]
    lineage=copy_tracked(runner,repo,snapshot,prefixes,root,'rx-platform')
    original_manifest=(root/'Cargo.toml').read_bytes();original_lock=(root/'Cargo.lock').read_bytes()
    (root/'Cargo.toml').write_bytes(minimal_workspace(original_manifest))
    expected_toolchain=tomllib.loads((root/'rust-toolchain.toml').read_text())['toolchain']['channel']
    if shutil.which('rustup'):
        installed=runner.text('installed-rust-toolchains',['rustup','toolchain','list'],cwd=runner.work)
        if not any(line.startswith(expected_toolchain+'-') or line.split(' ')[0]==expected_toolchain for line in installed.splitlines()):
            raise ValueError('Pinned Rust toolchain must already be installed on the CI runner')
    rustc=runner.text('rustc-version',['rustc','--version'],cwd=root)
    cargo=runner.text('cargo-version',['cargo','--version'],cwd=root)
    if not rustc.startswith('rustc '+expected_toolchain+' '):raise ValueError('Selected Rust toolchain differs from pinned source')
    # Only this generated workspace lock may change. Existing locked versions are
    # retained unless Cargo cannot resolve them; any update fails the subset gate.
    resolved=runner.run('resolve-prune-generated-lock',['cargo','metadata','--format-version','1'],cwd=root)
    metadata=json.loads(resolved.stdout);validate_rust_metadata(metadata,root)
    generated_lock=(root/'Cargo.lock').read_bytes()
    lock=validate_lock_subset(original_lock,generated_lock)
    runner.run('locked-offline-public-contract-check',['cargo','check','--workspace','--lib','--locked','--offline'],cwd=root)
    if (root/'Cargo.lock').read_bytes()!=generated_lock:raise ValueError('--locked check changed the generated lock')
    metadata_file={'schema':'rx.public-rust-contracts-provenance.v1','repository':REPOSITORY,'commit':snapshot['commit'],
        'component_path':'rx-platform','component_tree_oid':snapshot['components']['rx-platform']['tree_oid'],
        'source_crates_unchanged':True,'source_inventory':lineage,
        'workspace_manifest_derivation':'workspace.members narrowed to two public crates only',
        'original_manifest_sha256':hashlib.sha256(original_manifest).hexdigest(),'generated_manifest_sha256':digest(root/'Cargo.toml'),
        'original_lock_sha256':hashlib.sha256(original_lock).hexdigest(),'generated_lock_sha256':digest(root/'Cargo.lock'),
        'lock_gate':lock,'validation':'cargo check --workspace --lib --locked --offline',
        'scope':'source contract API only; no Host/Engine services or arbitrary plugin ABI claim'}
    publish(root/'PROVENANCE.json',metadata_file)
    artifact=archive(root,output/'public-rust-contracts.tar.gz','public-rust-contracts')
    artifact['scope']=metadata_file['scope']
    return {'status':'LOCKED_PUBLIC_CONTRACT_CHECK_PASSED','artifact':artifact,'toolchain':{'rustc':rustc,'cargo':cargo},
            'lock':lock,'manifest_sha256':digest(root/'Cargo.toml'),'lock_sha256':digest(root/'Cargo.lock')}



def record_closed_sdk_failure(runner,public_vocab):
    if public_vocab is None:return
    # Raw failure details remain local; only candidate-bounded locations and
    # fixed categories can reach the early-failure publication path.
    try:
        detail=runner.work/'wrapper-failure.stderr';detail.write_text(traceback.format_exc())
        logs=[('stderr',detail)]
        if runner.commands:
            item=runner.commands[-1]
            if item['returncode']:
                files=sorted(runner.logs.glob('*'+item['label']+'.stderr'))
                if files:logs.append(('stderr',files[-1]))
        save_failure(runner.work/'closed-failure.json',public_vocab,'SDK_BUILD','sdk',1,logs,runner.work)
    except Exception:pass  # Diagnostic unavailability cannot make the build pass.

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--solutions-image',required=True,help='Exact local immutable sha256 image ID; no mutable tag')
    p.add_argument('--architecture',choices=['amd64','arm64'],required=True)
    p.add_argument('--historical-bundle',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True,help='Fresh private build/log tree, outside repo and output')
    p.add_argument('--output',type=Path,required=True,help='Fresh public unsigned artifact tree')
    p.add_argument('--adapter-assets',type=Path,default=Path(__file__).parent/'sdk/external-adapter')
    p.add_argument('--full-run',type=Path,default=Path(__file__).parent/'full_run')
    p.add_argument('--include-rust',action=argparse.BooleanOptionalAction,default=True)
    p.add_argument('--execute',action='store_true')
    return p


def main():
    p=parser();a=p.parse_args()
    if not a.execute or platform.system()!='Linux' or os.environ.get('CI')!='true':
        p.error('Only a fresh Linux CI runner with CI=true and --execute may run this builder')
    if native_architecture(platform.machine())!=a.architecture:p.error('Native builder architecture differs from requested artifacts')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',a.solutions_image):p.error('An immutable local S image ID is required')
    repo,work,output=validate_paths(a.repo,a.work,a.output)
    os.umask(0o022);work.mkdir(parents=True);output.mkdir(parents=True)
    runner=Runner(work)
    state={'schema':'rx.sdk-build-state.v1','status':'BUILDING','registered_run_executed':False,
           'publication_signature_created':False,'architecture':a.architecture,'artifacts':{}}
    public_vocab=None
    try:
        source=source_snapshot(runner,repo,a.expected_head);state['source']=source
        public_vocab=vocabulary(repo,a.expected_head)
        image=json.loads(runner.text('candidate-s-image',['docker','image','inspect',a.solutions_image]))
        if len(image)!=1 or image[0]['Id']!=a.solutions_image or image[0]['Os']!='linux' or image[0]['Architecture']!=a.architecture:
            raise ValueError('Candidate S image identity/platform differs')
        state['solutions_image']={'id':image[0]['Id'],'architecture':image[0]['Architecture'],'os':image[0]['Os']}
        versions=toolchain(runner,repo/'rx-platform');state['toolchain']=versions
        clients=build_clients(runner,repo,source,output);state['clients']=clients;state['artifacts'].update(clients['artifacts'])
        adapter=build_adapter(runner,repo,source,a.solutions_image,a.adapter_assets.resolve(),output)
        state['external_adapter']=adapter;state['artifacts']['external_adapter']=adapter['artifact']
        kit=build_verification_kit(runner,repo,source,a.full_run.resolve(),output)
        state['verification_kit']=kit;state['artifacts']['verification_kit']=kit['artifact']
        historical=build_historical(runner,a.historical_bundle.resolve(),output)
        state['historical_runtime_client']=historical;state['artifacts']['historical_runtime_client']=historical['artifact']
        if a.include_rust:
            try:
                rust=build_rust(runner,repo,source,output)
            except Exception as error:
                record_closed_sdk_failure(runner,public_vocab)
                state.update(status='PARTIAL_UNVERIFIED',rust={'status':'UNVERIFIED','reason':str(error),
                    'runtime_api_qualification_claim':False})
                publish(work/'partial-build.json',state)
                print('Rust source bundle is UNVERIFIED; final manifest/CHECKSUMS.sha256 were not created.',file=sys.stderr)
                return 2
            state['rust']=rust;state['artifacts']['public_rust_contracts']=rust['artifact']
        else:
            state['rust']={'status':'NOT_SELECTED','explicit_include_rust':False,'support_claim':False}
        after=source_snapshot(runner,repo,a.expected_head)
        if source!=after:raise ValueError('Source identity/cleanliness changed during build')
        state.update(schema='rx.sdk-artifact-manifest.v1',status='SDK_ARTIFACTS_BUILT_FOR_REPORTED_SCOPES',created_at_utc=datetime.now(timezone.utc).isoformat(),
            producer={'builder_sha256':digest(Path(__file__)),'artifact_utility_sha256':digest(Path(__file__).with_name('artifacts.py'))},
            scopes={'client_package_conformance':'EXECUTED_IN_PRODUCER','external_helper_source_parity':'VERIFIED',
                'adapter_protocol_conformance':'NOT_EXECUTED_BY_BUILDER','artifact_only_consumer':'NOT_EXECUTED_BY_BUILDER',
                'registered_external_run':'NOT_EXECUTED_BY_BUILDER','physical_execution':'NOT_PERFORMED'},
            signing={'status':'UNSIGNED','required_next_step':'Root offline GPG signature over CHECKSUMS.sha256; no CI private key'})
        publish(output/'manifest.json',state)
        files={item['path'] for item in state['artifacts'].values()}|{'manifest.json'}
        raw=checksums(output,files)
        (output/'CHECKSUMS.sha256').write_bytes(raw)
        verify_checksums(output,raw,allowed_extras=('CHECKSUMS.sha256',))
        publish(work/'result.json',{'status':state['status'],'manifest_sha256':digest(output/'manifest.json'),
            'checksums_sha256':digest(output/'CHECKSUMS.sha256'),'artifact_names':sorted(files),
            'unsigned':True,'registered_run_executed':False})
        print(json.dumps({'status':state['status'],'manifest':str(output/'manifest.json'),'unsigned':True}))
        return 0
    except Exception as error:
        record_closed_sdk_failure(runner,public_vocab)
        state.update(status='FAILED_UNVERIFIED',failure={'type':type(error).__name__,'reason':str(error)},
            final_candidate_authorized=False)
        if not (work/'partial-build.json').exists():publish(work/'partial-build.json',state)
        print('SDK candidate failed; raw details retained privately; closed diagnostics may be available. No release acceptance claim.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
