"""Existing public review/Host-acknowledgement/qualification path, measured on fresh Linux."""
from __future__ import annotations

import shutil

from common import *
from cell_delivery.api import Rejected
from cell_delivery.commission import Commission, wait_for
from cell_delivery.qualification import build_report, verified_release_evidence
from test_runtime_skills import recovery_evidence


def cell_row(overview, cell):
    return next(row for row in overview['cells'] if row['cell']['value']['id'] == cell)


def provider_effects(site):
    raw = site.d.run('exec', site.services['h'], '/bin/sh', '-c',
                    'if [ -f /data/material-alignment/effects.jsonl ]; then cat /data/material-alignment/effects.jsonl; fi')
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def commission(site):
    engineer, reviewer, release, operator = [site.users[k] for k in ('engineer', 'verifier', 'release', 'operator')]
    def overview():
        return engineer.get('/api/v1/overview')
    current = wait_for(overview, lambda v: bool(cell_row(v, site.cell)['diagnostics']['hosts'])
        and all(h['context'] == 'CURRENT' for h in cell_row(v, site.cell)['diagnostics']['hosts'])
        and all(s['usable'] for s in cell_row(v, site.cell)['diagnostics']['sources']))
    host = json.loads(site.d.run('exec', site.services['h'], 'cat', '/run/rx-host/host-status.json'))
    journals = json.loads(site.d.run('exec', site.services['h'], 'cat', '/data/host/installation.json'))
    if host['phase'] != 'SOFTWARE_READY_UNARMED' or cell_row(current, site.cell)['runs'] or provider_effects(site):
        raise ValueError('fresh installation has unexpected activity before qualification')
    recovery_dir = site.root / 'recovery-private'
    recovery_dir.mkdir()
    evidence, _ = recovery_evidence(site.d, site.simage, SOLUTIONS, recovery_dir)
    recovery = verified_release_evidence(evidence, site.s)
    client = Commission(engineer, reviewer, release, site.cell, site.target,
                        execution_configuration=site.configuration, package_path='m1-process')
    selections = {'skill/' + str(i + 1): 'step/' + step['id'] for i, step in enumerate(site.scenario['steps'])}
    job = client.import_process(sha(site.process / 'package/manifest.json'),
                                sha(site.process / 'package/manifest.sig.json'), selections)
    save(site.process / 'review-request.json', job['request'])
    site.d.put(site.s, site.volumes['process'], site.process)
    mounts = [site.volumes['process'] + ':/work']
    def call(args, label):
        site.d.prepare_permissions(site.s, [site.volumes['provider'] + ':/config',
            site.volumes['process-data'] + ':/data', site.volumes['process'] + ':/work'])
        return site.d.command(site.s, '/opt/rx/bin/rx-process-package', args, mounts, label)
    result = json.loads(call(['review', '/work/package', '/work/policy.json', '/work/review-request.json',
                              '/work/review'], 'm1-process-review'))
    if not result['compiler_checks_passed'] or result['activation_authorized']:
        raise ValueError('actual process software review failed or overclaims activation')
    call(['review-signing-request', '/work/review/verification.json', 'delivery-review-signer',
          '/work/review-signing.json'], 'm1-review-signing')
    site.d.extract(site.s, site.volumes['process'], 'review-signing.json', site.process / 'review-signing.json')
    signing = read(site.process / 'review-signing.json')
    signature = site.materials.sign({k: signing[k] for k in ('key', 'message_hex')}, 'm1-review')
    site.d.extract(site.s, site.volumes['process'], 'review', site.process / 'review')
    shutil.copyfile(signature, site.process / 'review/verification.sig.json')
    site.materials.preserve_public(site.process / 'review', 'process-review')
    upload = site.root / 'review-upload'
    upload.mkdir()
    shutil.copytree(site.process / 'review', upload / 'process-review')
    site.d.put(site.p, site.volumes['imports'], upload)
    site.permissions()
    applied = client.accept_process_report(job, result['report_digest'])
    save(site.evidence / 'applied-unqualified.json', applied)
    negative_id = read(site.final / 'delivery.json')['negative_cell']
    negative = operator.get('/api/v1/cell', id=negative_id)
    cfg = negative['value']['configuration']
    negative_run = operator.mutate('negative-create', '/api/v1/runs', {'cell': cfg['id'],
        'recipe_digest': cfg['recipe']['sha256'], 'site_config_digest': cfg['site_config_digest'],
        'expected_cell': negative['revision']})
    candidate = operator.get('/api/v1/run/start-context', cell=cfg['id'], run=negative_run['id'],
                             purpose='PRODUCTION', budget_limit='1')
    try:
        operator.mutate('negative-start', '/api/v1/runs/start', candidate['request'])
    except Rejected as error:
        negative_denial = {'status': error.status, 'body': error.body}
        if error.status not in (403, 409, 422):
            raise
    else:
        raise AssertionError('unconfigured physical cell accepted a start')
    try:
        operator.get('/api/v1/package-intake-context', cell=site.cell)
    except Rejected as error:
        if error.status != 403:
            raise
        role_denial = {'status': error.status, 'body': error.body}
    else:
        raise AssertionError('operator acquired engineering intake access')
    qjob = client.begin_requalification(applied, site.qualification_digest)
    qdetail = release.get('/api/v1/qualification-review', cell=site.cell, id=qjob['request']['id'])
    current = overview()
    equipment = cell_row(current, site.cell)['diagnostics']
    after_journals = json.loads(site.d.run('exec', site.services['h'], 'cat', '/data/host/installation.json'))
    effects = provider_effects(site)
    limits = ['DRAFT-M1 FILE_SIMULATION only; no physical operation or owner milestone acceptance.',
              'Qualification precedes the actual M1 browser run; its outcome is recorded separately.']
    observations = {
        'SOFTWARE': {'assertions': {'actual_signed_compiler_passed': result['compiler_checks_passed'],
            'exact_target_applied': applied['change']['after'] == site.configuration},
            'observations': {'compiler': result, 'publication': site.publication, 'applied': applied['change']['after']}, 'limitations': limits},
        'EQUIPMENT': {'assertions': {'current_sources': bool(equipment['sources']) and all(s['usable'] for s in equipment['sources']),
            'host_unarmed': host['phase'] == 'SOFTWARE_READY_UNARMED', 'same_kernel_clock': host['clock_id'] == current['installation']['clock_id'],
            'unchanged_journals': journals == after_journals}, 'observations': {'host': host, 'diagnostics': equipment, 'journals': after_journals}, 'limitations': limits},
        'CELL_INTEGRATION': {'assertions': {'applied_unqualified': applied['change']['state'] == 'APPLIED_UNQUALIFIED',
            'actual_host_acknowledgement': client.pre_apply_detail['host_configuration']['all_hosts_acknowledged'],
            'committed_host_proofs': bool(applied['change']['application']['host_proofs']),
            'current_fences': qdetail['context_current'] and qdetail['fences_confirmed']},
            'observations': {'application': applied['change']['application'], 'fences': qjob['request']['fences'],
                             'clear_blocks': client.clear_candidates}, 'limitations': limits},
        'RECOVERY': {'assertions': {'exact_image_sealed_recovery_tests': len(recovery['verified_tests']) == 3,
            'journal_identity_preserved': journals == after_journals, 'recorded_runtime_origins': bool(qjob['request']['runtime_restrictions'])},
            'observations': recovery, 'limitations': limits + ['Generic release recovery evidence does not certify M1 native UNKNOWN recovery.']},
        'PROTECTION': {'assertions': {'physical_unconfigured': candidate['blocking_reason'] == 'NOT_COMMISSIONED',
            'read_did_not_authorize': candidate['can_request'] is False}, 'observations': negative_denial, 'limitations': limits},
        'OPERATIONS': {'assertions': {'operator_denied_engineering': role_denial['status'] == 403,
            'distinct_roles': len({a.get('/api/v1/overview')['user']['principal'] for a in (engineer, reviewer, release)}) == 3,
            'no_main_runs': not cell_row(current, site.cell)['runs'], 'no_native_effects': not effects},
            'observations': {'role_denial': role_denial, 'effects': effects}, 'limitations': limits},
    }
    qreport = site.root / 'qualification-report'
    build_report(qjob, site.validator, site.final / 'qualification-materials', observations, qreport,
                 scope='DRAFT_M1_MATERIAL_ALIGNMENT_FILE_SIMULATION')
    signature = site.materials.sign({'key': 'delivery-qualification-signer',
                                     'qualification_report': str(qreport / 'qualification.json')}, 'm1-qualification')
    metadata = read(signature.with_suffix('.metadata.json'))
    shutil.copyfile(signature, qreport / 'qualification.sig.json')
    site.materials.preserve_public(qreport, 'qualification-report')
    upload = site.root / 'qualification-upload'
    upload.mkdir()
    shutil.copytree(qreport, upload / 'qualification-report')
    site.d.put(site.p, site.volumes['imports'], upload)
    site.permissions()
    active = client.activate(qjob, metadata['report_digest'])
    save(site.evidence / 'activation.json', active)
    return active
