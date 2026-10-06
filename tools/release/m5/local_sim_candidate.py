#!/usr/bin/env python3
"""Future fresh Linux CI: build and exercise the existing LOCAL_SIM installer.

This scope is rx-skill-server plus its installed worker, not the registered
P/Host/Executor external-adapter simulation. Old SDK artifact compatibility is
NOT_PROVEN. No public signature or global M5 PASS is produced by this script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tarfile
import uuid

from full_run.leak_audit import collect_private, approve_public, refuse_public
from artifacts import checksums, inventory, sha_file, validate_tar, verify_checksums
from build_sdk_artifacts import Runner, encoded, git, native_architecture, parse_tree, publish, source_snapshot, validate_paths

EXPECTED_CHECKS={
    'clean-installer-and-cli-link',
    'client-worker-authentication-separation',
    'external-code-executed-once-and-original-request-replayed',
    'key-version-and-physical-scope-refusals',
    'lost-admission-body-recovered-by-original-id',
    'real-exception-output-schema-and-timeout',
    'four-skill-process-dataflow-identity-failure-unknown-and-versioned-metrics',
    'persistent-installation-restart',
    'killed-worker-quarantined-original-and-accepted-distinct-next-run',
    'non-root-readonly-no-devices-no-docker-socket',
    'lost-database-refused-and-preserved-original-restored',
    'lost-volume-refused-without-recreating-ledger',
}
SOURCE_PATHS=['repository-settings.json','rx-platform/Cargo.toml','rx-platform/Cargo.lock',
    'rx-platform/crates','rx-platform/proto','rx-platform/spec',
    'rx-solutions/docker/Skills.Dockerfile','rx-solutions/deployment/local-skills',
    'rx-solutions/tools/build_skill_release.py','rx-solutions/tools/test_skill_install.py',
    'rx-solutions/tools/skill_process_acceptance.py','rx-solutions/LICENSE','rx-solutions/NOTICE']
PUBLIC_IMAGE_FILES=['/usr/local/bin/rx-skill-server','/opt/rx/worker.py','/opt/rx/runner.py','/opt/rx/LICENSE','/opt/rx/NOTICE']


def source_inventory(runner,repo,snapshot):
    raw=runner.run('local-sim-source-list',['git','-C',repo,'ls-tree','-r','-z','--full-tree',snapshot['commit'],'--',*SOURCE_PATHS]).stdout
    records={}
    for entry in parse_tree(raw):
        file=repo/entry['path']
        if file.is_symlink() or not file.is_file():raise ValueError('Nonregular selected source')
        blob=hashlib.new(snapshot['object_format']);blob.update(b'blob '+str(file.stat().st_size).encode()+b'\0')
        with file.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):blob.update(chunk)
        actual_mode='100755' if file.stat().st_mode&0o111 else '100644'
        if blob.hexdigest()!=entry['blob'] or actual_mode!=entry['mode']:raise ValueError('Selected source bytes/mode differ from expected HEAD')
        records[entry['path']]={'blob':entry['blob'],'mode':entry['mode'],'sha256':sha_file(file),'bytes':file.stat().st_size}
    if not records:raise ValueError('Empty selected source inventory')
    return records


def reject_untracked_build_inputs(repo,records):
    # Docker copies these complete directories, and the release builder copies
    # local-skills. An ignored stray file must not become an unpinned input.
    prefixes=['rx-platform/crates','rx-platform/proto','rx-platform/spec','rx-solutions/deployment/local-skills']
    for prefix in prefixes:
        actual=set()
        for file in (repo/prefix).rglob('*'):
            relative=file.relative_to(repo).as_posix()
            if prefix.endswith('local-skills') and ('__pycache__' in file.parts or file.suffix=='.pyc'):continue
            if file.is_symlink():raise ValueError('Symlink in source build context')
            if file.is_file():actual.add(relative)
        expected={name for name in records if name.startswith(prefix+'/')}
        if actual!=expected:raise ValueError('Untracked or missing source build-context input under '+prefix)


def validate_release(release,snapshot,architecture,version,cache_namespace):
    if (release.get('schema')!='rx.local-sim.release.v1' or release.get('architecture')!=architecture
            or release.get('version')!=version or release.get('source_dirty') is not False
            or release.get('physical_execution')!='NOT_SUPPORTED' or release.get('build_jobs')!=1
            or release.get('cache_namespace')!=cache_namespace):
        raise ValueError('Local release metadata does not match this candidate request')
    if release.get('platform_commit')!=snapshot['commit'] or release.get('solutions_commit')!=snapshot['commit']:
        raise ValueError('Both LOCAL_SIM components must come from the exact monorepo commit')
    expected={role:{'repository':snapshot['repository'],'commit':snapshot['commit'],
        'component_path':component,'tree_oid':snapshot['components'][component]['tree_oid']}
        for role,component in [('platform','rx-platform'),('solutions','rx-solutions')]}
    if release.get('component_sources')!=expected:raise ValueError('Local release component tuple differs')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',release.get('image_id','')):raise ValueError('Immutable image identity absent')
    if release.get('image')!='rx-local-skills:'+version+'-'+architecture:raise ValueError('Local candidate image tag differs')
    return expected


def validate_acceptance(result,release):
    if result.get('status')!='PASS' or result.get('physical_execution')!='NOT_PERFORMED' or result.get('release')!=release:
        raise ValueError('Installed acceptance does not cover this exact candidate release')
    checks=result.get('checks',[])
    if not isinstance(checks,list) or len(set(checks))!=len(checks) or not EXPECTED_CHECKS<=set(checks):
        raise ValueError('Installed acceptance lacks required concrete regression checks')
    normal=result['normal_result']
    if (normal['request']['skill']!='external-sum' or normal['request']['version']!='1.0.0'
            or normal['request']['input']!={'values':[2,4,8]} or normal['output']['total']!=14
            or normal['operation']['outcome']!='SUCCEEDED'):
        raise ValueError('Installed actual external skill result differs')
    uuid.UUID(normal['request']['request_id']);uuid.UUID(normal['output']['receipt'])
    return {'executed_checks':checks,'recognized_checks':sorted(EXPECTED_CHECKS),
        'additional_reported_checks':sorted(set(checks)-EXPECTED_CHECKS),
        'scope':'current candidate LOCAL_SIM behavior only; no legacy SDK compatibility claim'}


def validate_current_image(image,release):
    if len(image)!=1 or image[0]['Id']!=release['image_id'] or image[0]['Os']!='linux' or image[0]['Architecture']!=release['architecture']:
        raise ValueError('Current local image differs from checksum-bound candidate release')
    if image[0]['Config'].get('User')!='10001:10001':raise ValueError('Candidate image must retain non-root runtime identity')
    return {'id':image[0]['Id'],'os':image[0]['Os'],'architecture':image[0]['Architecture'],
            'runtime_user':image[0]['Config']['User'],'labels':image[0]['Config'].get('Labels',{})}


def validate_original_archive_checksum(file,checksum_file):
    lines=checksum_file.read_text().splitlines()
    if len(lines)!=1:raise ValueError('Original LOCAL_SIM build must contain one release archive')
    expected,separator,name=lines[0].partition('  ')
    if not separator or name!=file.name or expected!=sha_file(file):raise ValueError('Original bundle checksum mismatch')


def verify_bundle_archive(path,bundle_inventory):
    validate_tar(path);actual={}
    with tarfile.open(path,'r:*') as stream:
        for member in stream:
            if member.isdir():continue
            if not member.isfile() or not member.name.startswith('rx-local-skills/'):
                raise ValueError('Unexpected local bundle archive member')
            relative=member.name.removeprefix('rx-local-skills/')
            with stream.extractfile(member) as source:
                digest=hashlib.file_digest(source,'sha256').hexdigest()
            actual[relative]={'sha256':digest,'bytes':member.size,'mode':oct(member.mode&0o777)}
    expected={name:{key:item[key] for key in ['sha256','bytes','mode']} for name,item in bundle_inventory.items()}
    if actual!=expected:raise ValueError('Tested extracted bundle differs from its published archive')


def image_inventory(runner,release,source_files):
    code='import hashlib,json,pathlib; print(json.dumps({p:hashlib.file_digest(pathlib.Path(p).open("rb"),"sha256").hexdigest() for p in '+repr(PUBLIC_IMAGE_FILES)+'}))'
    result=json.loads(runner.text('local-sim-image-payload',['docker','run','--rm','--network','none','--read-only',
        '--memory=256m','--cpus=1','--pids-limit=32','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--entrypoint','python3',release['image_id'],'-c',code]))
    if set(result)!=set(PUBLIC_IMAGE_FILES) or any(not re.fullmatch('[0-9a-f]{64}',value) for value in result.values()):
        raise ValueError('Image payload inventory is incomplete')
    for output,source in [('/opt/rx/worker.py','rx-solutions/deployment/local-skills/worker.py'),
        ('/opt/rx/runner.py','rx-solutions/deployment/local-skills/runner.py'),
        ('/opt/rx/LICENSE','rx-solutions/LICENSE'),('/opt/rx/NOTICE','rx-solutions/NOTICE')]:
        if result[output]!=source_files[source]['sha256']:raise ValueError('Installed image source payload differs: '+output)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--expected-head',required=True)
    p.add_argument('--architecture',choices=['amd64','arm64'],required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute-fresh-linux-ci',action='store_true')
    a=p.parse_args()
    if not a.execute_fresh_linux_ci or platform.system()!='Linux' or os.environ.get('CI')!='true':
        p.error('Fresh Linux CI=true and --execute-fresh-linux-ci are required; no local product execution')
    if native_architecture(platform.machine())!=a.architecture:p.error('Builder native architecture differs')
    repo,work,output=validate_paths(a.repo,a.work,a.output)
    work.mkdir(parents=True);runner=Runner(work)
    runner.environment.update(PYTHONOPTIMIZE='0',PYTHONPATH='')
    state={'schema':'rx.local-sim-candidate.v1','status':'BUILDING','profile':'LOCAL_SIM','m5_complete':False,
        'old_sdk_artifact_compatibility':'NOT_PROVEN','registered_external_adapter_run':'NOT_ASSESSED',
        'physical_execution':'NOT_PERFORMED','public_signature_created':False}
    try:
        source=source_snapshot(runner,repo,a.expected_head);files=source_inventory(runner,repo,source)
        reject_untracked_build_inputs(repo,files);state['source']=source
        nonce=uuid.uuid4().hex[:12]
        version='migration-rc.'+source['commit'][:12]+'.'+nonce
        cache='m5-local-'+source['commit'][:12]+'-'+nonce
        build=work/'built-local-sim';script=repo/'rx-solutions/tools/build_skill_release.py'
        build_script_sha=sha_file(script)
        runner.run('build-existing-local-sim-candidate',[sys.executable,script,'--platform',repo/'rx-platform',
            '--output',build,'--architecture',a.architecture,'--version',version,'--build-jobs','1','--cache-namespace',cache],
            cwd=repo/'rx-solutions')
        bundle=build/'bundle';release=json.loads((bundle/'release.json').read_bytes())
        validate_release(release,source,a.architecture,version,cache)
        archive=build/('rx-local-skills-'+version+'-linux-'+a.architecture+'.tar.gz')
        validate_original_archive_checksum(archive,build/'CHECKSUMS.sha256')
        if sha_file(bundle/'runtime.tar.gz')!=release['image_sha256']:raise ValueError('Runtime image archive differs')
        bundle_inventory=inventory(bundle)
        verify_bundle_archive(archive,bundle_inventory)
        info=lambda:json.loads(runner.text('inspect-current-local-image',['docker','image','inspect',release['image']]))
        before=validate_current_image(info(),release);payload=image_inventory(runner,release,files)
        expected_archive_ids=json.loads(runner.text('verify-image-archive-identities',[sys.executable,'-c',
            'import json,sys;sys.path.insert(0,sys.argv[1]);from image_identity import identities;print(json.dumps(sorted(identities(sys.argv[2],sys.argv[3]))))',
            bundle,bundle/'runtime.tar.gz',a.architecture]))
        if release['image_id'] not in expected_archive_ids:raise ValueError('Current image is not an identity of the saved image archive')
        evidence=work/'installer-acceptance';retained=work/'private-acceptance'
        shim=Path(__file__).parent/'full_run/leak_audit.py'
        runner.run('actual-existing-installed-skill-tests',[sys.executable,shim,'retain-tempdirs','--root',retained,
            '--script',repo/'rx-solutions/tools/test_skill_install.py','--','--bundle',bundle,'--evidence',evidence],cwd=repo/'rx-solutions')
        result=json.loads((evidence/'result.json').read_bytes());acceptance=validate_acceptance(result,release)
        after=validate_current_image(info(),release);after_payload=image_inventory(runner,release,files)
        if before!=after or payload!=after_payload:raise ValueError('Current image/payload changed during installer acceptance')
        if source_snapshot(runner,repo,a.expected_head)!=source or source_inventory(runner,repo,source)!=files:
            raise ValueError('Source identity/inventory changed during LOCAL_SIM build or tests')
        if sha_file(script)!=build_script_sha:raise ValueError('Existing release builder changed during execution')
        if inventory(bundle)!=bundle_inventory:raise ValueError('Installed test modified the candidate bundle')
        stage=work/'candidate-public';stage.mkdir()
        # Preserve the producer archive bytes rather than rebranding or rebuilding it.
        shutil.copyfile(archive,stage/archive.name)
        for name in ['LICENSE','NOTICE','release.json']:shutil.copyfile(bundle/name,stage/name)
        shutil.copyfile(build/'CHECKSUMS.sha256',stage/'bundle-CHECKSUMS.sha256')
        publish(stage/'acceptance.json',result)
        shutil.copyfile(evidence/'processes.json',stage/'processes.json')
        publish(stage/'source-inventory.json',{'source':source,'files':files})
        publish(stage/'runtime-inventory.json',{'image':after,'files':after_payload,'verified_archive_identities':expected_archive_ids})
        state.update(status='LOCAL_SIM_CURRENT_CANDIDATE_VALIDATED',release=release,acceptance=acceptance,
            candidate={'path':archive.name,'prefix':'rx-local-skills','sha256':sha_file(archive),
                'bytes':archive.stat().st_size,'inventory':bundle_inventory},
            source_inventory_sha256=sha_file(stage/'source-inventory.json'),
            runtime_inventory_sha256=sha_file(stage/'runtime-inventory.json'),
            producer={'wrapper_sha256':sha_file(Path(__file__)),'original_build_script_sha256':build_script_sha,
                'original_test_script_sha256':sha_file(repo/'rx-solutions/tools/test_skill_install.py'),
                'build_jobs':1,'cache_namespace':cache,'git_optional_locks':'0'},
            evidence_files={'acceptance.json':sha_file(stage/'acceptance.json'),'processes.json':sha_file(stage/'processes.json')},
            limitations=['LOCAL_SIM skill server/worker scope only; no Cell/Host physical authority.',
                'Only the named current-release regression checks were executed.',
                'Old SDK artifacts and cross-release migration compatibility remain NOT_PROVEN.',
                'This result does not establish the separate registered external-adapter Run or all of M5.'],
            signing={'status':'UNSIGNED','required_next_step':'Root offline GPG signature over CHECKSUMS.sha256'})
        state['producer']['private_value_audit_bounds']={'maximum_total_bytes':8*1024**3,'maximum_member_bytes':2*1024**3,'streaming':True}
        state['producer']['retention_shim']={'path':'full_run/leak_audit.py','sha256':sha_file(shim),
            'selection':'only TemporaryDirectory prefix rx-installed-acceptance-',
            'effect':'retain temporary credential files privately; original test and Docker cleanup unchanged'}
        shutil.copytree(runner.logs,stage/'producer-logs')
        installer_logs=stage/'installer-logs';installer_logs.mkdir()
        for name in ['server.log','worker.log']:shutil.copyfile(evidence/name,installer_logs/name)
        publish(stage/'manifest.json',state)
        names={f.relative_to(stage).as_posix() for f in stage.rglob('*') if f.is_file()}
        raw=checksums(stage,names);(stage/'CHECKSUMS.sha256').write_bytes(raw)
        verify_checksums(stage,raw,allowed_extras=('CHECKSUMS.sha256',))
        secrets=collect_private([retained],required_minimums={'TOKEN':2})
        approved=work/'public-approved'
        audit=approve_public(secrets,stage,approved,max_bytes=8*1024**3,max_member_bytes=2*1024**3)
        if audit['status']!='PUBLIC_EVIDENCE_APPROVED':
            shutil.copytree(approved,output)  # Redacted LEAK_AUDIT.json alone.
            raise RuntimeError('LOCAL_SIM public evidence refused by private-value audit')
        final=work/'final-public';shutil.copytree(approved/'evidence',final)
        verify_checksums(final,raw,allowed_extras=('CHECKSUMS.sha256',))
        publish(final/'LEAK_AUDIT.json',audit)
        final_names={f.relative_to(final).as_posix() for f in final.rglob('*') if f.is_file() and f.relative_to(final).as_posix()!='CHECKSUMS.sha256'}
        final_checksums=checksums(final,final_names);(final/'CHECKSUMS.sha256').write_bytes(final_checksums)
        verify_checksums(final,final_checksums,allowed_extras=('CHECKSUMS.sha256',))
        os.rename(final,output)  # Public interface receives only already inspected bytes.
        publish(work/'result.json',{'status':state['status'],'checksums_sha256':sha_file(output/'CHECKSUMS.sha256'),
            'm5_complete':False,'old_sdk_artifact_compatibility':'NOT_PROVEN'})
        print(json.dumps({'status':state['status'],'manifest':str(output/'manifest.json'),'m5_complete':False}))
        return 0
    except Exception as error:
        state.update(status='FAILED_UNVERIFIED',error={'type':type(error).__name__,'message':str(error)})
        publish(work/'failure.json',state)
        if not output.exists():refuse_public(output,'LOCAL_SIM_UNVERIFIED')
        print('LOCAL_SIM candidate failed; original diagnostics remain private under --work. Upload only the approved output.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
