#!/usr/bin/env python3
"""Future Linux CI only: fresh registered external adapter on P/Host/Executor.

This script is a verification kit consumer, not an author SDK. It never imports
product source in author containers. No success claim exists until all predicates
below observe the installed products. Failed artifacts remain under --output.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time
import uuid
from fixtures import encoded, pin, fresh_definitions, execution_target, assert_success, assert_unknown_held, assert_effect_identity, accepted_start, assert_native_snapshot
from leak_audit import collect_private, approve_public, refuse_public
from historical_bundle import validate_historical_bundle, validate_live_receipt
from infrastructure import (Author, PublicApi, Signer, connections, installed_materials_type,
    owned_docker_type, read, sha, write, replace_configuration)


def wait(read_state, accepted, timeout=90):
    end = time.monotonic()+timeout
    last = None
    while time.monotonic() < end:
        last = read_state()
        if accepted(last): return last
        time.sleep(.25)
    raise RuntimeError('Required public state was not reached: '+str(last)[-3000:])


def fresh_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


def external_package(c):
    a,root=c['author'],c['author'].root
    native=root/'native';native.mkdir()
    for name in ['counter.py','rx_external_adapter.py']:
        shutil.copyfile(c['sdk']/name,native/name)
    shutil.copyfile(c['sdk']/'make_package_inputs.py',root/'make_package_inputs.py')
    a.product('rx-device-package',['external-sdk','/author/candidate-exported-sdk'],'export-candidate-sdk')
    if sha(root/'candidate-exported-sdk/rx_external_adapter.py')!=sha(native/'rx_external_adapter.py'):
        raise ValueError('Released SDK helper differs from candidate installed product')
    a.command('python3',['-c',
        'from pathlib import Path; import shutil; '
        'assert not any(Path(p).exists() for p in ["/source/Cargo.toml","/workspace/Cargo.toml","/opt/rx/dev/source"]); '
        'assert shutil.which("cargo") is None'], 'author-source-absence')
    initial=read(c['final']/'reference/initial-cell.json')
    write(root/'context.json',{'installation':c['delivery']['installation'],'cell':initial['id'],
        'host':initial['hosts'][0],'site_config_digest':initial['site_config_digest'],
        'resources':initial['steps'][0]['intent']['resource_set'],'condition_ids':initial['steps'][0]['condition_ids'],
        'architecture':c['s']['Architecture'].upper()})
    write(root/'arguments.json',['-I','-S','-B','/author/native/counter.py','--simulation-dir','/simulation'])
    write(root/'dependencies.json',['/author/native/counter.py','/author/native/rx_external_adapter.py'])
    reference=a.product('rx-device-package',['external-program','/opt/rx/python/python','/author/arguments.json',
        '/author/dependencies.json','/author/program.json'],'pin-program')
    write(root/'program-reference.json',reference)
    a.command('python3',['/author/make_package_inputs.py','--context','/author/context.json',
        '--program','/author/program.json','--program-reference','/author/program-reference.json','--output','/author/inputs'],'make-package')
    a.product('rx-device-package',['external-assemble','/author/inputs/assembly.json','/author/inputs/recipe.json',
        '/author/device-candidate'],'assemble-device')
    manifest=read(root/'device-candidate/manifest.json')
    a.product('rx-device-package',['request','/author/device-candidate','delivery-package-signer',
        '/author/device-signing.json'],'device-signing-request')
    c['signer'].sign(root/'device-signing.json',root/'device-signature.json')
    policy=copy.deepcopy(read(c['materials'].public_seed/'package-policy.json'))
    policy.update(contracts=manifest['contracts'],target=manifest['targets'][0],dependencies=[])
    policy['keys']=[{'id':'delivery-package-signer','publisher':manifest['publisher'],
        'verifying_key':c['signer'].keys['delivery-package-signer'][1],
        'kinds':['DEVICE'],'permissions':manifest['permissions']}]
    files={sha(f):f for f in (root/'device-candidate').rglob('*') if f.is_file()}
    policy['assets']=[{'reference':ref,'path':'/author/'+str(files[ref['sha256']].relative_to(root))} for ref in manifest['assets']]
    write(root/'device-policy.json',policy)
    a.product('rx-device-package',['seal','/author/device-candidate','/author/device-signature.json',
        '/author/device-policy.json','/author/device-package'],'seal-device')
    # Repoint to sealed public files before creating the registry pin.
    files={sha(f):f for f in (root/'device-package').rglob('*') if f.is_file()}
    for item in policy['assets']:item['path']='/author/'+str(files[item['reference']['sha256']].relative_to(root))
    write(root/'host-device-policy.json',policy)
    registration=a.product('rx-device-package',['external-register','/author/device-package',
        '/author/host-device-policy.json','m5/counter','/author/registry.json'],'register-availability')
    if registration['activation_authorized'] or registration['native_processes_started']!=0:
        raise ValueError('Registration must be availability only')
    c['registration']=registration
    catalog=read(root/'device-package/execution-template-catalog.json')
    if list(catalog['templates'])!=['count']: raise ValueError('Exactly count template required')
    template=catalog['templates']['count'];c['template']=template
    # Fresh initial config is chosen before P init and before any Host instance exists.
    initial['steps'][0].update(id='step/count',host=template['action']['host'],intent=template['action']['intent'])
    initial['steps'][0]['completion']['schema']=template['action']['intent']['completion_rule']
    # The fresh initial envelope must describe the actual external simulation.
    old_envelope=read(c['final']/'qualification-materials/artifacts'/(initial['envelope']['sha256']+'.bin'))
    old_envelope.update(native_backend='EXTERNAL_PROCESS_PACKAGE',
        timing_basis='EXTERNAL_ADAPTER_SIMULATION counter; existing admission and freshness limits unchanged')
    raw=encoded(old_envelope);initial['envelope']=pin(raw,'rx.operating-envelope.v1')
    (c['final']/'qualification-materials/artifacts'/(initial['envelope']['sha256']+'.bin')).write_bytes(raw)
    config=c['final']/'config'
    bootstrap=read(config/'catalog.json')
    bootstrap['cells']=[initial if x['id']==initial['id'] else x for x in bootstrap['cells']]
    replace_configuration(config/'catalog.json',bootstrap)
    # Preserve initial v1 compiler scaffold solely as provisioning material.
    c['initial']=initial
    policy=read(config/'package-policy.json')
    policy.update(schema='rx.package-verification-policy.v2',additional_package_abis=['rx.package-abi.v2'])
    key=policy['keys'][0]
    key.update(publisher=manifest['publisher'],kinds=['DEVICE','PROCESS'])
    permissions=key['permissions']+manifest['permissions']+[{'kind':'OPERATION_SUBMIT','operation':'skill/1'}]
    key['permissions']=list({encoded(p):p for p in permissions}.values())
    assets={item['reference']['sha256']:item for item in policy['assets']}
    for ref in manifest['assets']:
        target=config/'assets'/(ref['sha256']+'.bin');shutil.copyfile(files[ref['sha256']],target)
        assets[ref['sha256']]={'reference':ref,'path':'/config/assets/'+target.name}
    policy['assets']=list(assets.values());replace_configuration(config/'package-policy.json',policy)
    startup=read(config/'startup.json')
    startup['catalog']['sha256']=sha(config/'catalog.json')
    startup['package_intake']['policy']['sha256']=sha(config/'package-policy.json')
    replace_configuration(config/'startup.json',startup)
    shutil.copytree(root/'device-package',c['final']/'import/device-package')
    write(c['evidence']/'initial-host-choice.json',{'backend':'EXTERNAL_PROCESS_PACKAGE','adapter':'m5/counter',
        'before_first_host_init':True,'initial_cell_sha256':hashlib.sha256(encoded(initial)).hexdigest(),
        'registry':registration,'manifest_sha256':sha(root/'device-package/manifest.json')})


def start_platform(c):
    d,p,final=c['docker'],c['p']['Id'],c['final']
    c['volumes']={k:d.volume(k) for k in ['p-config','p-data','p-work','imports']}
    v=c['volumes'];d.put(p,v['p-config'],final/'config');d.put(p,v['imports'],final/'import')
    d.prepare_permissions(p,[v['p-config']+':/config',v['p-data']+':/data',v['p-work']+':/work'])
    mounts=[v['p-config']+':/config:ro',v['p-data']+':/data',v['imports']+':/import:ro']
    d.command(p,'/usr/local/bin/rx-platformd',['init','/config/startup.json'],mounts,'p-init')
    d.make_network()
    c['platform']=d.start(p,'p','p','/usr/local/bin/rx-platformd',['run','/config/startup.json'],mounts,
        ['127.0.0.1:'+str(c['port'])+':8443'])
    deadline=time.monotonic()+45
    while True:
        try:
            view=c['users']['installer'].get('/api/v1/overview');break
        except (RuntimeError,OSError):
            if time.monotonic()>deadline or not d.state(c['platform'])['State']['Running']:raise
            time.sleep(.5)
    if view['installation']['id']!=c['delivery']['installation'] or any(x['runs'] for x in view['cells']):
        raise ValueError('Fresh installation identity/empty Run state required')
    c['installation']=view['installation']


def author_workflow(c):
    a,api,root=c['author'],c['users']['engineer'],c['author'].root
    catalog=api.get('/api/v1/definition-catalog')['id']
    definitions,workflow=fresh_definitions(catalog,c['template']['contract'])
    write(root/'definitions.json',definitions);write(root/'workflow.json',workflow)
    refs=a.cli('definitions',['apply','/author/definitions.json','--output','/author/definitions-receipt.json'],'definitions')
    a.cli('workflow',['--references','/author/definitions-receipt.json','apply','/author/workflow.json',
        '--output','/author/workflow-receipt.json'],'workflow')
    resolved=a.cli('workflow',['--references','/author/definitions-receipt.json','resolve','/author/workflow-receipt.json',
        '--context','part=object_model','--output','/author/resolution.json'],'resolve')
    if not resolved['report']['valid'] or not resolved['report']['concrete'] or len(resolved['report']['steps'])!=1:
        raise ValueError('Counter workflow must resolve exactly one concrete step')
    preview={'id':str(uuid.uuid4()),'candidates':[{'key':'counter','object_model':refs['references']['object_model'],
        'request':resolved['report']['request']}],'slots':1,'templates':{'count':c['template']['action']},
        'node_contracts':{'count':c['template']['contract']}}
    write(root/'preview-input.json',preview)
    a.cli('execution',['preview','/author/preview-input.json','--output','/author/preview.json'],'preview')
    a.cli('execution',['export','/author/preview.json','/author/material'],'export-material')
    intake_context=api.get('/api/v1/package-intake-context',cell='cell/a')
    command={'id':str(uuid.uuid4()),'cell':'cell/a','title':'M5 counter device','relative_path':'device-package',
        'object':{'manifest':sha(root/'device-package/manifest.json'),'signature':sha(root/'device-package/manifest.sig.json')},
        'configuration_digest':intake_context['configuration_digest'],'policy_generation':intake_context['registration']['generation']}
    receipt=api.mutate('device-intake','/api/v1/package-intakes',command)
    write(root/'publication-input.json',{'id':str(uuid.uuid4()),'preview':read(root/'preview.json')['reference'],'cell':'cell/a',
        'bindings':{'count':{'intake':receipt['id'],'template':'count'}}})
    publication=a.cli('execution',['publish','/author/publication-input.json','--output','/author/publication.json'],'publish')
    composed=a.cli('runtime',['compose','m5/counter','--cell','cell/a','--step','step/count'],'compose')
    write(root/'compile-input.json',composed['compile_input'])
    recipe=read(c['materials'].public_seed/'package-recipe.json')
    manifest=read(root/'device-package/manifest.json')
    recipe.update(package='m5/counter-process',publisher=manifest['publisher'])
    refs={}
    for action in composed['compile_input']['bindings'].values():
        for ref in action['intent']['body']['program'].values():refs[(ref['sha256'],ref['schema_id'])]=ref
    recipe['assets']=list(refs.values());write(root/'process-recipe.json',recipe)
    policy=copy.deepcopy(read(c['final']/'config/package-policy.json'))
    public_assets=root/'assets';shutil.copytree(c['final']/'config/assets',public_assets)
    for item in policy['assets']: item['path']='/author/assets/'+item['reference']['sha256']+'.bin'
    write(root/'process-policy.json',policy)
    for args,label in [(['assemble','/author/compile-input.json','/author/process-recipe.json','/author/process-candidate'],'process-assemble'),
                       (['request','/author/process-candidate','delivery-package-signer','/author/process-signing.json'],'process-signing')]:
        a.product('rx-process-package',args,label)
    c['signer'].sign(root/'process-signing.json',root/'process-signature.json')
    a.product('rx-process-package',['seal','/author/process-candidate','/author/process-signature.json',
        '/author/process-policy.json','/author/process-package'],'process-seal')
    a.product('rx-process-package',['compile','/author/process-package','/author/process-policy.json','/author/compiled'],'compile')
    target,plan=execution_target(c['initial'],read(root/'compiled/resolved.json'),publication)
    write(root/'plan.json',plan);write(root/'target.json',target)
    config=api.post('prepare-execution-configuration','/api/v1/workflow-executions/configuration',target)
    if config['configuration']!=pin(encoded(target),'rx.cell-configuration.v2'):
        raise ValueError('Public configuration receipt differs from authored canonical bytes')
    c.update(target=target,configuration=config['configuration'],publication=publication)
    write(root/'configuration.json',config)
    write(root/'object.json',read(root/'definitions-receipt.json')['references']['object_instance'])


def install_runtime(c):
    """Pin exact public v2 target before first Host init. No FILE Host was started."""
    d,root,final=c['docker'],c['author'].root,c['final'];p,s=c['p']['Id'],c['s']['Id']
    pool=final/'qualification-materials/artifacts'
    def add(raw,schema):
        ref=pin(raw,schema);write_file=pool/(ref['sha256']+'.bin')
        if not write_file.exists():write_file.write_bytes(raw)
        return ref
    for location in [final/'config/assets',root/'device-package',root/'process-package']:
        for file in location.rglob('*'):
            if file.is_file(): add(file.read_bytes(),'rx.package-file.v1')
    material=read(root/'material/host-material.json');known=[]
    for item in material.values():
        raw=b''.join((root/Path(part['path']).relative_to('/author')).read_bytes() for part in item['parts'])
        if pin(raw,item['reference']['schema_id'])!=item['reference']:raise ValueError('Material pin differs')
        known.append(add(raw,item['reference']['schema_id']))
    pubref=add(encoded(c['publication']),'rx.workflow-publication.v2')
    add(encoded(c['target']),'rx.cell-configuration.v2');add(encoded(read(root/'plan.json')),'rx.execution-plan.v2')
    policy=read(final/'config/qualification-policy.json');profile=policy['profiles'][0]
    profile.update(configuration=c['configuration'],definition=c['target']['definition'],envelope=c['target']['envelope'])
    plan=read(pool/(profile['acceptance_plan']['sha256']+'.bin'))
    plan.update(configuration=c['configuration'],scope='M5 one-node external counter EXTERNAL_ADAPTER_SIMULATION only; cold Host recovery not supported')
    profile['acceptance_plan']=add(encoded(plan),plan['schema'])
    limitations=read(pool/(profile['limitations']['sha256']+'.bin'))
    limitations.update(native_backend='EXTERNAL_PROCESS_PACKAGE',
        claim='One-node external counter EXTERNAL_ADAPTER_SIMULATION only; no physical safety or cold recovery support')
    profile['limitations']=add(encoded(limitations),limitations['schema'])
    refs=[c['target']['definition'],c['target']['envelope'],c['target']['recipe'],c['publication']['policy'],pubref,*known]
    for package in c['publication']['packages'].values():refs+=package['dependencies']
    refs+=read(root/'device-package/manifest.json')['assets']
    refs += [ref for ref in profile['dependencies'] if ref['sha256']==c['target']['site_config_digest']]
    profile['dependencies']=sorted({(r['sha256'],r['schema_id']):r for r in refs}.values(),key=lambda r:(r['sha256'],r['schema_id']))
    for ref in c['qualification'].references(policy).values():
        if pin((pool/(ref['sha256']+'.bin')).read_bytes(),ref['schema_id'])!=ref:raise ValueError('Qualification closure incomplete')
    replace_configuration(final/'config/qualification-policy.json',policy)
    c['q_policy_digest']=hashlib.sha256(b'RX-REQUALIFICATION-POLICY-v1\n'+encoded(policy)).hexdigest()
    startup=read(final/'config/startup.json');startup['package_intake']['qualification_policy']['sha256']=sha(final/'config/qualification-policy.json')
    replace_configuration(final/'config/startup.json',startup)
    shutil.copytree(root/'process-package',final/'import/process-package')
    d.run('stop','--time','20',c['platform'])
    d.put(p,c['volumes']['p-config'],final/'config');d.put(p,c['volumes']['imports'],final/'import')
    d.run('start',c['platform'])
    wait(lambda:c['users']['engineer'].get('/api/v1/overview'),lambda v:v['installation']['id']==c['installation']['id'])
    binding=read(final/'host-config/binding-input.json');binding.update(initial_cell=c['initial'],target_cell=c['target'])
    replace_configuration(final/'host-config/binding-input.json',binding)
    host=read(final/'host-config/startup.template.json')
    host['backend']={'kind':'EXTERNAL_PROCESS_PACKAGE','adapter':'m5/counter',
        'registry':{'path':'/author/registry.json','sha256':sha(root/'registry.json')}}
    shutil.copytree(root/'material',final/'host-config/material')
    for item in material.values():
        for part in item['parts']:part['path']='/config/host/material/'+Path(part['path']).name
    host['execution_materials']=[material]
    replace_configuration(final/'host-config/startup.template.json',host)
    engine=c['private']/'engine'
    holder=d.holder(s,[]);d.run('cp',holder+':/opt/rx/bin/rx-bt-engine',str(engine))
    c['installation_api'].patch_s(final,c['installation'],sha(engine),'EXTERNAL_PROCESS_PACKAGE')
    public=c['private']/'runtime-public';public.mkdir()
    for name in ['native','device-package'] :shutil.copytree(root/name,public/name)
    for name in ['host-device-policy.json','registry.json']:shutil.copyfile(root/name,public/name)
    v=c['volumes']
    for k in ['author-public','simulation','h-config','h-data','h-runtime','e-config','e-data','e-work']:v[k]=d.volume(k)
    d.put(s,v['author-public'],public);d.put(s,v['h-config'],final/'host-config');d.put(s,v['e-config'],final/'executor-config')
    d.prepare_permissions(s,[v['h-config']+':/config',v['h-data']+':/data',v['h-runtime']+':/work'])
    d.prepare_permissions(s,[v['author-public']+':/config',v['simulation']+':/data',v['e-work']+':/work'])
    d.prepare_permissions(s,[v['e-config']+':/config',v['e-data']+':/data',v['e-work']+':/work'])
    c['host_mounts']=[v['h-config']+':/config/host:ro',v['h-data']+':/data',v['h-runtime']+':/run/rx-host',
        v['author-public']+':/author:ro',v['simulation']+':/simulation']
    d.command(s,'/opt/rx/bin/rx-hostd',['inspect','/config/host/startup.json'],c['host_mounts'],'h-inspect')
    d.command(s,'/opt/rx/bin/rx-hostd',['init','/config/host/startup.json'],c['host_mounts'],'h-init')
    c['host']=d.start(s,'h','s','/opt/rx/bin/rx-hostd',['run','/config/host/startup.json'],c['host_mounts'])
    mounts=[v['e-config']+':/config/executor:ro',v['e-data']+':/data']
    d.command(s,'/opt/rx/bin/rx-executor-service',['cell','init','/config/executor/cell.json'],mounts,'e-init')
    c['executor']=d.start(s,'e','e','/opt/rx/bin/rx-executor-service',['cell','run','/config/executor/cell.json'],mounts)


def simulation_records(c,name):
    if name not in ['effects.jsonl','entries.jsonl','completions.jsonl']:
        raise ValueError('Unknown simulator record')
    raw=c['docker'].run('exec',c['host'],'/bin/sh','-c',
        'if test -f /simulation/'+name+'; then cat /simulation/'+name+'; fi')
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def effects(c):return simulation_records(c,'effects.jsonl')


def native_boundaries(c,receipt,completions):
    work=receipt['result']['work'][0]
    entry=simulation_records(c,'entries.jsonl')
    complete=simulation_records(c,'completions.jsonl')
    assert_effect_identity(work,entry,1)
    assert_effect_identity(work,complete,completions)
    return {'entries':entry,'completions':complete}


def immutable_native(c,receipt,has_completion):
    work=receipt['result']['work'][0]
    operation=str(uuid.UUID(work['operation']['operation_id']))
    c['native_snapshot_serial']=c.get('native_snapshot_serial',0)+1
    code="""import hashlib,json,pathlib,sys,uuid
root=pathlib.Path('/data/host');operation=str(uuid.UUID(sys.argv[1]));files={}
def read(name,path,required=True):
    if not path.exists() and not path.is_symlink():
        if required:raise ValueError('missing native fact: '+name)
        return None
    if any(p.is_symlink() for p in [path,*path.parents]) or not path.is_file() or path.stat().st_size>1048576:
        raise ValueError('regular bounded native fact required')
    raw=path.read_bytes();files[name]={'path':str(path.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'raw_hex':raw.hex()}
    return raw
installation=json.loads(read('installation',root/'installation.json'))
if installation.get('native_directory') is not None:raise ValueError('fresh native generation required')
native=root/'native-external';read('device_session',native/'device-session')
read('request',native/operation/'request.json');read('completion',native/operation/'completion.json',False)
print(json.dumps({'schema':'rx.m5-native-fact-snapshot.v1','files':files}))
"""
    value=json.loads(c['docker'].command(c['s']['Id'],'python3',['-c',code,operation],
        [c['volumes']['h-data']+':/data:ro'],'native-snapshot-'+str(c['native_snapshot_serial'])))
    verified=assert_native_snapshot(value,work,sha(c['author'].root/'device-package/profile.json'),
        read(c['author'].root/'program-reference.json')['reference']['sha256'],c['template']['action']['intent'],has_completion)
    return {'snapshot':value,'verified_tuple':verified}


def wait_complete(c,inspect,run,timeout=120):
    deadline=time.monotonic()+timeout;last=None;reason=None
    while time.monotonic()<deadline:
        receipt=inspect();observed=effects(c)
        try:
            assert_success(receipt,observed,run)
            boundaries=native_boundaries(c,receipt,1)
        except AssertionError as error:
            reason=str(error);last={'receipt':receipt,'effects':observed,'reason':reason}
            time.sleep(.25);continue
        return receipt,observed,boundaries
    write(c['evidence']/'normal-wait-timeout.json',last or {'reason':'No sample'})
    raise RuntimeError('Full final-state success predicate timed out: '+str(reason))


def historical_live_gate(c,bundle):
    pins=validate_historical_bundle(bundle);author=c['author'];root=author.root
    for source,target in [('historical_runtime_probe.py','historical-runtime-probe.py'),
                          ('HISTORICAL_CONSUMER_LOCK.json','HISTORICAL_CONSUMER_LOCK.json')]:
        shutil.copyfile(bundle/source,root/target)
    (root/'historical-client').mkdir()
    def observation():
        overview=c['users']['engineer'].get('/api/v1/overview')
        rows=[row for row in overview['cells'] if row['cell']['value']['id']=='cell/a']
        if (len(rows)!=1 or rows[0]['runs_truncated'] is not False or rows[0]['work_truncated'] is not False
                or rows[0]['runs'] or rows[0]['work']):raise AssertionError('Historical gate requires a complete empty main Run/work view')
        native={'entries':simulation_records(c,'entries.jsonl'),'effects':effects(c),'completions':simulation_records(c,'completions.jsonl')}
        if any(native.values()):raise AssertionError('Historical facade must not enter native work')
        return {'installation':overview['installation'],'runs':rows[0]['runs'],'work':rows[0]['work'],'native':native}
    before=observation()
    result=author.command('python3',['-E','-s','-B','/author/historical-runtime-probe.py',
        '--client','/author/historical-client','--lock','/author/HISTORICAL_CONSUMER_LOCK.json',
        '--connection','/terminal/engineer.json','--cell','cell/a','--step','step/count',
        '--state','/author/historical-state','--output','/author/historical-runtime.json','--execute'],
        'historical-runtime-live-probe',check=False,network=True,historical_client=bundle/'client')
    destination=c['evidence']/'historical-runtime';destination.mkdir()
    if (root/'historical-runtime.json').is_file():shutil.copyfile(root/'historical-runtime.json',destination/'receipt.json')
    if (root/'historical-runtime.logs').is_dir():shutil.copytree(root/'historical-runtime.logs',destination/'logs')
    if result.returncode:raise RuntimeError('Pinned historical runtime facade failed; retained receipt/logs require secret audit')
    receipt=read(root/'historical-runtime.json');validate_live_receipt(receipt,pins)
    after=observation()
    if before!=after or validate_historical_bundle(bundle)!=pins:raise AssertionError('Historical probe changed runtime state, native effects, or original bytes')
    proof={'status':'PASS_FOR_REPORTED_SCOPE','classification':pins['classification'],
        'pins':pins,'before':before,'after':after,
        'scope':'old published runtime-v1 catalog/draft compose/original-request recovery only; no v2 or native execution'}
    write(destination/'gate.json',proof)
    return proof


def commission(c):
    d,a,root=c['docker'],c['author'],c['author'].root
    users=c['users'];engineer,reviewer,release,operator=[users[x] for x in ['engineer','verifier','release','operator']]
    main=lambda value:next(x for x in value['cells'] if x['cell']['value']['id']=='cell/a')
    overview=lambda:engineer.get('/api/v1/overview')
    ready=wait(overview,lambda v:len(main(v)['diagnostics']['hosts'])==1 and
        all(x['context']=='CURRENT' for x in main(v)['diagnostics']['hosts']) and
        bool(main(v)['diagnostics']['sources']) and all(x['usable'] for x in main(v)['diagnostics']['sources']))
    host=read_host(c,'/run/rx-host/host-status.json');journals=read_host(c,'/data/host/installation.json')
    if host['phase']!='SOFTWARE_READY_UNARMED' or effects(c) or main(ready)['runs']:raise ValueError('Fresh unarmed Host required')
    release_proof=c['qualification'].verified_release_evidence(c['release_evidence'],c['s']['Id'])
    negative=operator.get('/api/v1/cell',id=c['delivery']['negative_cell']);cfg=negative['value']['configuration']
    denied_run=operator.mutate('negative-create','/api/v1/runs',{'cell':cfg['id'],'recipe_digest':cfg['recipe']['sha256'],
        'site_config_digest':cfg['site_config_digest'],'expected_cell':negative['revision']})
    start=operator.get('/api/v1/run/start-context',cell=cfg['id'],run=denied_run['id'],purpose='PRODUCTION',budget_limit='1')
    try:operator.mutate('negative-start','/api/v1/runs/start',start['request'])
    except c['Rejected'] as error:negative_denial={'status':error.status,'body':error.body}
    else:raise AssertionError('Unconfigured PHYSICAL admission accepted')
    try:operator.get('/api/v1/package-intake-context',cell='cell/a')
    except c['Rejected'] as error:role_denial={'status':error.status,'body':error.body}
    else:raise AssertionError('Operator acquired Engineer intake context')
    flow=c['Commission'](engineer,reviewer,release,'cell/a',c['target'],
        execution_configuration=c['configuration'],package_path='process-package')
    job=flow.import_process(sha(root/'process-package/manifest.json'),sha(root/'process-package/manifest.sig.json'),{'skill/1':'step/count'})
    first=engineer.recover('process-intake');second=engineer.recover('process-intake')
    write(root/'review-request.json',job['request'])
    review=a.product('rx-process-package',['review','/author/process-package','/author/process-policy.json',
        '/author/review-request.json','/author/process-review'],'review-process')
    if not review['compiler_checks_passed'] or review['activation_authorized']:raise ValueError('Software review is not authority')
    a.product('rx-process-package',['review-signing-request','/author/process-review/verification.json','delivery-review-signer',
        '/author/review-signing.json'],'review-signing')
    c['signer'].sign(root/'review-signing.json',root/'process-review/verification.sig.json')
    upload=c['private']/'review-upload';upload.mkdir();shutil.copytree(root/'process-review',upload/'process-review')
    d.put(c['p']['Id'],c['volumes']['imports'],upload)
    applied=flow.accept_process_report(job,review['report_digest'])
    qjob=flow.begin_requalification(applied,c['q_policy_digest'])
    qdetail=release.get('/api/v1/qualification-review',cell='cell/a',id=qjob['request']['id'])
    current=main(overview());after_journals=read_host(c,'/data/host/installation.json')
    limit=['Fresh one-node external counter EXTERNAL_ADAPTER_SIMULATION only; no physical qualification.',
        'Pre-Run software and installation controls only. Cold Host recovery remains unsupported.',
        'CI role separation uses distinct principals, not independent human acceptance.']
    def area(assertions,observations):return {'assertions':assertions,'observations':observations,'limitations':limit}
    observations={
      'SOFTWARE':area({'compiler_passed':review['compiler_checks_passed'],'exact_v2_target':applied['change']['after']==c['configuration']},{'compiler':review,'applied':applied['change']['after']}),
      'EQUIPMENT':area({'one_current_host':len(current['diagnostics']['hosts'])==1 and all(h['context']=='CURRENT' for h in current['diagnostics']['hosts']),
          'sources_usable':bool(current['diagnostics']['sources']) and all(s['usable'] for s in current['diagnostics']['sources']),
          'same_clock':host['clock_id']==c['installation']['clock_id'],'unarmed':host['phase']=='SOFTWARE_READY_UNARMED'}, {'host':host,'diagnostics':current['diagnostics']}),
      'CELL_INTEGRATION':area({'applied_unqualified':applied['change']['state']=='APPLIED_UNQUALIFIED',
          'host_acknowledged':flow.pre_apply_detail['host_configuration']['all_hosts_acknowledged'],
          'proofs_present':bool(applied['change']['application']['host_proofs']),
          'fences_confirmed':qdetail['context_current'] and qdetail['fences_confirmed']}, {'application':applied['change']['application'],'fences':qdetail,'clearance':flow.clearance_snapshot,'proposed_clear_block_ids':flow.clear_candidates}),
      'RECOVERY':area({'exact_release_tests':len(release_proof['verified_tests'])==3,'journals_unchanged':journals==after_journals,
          'same_intake_receipt':first==second,'recorded_origins':bool(qjob['request']['runtime_restrictions'])}, {'sealed':release_proof,'journals':journals,'intake':first}),
      'PROTECTION':area({'physical_unconfigured':cfg['environment']=='PHYSICAL' and negative['value']['commissioning']=='NOT_COMMISSIONED',
          'start_denied':negative_denial['status'] in [403,409,422] and not start['can_request'] and start['blocking_reason']=='NOT_COMMISSIONED'}, {'start':start,'denial':negative_denial}),
      'OPERATIONS':area({'operator_denied':role_denial['status']==403,'principals_separate':len({users[r].get('/api/v1/overview')['user']['principal'] for r in ['engineer','verifier','release']})==3,
          'no_main_runs':not current['runs'],'no_native_effects':not effects(c),'no_native_entries':not simulation_records(c,'entries.jsonl')}, {'role_denial':role_denial,'runs':current['runs']})}
    report=c['private']/'qualification-report'
    c['qualification'].build_report(qjob,c['validator'],c['final']/'qualification-materials',observations,report,scope='M5_EXTERNAL_COUNTER_PRE_RUN_EXTERNAL_ADAPTER_SIMULATION')
    # Trusted fixture signer reads only fresh private tree. Author receives no key.
    signature=c['materials'].sign({'key':'delivery-qualification-signer','qualification_report':str(report/'qualification.json')},'qualification')
    digest=read(signature.with_suffix('.metadata.json'))['report_digest']
    shutil.copyfile(signature,report/'qualification.sig.json')
    c['materials'].preserve_public(report,'qualification-report')
    upload=c['private']/'qualification-upload';upload.mkdir();shutil.copytree(report,upload/'qualification-report')
    d.put(c['p']['Id'],c['volumes']['imports'],upload)
    active=flow.activate(qjob,digest)
    write(c['evidence']/'commissioning.json',{'activation':active,'observations':observations,
        'scope':'measured pre-Run EXTERNAL_ADAPTER_SIMULATION only','execution_claim':False})


def read_host(c,path):return json.loads(c['docker'].run('exec',c['host'],'cat',path))


def run_case(c,case):
    a,api,root,d=c['author'],c['users']['operator'],c['author'].root,c['docker']
    if case.startswith('cold_'):
        fault='after_entry_exit' if case=='cold_after_entry' else 'drop_completion'
        directory=c['private']/'fault';directory.mkdir();write(directory/'fault.json',{'mode':fault})
        d.put(c['s']['Id'],c['volumes']['simulation'],directory)
    cell=api.get('/api/v1/cell',id='cell/a')
    request=str(uuid.uuid4())
    write(root/'create-run.json',{'cell':'cell/a','publication':c['publication']['reference'],
        'expected_cell':cell['revision'],'count':'1'})
    created=a.cli('execution',['create-run','/author/create-run.json','--request-id',request],case+'-create','operator')
    run=created['binding']['run']
    write(root/'bind-object.json',{'run':run,'ordinal':'1','object':read(root/'object.json')})
    a.cli('execution',['bind-object','/author/bind-object.json','--request-id',str(uuid.uuid4())],case+'-object','operator')
    start_id=str(uuid.uuid4());write(c['evidence']/'original-request.json',{'create_request':request,'start_request':start_id,'run':run,'case':case})
    if case=='consumer_response_loss':
        # The registered CLI consumes P's response, but its stdout is deliberately
        # discarded at the consumer transport boundary. Next lookup is a new process.
        args=['/opt/rx/client/rx','execution','--connection','/terminal/operator.json',
            '--state-dir','/author/client/execution/operator','start',run,'--request-id',start_id,'--wait-seconds','120']
        result=a.command('python3',args,case+'-discard-receipt',check=False,network=True,drop_stdout=True)
        write(c['evidence']/'consumer-loss-injection.json',{'returncode':result.returncode,
            'receipt_stdout_deliberately_discarded':True,'new_consumer_process_for_original_query':True,
            'scope':'CLI result transport loss, not HTTP packet loss; P/Host/Executor were not restarted'})
        if result.returncode:raise RuntimeError('Consumer CLI failed before controlled response loss: '+result.stderr)
    else:
        started=a.cli('execution',['start',run,'--request-id',start_id,'--wait-seconds','0'],case+'-start','operator',False)
        write(c['evidence']/'start-receipt.json',accepted_start(started.stdout,started.returncode,start_id,run))
    inspect=lambda:a.cli('execution',['inspect',run,'--reports'],case+'-original-query','operator')
    if not case.startswith('cold_'):
        final,count,boundaries=wait_complete(c,inspect,run)
        native_before=immutable_native(c,final,True)
        second=inspect();assert_success(second,effects(c),run)
        native_after=immutable_native(c,second,True)
        if native_before!=native_after:raise AssertionError('Immutable native facts changed during original query')
        return {'status':'PASS_FOR_REPORTED_SCOPE','case':case,'receipt':second,'effects':count,'native_boundaries':boundaries,'immutable_native_facts':native_after,
            'scope':'registered P/Host/Executor execution-v2 EXTERNAL_ADAPTER_SIMULATION; exactly one native increment'}
    before=wait(inspect,lambda r:len(r['result']['work'])==1 and r['result']['work'][0].get('invocation') is not None
        and r['result']['work'][0]['operation']['execution_knowledge']=='UNKNOWN',120)
    expected=0 if case=='cold_after_entry' else 1
    initial_effects=effects(c)
    original_boundaries=native_boundaries(c,before,expected)
    original_native=immutable_native(c,before,bool(expected))
    if len(initial_effects)!=expected:raise AssertionError('Fault did not reach the declared effect boundary')
    old_status=read_host(c,'/run/rx-host/host-status.json')
    old_lifecycle=d.state(c['host'])['State']
    write(c['evidence']/'before-cold-restart.json',{'receipt':before,'effects':initial_effects,'native_boundaries':original_boundaries,'immutable_native_facts':original_native,'status':old_status})
    d.run('stop','--time','20',c['executor'])
    d.run('kill','--signal','KILL',c['host'])
    d.run('start',c['host'])
    new_lifecycle=d.state(c['host'])['State']
    if new_lifecycle['StartedAt']==old_lifecycle['StartedAt']:
        raise AssertionError('A fresh Host process start was not observed')
    try:
        new_status=wait(lambda:read_host(c,'/run/rx-host/host-status.json'),lambda v:v!=old_status,30)
    except RuntimeError:
        new_status={'startup_state':d.state(c['host'])['State'],'status_publication_unavailable':True}
    # An unsupported cold path may refuse service startup; either way it must not
    # manufacture completion or discharge P's original held resources.
    readings=[]
    for _ in range(5):
        current=inspect()
        if d.state(c['host'])['State']['Running']:
            current_effects=effects(c)
            current_boundaries=native_boundaries(c,current,expected)
        else:
            snapshot=c['private']/('effect-snapshot-'+str(len(readings)))
            d.extract(c['s']['Id'],c['volumes']['simulation'],'/',snapshot)
            def saved_records(name):
                file=snapshot/name
                return [json.loads(x) for x in file.read_text().splitlines()] if file.exists() else []
            current_effects=saved_records('effects.jsonl')
            current_boundaries={'entries':saved_records('entries.jsonl'),'completions':saved_records('completions.jsonl')}
        assert_unknown_held(current,before,current_effects,expected)
        if current_boundaries!=original_boundaries:raise AssertionError('Native entry/completion markers changed after cold restart')
        current_native=immutable_native(c,current,bool(expected))
        if current_native!=original_native:raise AssertionError('Immutable native request/completion tuple changed after cold restart')
        readings.append({'receipt':current,'effects':current_effects,'immutable_native_facts':current_native});time.sleep(1)
    return {'status':'PASS_FOR_REPORTED_SCOPE','case':case,'before':before,
        'post_restart_host':new_status,'host_lifecycle_before':old_lifecycle,'host_lifecycle_after':new_lifecycle,'original_queries':readings,'scope':'unsupported cold Host recovery remains UNKNOWN/held; no native replay',
        'successful_recovery_claim':False}


def scenario(args,case,kit):
    output=args.output/case;output.mkdir()
    private=output/'private';private.mkdir(mode=0o700)
    evidence=output/'evidence';evidence.mkdir()
    Docker=owned_docker_type(kit['Docker']);docker=Docker(evidence)
    c={'private':private,'evidence':evidence,'docker':docker,'sdk':args.adapter_sdk,
        'release_evidence':args.release_evidence,**kit}
    error=None;verdict=None
    try:
        p,s=docker.image(args.platform_image),docker.image(args.solutions_image)
        if p['Architecture']!=s['Architecture'] or s['Architecture'] not in ('amd64','arm64'):raise ValueError('Same Linux architecture required')
        sources={}
        for name in ['run_registered_counter.py','infrastructure.py','fixtures.py','counter_commission.py','leak_audit.py','historical_bundle.py']:
            sources['full_run/'+name]=sha(Path(__file__).parent/name)
        for group,directory in [('verification-kit',args.verification_kit),('adapter-sdk',args.adapter_sdk)]:
            for file in sorted(directory.rglob('*.py')):
                if file.is_symlink():raise ValueError('Verification source symlinks are not supported')
                sources[group+'/'+str(file.relative_to(directory))]=sha(file)
        validator_manifest={'schema':'rx.m5-counter-validator-sources.v1','files':sources}
        validator=hashlib.sha256(encoded(validator_manifest)).hexdigest()
        write(evidence/'validator-source-closure.json',{'validator':validator,**validator_manifest})
        c.update(p=p,s=s,signer=Signer(private/'signers'),port=fresh_port(),validator=validator)
        Materials=installed_materials_type(kit['Materials'])
        material=Materials(Path('/NO_PRODUCT_SOURCE'),private,evidence,docker,s['Id'])
        material.configure(p['Id'],c['signer']);c['materials']=material
        material.create_seed(s['Architecture']);package,compiled,compiler=material.compile()
        final=material.finalize(package,compiled,compiler,c['port'],None,c['validator'])
        c.update(final=final,delivery=read(final/'delivery.json'))
        author=private/'author';author.mkdir();terminal=private/'terminal'
        connections(final,terminal)
        command_evidence=evidence/'author-commands';command_evidence.mkdir()
        c['author']=Author(docker,s['Id'],author,terminal,command_evidence)
        c['users']={who:PublicApi(c['author'],who,kit['Rejected']) for who in ['installer','engineer','verifier','release','operator']}
        write(evidence/'boundary.json',{'platform_image':p['Id'],'host_image':s['Id'],'author_image':s['Id'],
            'author_product_source_mounts':[],'author_private_signer_mounts':[],
            'verification_kit':args.verification_kit.name,'fresh_container_prefix':docker.prefix,
            'fixture_scope':'EXTERNAL_ADAPTER_SIMULATION counter only; fresh TLS/keys/volumes/Run per case'})
        def core_identity(stage):
            pcode='import hashlib,json,pathlib; print(json.dumps({p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ["/usr/local/bin/rx-platformd","/usr/local/bin/rx-package-store"]}))'
            return {'solutions':c['author'].core_identity('s-core-binaries-'+stage),
                'platform':json.loads(docker.command(p['Id'],'python3',['-c',pcode],[],'p-core-binaries-'+stage))}
        before=core_identity('before')
        write(evidence/'core-binaries-before.json',before)
        external_package(c);start_platform(c);author_workflow(c);install_runtime(c)
        runtime={}
        for role in ['platform','host','executor']:
            state=docker.state(c[role])
            runtime[role]={'image':state['Image'],'mounts':state['Mounts'],
                'readonly_rootfs':state['HostConfig']['ReadonlyRootfs'],'user':state['Config']['User']}
        write(evidence/'runtime-boundaries.json',runtime)
        historical=historical_live_gate(c,args.historical_bundle) if case=='normal' else None
        commission(c);verdict=run_case(c,case)
        if historical is not None:verdict['historical_runtime_client']=historical
        after=core_identity('after')
        if before!=after:raise AssertionError('Installed core binary bytes changed during external authoring')
        write(evidence/'core-binaries-after.json',after)
    except BaseException as exc:
        error=exc
        write(evidence/'failure.json',{'status':'FAIL','case':case,'type':type(exc).__name__,'message':str(exc),
            'success_claim':False,'retry_new_request_for_green':False})
    finally:
        try:
            docker.capture_logs()
            write(evidence/'owned-resources.json',{'prefix':docker.prefix,'containers':docker.containers,'volumes':docker.volumes,
                'network':docker.network,'front_network':docker.front_network})
            if not args.keep_resources:docker.cleanup()
        except BaseException as cleanup_error:
            if error is None:error=cleanup_error
            if not (evidence/'failure.json').exists():
                write(evidence/'failure.json',{'status':'FAIL','type':type(cleanup_error).__name__,
                    'message':str(cleanup_error),'success_claim':False})
        approved=output/'public-approved'
        try:
            secrets=collect_private([private],required_minimums={'PRIVATE_KEY':1,'PRIVATE_SEED':1,'PASSWORD':1})
            audit=approve_public(secrets,evidence,approved,
                extra_documents={'result.json':verdict} if error is None and verdict is not None else {})
        except Exception:
            audit=refuse_public(approved) if not approved.exists() else {'status':'PUBLIC_EVIDENCE_REFUSED'}
        if audit['status']!='PUBLIC_EVIDENCE_APPROVED':
            error=RuntimeError('Public evidence refused by the private-value audit; only the redacted receipt may be uploaded')
    if error is not None:
        # Original diagnostics remain in raw evidence. Do not echo possible private
        # bytes from that exception into the CI console or an outer upload log.
        raise RuntimeError('Scenario failed; inspect retained raw evidence privately and publish only public-approved/') from None
    return verdict.get('historical_runtime_client')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--platform-image',required=True,help='Candidate developer P image containing installed delivery-fixture')
    p.add_argument('--solutions-image',required=True,help='Candidate S runtime image; used identically for Host and author')
    p.add_argument('--verification-kit',type=Path,required=True,help='Extracted artifact directory containing cell_delivery/')
    p.add_argument('--adapter-sdk',type=Path,required=True,help='Released adapter-sdk containing helper/template/input generator')
    p.add_argument('--historical-bundle',type=Path,required=True,help='Exact prepared four-file published old runtime facade with pinned probe')
    p.add_argument('--release-evidence',type=Path,required=True,help='Exact candidate S recovery test evidence with archive/logs')
    p.add_argument('--output',type=Path,required=True,help='Fresh output path; never reuse')
    p.add_argument('--case',choices=['normal','consumer_response_loss','cold_after_entry','cold_drop_completion','all'],default='all')
    p.add_argument('--execute-fresh-linux-ci',action='store_true')
    p.add_argument('--keep-resources',action='store_true',help='Retain only this fresh run resources for diagnosis')
    args=p.parse_args()
    if platform.system()!='Linux' or not args.execute_fresh_linux_ci or os.environ.get('CI')!='true':
        p.error('Execution requires Linux, CI=true, and --execute-fresh-linux-ci; no local product execution')
    os.umask(0o077)
    for key in ['verification_kit','adapter_sdk','historical_bundle','release_evidence','output']:setattr(args,key,getattr(args,key).resolve())
    validate_historical_bundle(args.historical_bundle)
    if args.output.exists():p.error('Output already exists; preserve original Run and artifacts')
    for name in ['counter.py','rx_external_adapter.py','make_package_inputs.py']:
        if not (args.adapter_sdk/name).is_file():p.error('Missing released adapter input: '+name)
    if not (args.verification_kit/'cell_delivery/__init__.py').exists() and not (args.verification_kit/'cell_delivery/materials.py').is_file():
        p.error('Explicit packaged cell_delivery verification kit required')
    sys.path.insert(0,str(args.verification_kit))
    from cell_delivery.docker import Docker
    from cell_delivery.materials import Materials
    from cell_delivery.api import Rejected
    from counter_commission import Commission
    from cell_delivery import qualification,installation
    args.output.mkdir(parents=True)
    kit={'Docker':Docker,'Materials':Materials,'Rejected':Rejected,'Commission':Commission,
         'qualification':qualification,'installation_api':installation}
    cases=['normal','consumer_response_loss','cold_after_entry','cold_drop_completion'] if args.case=='all' else [args.case]
    historical_results={case:scenario(args,case,kit) for case in cases}
    historical=historical_results.get('normal')
    summary={'status':'PASS_FOR_REPORTED_SCOPE' if historical else 'PARTIAL_NOT_ALL_REQUIRED_GATES',
        'historical_runtime_client':historical or {'status':'NOT_EXECUTED_WITH_CASE_SUBSET'},'cases':cases,'physical_claim':False,
        'scope':'actual registered execution-v2 EXTERNAL_ADAPTER_SIMULATION; consumer receipt-loss original query; unsupported cold Host UNKNOWN/no replay'}
    secrets=collect_private([args.output/case/'private' for case in cases])
    audit=approve_public(secrets,None,args.output/'public-approved',extra_documents={'summary.json':summary})
    if audit['status']!='PUBLIC_EVIDENCE_APPROVED':raise RuntimeError('Summary public evidence refused')
    write(args.output/'summary.json',summary)  # Audited compatibility mirror; upload approved tree only.


if __name__=='__main__':main()
