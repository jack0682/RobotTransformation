#!/usr/bin/env python3
"""Artifact-only Linux installation and required FILE/registered-external SIM gates.

Installer/provisioner may read the delivered source bundle/verification kit. The
external author is a separate read-only installed image with no core source mount.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from artifacts import sha,sha_file,verify_checksums,extract_new,inventory


def selected(root,digest):
    raw=(root/'CHECKSUMS.sha256').read_bytes()
    if sha(raw)!=digest:raise ValueError('selected checksums differ')
    return verify_checksums(root,raw,allowed_extras=('CHECKSUMS.sha256',))


def installer_result(state,images):
    sessions=list((state/'sessions').glob('*/session.json'))
    if len(sessions)!=1:raise ValueError('exactly one fresh FILE_SIMULATION session required')
    value=json.loads(sessions[0].read_text())
    if value['images']!=images or value['profile']!='FILE_SIMULATION' or value['physical_execution']!='NOT_SUPPORTED':raise ValueError('installer result identity/profile differs')
    if value['phase']!='STOPPED' or value.get('recorded_verification',{}).get('status')!='PASS':raise ValueError('installer verification/retained shutdown did not pass')
    if not value['shutdown'] or any(x.get('running') or 'error' in x or x.get('exit_code',0)!=0 for x in value['shutdown']):raise ValueError('installer shutdown incomplete')
    return {'session':sessions[0].parent.name,'session_sha256':sha_file(sessions[0]),'record':value}


def registered_result(root,images,cases):
    summary_audit=json.loads((root/'public-approved/LEAK_AUDIT.json').read_text())
    if summary_audit['status']!='PUBLIC_EVIDENCE_APPROVED':raise ValueError('registered summary publication was refused')
    summary=json.loads((root/'public-approved/evidence/summary.json').read_text())
    if summary['status']!='PASS_FOR_REPORTED_SCOPE' or summary['cases']!=cases or summary['physical_claim'] is not False:raise ValueError('registered Run summary incomplete')
    historical=summary.get('historical_runtime_client',{})
    if historical.get('status')!='PASS_FOR_REPORTED_SCOPE' or historical.get('classification')!='PUBLISHED_INSTALLED_RUNTIME_CLIENT':
        raise ValueError('historical published runtime consumer gate did not pass')
    result={}
    for case in cases:
        approved=root/case/'public-approved'
        if json.loads((approved/'LEAK_AUDIT.json').read_text())['status']!='PUBLIC_EVIDENCE_APPROVED':raise ValueError('registered case publication was refused')
        evidence=approved/'evidence';value=json.loads((evidence/'result.json').read_text());boundary=json.loads((evidence/'boundary.json').read_text())
        if value['status']!='PASS_FOR_REPORTED_SCOPE' or value['case']!=case:raise ValueError('registered case did not pass')
        if case=='normal':
            if value.get('historical_runtime_client')!=historical or json.loads((evidence/'historical-runtime/gate.json').read_text())!=historical:
                raise ValueError('normal case historical proof differs from approved summary')
        if boundary['platform_image']!=images['platform'] or boundary['host_image']!=images['solutions'] or boundary['author_image']!=images['solutions']:
            raise ValueError('registered case used a different candidate image')
        if boundary['author_product_source_mounts'] or boundary['author_private_signer_mounts']:raise ValueError('author isolation claim differs')
        if case.startswith('cold_') and value['successful_recovery_claim'] is not False:raise ValueError('unsupported cold recovery was relabelled successful')
        before=json.loads((evidence/'core-binaries-before.json').read_text());after=json.loads((evidence/'core-binaries-after.json').read_text())
        if before!=after or set(before)!= {'platform','solutions'}:raise ValueError('core binaries changed/missing')
        result[case]={'result_sha256':sha_file(evidence/'result.json'),'boundary_sha256':sha_file(evidence/'boundary.json'),'core_binaries':before}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('distribution','sdk','work'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--distribution-checksums-sha256',required=True);p.add_argument('--sdk-checksums-sha256',required=True)
    p.add_argument('--execute-fresh-linux-ci',action='store_true');a=p.parse_args()
    if not a.execute_fresh_linux_ci or sys.platform!='linux' or os.environ.get('CI')!='true':p.error('explicit fresh Linux CI execution required')
    dist=a.distribution.resolve(strict=True);sdk=a.sdk.resolve(strict=True);work=a.work.resolve()
    if any(work.is_relative_to(x) or x.is_relative_to(work) for x in (dist,sdk)):raise ValueError('work/input roots must be disjoint')
    selected(dist,a.distribution_checksums_sha256);selected(sdk,a.sdk_checksums_sha256)
    original={str(x):inventory(x) for x in (dist,sdk)};work.mkdir(parents=True,exist_ok=False)
    d=json.loads((dist/'manifest.json').read_text());s=json.loads((sdk/'manifest.json').read_text())
    if d['schema']!='rx.m5.distribution-candidate.v1' or s['schema']!='rx.sdk-artifact-manifest.v1':raise ValueError('candidate manifest schema differs')
    if d['source']['commit']!=s['source']['commit'] or d['source']['components']!=s['source']['components']:raise ValueError('SDK/distribution component source tuple differs')
    images=d['images']
    if s['solutions_image']['id']!=images['solutions']:raise ValueError('SDK export and runtime image differ')
    bundle=extract_new(dist/'rx-linux-dev.tar.gz',work/'distribution','rx-linux-dev')
    recovery=extract_new(dist/'sealed-recovery.tar.gz',work/'recovery','sealed-recovery')
    kit=extract_new(sdk/'verification-kit.tar.gz',work/'kit','verification-kit')
    adapter=extract_new(sdk/'external-adapter-sdk.tar.gz',work/'adapter','external-adapter-sdk')
    historical=extract_new(sdk/'historical-runtime-client.tar.gz',work/'historical','historical-runtime-client')
    manifest=json.loads((bundle/'bundle.json').read_text())
    if not manifest['binary_images_included'] or manifest['images']!=images:raise ValueError('prebuilt selected images required; no source rebuild in consumer')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    env.pop('PYTHONPATH',None)
    def run(command,label):
        result=subprocess.run(list(map(str,command)),env=env,capture_output=True,text=True)
        (work/(label+'.stdout')).write_text(result.stdout);(work/(label+'.stderr')).write_text(result.stderr)
        if result.returncode:raise RuntimeError(label+' failed; preserve original outputs/volumes and inspect retained evidence')
    run([sys.executable,bundle/'rx-dev','install','--state-dir',work/'file-state'],'binary-install')
    for role,image in images.items():
        info=json.loads(subprocess.check_output(['docker','image','inspect',image]))[0]
        if info['Id']!=image or info['Architecture']!=d['architecture'] or info['Os']!='linux':raise ValueError('loaded image identity differs')
    run([sys.executable,bundle/'rx-dev','verify','--state-dir',work/'file-state'],'file-simulation')
    file_result=installer_result(work/'file-state',images)
    cases=['normal','consumer_response_loss','cold_after_entry','cold_drop_completion']
    run([sys.executable,kit/'full_run/run_registered_counter.py','--platform-image',images['platform'],'--solutions-image',images['solutions'],
         '--verification-kit',kit,'--adapter-sdk',adapter,'--historical-bundle',historical,'--release-evidence',recovery/'release-evidence.json','--output',work/'registered',
         '--case','all','--keep-resources','--execute-fresh-linux-ci'],'registered-external-simulation')
    registered=registered_result(work/'registered',images,cases)
    for root in (dist,sdk):
        if inventory(root)!=original[str(root)]:raise ValueError('runtime consumer modified immutable artifacts')
    value={'schema':'rx.m5.runtime-artifact-consumer.v1','status':'PASS_FOR_REPORTED_SCOPE','source':d['source'],'images':images,
           'distribution_checksums_sha256':a.distribution_checksums_sha256,'sdk_checksums_sha256':a.sdk_checksums_sha256,
           'file_simulation':file_result,'registered_external_cases':registered,'publisher_signature':'SEPARATE_REQUIRED_GATE',
           'scope':'fresh FILE_SIMULATION plus registered EXTERNAL_ADAPTER_SIMULATION; successful consumer receipt-loss query; cold Host remains UNKNOWN/held/no replay',
           'physical_claim':False,'cp2_original_run_reused':False,'private_fixture_keys':'isolated acceptance only, never publisher custody'}
    (work/'result.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'status':value['status'],'cases':cases}))


if __name__=='__main__':main()
