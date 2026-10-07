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
        program_file = 'adapter.py'
        if self.case == 'completion-loss':
            shutil.copyfile(Path(__file__).with_name('completion_link.py'), provider / 'completion_link.py')
            program_file = 'completion_link.py'
            self.d.put(self.s, self.volumes['provider'], provider)
        args = ['--python', '/opt/rx/python/python', '--adapter', '/config/host/' + program_file, '--config', '/config/host/m1-provider.json',
                '--sdk', '/config/host/rx_external_adapter.py']
        dependencies = ['/opt/rx/python/python', '/config/host/adapter.py', '/config/host/m1-provider.json',
                        '/config/host/rx_external_adapter.py']
        if self.case == 'completion-loss':
            dependencies.append('/config/host/completion_link.py')
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
        # Never invoke Docker.cleanup(): it force-removes all state, including UNKNOWN custody.
        save(self.evidence / 'preservation.json', {'state': 'PRESERVED',
            'containers': self.d.containers, 'volumes': self.d.volumes,
            'network': self.d.network, 'terminal_network': self.d.front_network,
            'case': self.case, 'workspace': str(self.root),
            'limitations': ['CI runner disposal ends container lifetime; archived public evidence is not a resumable installation.']})
