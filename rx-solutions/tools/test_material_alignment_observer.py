#!/usr/bin/env python3
"""Linux process comparison for the package observer; not Host/Run acceptance.

RX_M1_OBSERVER_BINARY may select a previously built candidate. Otherwise this
test compiles observer.cpp with the installed Linux g++/nlohmann/OpenSSL headers.
RX_M1_OBSERVER_DIAGNOSTICS optionally saves all five latency samples per provider.
No timing threshold or successful-retry selection is used here.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


SOURCE = Path(__file__).resolve().parents[1] / 'examples/process/material-alignment'
SDK = Path(__file__).resolve().parents[1] / 'deployment/external-adapters/rx_external_adapter.py'
SOURCES = ['ready', 'sim/ready', 'shelf.occupied', 'shelf.stopped', 'gripper.part_held',
           'ft.part_seated', 'vision.result_available', 'vision.groove_detected']
PYTHON = str(Path(sys.executable).resolve())


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def identifier():
    return str(uuid.uuid4())


def now():
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    return {'clock_id': 'linux-boottime/' + boot,
            'ticks_ns': str(time.clock_gettime_ns(time.CLOCK_BOOTTIME))}


def resolved(spec, value):
    kind = spec['value_type']
    if kind == 'NUMBER':
        data = {'kind': kind, 'range': {'min': value, 'max': value}}
    elif kind == 'VECTOR':
        data = {'kind': kind, 'ranges': [{'min': item, 'max': item} for item in value]}
    else:
        data = {'kind': kind, 'value': value}
    return {'value': {'unit': spec['unit'], 'data': data}, 'frame': None}


@unittest.skipUnless(sys.platform == 'linux', 'observer/process comparison requires isolated Linux')
class MaterialAlignmentObserver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix='rx-m1-observer-build-')
        cls.addClassCleanup(cls.build.cleanup)
        prepared = os.environ.get('RX_M1_OBSERVER_BINARY')
        cls.binary = Path(prepared).resolve() if prepared else Path(cls.build.name) / 'observer'
        if not prepared:
            result = subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                                     str(SOURCE / 'observer.cpp'), '-o', str(cls.binary), '-lcrypto'],
                                    capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise AssertionError('Linux observer build failed:\n' + result.stdout + result.stderr)
        if not cls.binary.is_file() or not os.access(cls.binary, os.X_OK):
            raise AssertionError('an actual compiled observer executable is required')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rx-m1-observer-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.device = self.root / 'device'
        self.device.mkdir()
        self.native = self.root / 'native'
        self.native.mkdir()
        self.session = identifier()
        (self.native / 'device-session').write_text(self.session)
        config = json.loads((SOURCE / 'config.example.json').read_bytes())
        config['state_directory'] = str(self.device)
        self.config = self.root / 'config.json'
        self.config.write_bytes(encoded(config))
        initialized = subprocess.run([PYTHON, '-I', '-S', '-B', str(SOURCE / 'adapter.py'),
                                      '--config', str(self.config), '--initialize'],
                                     capture_output=True, timeout=10)
        self.assertEqual(initialized.returncode, 0, initialized.stderr.decode(errors='replace'))
        self.scenario = json.loads((SOURCE / 'scenario.json').read_bytes())
        self.values = {key: resolved(spec, spec['default'])
                       for key, spec in self.scenario['parameters'].items()}
        self.object = {'catalog': identifier(), 'id': identifier(), 'revision': '1', 'digest': 'a'*64}
        self.selection = {'run': identifier(), 'part': identifier(), 'object': self.object,
                          'candidate': 0, 'slot': 0, 'publication': identifier(),
                          'policy_digest': 'b'*64, 'configuration_digest': 'c'*64,
                          'object_values_digest': 'd'*64, 'ordinal': '1', 'slot_ordinal': '1',
                          'authority_generation': '1'}

    def arguments(self, provider, mode='observe', adapter=None):
        adapter = str(adapter or SOURCE / 'adapter.py')
        common = ['--config', str(self.config), '--sdk', str(SDK), mode, str(self.native)]
        if provider == 'python':
            return [PYTHON, '-I', '-S', '-B', adapter, *common]
        return [str(self.binary), '--python', PYTHON, '--adapter', adapter, *common]

    def request(self, sources=None):
        return {'schema': 'rx.external-process-channel.v1', 'challenge': identifier(),
                'profile_digest': 'e'*64, 'device_session': self.session, 'now': now(),
                'dispatch': None, 'sources': SOURCES if sources is None else sources}

    def invoke(self, provider, request, mode='observe', raw=None):
        return subprocess.run(self.arguments(provider, mode),
                              input=encoded(request) if raw is None else raw,
                              capture_output=True, timeout=10)

    def files(self):
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob('*') if p.is_file() and not p.is_symlink()}

    def snapshot(self, provider, request):
        response = self.invoke(provider, request)
        self.assertEqual(response.returncode, 0, response.stderr.decode(errors='replace'))
        value = json.loads(response.stdout)
        received = now()
        self.assertEqual(set(value), {'schema', 'challenge', 'profile_digest', 'device_session',
            'observed_at', 'uncertainty_ns', 'no_pending_commands', 'control_available',
            'support_stable', 'safe_to_drop', 'samples'})
        self.assertEqual(value['schema'], 'rx.external-native-snapshot.v1')
        for key in ('challenge', 'profile_digest', 'device_session'):
            self.assertEqual(value[key], request[key])
        self.assertEqual(value['observed_at']['clock_id'], request['now']['clock_id'])
        self.assertEqual(value['uncertainty_ns'], '0')
        self.assertEqual(set(value['samples']), set(request['sources']))
        for sample in value['samples'].values():
            self.assertEqual(set(sample), {'value', 'acquired_at', 'uncertainty_ns',
                                          'quality_good', 'origin_age_bounded'})
            self.assertIs(type(sample['value']['boolean']), bool)
            self.assertEqual(sample['uncertainty_ns'], '0')
            self.assertTrue(sample['quality_good'] and sample['origin_age_bounded'])
            self.assertEqual(sample['acquired_at']['clock_id'], request['now']['clock_id'])
            self.assertLessEqual(int(request['now']['ticks_ns']), int(sample['acquired_at']['ticks_ns']))
            self.assertLessEqual(int(sample['acquired_at']['ticks_ns']), int(value['observed_at']['ticks_ns']))
        self.assertLessEqual(int(value['observed_at']['ticks_ns']), int(received['ticks_ns']))
        return value

    def equivalent(self):
        request = self.request()
        before = self.files()
        snapshots = [self.snapshot(provider, request) for provider in ('python', 'observer')]
        self.assertEqual(before, self.files(), 'passive observation changed device/native files')
        for value in snapshots:
            value.pop('observed_at')
            for sample in value['samples'].values():
                sample.pop('acquired_at')
        self.assertEqual(*snapshots)
        return snapshots[0]

    def native_request(self, primitive):
        step = next(s for s in self.scenario['steps'] if s['id'] == primitive)
        envelope = {'schema': 'rx.workflow-parameters.v2',
            'inputs': {'schema_id': 'rx.execution-input-closure.v2', 'sha256': 'f'*64, 'size_bytes': '1'},
            'templates_digest': '1'*64, 'candidate': 0, 'slot': 0, 'node': primitive,
            'task': primitive, 'primitive': primitive, 'values': copy.deepcopy(self.values),
            'done': {'observation': step['done'], 'property': {**self.object, 'id': identifier()},
                     'equals': {'unit': 'unitless', 'data': {'kind': 'BOOLEAN', 'value': True}}},
            'on_failure': 'STOP', 'on_unknown': 'HOLD_AND_RECONCILE'}
        data = encoded(envelope)
        selection = {**self.selection, 'node': primitive, 'intent_digest': '2'*64,
            'parameter': {'schema_id': 'rx.workflow-parameters.v2',
                          'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': str(len(data))}}
        request = self.request()
        stamp = now()
        request['dispatch'] = {'operation': identifier(), 'invocation': identifier(),
            'intent': {}, 'input': {'parameters': list(data), 'binding': {'selection': selection}},
            'device_session': self.session, 'admitted_at': stamp,
            'expires_at': {**stamp, 'ticks_ns': str(int(stamp['ticks_ns']) + 10_000_000_000)}}
        return request

    def execute(self, primitive):
        request = self.native_request(primitive)
        # Deliberately noncanonical channel bytes show delegation does not reserialize stdin.
        raw = json.dumps(request, indent=1).encode()
        result = self.invoke('observer', request, 'execute', raw=raw)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        entry, completion = map(json.loads, result.stdout.splitlines())
        self.assertEqual(entry['request_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(entry['operation'], request['dispatch']['operation'])
        self.assertEqual(entry['invocation'], request['dispatch']['invocation'])
        self.assertEqual(completion['capture']['native_id'], entry['invocation'])
        stored = json.loads((self.native / entry['operation'] / 'request.json').read_bytes())
        self.assertEqual(stored['dispatch'], request['dispatch'])
        return request, completion

    def test_actual_six_command_states_match_python_observer_without_mutation(self):
        initial = self.equivalent()
        self.assertFalse(initial['samples']['vision.result_available']['value']['boolean'])
        self.assertFalse(initial['samples']['vision.groove_detected']['value']['boolean'])
        for step in self.scenario['steps']:
            _, result = self.execute(step['id'])
            self.assertEqual(result['capture']['status'], 0)
            observed = self.equivalent()
            if step['id'] == 'groove-detect':
                self.assertTrue(observed['samples']['vision.result_available']['value']['boolean'])
                self.assertTrue(observed['samples']['vision.groove_detected']['value']['boolean'])
        self.assertFalse(observed['samples']['shelf.occupied']['value']['boolean'])
        self.assertTrue(observed['samples']['ft.part_seated']['value']['boolean'])
        self.assertTrue(observed['no_pending_commands'] and observed['safe_to_drop'])

    def test_completed_miss_matches_available_true_detected_false(self):
        self.values['groove_found'] = resolved(self.scenario['parameters']['groove_found'], False)
        self.execute('shelf-seat')
        _, result = self.execute('groove-detect')
        self.assertEqual(result['capture']['status'], 10)
        observed = self.equivalent()
        self.assertTrue(observed['samples']['vision.result_available']['value']['boolean'])
        self.assertFalse(observed['samples']['vision.groove_detected']['value']['boolean'])
        self.assertTrue(observed['samples']['shelf.occupied']['value']['boolean'])

    def test_pending_device_and_live_native_owner_keep_same_custody(self):
        operation = self.native / identifier()
        operation.mkdir()
        with (operation / 'owner.lock').open('xb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertFalse(self.equivalent()['no_pending_commands'])
        self.assertTrue(self.equivalent()['no_pending_commands'])
        path = self.device / 'state.json'
        state = json.loads(path.read_bytes())
        state['pending'] = {'operation': identifier()}  # Explicit interrupted-write fixture only.
        path.write_bytes(encoded(state))
        observed = self.equivalent()
        self.assertFalse(observed['no_pending_commands'])
        self.assertFalse(observed['control_available'])
        self.assertFalse(observed['safe_to_drop'])
        self.assertFalse(observed['samples']['ready']['value']['boolean'])

    def wait_for_shared_state_lock(self, process):
        inode = str((self.device / 'state.lock').stat().st_ino)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            self.assertIsNone(process.poll(), 'observer exited before writer released its state lock')
            self.assertFalse(select.select([process.stdout], [], [], 0)[0],
                             'observer emitted a premature snapshot during the writer transaction')
            for line in Path('/proc/locks').read_text().splitlines():
                fields = line.split()
                if '->' not in fields or 'FLOCK' not in fields or 'READ' not in fields:
                    continue
                position = fields.index('READ')
                if (fields[position + 1] == str(process.pid)
                        and fields[position + 2].rsplit(':', 1)[-1] == inode):
                    return
            time.sleep(.005)
        self.fail('observer did not reach the shared state lock within the test setup bound')

    def coherent_read_case(self, commit):
        state_path = self.device / 'state.json'
        initial = json.loads(state_path.read_bytes())
        pending = copy.deepcopy(initial)
        pending['pending'] = {'operation': identifier()}
        pending['channels']['new-material']['holding'] = False
        pending['shelf_occupied'] = True
        readers = []
        try:
            with (self.device / 'state.lock').open('rb') as writer:
                fcntl.flock(writer, fcntl.LOCK_EX)
                # Isolated write-boundary fixture, not a fabricated Host/Run outcome.
                state_path.write_bytes(encoded(pending))
                for provider in ('python', 'observer'):
                    request = self.request()
                    process = subprocess.Popen(self.arguments(provider), stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    readers.append((provider, request, process))
                    process.stdin.write(encoded(request))
                    process.stdin.close()
                    process.stdin = None
                for _, _, process in readers:
                    self.wait_for_shared_state_lock(process)
                if commit:
                    final = copy.deepcopy(pending)
                    final['pending'] = None
                    final['channels']['new-material']['holding'] = True
                    state_path.write_bytes(encoded(final))
                expected = self.files()
                released_at = now()
                fcntl.flock(writer, fcntl.LOCK_UN)
            for provider, request, process in readers:
                output, error = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, (provider, error.decode(errors='replace')))
                snapshot = json.loads(output)
                for key in ('challenge', 'profile_digest', 'device_session'):
                    self.assertEqual(snapshot[key], request[key])
                for key in ('ready', 'sim/ready', 'gripper.part_held'):
                    self.assertEqual(snapshot['samples'][key]['value']['boolean'], commit)
                self.assertEqual(snapshot['no_pending_commands'], commit)
                self.assertEqual(snapshot['control_available'], commit)
                for sample in snapshot['samples'].values():
                    self.assertGreaterEqual(int(sample['acquired_at']['ticks_ns']),
                                            int(released_at['ticks_ns']))
            self.assertEqual(expected, self.files(), 'passive readers mutated state/native records')
            self.assertFalse((self.device / 'effects.jsonl').exists())
        finally:
            for _, _, process in readers:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=10)

    def test_writer_commit_hides_transient_pending_marker_from_both_passive_readers(self):
        self.coherent_read_case(commit=True)

    def test_writer_exit_retains_persisted_pending_marker_in_both_passive_readers(self):
        self.coherent_read_case(commit=False)

    def test_original_lookup_returns_same_capture_and_execute_is_not_replayed(self):
        request, completion = self.execute('shelf-seat')
        original = self.files()
        request['challenge'] = identifier()
        request['now'] = now()
        result = self.invoke('observer', request, 'lookup')
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertEqual(json.loads(result.stdout)['capture'], completion['capture'])
        self.assertEqual(original, self.files())
        refused = self.invoke('observer', request, 'execute')
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(original, self.files())
        self.assertEqual(len((self.device / 'effects.jsonl').read_bytes().splitlines()), 1)

    def test_execv_retains_original_pid_group_payload_and_fixed_argv(self):
        probe = self.root / 'delegation_probe.py'
        probe.write_text('import json,os,sys\n'
            'raw=sys.stdin.buffer.read()\n'
            'print(json.dumps({"pid":os.getpid(),"group":os.getpgrp(),'
            '"raw":raw.hex(),"argv":sys.argv[1:]}))\n')
        raw = b' { "unchanged channel": [1, 2, 3] } \n'
        before = self.files()
        for mode in ('execute', 'lookup'):
            process = subprocess.Popen(self.arguments('observer', mode, probe),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True)
            output, error = process.communicate(raw, timeout=10)
            self.assertEqual(process.returncode, 0, error.decode(errors='replace'))
            result = json.loads(output)
            self.assertEqual(result['pid'], process.pid)
            self.assertEqual(result['group'], process.pid)
            self.assertEqual(result['raw'], raw.hex())
            self.assertEqual(result['argv'], ['--config', str(self.config), '--sdk', str(SDK),
                                               mode, str(self.native)])
        self.assertEqual(before, self.files())

    def test_invalid_protocol_sources_and_symlinks_fail_without_observation_output(self):
        original = self.request()
        malformed = []
        for key, value in [('sources', ['not/declared']), ('dispatch', {}),
                           ('device_session', identifier()), ('challenge', 'not-a-uuid'),
                           ('schema', 'wrong/schema')]:
            changed = copy.deepcopy(original)
            changed[key] = value
            malformed.append(changed)
        before = self.files()
        for request in malformed:
            for provider in ('python', 'observer'):
                result = self.invoke(provider, request)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'')
        for raw in [b'x' * (1_048_576 + 1),
                    encoded(original)[:-1] + b',"challenge":"duplicate"}']:
            result = self.invoke('observer', original, raw=raw)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'')
        self.assertEqual(before, self.files())
        state = self.device / 'state.json'
        state.rename(self.device / 'saved-state.json')
        state.symlink_to(self.device / 'saved-state.json')
        for provider in ('python', 'observer'):
            self.assertNotEqual(self.invoke(provider, original).returncode, 0)
        self.assertTrue(state.is_symlink())

    def test_configuration_identity_mismatch_does_not_emit_cached_samples(self):
        self.equivalent()
        state = self.device / 'state.json'
        value = json.loads(state.read_bytes())
        value['configuration_digest'] = '0'*64
        state.write_bytes(encoded(value))
        before = self.files()
        for provider in ('python', 'observer'):
            result = self.invoke(provider, self.request())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'')
        self.assertEqual(before, self.files())

    def test_five_passive_latency_samples_are_reported_without_a_pass_threshold(self):
        diagnostics = {'schema': 'rx.m1-observer-latency-diagnostic.v1',
            'os': platform.system(), 'architecture': platform.machine(),
            'observer_sha256': hashlib.sha256(self.binary.read_bytes()).hexdigest(),
            'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (SOURCE / 'observer.cpp', SOURCE / 'adapter.py', SDK)},
            'samples': {'python': [], 'observer': []},
            'scope': 'Five actual passive process calls per implementation, no retries or timing pass threshold; not Host freshness acceptance.'}
        before = self.files()
        for index in range(5):
            for provider in ('python', 'observer'):
                request = self.request()
                started = time.perf_counter_ns()
                try:
                    result = self.invoke(provider, request)
                except subprocess.TimeoutExpired:
                    diagnostics['samples'][provider].append({'index': index + 1,
                        'elapsed_ns': time.perf_counter_ns() - started, 'returncode': None,
                        'error': 'passive process did not exit within the test invocation timeout'})
                    continue
                elapsed = time.perf_counter_ns() - started
                sample = {'index': index + 1, 'elapsed_ns': elapsed, 'returncode': result.returncode}
                if result.returncode == 0:
                    try:
                        snapshot = json.loads(result.stdout)
                        received = now()
                        sample['acquired_at'] = snapshot['samples']['ready']['acquired_at']
                        sample['observed_at'] = snapshot['observed_at']
                        sample['source_age_at_parent_receive_ns'] = int(received['ticks_ns']) - int(sample['acquired_at']['ticks_ns'])
                    except (ValueError, KeyError, TypeError):
                        sample['error'] = 'passive process returned an invalid snapshot'
                else:
                    sample['error'] = result.stderr.decode(errors='replace')[-1000:]
                diagnostics['samples'][provider].append(sample)
        target = os.environ.get('RX_M1_OBSERVER_DIAGNOSTICS')
        if target:
            with Path(target).open('xb') as stream:
                stream.write(encoded(diagnostics))
        print(json.dumps(diagnostics, sort_keys=True))
        self.assertTrue(all(row['returncode'] == 0 and 'error' not in row
                            for rows in diagnostics['samples'].values() for row in rows))
        self.assertEqual(before, self.files())


if __name__ == '__main__':
    unittest.main()
