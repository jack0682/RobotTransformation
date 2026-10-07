"""Compile the P-authored process; prepare, install and pin the exact v2 input closure."""
from __future__ import annotations

import copy
import shutil
import time

from common import *
from cell_delivery.commission import wait_for
from cell_delivery.qualification import references


def compile_process(site):
    root = site.root / 'process'
    root.mkdir()
    site.process = root
    policy = read(site.final / 'config/package-policy.json')
    assets = root / 'assets'
    shutil.copytree(site.final / 'config/assets', assets)
    for entry in policy['assets']:
        entry['path'] = '/work/assets/' + Path(entry['path']).name
    recipe = read(site.materials.seed / 'package-recipe.json')
    recipe['package'] = 'simulation/material-alignment-process'
    goal = next(iter(site.compile_input['bindings'].values()))['intent']['body']['program']
    recipe['assets'] = [goal['program'], goal['parameter_set']]
    save(root / 'recipe.json', recipe)
    save(root / 'policy.json', policy)
    save(root / 'compile-input.json', site.compile_input)
    site.volume('process')
    site.volume('process-data')
    site.d.put(site.s, site.volumes['process'], root)
    site.d.prepare_permissions(site.s, [site.volumes['provider'] + ':/config',
        site.volumes['process-data'] + ':/data', site.volumes['process'] + ':/work'])
    mounts = [site.volumes['process'] + ':/work']
    def call(args, label):
        site.d.prepare_permissions(site.s, [site.volumes['provider'] + ':/config',
            site.volumes['process-data'] + ':/data', site.volumes['process'] + ':/work'])
        return site.d.command(site.s, '/opt/rx/bin/rx-process-package', args, mounts, label)
    call(['assemble', '/work/compile-input.json', '/work/recipe.json', '/work/candidate'], 'm1-process-assemble')
    call(['request', '/work/candidate', 'delivery-package-signer', '/work/signing.json'], 'm1-process-signing')
    site.d.extract(site.s, site.volumes['process'], 'signing.json', root / 'signing.json')
    signing = read(root / 'signing.json')
    signature = site.materials.sign({k: signing[k] for k in ('key', 'message_hex')}, 'm1-process')
    shutil.copyfile(signature, root / 'signature.json')
    site.d.put(site.s, site.volumes['process'], root)
    call(['seal', '/work/candidate', '/work/signature.json', '/work/policy.json', '/work/package'], 'm1-process-seal')
    call(['compile', '/work/package', '/work/policy.json', '/work/compiled'], 'm1-process-compile')
    site.d.extract(site.s, site.volumes['process'], 'package', root / 'package')
    site.d.extract(site.s, site.volumes['process'], 'compiled', root / 'compiled')
    site.materials.preserve_public(root / 'package', 'process-package')
    site.materials.preserve_public(root / 'compiled', 'process-compiled')
    resolved = read(root / 'compiled/resolved.json')
    children = resolved['root']['body']['children']
    steps = site.scenario['steps']
    if len(children) != len(steps):
        raise ValueError('compiled process does not contain the six selected steps')
    binding = {'schema': 'rx.workflow-execution-binding.v2', 'publication': site.publication['reference'],
        'policy': site.publication['policy'], 'nodes': {node['id']: step['id'] for node, step in zip(children, steps)}}
    plan = {'schema': 'rx.execution-plan.v2', 'binding': binding, 'process': resolved}
    target = copy.deepcopy(site.initial)
    target.update(process=resolved, execution=binding, recipe=artifact(encoded(plan), 'rx.execution-plan.v2'))
    target['steps'] = []
    for node in children:
        action = resolved['bindings'][node['body']['binding']]
        step = copy.deepcopy(next(s for s in site.initial['steps'] if s['host'] == action['host'] and s['intent'] == action['intent']))
        step.update(id=node['id'], predecessors=[])
        target['steps'].append(step)
    save(root / 'plan.json', plan)
    save(root / 'target.json', target)
    # This authenticated existing endpoint saves a candidate, never applies or qualifies it.
    prepared = site.users['engineer']._request('/api/v1/workflow-executions/configuration', encoded(target))
    if prepared != {'configuration': artifact(encoded(target), 'rx.cell-configuration.v2'),
                    'installed': False, 'qualified': False}:
        raise ValueError('configuration preparation receipt differs')
    save(site.evidence / 'configuration-prepared.json', prepared)
    site.target, site.configuration = target, prepared['configuration']
    shutil.copytree(root / 'package', site.final / 'import/m1-process')


def qualification_policy(site):
    materials = site.final / 'qualification-materials'
    pool = materials / 'artifacts'
    def add(raw, schema):
        ref = artifact(raw, schema)
        (pool / (ref['sha256'] + '.bin')).write_bytes(raw)
        return ref
    for directory in [site.final / 'config/assets', site.author / 'package']:
        for path in directory.rglob('*'):
            if path.is_file():
                raw = path.read_bytes()
                (pool / (digest(raw) + '.bin')).write_bytes(raw)
    known = []
    material = read(site.root / 'material/host-material.json')
    for value in material.values():
        raw = b''.join(Path(part['path']).read_bytes() for part in value['parts'])
        if artifact(raw, value['reference']['schema_id']) != value['reference']:
            raise ValueError('exported material differs from P-approved bytes')
        known.append(add(raw, value['reference']['schema_id']))
    publication = add(encoded(site.publication), 'rx.workflow-publication.v2')
    if add(encoded(site.target), 'rx.cell-configuration.v2') != site.configuration:
        raise ValueError('target artifact identity differs')
    add((site.process / 'plan.json').read_bytes(), 'rx.execution-plan.v2')
    policy = read(site.final / 'config/qualification-policy.json')
    policy['schema'] = 'rx.requalification-policy.v3'
    profile = policy['profiles'][0]
    profile.update(configuration=site.configuration, definition=site.target['definition'], envelope=site.target['envelope'])
    plan = read(pool / (profile['acceptance_plan']['sha256'] + '.bin'))
    plan.update(configuration=site.configuration, scope='DRAFT-M1 six-step external FILE_SIMULATION; one held material and shelf seat only')
    profile['acceptance_plan'] = add(encoded(plan), plan['schema'])
    refs = [site.target['definition'], site.target['envelope'], site.target['recipe'], publication,
            site.publication['policy'], *known, *read(site.author / 'package/manifest.json')['assets']]
    for package in site.publication['packages'].values():
        refs.extend(package['dependencies'])
    refs.extend(ref for ref in profile['dependencies'] if ref['sha256'] == site.target['site_config_digest'])
    unique = {(ref['sha256'], ref['schema_id']): ref for ref in refs}
    profile['dependencies'] = sorted(unique.values(), key=lambda r: (r['sha256'], r['schema_id']))
    policy['keys'][0]['validators'] = [site.validator]
    # Match the existing policy's canonical digest recipe; this is not a new policy meaning.
    policy['profiles'].sort(key=lambda p: (p['cell'], p['configuration']['sha256']))
    policy['keys'].sort(key=lambda key: key['id'])
    for declared in policy['profiles']:
        declared['criteria'].sort(key=lambda criterion: criterion['id'])
        declared['dependencies'].sort(key=lambda ref: (ref['sha256'], ref['schema_id']))
    for ref in references(policy).values():
        if artifact((pool / (ref['sha256'] + '.bin')).read_bytes(), ref['schema_id']) != ref:
            raise ValueError('qualification dependency bytes differ')
    replace_generated(materials / 'policy.json', policy)
    replace_generated(site.final / 'config/qualification-policy.json', policy)
    startup = read(site.final / 'config/startup.json')
    startup['package_intake']['qualification_policy']['sha256'] = sha(site.final / 'config/qualification-policy.json')
    replace_generated(site.final / 'config/startup.json', startup)
    site.qualification_digest = digest(b'RX-REQUALIFICATION-POLICY-v1\n' + encoded(policy))
    # Still unqualified and with zero Runs: ordinary P restart reads the new pinned policy.
    site.d.run('stop', '--timeout', '20', site.services['p'])
    site.d.put(site.p, site.volumes['p-config'], site.final / 'config')
    site.d.put(site.p, site.volumes['imports'], site.final / 'import')
    site.permissions()
    site.d.run('start', site.services['p'])
    deadline = time.monotonic() + 30
    while True:
        try:
            for who, api in site.users.items():
                api.login(who, site.browser['credentials'][who])
            site.installation = site.users['engineer'].get('/api/v1/overview')['installation']
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(.2)


def start_services(site):
    folder = site.final / 'host-config'
    host = read(folder / 'startup.template.json')
    info = read(folder / 'binding-input.json')
    initial = site.initial
    binding = {'host': host['host'], 'platform': info['platform'], 'cell': site.cell,
        'definition': initial['definition'], 'envelope': initial['envelope'],
        'qualification': info['initial_unqualified_reference'], 'qualification_revision': '1',
        'allowed_intents': [step['intent'] for step in initial['steps']], 'scope_ids': initial['scopes'],
        'condition_ids': sorted({v for step in initial['steps'] for v in step['condition_ids']}),
        'environment': 'SIMULATION', 'purposes': ['PRODUCTION']}
    save(folder / 'bindings.json', [binding])
    host['bindings']['sha256'] = sha(folder / 'bindings.json')
    host['publisher']['store_generation'] = site.installation['store_generation']
    shutil.copytree(site.author / 'package', folder / 'templates')
    shutil.copytree(site.root / 'provider', folder, dirs_exist_ok=True)
    policy = read(site.author / 'policy.json')
    assets = folder / 'assets'
    assets.mkdir()
    for entry in policy['assets']:
        source = site.author / entry['path'].removeprefix('/author/')
        dest = assets / (entry['reference']['sha256'] + '.bin')
        shutil.copyfile(source, dest)
        entry['path'] = '/config/host/assets/' + dest.name
    save(folder / 'package-policy.json', policy)
    registry = {'schema': 'rx.external-adapter-registry.v1', 'entries': {'simulation/material-alignment': {
        'directory': '/config/host/templates', 'manifest_digest': sha(site.author / 'package/manifest.json'),
        'policy': {'path': '/config/host/package-policy.json', 'sha256': sha(folder / 'package-policy.json')}}}}
    save(folder / 'registry.json', registry)
    host['backend'] = {'kind': 'EXTERNAL_PROCESS_PACKAGE', 'adapter': 'simulation/material-alignment',
        'registry': {'path': '/config/host/registry.json', 'sha256': sha(folder / 'registry.json')}}
    shutil.copytree(site.root / 'material', folder / 'material')
    material = read(folder / 'material/host-material.json')
    for item in material.values():
        for part in item['parts']:
            part['path'] = '/config/host/material/' + Path(part['path']).name
    host['execution_materials'] = [material]
    save(folder / 'startup.json', host)
    for name in ('h-config', 'h-data', 'h-runtime', 'e-config', 'e-data', 'e-work'):
        site.volume(name)
    site.d.put(site.s, site.volumes['h-config'], folder)
    site.d.prepare_permissions(site.s, [site.volumes['h-config'] + ':/config',
        site.volumes['h-data'] + ':/data', site.volumes['h-runtime'] + ':/work'])
    mounts = [site.volumes['h-config'] + ':/config/host:ro', site.volumes['h-data'] + ':/data',
              site.volumes['h-runtime'] + ':/run/rx-host']
    site.d.command(site.s, '/bin/mkdir', ['/data/material-alignment'], mounts, 'provider-state-directory')
    site.d.command(site.s, '/opt/rx/python/python', ['-I', '-S', '-B', '/config/host/adapter.py',
        '--config', '/config/host/m1-provider.json', '--initialize'], mounts, 'provider-initialize')
    site.d.command(site.s, '/opt/rx/bin/rx-hostd', ['inspect', '/config/host/startup.json'], mounts, 'h-inspect')
    site.d.command(site.s, '/opt/rx/bin/rx-hostd', ['init', '/config/host/startup.json'], mounts, 'h-init')
    site.services['h'] = site.d.start(site.s, 'h', 's', '/opt/rx/bin/rx-hostd', ['run', '/config/host/startup.json'], mounts)
    executor = read(site.final / 'executor-config/cell.template.json')
    executor['execution_v2'] = True
    executor['expected_service']['scope']['store_generation'] = site.installation['store_generation']
    executor['engine']['sha256'] = site.d.run('run', '--rm', '--network', 'none', '--entrypoint', 'sha256sum',
                                           site.s, '/opt/rx/bin/rx-bt-engine').split()[0]
    save(site.final / 'executor-config/cell.json', executor)
    site.d.put(site.s, site.volumes['e-config'], site.final / 'executor-config')
    site.d.prepare_permissions(site.s, [site.volumes['e-config'] + ':/config',
        site.volumes['e-data'] + ':/data', site.volumes['e-work'] + ':/work'])
    mounts = [site.volumes['e-config'] + ':/config/executor:ro', site.volumes['e-data'] + ':/data']
    site.d.command(site.s, '/opt/rx/bin/rx-executor-service', ['cell', 'init', '/config/executor/cell.json'], mounts, 'e-init')
    site.services['e'] = site.d.start(site.s, 'e', 'e', '/opt/rx/bin/rx-executor-service',
                                   ['cell', 'run', '/config/executor/cell.json'], mounts)
    site.record()
