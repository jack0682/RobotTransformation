"""Fresh real P/Executor/Host installation using the existing signed-package tools."""
from __future__ import annotations

import copy
import shutil
import socket
import time

from common import *
from cell_delivery.api import Api
from cell_delivery.commission import wait_for
from cell_delivery.docker import Docker
from cell_delivery.materials import Materials
from cell_delivery.qualification import references
from runtime_client import Terminal, RuntimeClient
from execution_client import ExecutionClient


class FreshMaterials(Materials):
    def exporter(self, test, environment, label):
        # Only disposable fixture preparation/signing; never a runtime service or ledger writer.
        args = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges', '--user', f'{os.getuid()}:{os.getgid()}',
                '--tmpfs', '/tmp', '-v', str(self.temporary) + ':' + str(self.temporary)]
        for key, value in environment.items():
            args.extend(['-e', key + '=' + value])
        args.extend(['--entrypoint', '/opt/rx/test/delivery_fixture', self.solutions,
                     test, '--ignored', '--exact'])
        log = self.evidence / (label + '.log')
        result = command(args, log=log)
        if '1 passed; 0 failed' not in result:
            raise RuntimeError('fixture exporter did not run exactly one successful test: ' + label)

    def create_seed(self, architecture, composition_draft=None):
        # Existing exporter supplies public contract data and fresh installation/TLS IDs.
        # Replace its deterministic test signing keys in this NEW generated seed only.
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
        self.exporter('export_delivery_seed', {'RX_CELL_DELIVERY_OUTPUT': str(self.seed),
                      'RX_CELL_DELIVERY_ARCH': architecture}, 'export-seed')
        signers = read(self.seed / 'signing-fixtures.json')
        metadata = read(self.seed / 'seed.json')
        policy = read(self.seed / 'package-policy.json')
        for signer in signers['keys']:
            key = Ed25519PrivateKey.generate()
            signer['private_seed_hex'] = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()
            signer['public_key'] = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
            metadata['public_signers'][signer['id']] = signer['public_key']
            for trusted in policy['keys']:
                if trusted['id'] == signer['id']:
                    trusted['verifying_key'] = signer['public_key']
        replace_generated(self.seed / 'signing-fixtures.json', signers)
        replace_generated(self.seed / 'package-policy.json', policy)
        metadata['package_policy_sha256'] = sha(self.seed / 'package-policy.json')
        replace_generated(self.seed / 'seed.json', metadata)
        shutil.copytree(self.seed, self.public_seed, ignore=shutil.ignore_patterns('signing-fixtures.json'))
        self.preserve_public(self.public_seed, 'seed')


class Installation:
    def __init__(self, workspace, evidence, platform_image, solutions_image, case):
        self.root, self.evidence, self.case = workspace, evidence, case
        self.d = Docker(evidence)
        self.pimage = self.d.image(platform_image)
        self.simage = self.d.image(solutions_image)
        if self.pimage['Architecture'] != self.simage['Architecture']:
            raise ValueError('P and S architecture differs')
        self.p, self.s = self.pimage['Id'], self.simage['Id']
        self.volumes = {}
        self.services = {}
        self.materials = FreshMaterials(PLATFORM, workspace, evidence, self.d, self.s)
        self.validator = digest(b''.join(p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py'))))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.origin = f'https://127.0.0.1:{self.port}'

    def volume(self, name):
        self.volumes[name] = self.d.volume(name)
        self.record()
        return self.volumes[name]

    def record(self):
        # Private operational inventory is deliberately separate from uploaded evidence.
        replace_generated(self.root / 'installation.json', {
            'platform_image': self.p, 'solutions_image': self.s,
            'volumes': self.volumes, 'services': self.services,
            'containers': self.d.containers, 'network': self.d.network,
            'terminal_network': self.d.front_network, 'origin': self.origin,
            'workspace': str(self.root), 'preserve': True,
        })

    def generated_command(self, binary, args, label):
        self.d.prepare_permissions(self.s, [self.volumes['provider'] + ':/config',
            self.volumes['author-data'] + ':/data', self.volumes['author'] + ':/work'])
        return self.d.command(self.s, binary, args,
                              [self.volumes['author'] + ':/author:rw',
                               self.volumes['provider'] + ':/config/host:ro'], label)

    def prepare(self, scenario):
        m = self.materials
        m.create_seed(self.simage['Architecture'])
        package, compiled, compiler = m.compile()
        self.bundle = self.root / 'operator'
        holder = self.d.holder(self.s, [])
        self.d.run('cp', holder + ':/opt/rx/operator', str(self.bundle))
        self.d.run('cp', holder + ':/data/observer-latency.json', str(self.evidence / 'observer-latency.json'))
        self.final = m.finalize(package, compiled, compiler, self.port, self.bundle, self.validator)
        self.browser = read(self.final / 'browser-fixture.json')
        self.initial = read(m.seed / 'initial-cell.json')
        self.cell = self.initial['id']
        self.scenario = scenario
        self._external_package()
        if self.case == 'completion-loss':
            self._prepare_loss_link()
        self._start_platform()

    def _external_package(self):
        provider = self.root / 'provider'
        provider.mkdir()
        source = SOLUTIONS / 'examples/process/material-alignment'
        for name in ('adapter.py',):
            shutil.copyfile(source / name, provider / name)
        shutil.copyfile(SOLUTIONS / 'deployment/external-adapters/rx_external_adapter.py',
                        provider / 'rx_external_adapter.py')
        config = read(source / 'config.example.json')
        config['state_directory'] = '/data/material-alignment'
        save(provider / 'm1-provider.json', config)
        author = self.root / 'author'
        author.mkdir()
        self.author = author
        self.volume('provider')
        self.volume('author')
        self.volume('author-data')
        self.d.put(self.s, self.volumes['provider'], provider)
        self.d.prepare_permissions(self.s, [self.volumes['provider'] + ':/config',
                                   self.volumes['author-data'] + ':/data', self.volumes['author'] + ':/work'])
        # T06 loses the existing Host/P transport after entry. Native completion
        # must reach Host normally; the historical native wrapper is not selected.
        args = ['--python', '/opt/rx/python/python', '--adapter', '/config/host/adapter.py', '--config', '/config/host/m1-provider.json',
                '--sdk', '/config/host/rx_external_adapter.py']
        dependencies = ['/opt/rx/python/python', '/config/host/adapter.py', '/config/host/m1-provider.json',
                        '/config/host/rx_external_adapter.py']
        save(author / 'arguments.json', args)
        save(author / 'dependencies.json', dependencies)
        self.d.put(self.s, self.volumes['author'], author)
        self.generated_command('/opt/rx/bin/rx-device-package', [
            'external-program', '/opt/rx/bin/m1-observer', '/author/arguments.json',
            '/author/dependencies.json', '/author/program.json'], 'external-program')
        self.d.extract(self.s, self.volumes['author'], 'program.json', author / 'program.json')
        program = read(author / 'program.json')
        program_ref = artifact(encoded(program), 'rx.external-process-program.v1')
        contracts = {step['id']: {'implementation': self.scenario['implementation'],
            'version': self.scenario['version'], 'primitive': step['id'],
            'parameters': {key: {k: value[k] for k in ('unit', 'value_type', 'frame')}
                           for key, value in self.scenario['parameters'].items()}}
                     for step in self.scenario['steps']}
        profile = {'schema': 'rx.external-process-profile.v1', 'protocol': 'rx.external-process-channel.v1',
                   'program': program_ref, 'commands': contracts,
                   'observations': {source: {'schema': 'boolean/v1', 'unit': 'unitless',
                       'value_type': 'BOOLEAN', 'maximum_age_ns': '1000000000', 'maximum_uncertainty_ns': '0'}
                       for source in ('ready', 'sim/ready', 'shelf.occupied', 'shelf.stopped',
                                      'gripper.part_held', 'ft.part_seated',
                                      'vision.result_available', 'vision.groove_detected')},
                   'conditions': {'sim/ready': 'sim/ready'}}
        templates = {}
        for node, contract in contracts.items():
            intent = copy.deepcopy(self.initial['steps'][0]['intent'])
            intent.update(kind='FINITE_ACTION', target='device/material-alignment/' + node,
                          completion_rule='m1/alignment-result', cancel_rule='sim/stop',
                          execution_timeout_ms='30000')
            intent['body'] = {'program': {'program': program_ref,
                            'parameter_set': artifact(b'{}', 'rx.workflow-parameters.v2')}}
            templates[node] = {'action': {'host': self.initial['hosts'][0], 'intent': intent},
                               'contract': contract}
        assembly = {'schema': 'rx.external-process-assembly.v1', 'profile': profile, 'program': program,
                    'catalog': {'schema': 'rx.execution-template-catalog.v2',
                        'installation': read(self.materials.seed / 'seed.json')['installation'],
                        'cell': self.cell, 'environment': 'SIMULATION', 'templates': templates, 'documents': {}},
                    'outcomes': {'schema': 'rx.native-outcome-table.v1', 'profile_digest': '00' * 32,
                        'completion_rule': 'm1/alignment-result', 'cases': self.scenario['outcomes']}}
        recipe = read(self.materials.seed / 'package-recipe.json')
        save(author / 'assembly.json', assembly)
        save(author / 'recipe.json', {'schema': 'rx.device-package-recipe.v1',
            'package': 'simulation/material-alignment', 'version': '1.0.0',
            'publisher': recipe['publisher'], 'targets': recipe['targets']})
        self.d.put(self.s, self.volumes['author'], author)
        self.generated_command('/opt/rx/bin/rx-device-package', ['external-assemble',
            '/author/assembly.json', '/author/recipe.json', '/author/candidate'], 'external-assemble')
        self.d.extract(self.s, self.volumes['author'], 'candidate', author / 'candidate')
        self.generated_command('/opt/rx/bin/rx-device-package', ['request', '/author/candidate',
            'delivery-package-signer', '/author/signing.json'], 'external-signing-request')
        self.d.extract(self.s, self.volumes['author'], 'signing.json', author / 'signing.json')
        request = read(author / 'signing.json')
        signature = self.materials.sign({k: request[k] for k in ('key', 'message_hex')}, 'external')
        shutil.copyfile(signature, author / 'signature.json')
        manifest = read(author / 'candidate/manifest.json')
        by_hash = {sha(p): p for p in (author / 'candidate').rglob('*') if p.is_file()}
        policy = read(self.materials.seed / 'package-policy.json')
        policy.update(contracts=manifest['contracts'], target=manifest['targets'][0])
        policy['keys'][0].update(kinds=['DEVICE'], permissions=manifest['permissions'])
        policy['assets'] = [{'reference': a, 'path': '/author/' + str(by_hash[a['sha256']].relative_to(author))}
                            for a in manifest['assets']]
        save(author / 'policy.json', policy)
        self.d.put(self.s, self.volumes['author'], author)
        self.generated_command('/opt/rx/bin/rx-device-package', ['seal', '/author/candidate',
            '/author/signature.json', '/author/policy.json', '/author/package'], 'external-seal')
        self.d.extract(self.s, self.volumes['author'], 'package', author / 'package')
        self.templates = read(author / 'package/execution-template-catalog.json')['templates']
        self.materials.preserve_public(author / 'package', 'external-package')
        shutil.copytree(author / 'package', self.final / 'import/templates')
        prototype = self.initial['steps'][0]
        self.initial['steps'] = []
        for declared in self.scenario['steps']:
            node = declared['id']
            action = self.templates[node]['action']
            step = copy.deepcopy(prototype)
            step.update(id='step/' + node, host=action['host'], intent=action['intent'])
            step['completion']['schema'] = 'm1/alignment-result'
            step['completion']['failure'] = ['10', '11', '12']
            self.initial['steps'].append(step)
        for source in ('shelf.occupied', 'shelf.stopped', 'gripper.part_held', 'ft.part_seated',
                       'vision.result_available', 'vision.groove_detected'):
            self.initial['fact_specs'].append({'id': source, 'host': self.initial['hosts'][0],
                'schema': 'boolean/v1', 'unit': 'unitless', 'maximum_age_ns': '1000000000',
                'maximum_uncertainty_ns': '0'})
        catalog = read(self.final / 'config/catalog.json')
        catalog['cells'] = [self.initial if cell['id'] == self.cell else cell for cell in catalog['cells']]
        # Test author operates the one SIM cell; reviewer and release remain distinct identities.
        engineer = next(p for p in catalog['principals'] if p['id'] == 'engineer')
        engineer['roles'] = sorted(set(engineer['roles']) | {'OPERATOR'})
        replace_generated(self.final / 'config/catalog.json', catalog)
        ppolicy = read(self.final / 'config/package-policy.json')
        ppolicy.update(schema='rx.package-verification-policy.v2', additional_package_abis=['rx.package-abi.v2'])
        ppolicy['keys'][0].update(kinds=['PROCESS', 'DEVICE'], permissions=manifest['permissions'] + [
            {'kind': 'OPERATION_SUBMIT', 'operation': 'skill/' + str(i + 1)} for i in range(len(self.templates))])
        ppolicy['assets'] = []
        for a in manifest['assets']:
            dest = self.final / 'config/assets' / (a['sha256'] + '.bin')
            shutil.copyfile(by_hash[a['sha256']], dest)
            ppolicy['assets'].append({'reference': a, 'path': '/config/assets/' + dest.name})
        replace_generated(self.final / 'config/package-policy.json', ppolicy)
        startup = read(self.final / 'config/startup.json')
        startup['catalog']['sha256'] = sha(self.final / 'config/catalog.json')
        startup['package_intake']['policy']['sha256'] = sha(self.final / 'config/package-policy.json')
        replace_generated(self.final / 'config/startup.json', startup)

    def _prepare_loss_link(self):
        """Private test transport material only; no product ledger or native mounts."""
        folder = self.root / 'result-link'
        (folder / 'pki').mkdir(parents=True)
        for source, names in [('config', ('ca.pem', 'p-server.pem', 'p-server.key',
                                         'p-host-client.pem', 'p-host-client.key')),
                              ('host-config', ('h-server.pem', 'h-server.key',
                                               'h-publisher.pem', 'h-publisher.key'))]:
            for name in names:
                shutil.copyfile(self.final / source / 'pki' / name, folder / 'pki' / name)
        def tls(name):
            return '/config/result-link/pki/' + name
        relays = [
            {'listen': '0.0.0.0:7444', 'upstream': 's:7444', 'server_name': 's',
             'ca': tls('ca.pem'), 'server_key': tls('h-server.key'),
             'server_certificate': tls('h-server.pem'), 'client_key': tls('p-host-client.key'),
             'client_certificate': tls('p-host-client.pem'), 'allowed_peer': tls('p-host-client.pem')},
            {'listen': '0.0.0.0:7443', 'upstream': 'p:7443', 'server_name': 'p',
             'ca': tls('ca.pem'), 'server_key': tls('p-server.key'),
             'server_certificate': tls('p-server.pem'), 'client_key': tls('h-publisher.key'),
             'client_certificate': tls('h-publisher.pem'), 'allowed_peer': tls('h-publisher.pem')},
        ]
        save(folder / 'config.json', {'environment': 'SIMULATION', 'relays': relays})
        startup = read(self.final / 'config/startup.json')
        selected = [link for link in startup['host_links'] if link['cell'] == self.cell]
        if len(selected) != 1 or selected[0]['uri'] != 'https://s:7444' or selected[0]['server_name'] != 's':
            raise ValueError('expected original simulation Host transport required')
        selected[0]['uri'] = 'https://loss-link:7444'
        replace_generated(self.final / 'config/startup.json', startup)
        for name in ('loss-config', 'loss-data', 'loss-work'):
            self.volume(name)
        self.d.put(self.s, self.volumes['loss-config'], folder)
        self.d.prepare_permissions(self.s, [self.volumes['loss-config'] + ':/config',
            self.volumes['loss-data'] + ':/data', self.volumes['loss-work'] + ':/work'])

    def _start_loss_link(self):
        mounts = [self.volumes['loss-config'] + ':/config/result-link:ro',
                  self.volumes['loss-data'] + ':/data']
        self.services['loss'] = self.d.start(self.s, 'loss', 'loss-link', '/usr/bin/env',
            ['PYTHONPATH=/opt/rx/result-link/generated', '/usr/local/bin/python3', '-B',
             '/opt/rx/result-link/link.py', '--state', '/data/control', 'serve',
             '--config', '/config/result-link/config.json'], mounts)
        def ready():
            status = self.d.state(self.services['loss'])
            if not status['State']['Running']:
                raise RuntimeError('existing result-link fixture exited before readiness')
            return self.d.run('logs', self.services['loss'])
        wait_for(ready, lambda log: 'SIM result-link ready' in log, timeout=30)
        source = SOLUTIONS / 'deployment/simulation/result-link/link.py'
        installed = self.d.run('exec', self.services['loss'], 'sha256sum', '/opt/rx/result-link/link.py').split()[0]
        if installed != sha(source):
            raise ValueError('installed result-link differs from unchanged source')
        save(self.evidence / 'loss-link-fixture.json', {'source': str(source.relative_to(REPOSITORY)),
            'sha256': installed, 'image': self.s, 'environment': 'SIMULATION',
            'p_to_host': 'https://loss-link:7444', 'host_publisher_to_p': 'https://loss-link:7443',
            'native_storage_mounted': False, 'product_database_mounted': False,
            'signing_seeds_mounted': False, 'private_tls_uploaded': False})
        self.record()

    def loss_evidence(self):
        """Read control and completed audit rows without calling the mutating control CLI."""
        if 'loss' not in self.services:
            raise ValueError('this fresh scene has no result-link fixture')
        reader = r'''
import base64,hashlib,json,os,stat
from pathlib import Path
root=Path('/data/control'); files={}; raw={}
if not root.is_dir() or root.is_symlink() or root.stat().st_uid!=os.getuid():
    raise ValueError('owned result-link control directory required')
for name in ('fault.json','transport.jsonl'):
    p=root/name
    if not p.exists(): continue
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_size>4194304:
        raise ValueError('bounded owned result-link evidence required')
    data=p.read_bytes(); raw[name]=data
    files[name]={'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),
                 'bytes_base64':base64.b64encode(data).decode()}
transport=raw.get('transport.jsonl',b''); pending=bool(transport and not transport.endswith(b'\n'))
lines=transport.splitlines()
if pending: lines=lines[:-1]
print(json.dumps({'control':json.loads(raw['fault.json']) if 'fault.json' in raw else None,
    'transport':[json.loads(line) for line in lines], 'transport_pending':pending, 'raw_files':files},sort_keys=True))
'''
        return json.loads(self.d.run('exec', self.services['loss'], '/usr/local/bin/python3',
                                    '-I', '-S', '-B', '-c', reader))

    def arm_loss_link(self):
        if self.case != 'completion-loss':
            return
        previous = self.loss_evidence()['control']
        if previous is not None:
            raise ValueError('result-link may only be armed once in this fresh scene')
        raw = self.d.run('exec', self.services['loss'], '/usr/local/bin/python3', '-B',
            '/opt/rx/result-link/link.py', '--state', '/data/control', 'arm',
            '--publication', self.publication['reference']['id'], '--ordinal', '1', '--node', 'shelf-seat')
        control = json.loads(raw)
        if (control['phase'] != 'ARMED' or control['publication'] != self.publication['reference']['id']
                or control['ordinal'] != 1 or control['node'] != 'shelf-seat'):
            raise ValueError('result-link selector differs from this publication and A1')
        save(self.evidence / 'loss-link-armed.json', control)

    def _start_platform(self):
        for name in ('p-config', 'p-data', 'p-work', 'imports', 'ui'):
            self.volume(name)
        self.d.put(self.p, self.volumes['p-config'], self.final / 'config')
        self.d.put(self.p, self.volumes['imports'], self.final / 'import')
        self.d.put(self.p, self.volumes['ui'], self.bundle)
        self.permissions()
        self.pmounts = [self.volumes['p-config'] + ':/config:ro', self.volumes['p-data'] + ':/data',
                        self.volumes['imports'] + ':/import:ro', self.volumes['ui'] + ':/operator:ro']
        self.d.command(self.p, '/usr/local/bin/rx-platformd', ['init', '/config/startup.json'], self.pmounts, 'p-init')
        self.d.make_network()
        if self.case == 'completion-loss':
            self._start_loss_link()
        self.services['p'] = self.d.start(self.p, 'p', 'p', '/usr/local/bin/rx-platformd',
            ['run', '/config/startup.json'], self.pmounts, [f'127.0.0.1:{self.port}:8443'])
        self.record()
        self.users = {}
        self.connections = {}
        for who in ('installer', 'engineer', 'verifier', 'release', 'operator'):
            b = self.browser
            api = Api(self.origin, self.final / b['ca'], self.final / b['certificate'],
                      self.final / b['private_key'], self.evidence / 'api' / who)
            deadline = time.monotonic() + 30
            while True:
                try:
                    api.login(who, b['credentials'][who])
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.2)
            self.users[who] = api
            password = self.root / (who + '.password')
            password.write_text(b['credentials'][who])
            connection = self.root / (who + '.json')
            save(connection, {'schema': 'rx.runtime-skill-connection.v1', 'origin': self.origin,
                'ca': str(self.final / b['ca']), 'certificate': str(self.final / b['certificate']),
                'private_key': str(self.final / b['private_key']), 'principal': who, 'password_file': str(password)})
            self.connections[who] = connection
        self.installation = self.users['engineer'].get('/api/v1/overview')['installation']

    def permissions(self):
        for name in ('p-config', 'imports'):
            self.d.prepare_permissions(self.p, [self.volumes[name] + ':/config',
                self.volumes['p-data'] + ':/data', self.volumes['p-work'] + ':/work'])

    def preserve(self):
        self.record()
        self.d.capture_logs()
        failures = []
        if 'engineer' in getattr(self, 'users', {}):
            try:
                save(self.evidence / 'final-cell.json', self.users['engineer'].get('/api/v1/cell', id=self.cell))
                save(self.evidence / 'final-overview.json', self.users['engineer'].get('/api/v1/overview'))
            except Exception as error:
                failures.append({'inspection': 'final P views', 'error': str(error)})
            if getattr(self, 'run', None):
                try:
                    terminal = Terminal(self.connections['engineer'])
                    receipt = ExecutionClient(terminal, self.root / 'final-inspection-client').inspect_execution(self.run, reports=True)
                    save(self.evidence / 'final-execution-receipt.json', receipt)
                except Exception as error:
                    failures.append({'inspection': 'final Run/resources/slot holds', 'error': str(error)})
        try:
            from diagnostics import preserve_host_dispatch
            failures.extend(preserve_host_dispatch(self))
        except Exception as error:
            failures.append({'inspection': 'Host dispatch diagnostic collector', 'error': str(error)})
        if 'loss' in self.services:
            try:
                loss = self.loss_evidence()
                save(self.evidence / 'loss-link-control.json', loss['control'])
                save(self.evidence / 'loss-link-transport.json', {'records': loss['transport'],
                    'trailing_append_pending': loss['transport_pending']})
                save(self.evidence / 'original-loss-link-facts.json', loss['raw_files'])
            except Exception as error:
                failures.append({'inspection': 'original result-link control/audit', 'error': str(error)})
        if 'h' in self.services:
            # Capture independent provider facts even when browser inspection timed out.
            provider_reader = r'''
import base64,hashlib,json,os,stat
from pathlib import Path
root=Path('/data/material-alignment'); records={}
if root.is_dir() and not root.is_symlink():
    for name in ('state.json','effects.jsonl','withheld.jsonl'):
        path=root/name
        if not path.exists(): continue
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_size>4194304:
            raise ValueError('bounded owned provider evidence required')
        raw=path.read_bytes()
        records[name]={'sha256':hashlib.sha256(raw).hexdigest(),
            'bytes_base64':base64.b64encode(raw).decode(), 'size_bytes':len(raw)}
print(json.dumps(records,sort_keys=True))
'''
            try:
                raw = self.d.run('exec', self.services['h'], '/opt/rx/python/python', '-I', '-S', '-B', '-c', provider_reader)
                save(self.evidence / 'original-provider-facts.json', json.loads(raw))
            except Exception as error:
                failures.append({'inspection': 'independent provider facts', 'error': str(error)})
            # Whitelist only synthetic native facts and status; never archive Host DB/TLS/config.
            reader = r'''
import base64,hashlib,json,os,stat,uuid
from pathlib import Path
root=Path('/data/host/native-external'); records={}
if root.is_dir() and not root.is_symlink():
    directories=[p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]
    if len(directories)>128: raise ValueError('native evidence directory bound')
    for directory in directories:
        if str(uuid.UUID(directory.name))!=directory.name: raise ValueError('native operation identity')
        for name in ('request.json','completion.json'):
            path=directory/name
            if not path.exists(): continue
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_size>1048576:
                raise ValueError('bounded owned native evidence required')
            raw=path.read_bytes()
            records[str(path.relative_to(root))]={'sha256':hashlib.sha256(raw).hexdigest(),
                'bytes_base64':base64.b64encode(raw).decode(), 'size_bytes':len(raw)}
print(json.dumps(records,sort_keys=True))
'''
            try:
                raw = self.d.run('exec', self.services['h'], '/opt/rx/python/python', '-I', '-S', '-B', '-c', reader)
                save(self.evidence / 'original-native-facts.json', json.loads(raw))
                raw = self.d.run('exec', self.services['h'], 'cat', '/run/rx-host/host-status.json')
                save(self.evidence / 'final-host-status.json', json.loads(raw))
            except Exception as error:
                failures.append({'inspection': 'original Host/native facts', 'error': str(error)})
        if failures:
            save(self.evidence / 'preservation-inspection-errors.json', failures)
        # Never invoke Docker.cleanup(): it force-removes all state, including UNKNOWN custody.
        save(self.evidence / 'preservation.json', {'state': 'PRESERVED',
            'containers': self.d.containers, 'volumes': self.d.volumes,
            'network': self.d.network, 'terminal_network': self.d.front_network,
            'case': self.case, 'workspace': str(self.root),
            'limitations': ['CI runner disposal ends container lifetime; archived public evidence is not a resumable installation.']})
