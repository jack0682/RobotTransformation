#!/usr/bin/env python3
"""Package only source-free consumer orchestration, pinned to same-run candidate inputs.

This unsigned CI handoff is not a publisher signature. Root must sign the final
release inventory offline and verify it with an independently trusted public key.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
from artifacts import sha_file,verify_checksums

TOOLS=['artifacts.py','consume_sdk_artifacts.py','consume_runtime_artifacts.py','verify_release_provenance.py','package_handoff.py','publish_ci_evidence.py','leak_audit.py']


def verify_tools(root):
    value=json.loads((root/'control.json').read_text())
    if value['schema']!='rx.m5.ci-handoff.v1' or set(value['tools'])!=set(TOOLS):raise ValueError('handoff tool inventory differs')
    if {p.name for p in root.iterdir()}!=set(TOOLS)|{'control.json'}:raise ValueError('extra/missing handoff input')
    for name,digest in value['tools'].items():
        if (root/name).is_symlink() or not (root/name).is_file() or sha_file(root/name)!=digest:raise ValueError('consumer tool changed: '+name)
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-tools',type=Path)
    for name in ('tools','sdk','distribution','local-sim','output'):p.add_argument('--'+name,type=Path)
    p.add_argument('--candidate');a=p.parse_args()
    if a.verify_tools:
        value=verify_tools(a.verify_tools);print(json.dumps({'status':'CI_HANDOFF_BYTES_MATCH','candidate':value['candidate']}));return
    if any(getattr(a,name) is None for name in ('tools','sdk','distribution','local_sim','output','candidate')):p.error('all producer arguments required')
    if not re.fullmatch('[0-9a-f]{40}',a.candidate):p.error('full candidate SHA required')
    inputs={name:getattr(a,name).resolve(strict=True) for name in ('sdk','distribution','local_sim')}
    a.output.mkdir(parents=True,exist_ok=False)
    value={'schema':'rx.m5.ci-handoff.v1','candidate':a.candidate,'tools':{},'publisher_provenance':'UNSIGNED_PENDING_OWNER_SIGNATURE'}
    for name,root in inputs.items():
        file=root/'CHECKSUMS.sha256';verify_checksums(root,file.read_bytes(),allowed_extras=('CHECKSUMS.sha256',))
        value[name+'_checksums_sha256']=sha_file(file)
    manifests={name:json.loads((root/'manifest.json').read_text()) for name,root in inputs.items()}
    reference=manifests['sdk']['source']['components']
    for name,manifest in manifests.items():
        if manifest['source']['commit']!=a.candidate or manifest['source']['components']!=reference:
            raise ValueError('handoff candidate/component trees differ from artifacts')
    if manifests['local_sim']['status']!='LOCAL_SIM_CURRENT_CANDIDATE_VALIDATED':raise ValueError('LOCAL_SIM validation incomplete')
    architectures={manifests['sdk']['architecture'],manifests['distribution']['architecture'],manifests['local_sim']['release']['architecture']}
    if len(architectures)!=1:raise ValueError('handoff architecture tuple differs')
    value['architecture']=next(iter(architectures));value['component_sources']=reference
    value['manifest_sha256']={name:sha_file(root/'manifest.json') for name,root in inputs.items()}
    for name in TOOLS:
        source=a.tools/('full_run/leak_audit.py' if name=='leak_audit.py' else name)
        if source.is_symlink() or not source.is_file():raise ValueError('regular consumer tool required')
        shutil.copyfile(source,a.output/name);value['tools'][name]=sha_file(source)
    (a.output/'control.json').write_text(json.dumps(value,indent=2)+'\n');verify_tools(a.output)
    print(json.dumps({'status':'CI_HANDOFF_PACKAGED','candidate':a.candidate,'publisher_provenance':'UNSIGNED'}))


if __name__=='__main__':main()
