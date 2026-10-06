#!/usr/bin/env python3
"""Create the only CI-uploadable diagnostic directory after private-value audit.

Raw logs, test credentials and failed audit inputs stay in runner work. A failed
scan emits only a non-secret audit receipt in --output and exits nonzero.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

# Installed producer path keeps the shared audit in full_run; source-free handoff
# receives identical bytes as a flat sibling module.
try:
    from leak_audit import collect_private,approve_public,refuse_public,AuditIncomplete,SecretInventory
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).with_name('full_run')))
    from leak_audit import collect_private,approve_public,refuse_public,AuditIncomplete,SecretInventory


def include_files(root,patterns,target,prefix):
    if not root.is_dir():return 0
    count=0;seen=set()
    for pattern in patterns:
        for file in root.glob(pattern):
            if not file.is_file() or file.is_symlink():continue
            relative=file.relative_to(root)
            if 'private' in relative.parts or 'private-acceptance' in relative.parts:raise ValueError('Private path cannot be a publication input')
            if relative in seen:continue
            seen.add(relative);destination=target/prefix/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(file,destination);count+=1
    return count



def publish_early_failure(base,output,repo,candidate):
    """No raw stage is inspected/copied here, including build-time test output."""
    if repo is None or candidate is None or any(path.exists() or path.is_symlink() for path in (base/'m5-local-work',base/'m5-local-sim')):return False
    from build_diagnostics import vocabulary,validate_report,render_report,encoded
    public_vocab=vocabulary(repo,candidate);reports=[]
    for folder,phase in [('m5-dist-work','DISTRIBUTION_BUILD'),('m5-sdk-work','SDK_BUILD')]:
        path=base/folder/'closed-failure.json'
        if not path.exists():continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:return False
        value=json.loads(path.read_bytes());validate_report(value,public_vocab)
        if value['phase']!=phase:return False
        reports.append(render_report(value,public_vocab))
    if not reports:return False
    # The producer remains failed. This is not private-value audit approval and
    # does not authorize any source artifact, archive, original JSON or raw log.
    import tempfile,os
    if output.exists() or output.is_symlink():return False
    temporary=Path(tempfile.mkdtemp(prefix='.m5-closed-public-',dir=base))
    directory=temporary/'evidence/diagnostics';directory.mkdir(parents=True)
    receipt={'schema':'rx.m5-early-diagnostic-publication.v1','status':'CLOSED_FAILURE_FACTS_ONLY',
        'source_commit':public_vocab['commit'],'acceptance_started':False,'raw_content_published':False,
        'artifacts_authorized':False,'cause_not_inferred_from_resource_snapshot':True,'reports':reports}
    (directory/'closed-build-failure.json').write_bytes(encoded(receipt)+b'\n')
    (temporary/'LEAK_AUDIT.json').write_bytes(encoded({'schema':'rx.private-value-leak-audit.v1','status':'PUBLIC_EVIDENCE_REFUSED',
        'reason':'EARLY_BUILD_CLOSED_FACTS_ONLY','values_disclosed':False,'raw_evidence_uploaded':False})+b'\n')
    os.rename(temporary,output)
    return True



def producer_ready():
    """Select only a fresh projection created by this exact workflow step."""
    output=os.environ.get('GITHUB_OUTPUT')
    if output:
        with Path(output).open('a') as stream:stream.write('m5_publication_ready=true\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['producer','sdk','runtime'],required=True)
    p.add_argument('--runner-temp',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repo',type=Path,help='Producer only: exact candidate for closed early-failure vocabulary validation')
    p.add_argument('--candidate',help='Producer only: immutable workflow contribution SHA, never inferred from current HEAD');a=p.parse_args()
    base=a.runner_temp.resolve(strict=True)
    if a.mode=='producer' and not any(path.exists() or path.is_symlink() for path in (base/'m5-local-work',base/'m5-local-sim')):
        # Try closed facts before copying even one raw log/archive. This path is
        # useful when image building itself exhausted disk or otherwise failed.
        try:
            published=publish_early_failure(base,a.output.absolute(),a.repo,a.candidate)
        except (OSError,ValueError,KeyError,TypeError):published=False
        if published:producer_ready()
        elif not a.output.exists() and not a.output.is_symlink():
            refuse_public(a.output.absolute(),'EARLY_DIAGNOSTIC_UNAVAILABLE');producer_ready()
        raise SystemExit('Producer failed before acceptance: raw evidence remains refused; only validated closed facts may be available')
    stage=base/('m5-'+a.mode+'-publication-inputs');stage.mkdir(exist_ok=False)
    private=[];count=0
    if a.mode=='producer':
        for name,patterns in [('m5-dist-work',['*.json','*.stdout','*.stderr']),
            ('m5-sdk-work',['*.json','logs/*.stdout','logs/*.stderr']),
            ('m5-local-work',['*.json','logs/*.stdout','logs/*.stderr','installer-acceptance/*.json','installer-acceptance/*.log'])]:
            count+=include_files(base/name,patterns,stage,'diagnostics/'+name)
        for name in ('sdk','distribution','local-sim','handoff'):
            count+=include_files(base/('m5-'+name),['**/*'],stage,'artifacts/'+name)
        private=[p for p in (base/'m5-local-work').glob('private-acceptance*') if p.is_dir()]
    elif a.mode=='sdk':
        count=include_files(base/'m5-sdk-consumer',['*.json','*.stdout','*.stderr','adapter-evidence/**/*.json','adapter-evidence/**/*.stdout','adapter-evidence/**/*.stderr'],stage,'sdk-consumer')
    else:
        root=base/'m5-runtime-consumer'
        count=include_files(root,['*.json','*.stdout','*.stderr','file-state/sessions/*/session.json','file-state/sessions/*/evidence/**/*',
            'registered/public-approved/**/*','registered/*/public-approved/**/*'],stage,'runtime-consumer')
        private=[*root.glob('file-state/sessions/*/private'),*root.glob('registered/*/private')]
    scope='ACTUAL_PRIVATE_FIXTURE_VALUES'
    try:
        if a.mode=='sdk':
            # This consumer installs packages and exercises a native file counter;
            # it creates no signer, TLS, credential, password or token fixture.
            # Check generic private-key envelopes without inventing private values.
            scratch=base/'m5-sdk-audit-scratch';scratch.mkdir(exist_ok=False)
            inventory=SecretInventory([scratch]);scope='NO_PRIVATE_FIXTURES_GENERATED_IN_SDK_CONSUMER'
            for marker in (b'-----BEGIN PRIVATE KEY-----',b'-----BEGIN ENCRYPTED PRIVATE KEY-----',
                           b'-----BEGIN RSA PRIVATE KEY-----',b'-----BEGIN EC PRIVATE KEY-----',
                           b'-----BEGIN OPENSSH PRIVATE KEY-----'):
                inventory._patterns[marker]={'UNEXPECTED_PRIVATE_KEY_MARKER'}
        else:
            inventory=collect_private(private,required_minimums={'TOKEN':2} if a.mode=='producer' else {'PRIVATE_KEY':1,'PASSWORD':1})
    except (AuditIncomplete,OSError,ValueError):
        if not a.output.exists() and not a.output.is_symlink():
            refuse_public(a.output.absolute(),'PRIVATE_INVENTORY_INCOMPLETE')
            if a.mode=='producer':producer_ready()
        raise SystemExit('Publication refused: private inventory unavailable; only redacted audit receipt may be uploaded') from None
    result=approve_public(inventory,stage,a.output.absolute(),max_bytes=8*1024**3,max_member_bytes=2*1024**3,extra_documents={'PUBLICATION_SCOPE.json':{
        'schema':'rx.m5-ci-publication-scope.v1','mode':a.mode,'candidate_files':count,
        'private_roots_scanned':len(private),'private_value_scan_scope':scope,
        'generic_private_key_markers_checked':a.mode=='sdk','raw_private_directories_uploaded':False,
        'limits':'Private trees and unrelated caches are excluded; producer mode audits every selected upload artifact and archive plus diagnostics; SDK mode has no generated private fixtures and checks private-key envelope markers.'}})
    if a.mode=='producer':producer_ready()
    # The helper owns leak details and guarantees they contain no secret values.
    if result.get('status') not in ('PASS','PUBLIC_EVIDENCE_APPROVED','PASS_NO_SECRET_MATCH'):
        raise SystemExit('Private-value audit did not approve publication; upload only the non-secret audit receipt')
    print(json.dumps({'status':'PUBLICATION_PROJECTION_APPROVED','files':count,'mode':a.mode}))


if __name__=='__main__':main()
