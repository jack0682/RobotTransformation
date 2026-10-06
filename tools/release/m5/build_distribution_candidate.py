#!/usr/bin/env python3
"""Build isolated Linux development candidate and current sealed recovery witnesses.

No publisher signature, product custody, qualification or physical claim is issued.
The generated resource-limited Docker recipe is archived separately from unchanged
product source. No private key is requested or mounted during image production.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from artifacts import sha,sha_file,inventory,archive,checksums,safe_name
from build_diagnostics import vocabulary,save_failure,encoded

BTCPP='6e469c6ba133aaa842dac9b096b41f2d33ee2b0e'
WITNESSES={'host-recovery.log':'sigkill_at_both_journal_native_boundaries_never_replays_device_effect',
 'executor-recovery.log':'lost_run_initialization_reply_recovers_binding_without_reinitializing',
 'executor-identity.log':'run_creation_marker_cannot_change_after_header_initialization'}


def git(repo,*args):
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.check_output(['git','-C',str(repo),*args],env=env)


def source_identity(repo,head):
    actual=git(repo,'rev-parse','--verify','HEAD^{commit}').decode().strip()
    if actual!=head or not re.fullmatch('[0-9a-f]{40}',head):raise ValueError('exact full candidate commit required')
    if git(repo,'status','--porcelain=v1','-z','--untracked-files=all'):raise ValueError('candidate checkout must be clean before/after build')
    return {'repository':'https://github.com/jack0682/RobotTransformation','commit':head,
        'tree_oid':git(repo,'rev-parse',head+'^{tree}').decode().strip(),
        'components':{name:{'component_path':name,'tree_oid':git(repo,'rev-parse',head+':'+name).decode().strip()}
                      for name in ('rx-platform','rx-solutions')}}


def verify_export(repo,head,prefix,exported):
    expected={}
    for row in git(repo,'ls-tree','-r','-z',head+':'+prefix).split(b'\0'):
        if not row:continue
        header,name=row.split(b'\t',1);mode,kind,oid=header.decode().split();name=safe_name(name.decode())
        if kind!='blob' or mode not in ('100644','100755'):raise ValueError('unreviewed source entry type/mode')
        raw=git(repo,'cat-file','blob',oid);expected[name]={'sha256':sha(raw),'mode':mode,'bytes':len(raw),'git_blob':oid}
        path=exported/name
        if path.is_symlink() or not path.is_file() or sha_file(path)!=expected[name]['sha256']:
            raise ValueError('source export differs from exact Git blob: '+prefix+'/'+name)
        if bool(path.stat().st_mode & 0o111)!=(mode=='100755'):raise ValueError('exported executable mode differs')
    if {p.relative_to(exported).as_posix() for p in exported.rglob('*') if p.is_file() or p.is_symlink()}!=set(expected):
        raise ValueError('source export omitted/added Git leaves')
    return expected


def bounded_recipe(runtime,append,namespace):
    if not re.fullmatch('[a-z0-9-]{1,40}',namespace):raise ValueError('invalid isolated cache namespace')
    recipe=runtime+'\n'+append
    for marker in (' AS p-build\n',' AS s-build\n'):
        if recipe.count(marker)!=1:raise ValueError('unrecognized build-stage recipe')
        recipe=recipe.replace(marker,marker+'ENV CARGO_BUILD_JOBS=1\n')
    recipe=recipe.replace('CARGO_BUILD_JOBS=2','CARGO_BUILD_JOBS=1').replace('-j2','-j1')
    recipe=recipe.replace('id=rx-runtime-skill-','id=rx-m5-'+namespace+'-')
    return recipe


def diagnostic_recipe(recipe):
    # The sidecar is build tooling outside /source and never enters a runtime
    # image. Failed sealed tests retain their original nonzero result while
    # publishing only a closed projection of their redirected stdout.
    marker='ENV CARGO_BUILD_JOBS=1\nRUN apt-get update'
    require=recipe.count(marker)==1
    if not require:raise ValueError('unrecognized solutions build stage')
    recipe=recipe.replace(marker,'ENV CARGO_BUILD_JOBS=1\nCOPY --from=m5_diagnostics / /opt/m5-diagnostics/\nRUN apt-get update')
    paths=['external-process.log','host-recovery.log','executor-recovery.log','executor-identity.log']
    for name in paths:
        pattern=r'(cargo test [^\n]*? > /out/'+re.escape(name)+r')(?= &&|\n|$)'
        replacement=lambda m:'('+m[1]+' || { rc=$?; python3 /opt/m5-diagnostics/build_diagnostics.py --vocabulary /opt/m5-diagnostics/vocabulary.json --log /out/'+name+' --returncode "$rc"; exit "$rc"; })'
        recipe,count=re.subn(pattern,replacement,recipe)
        if count!=1:raise ValueError('unrecognized sealed test command: '+name)
    return recipe


def verify_source_manifest(raw,source):
    result={}
    for line in raw.decode().splitlines():
        digest,sep,path=line.partition('  ')
        if not sep or len(digest)!=64 or not path.startswith('/source/'):raise ValueError('invalid image source witness')
        relative=safe_name(path[len('/source/'):]);file=source/relative
        if relative in result or file.is_symlink() or not file.is_file() or sha_file(file)!=digest:raise ValueError('image/source witness differs: '+relative)
        result[relative]=digest
    if not {'Cargo.toml','Cargo.lock'}<=set(result):raise ValueError('source witness lacks dependency closure')
    return result


def verify_recovery_logs(directory):
    result={}
    for name,witness in WITNESSES.items():
        raw=(directory/name).read_bytes();text=raw.decode('utf-8')
        if f'test {witness} ... ok' not in text or '1 passed; 0 failed' not in text:
            raise ValueError('current sealed recovery test did not pass: '+witness)
        result[name]=sha(raw)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--expected-head',required=True)
    p.add_argument('--architecture',choices=['amd64','arm64'],default='amd64');p.add_argument('--cache-namespace',required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-fresh-linux-ci',action='store_true')
    a=p.parse_args()
    if not a.execute_fresh_linux_ci or sys.platform!='linux' or os.environ.get('CI')!='true':p.error('explicit fresh Linux CI execution only')
    repo=a.repo.resolve(strict=True);work=a.work.resolve();out=a.output.resolve()
    if any(x.is_relative_to(repo) or repo.is_relative_to(x) for x in (work,out)) or work.is_relative_to(out) or out.is_relative_to(work):
        raise ValueError('source/work/output roots must be disjoint')
    identity=source_identity(repo,a.expected_head)
    if shutil.disk_usage(work.parent).free < 12*1024**3:raise ValueError('at least 12 GiB free runner disk required; no global Docker/cache cleanup is performed')
    work.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    public_vocab=vocabulary(repo,a.expected_head)
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',PYTHONDONTWRITEBYTECODE='1',DOCKER_BUILDKIT='1')
    def run(args,label,capture=False):
        result=subprocess.run(list(map(str,args)),env=env,capture_output=True,text=True)
        (work/(label+'.stdout')).write_text(result.stdout);(work/(label+'.stderr')).write_text(result.stderr)
        if result.returncode:
            if label in ('build-platform','build-solutions'):
                save_failure(work/'closed-failure.json',public_vocab,'DISTRIBUTION_BUILD',label.removeprefix('build-'),
                    result.returncode,[('stdout',work/(label+'.stdout')),('stderr',work/(label+'.stderr'))],work)
            raise RuntimeError(label+' failed; preserve logs')
        return result.stdout.strip()
    run([sys.executable,repo/'rx-solutions/tools/build_linux_dev_bundle.py','--platform',repo/'rx-platform',
        '--platform-ref',a.expected_head,'--architecture',a.architecture,'--output',work/'source-export'],'source-export')
    bundle=work/'source-export/rx-linux-dev'
    closure={role:verify_export(repo,a.expected_head,prefix,bundle/'sources'/role) for role,prefix in [('platform','rx-platform'),('solutions','rx-solutions')]}
    (out/'source-inventory.json').write_text(json.dumps({'source':identity,'components':closure},indent=2)+'\n')
    recipe=bounded_recipe((bundle/'sources/solutions/docker/RuntimeSkillValidation.Dockerfile').read_text(),
                          (bundle/'Dockerfile.append').read_text(),a.cache_namespace)
    recipe=diagnostic_recipe(recipe)
    dockerfile=out/'Developer.Dockerfile';dockerfile.write_text(recipe)
    diagnostic_context=work/'diagnostic-context';diagnostic_context.mkdir()
    diagnostic_helper=Path(__file__).with_name('build_diagnostics.py')
    shutil.copyfile(diagnostic_helper,diagnostic_context/'build_diagnostics.py')
    (diagnostic_context/'vocabulary.json').write_bytes(encoded(public_vocab))
    images={};inspections={};holders=[]
    try:
        for role in ('platform','solutions'):
            tag='rx-m5-'+role+':'+a.expected_head[:12]+'-'+a.architecture+'-'+a.cache_namespace
            run(['docker','build','--progress','plain','--platform','linux/'+a.architecture,
                 '--build-context','platform_source='+str(bundle/'sources/platform'),
                 '--build-context','m5_diagnostics='+str(diagnostic_context),
                 '--build-context','btcpp=https://github.com/BehaviorTree/BehaviorTree.CPP.git#'+BTCPP,
                 '--target','dev-'+role,'-f',dockerfile,'-t',tag,bundle/'sources/solutions'],'build-'+role)
            info=json.loads(run(['docker','image','inspect',tag],'inspect-'+role))[0]
            if info['Architecture']!=a.architecture or info['Os']!='linux':raise ValueError('candidate image platform differs')
            images[role]=info['Id'];inspections[role]=info
        evidence=out/'sealed-recovery';evidence.mkdir()
        image_closure={}
        for role in ('platform','solutions'):
            holder=run(['docker','create','--network','none','--entrypoint','/bin/true',images[role]],'holder-'+role);holders.append(holder)
            prefix='/usr/local/bin/' if role=='platform' else '/opt/rx/bin/'
            destination=out/(role+'-image-source.sha256')
            run(['docker','cp',holder+':'+prefix+'source.sha256',destination],'copy-source-'+role)
            image_closure[role]=verify_source_manifest(destination.read_bytes(),bundle/'sources'/role)
            if role=='solutions':
                for name in (*WITNESSES,'external-process.log'):
                    run(['docker','cp',holder+':'+prefix+name,evidence/name],'copy-'+name)
        logs=verify_recovery_logs(evidence)
        # Exact exported component archive is sealed; recorded paths remain relative
        # to this directory, as the existing public qualification verifier requires.
        record_archive=archive(bundle/'sources/solutions',evidence/'source.tar.gz','rx-solutions')
        record={'status':'PASS_FOR_REPORTED_SCOPE','images':images,'archive':{'path':'source.tar.gz','sha256':record_archive['sha256']},
            'logs_sha256':logs,'scope':'actual sealed current image generic recovery tests only; full registered M5 Run remains separately required'}
        (evidence/'release-evidence.json').write_text(json.dumps(record,indent=2)+'\n')
        state=work/'producer-images';state.mkdir();(state/'installation.json').write_text(json.dumps({'architecture':a.architecture,'images':images}))
        run([sys.executable,repo/'rx-solutions/tools/build_linux_dev_bundle.py','--platform',repo/'rx-platform','--platform-ref',a.expected_head,
             '--architecture',a.architecture,'--images-state',state,'--output',work/'binary-bundle'],'binary-bundle')
        binary=work/'binary-bundle/rx-linux-dev'
        for role,prefix in [('platform','rx-platform'),('solutions','rx-solutions')]:
            if verify_export(repo,a.expected_head,prefix,binary/'sources'/role)!=closure[role]:raise ValueError('binary bundle source export drifted')
        package=archive(binary,out/'rx-linux-dev.tar.gz','rx-linux-dev')
        recovery=archive(evidence,out/'sealed-recovery.tar.gz','sealed-recovery')
        manifest={'schema':'rx.m5.distribution-candidate.v1','status':'BUILT_NOT_ACCEPTED','source':identity,'architecture':a.architecture,
            'images':images,'image_inspections':inspections,'image_source_files':image_closure,
            'dockerfile':{'path':dockerfile.name,'sha256':sha_file(dockerfile),'resource_limit':'Cargo jobs1; CMake jobs1',
                          'diagnostic_sidecar_sha256':sha_file(diagnostic_helper),
                          'diagnostic_vocabulary_sha256':sha_file(diagnostic_context/'vocabulary.json'),
                          'source_recipe_sha256':sha((bundle/'sources/solutions/docker/RuntimeSkillValidation.Dockerfile').read_bytes()),
                          'source_append_sha256':sha((bundle/'Dockerfile.append').read_bytes())},
            'third_party':{'BehaviorTree.CPP':{'repository':'https://github.com/BehaviorTree/BehaviorTree.CPP','commit':BTCPP}},
            'artifacts':{'binary_bundle':package,'sealed_recovery':recovery},
            'signing':{'publisher_provenance':'NOT_SIGNED','product_custody':'NOT_ESTABLISHED','ci_private_publisher_key':'NEVER_PROVIDED'},
            'limits':['APT repositories are not snapshot-pinned; bit-reproducible rebuild is not claimed.',
                      'Generic sealed recovery tests do not prove cold external Host recovery or physical safety.']}
        if source_identity(repo,a.expected_head)!=identity:raise ValueError('candidate source changed during production')
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        # Keep only delivered tar/metadata files in the immutable checksum inventory;
        # unarchived evidence is retained separately as production work evidence.
        shutil.move(str(evidence),str(work/'sealed-recovery'))
        (out/'CHECKSUMS.sha256').write_bytes(checksums(out,[x.name for x in out.iterdir() if x.is_file()]))
        result={'status':manifest['status'],'images':images,'checksums_sha256':sha_file(out/'CHECKSUMS.sha256')}
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    finally:
        for holder in holders:
            subprocess.run(['docker','rm',holder],env=env,capture_output=True,check=False)


if __name__=='__main__':main()
