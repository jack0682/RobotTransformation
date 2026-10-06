#!/usr/bin/env python3
"""Validate the reviewed M5 workflow and independent required-check boundary."""
import hashlib
import json
from pathlib import Path
import re

# Filled when the staged workflow is frozen. A workflow edit requires an explicit
# reviewed policy update; content filters or tolerated failure cannot slip in.
REVIEWED_WORKFLOW_SHA256 = '82bff19aa0cdceffcfbd3d38b30567b604f61382e8b0442b81173c2802178dc7'
WORKFLOW = '.github/workflows/m5-artifact-candidate.yml'
JOBS = {'produce','sdk_consumer','runtime_consumer','simulation_candidate'}


def workflow_errors(text):
    errors=[]
    if re.search(r'(?m)^\s*(paths|paths-ignore|branches-ignore|continue-on-error)\s*:',text):errors.append('M5 filters or tolerated failures are forbidden')
    if 'pull_request_target' in text:errors.append('M5 contributor code cannot run under a privileged event')
    if not re.search(r'(?ms)^  pull_request:\n    branches: \[main, develop\]\n    types: \[opened, synchronize, reopened, edited, ready_for_review\]',text):
        errors.append('M5 must run for every exact main/develop PR update')
    body=text.partition('jobs:\n')[2]
    names=set(re.findall(r'(?m)^  ([a-z_]+):$',body))
    if names!=JOBS:errors.append('M5 job inventory differs')
    for job in ('produce','sdk_consumer','runtime_consumer'):
        match=re.search(r'(?ms)^  '+job+r':\n(.*?)(?=^  [a-z_]+:|\Z)',body)
        value=match.group(1) if match else ''
        if value.count('arch: amd64')!=1 or value.count('arch: arm64')!=1 or 'max-parallel: 2' not in value:
            errors.append('M5 must use both isolated native architecture runners: '+job)
        if job!='produce' and 'actions/checkout@' in value:errors.append('Artifact consumer cannot check out core source: '+job)
    for token in ("contents: read","CARGO_BUILD_JOBS: '1'","name: ${{ github.event_name == 'pull_request' && 'M5' || 'Branch M5' }}",
                  'needs: [produce, sdk_consumer, runtime_consumer]',"if: ${{ always() }}",
                  'ref: ${{ github.event.pull_request.head.sha || github.sha }}','publish_ci_evidence.py --mode runtime',
                  'prepare_historical_bundle.py','--historical-bundle',"v['result']!='success'"):
        if token not in text:errors.append('Missing required M5 boundary: '+token)
    for action in re.findall(r'(?m)^\s*- uses:\s*(\S+)',text):
        if not re.fullmatch(r'[^@\s]+@[0-9a-f]{40}',action):errors.append('M5 action must be SHA-pinned')
    allowed={'${{ always() }}','always()'}
    for line in text.splitlines():
        match=re.match(r'^\s*(?:-\s*)?if\s*:\s*(.+)$',line)
        if match and match.group(1).strip() not in allowed:errors.append('M5 required job/step can be conditionally skipped')
    return errors


def check(root):
    root=Path(root);errors=[]
    try:
        raw=(root/WORKFLOW).read_bytes();text=raw.decode()
        if hashlib.sha256(raw).hexdigest()!=REVIEWED_WORKFLOW_SHA256:errors.append('M5 workflow differs from reviewed execution policy')
        errors.extend(workflow_errors(text))
        settings=json.loads((root/'repository-settings.json').read_text())
        protected=next(r for r in settings['rulesets'] if r['name']=='RobotTransformation protected branches')
        checks=next(r for r in protected['rules'] if r['type']=='required_status_checks')['parameters']
        expected=[{'context':'CI','integration_id':15368},{'context':'DCO','integration_id':1861},{'context':'M5','integration_id':15368}]
        if checks['required_status_checks']!=expected or checks['strict_required_status_checks_policy'] is not True or protected['bypass_actors']:
            errors.append('CI/DCO/M5 must all remain strict required checks without quality bypass')
    except (OSError,ValueError,KeyError,StopIteration,TypeError) as error:
        errors.append('M5 policy unavailable: '+type(error).__name__)
    return errors
