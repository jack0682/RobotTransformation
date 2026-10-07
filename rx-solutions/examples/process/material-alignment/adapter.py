"""Six finite material-alignment commands. FILE_SIMULATION native facts only.

Use the installed external adapter SDK; never issue P/Host commands here. Device
state and append-only effects are independent of the SDK's native request facts.
"""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import uuid


SCHEMA = 'm1/alignment-result'
STEPS = {
    'shelf-seat': ('HELD', 'SEATED', 'shelf.part_supported'),
    'groove-detect': ('SEATED', 'DETECTED', 'vision.groove_detected'),
    'shelf-rotate': ('DETECTED', 'ROTATED', 'shelf.rotation_applied'),
    'alignment-check': ('ROTATED', 'ALIGNED', 'shelf.aligned_stopped'),
    'fixed-regrasp': ('ALIGNED', 'REGRASPED', 'gripper.part_regrasped'),
    'ft-seat-check': ('REGRASPED', 'COMPLETE', 'ft.part_seated'),
}
PARAMETERS = {
    **{k: ('TEXT', 'unitless') for k in
       ('material_model', 'robot_id', 'gripper_channel', 'shelf_id', 'vision_id', 'ft_id')},
    'groove_found': ('BOOLEAN', 'unitless'),
    'groove_angle_deg': ('NUMBER', 'deg'),
    'alignment_tolerance_deg': ('NUMBER', 'deg'),
    'fixed_orientation': ('VECTOR', 'unitless'),
    'ft_force_n': ('NUMBER', 'N'), 'ft_min_n': ('NUMBER', 'N'), 'ft_max_n': ('NUMBER', 'N'),
    'timeout_s': ('NUMBER', 's'),
}
SOURCES = {'ready', 'sim/ready', 'shelf.occupied', 'shelf.stopped', 'gripper.part_held',
           'ft.part_seated', 'vision.result_available', 'vision.groove_detected'}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                      ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= 1_048_576,
            'bounded regular simulation record required')
    return json.loads(path.read_bytes())


def sync_directory(root):
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(root, state):
    target = root / 'state.json'
    require(not target.is_symlink(), 'simulation state symlink refused')
    temporary = root / ('.state-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(encoded(state))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        sync_directory(root)
    finally:
        temporary.unlink(missing_ok=True)


def quantity(value, kind, unit):
    require(set(value) == {'value', 'frame'} and value['frame'] is None,
            'unframed resolved parameter required')
    q = value['value']
    require(set(q) == {'unit', 'data'} and q['unit'] == unit, 'parameter unit differs')
    data = q['data']
    require(data['kind'] == kind, 'parameter type differs')
    def number(span):
        result = span['min']
        require(set(span) == {'min', 'max'} and type(result) in (int, float)
                and type(span['max']) in (int, float) and math.isfinite(result)
                and math.isfinite(span['max']) and result == span['max'], 'finite concrete value required')
        return result
    if kind == 'NUMBER':
        require(set(data) == {'kind', 'range'}, 'number shape differs')
        return number(data['range'])
    if kind == 'VECTOR':
        require(set(data) == {'kind', 'ranges'}, 'vector shape differs')
        return [number(span) for span in data['ranges']]
    require(set(data) == {'kind', 'value'}, 'scalar shape differs')
    require(type(data['value']) is (str if kind == 'TEXT' else bool), 'scalar type differs')
    return data['value']


def canonical_uuid(value):
    require(isinstance(value, str) and str(uuid.UUID(value)) == value, 'canonical UUID required')


def validate_reference(ref):
    require(set(ref) == {'catalog', 'id', 'revision', 'digest'}, 'object reference shape differs')
    canonical_uuid(ref['catalog'])
    canonical_uuid(ref['id'])
    require(isinstance(ref['revision'], str) and ref['revision'].isdigit()
            and int(ref['revision']) > 0, 'positive object revision required')
    require(isinstance(ref['digest'], str) and len(ref['digest']) == 64
            and all(c in '0123456789abcdef' for c in ref['digest']), 'object digest differs')


def configuration(path):
    value = read(Path(path))
    require(set(value) == {'schema', 'environment', 'state_directory', 'material_models',
                          'robot_id', 'new_material_channel', 'other_channel',
                          'shelf_id', 'vision_id', 'ft_id'}, 'configuration shape differs')
    require(value['schema'] == 'rx.material-alignment-simulation.v1'
            and value['environment'] == 'FILE_SIMULATION', 'simulation configuration required')
    require(value['new_material_channel'] != value['other_channel'], 'two distinct channels required')
    require(type(value['material_models']) is list and value['material_models']
            and all(type(v) is str and v for v in value['material_models']), 'model identities required')
    for key in ('robot_id', 'new_material_channel', 'other_channel', 'shelf_id', 'vision_id', 'ft_id'):
        require(type(value[key]) is str and value[key], 'equipment identity required')
    root = Path(value['state_directory'])
    require(root.is_absolute() and root.is_dir() and not root.is_symlink()
            and root.resolve() == root and root.stat().st_uid == os.getuid(),
            'explicit owned real simulation directory required')
    return value


def initialize(config):
    """Explicit installation-only initialization. Never called by observe/execute."""
    root = Path(config['state_directory'])
    require(not (root / 'state.json').exists() and not (root / 'effects.jsonl').exists()
            and not (root / 'state.lock').exists(), 'existing simulation scene cannot be reset')
    descriptor = os.open(root / 'state.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    state = {'schema': 'rx.material-alignment-state.v1', 'environment': 'FILE_SIMULATION',
             'configuration_digest': digest(config), 'phase': 'HELD', 'identity': None,
             'parameters': None, 'pending': None, 'operations': [], 'shelf_occupied': False,
             'shelf_stopped': True, 'shelf_angle_deg': 0, 'groove': None, 'alignment': None,
             'ft': None, 'robot_orientation': None, 'robot_location': 'INITIAL_HELD_MATERIAL',
             'channels': {config['new_material_channel']: {'holding': True, 'role': 'NEW_MATERIAL'},
                          config['other_channel']: {'holding': False, 'role': 'OTHER_UNTOUCHED'}}}
    save(root, state)


class Adapter:
    def __init__(self, config, sdk):
        self.config, self.sdk = config, sdk
        self.root = Path(config['state_directory'])

    def state(self):
        state = read(self.root / 'state.json')
        require(state['schema'] == 'rx.material-alignment-state.v1'
                and state['environment'] == 'FILE_SIMULATION'
                and state['configuration_digest'] == digest(self.config), 'scene identity differs')
        return state

    def inputs(self, envelope, correlation):
        require(set(envelope) == {'schema', 'inputs', 'templates_digest', 'candidate', 'slot',
                                 'node', 'task', 'primitive', 'values', 'done',
                                 'on_failure', 'on_unknown'}, 'common envelope shape differs')
        require(envelope['schema'] == 'rx.workflow-parameters.v2'
                and envelope['on_failure'] == 'STOP'
                and envelope['on_unknown'] == 'HOLD_AND_RECONCILE', 'common envelope differs')
        primitive = envelope['primitive']
        require(primitive in STEPS, 'undeclared primitive')
        require(envelope['done'] == {'observation': STEPS[primitive][2],
                'equals': {'unit': 'unitless', 'data': {'kind': 'BOOLEAN', 'value': True}}},
                'done observation differs')
        require(set(envelope['values']) == set(PARAMETERS), 'exact parameter set required')
        params = {key: quantity(envelope['values'][key], *spec) for key, spec in PARAMETERS.items()}
        require(params['material_model'] in self.config['material_models'], 'unsupported material model')
        for key in ('robot_id', 'shelf_id', 'vision_id', 'ft_id'):
            require(params[key] == self.config[key], 'equipment identity differs: ' + key)
        require(params['gripper_channel'] == self.config['new_material_channel'], 'new-material channel differs')
        require(0 <= params['groove_angle_deg'] <= 360 and 0 < params['alignment_tolerance_deg'] <= 180,
                'simulation angle/tolerance invalid')
        orientation = params['fixed_orientation']
        require(len(orientation) == 4 and abs(sum(x*x for x in orientation)-1) < 1e-9,
                'normalized fixed orientation required')
        require(0 <= params['ft_min_n'] <= params['ft_max_n'] and params['ft_force_n'] >= 0,
                'simulation force bounds invalid')
        require(0 < params['timeout_s'] <= 60, 'finite simulation timeout invalid')
        require(set(correlation) == {'operation', 'invocation', 'selection'}, 'native correlation differs')
        canonical_uuid(correlation['operation'])
        canonical_uuid(correlation['invocation'])
        selected = correlation['selection']
        canonical_uuid(selected['run'])
        canonical_uuid(selected['part'])
        validate_reference(selected['object'])
        require(type(envelope['candidate']) is int and envelope['candidate'] >= 0
                and type(envelope['slot']) is int and envelope['slot'] >= 0
                and selected['candidate'] == envelope['candidate']
                and selected['slot'] == envelope['slot'] and selected['node'] == envelope['node'],
                'native input selection differs')
        # Node/parameter/intent vary per operation; the material and approval selection do not.
        identity = {key: copy.deepcopy(selected[key]) for key in
                    ('run', 'part', 'object', 'candidate', 'slot')}
        for key in ('publication', 'policy_digest', 'configuration_digest', 'object_values_digest',
                    'ordinal', 'slot_ordinal', 'authority_generation'):
            if key in selected:
                identity[key] = copy.deepcopy(selected[key])
        identity['inputs'] = envelope['inputs']
        identity['templates_digest'] = envelope['templates_digest']
        return primitive, params, identity

    def execute(self, envelope, correlation):
        # Reject malformed input/identity before opening any mutable device file.
        primitive, params, identity = self.inputs(envelope, correlation)
        descriptor = os.open(self.root / 'state.lock', os.O_RDWR | os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = self.state()
            require(before['pending'] is None, 'unfinished native state must be preserved')
            require(correlation['operation'] not in before['operations'], 'original operation cannot be repeated')
            require(before['phase'] == STEPS[primitive][0], 'simulation action order differs')
            require(before['identity'] is None or before['identity'] == identity, 'original material/selection differs')
            require(before['parameters'] is None or before['parameters'] == params, 'original task parameters differ')
            after = copy.deepcopy(before)
            after['identity'], after['parameters'] = identity, params
            selected_channel = after['channels'][params['gripper_channel']]
            facts, status = {}, 0
            if primitive == 'shelf-seat':
                require(selected_channel['holding'] and not after['shelf_occupied'], 'initial support differs')
                after['robot_orientation'] = params['fixed_orientation']
                after['robot_location'] = params['shelf_id']
                after['shelf_occupied'] = True
                selected_channel['holding'] = False
                facts = {'support_transfer': ['NEW_MATERIAL_GRIPPER', 'SHELF'],
                         'gripper_open_after_support': True, 'shelf_occupied': True}
            elif primitive == 'groove-detect':
                require(after['shelf_occupied'] and after['shelf_stopped'], 'shelf detection support differs')
                after['groove'] = {'found': params['groove_found'], 'angle_deg': params['groove_angle_deg']
                                  if params['groove_found'] else None, 'vision_id': params['vision_id'],
                                  'operation': correlation['operation'], 'object': identity['object']}
                facts = copy.deepcopy(after['groove'])
                if not params['groove_found']:
                    status = 10
            elif primitive == 'shelf-rotate':
                groove = after['groove']
                require(after['shelf_occupied'] and groove and groove['found']
                        and groove['object'] == identity['object'], 'matching groove evidence required')
                after['shelf_angle_deg'] = (-groove['angle_deg']) % 360
                after['shelf_stopped'] = True
                facts = {'actuator': 'ROTATING_SHELF', 'shelf_id': params['shelf_id'],
                         'source_detection_operation': groove['operation'],
                         'rotation_deg': after['shelf_angle_deg'], 'stopped': True,
                         'robot_orientation_unchanged': after['robot_orientation']}
            elif primitive == 'alignment-check':
                require(after['shelf_occupied'] and after['groove'], 'matching shelf evidence required')
                residual = (after['groove']['angle_deg'] + after['shelf_angle_deg']) % 360
                error = min(residual, 360-residual)
                aligned = after['shelf_stopped'] and error <= params['alignment_tolerance_deg']
                after['alignment'] = {'aligned': aligned, 'stopped': after['shelf_stopped'],
                                      'error_deg': error, 'operation': correlation['operation'],
                                      'object': identity['object'], 'shelf_id': params['shelf_id']}
                facts = copy.deepcopy(after['alignment'])
                if not aligned:
                    status = 11
            elif primitive == 'fixed-regrasp':
                proof = after['alignment']
                require(proof and proof['aligned'] and proof['stopped']
                        and proof['object'] == identity['object'] and after['shelf_stopped']
                        and after['shelf_occupied'] and not selected_channel['holding'],
                        'matching aligned/stopped shelf evidence required')
                require(after['robot_orientation'] == params['fixed_orientation']
                        and after['robot_location'] == params['shelf_id'], 'fixed pose differs')
                selected_channel['holding'] = True
                facts = {'robot_id': params['robot_id'], 'channel': params['gripper_channel'],
                         'orientation': after['robot_orientation'],
                         'fixed_location': after['robot_location'], 'pose_basis': 'SYMBOLIC_FILE_SIMULATION',
                         'source_alignment_operation': proof['operation'], 'shelf_occupied': True}
            else:
                require(selected_channel['holding'] and after['shelf_occupied'], 'regrasp support differs')
                seated = params['ft_min_n'] <= params['ft_force_n'] <= params['ft_max_n']
                after['ft'] = {'seated': seated, 'force_n': params['ft_force_n'],
                               'ft_id': params['ft_id'], 'channel': params['gripper_channel'],
                               'object': identity['object'], 'operation': correlation['operation']}
                if seated:
                    after['shelf_occupied'] = False
                else:
                    status = 12
                facts = {**after['ft'], 'shelf_occupied': after['shelf_occupied']}
            after['phase'] = STEPS[primitive][1] if status == 0 else 'KNOWN_FAILURE'
            after['operations'].append(correlation['operation'])
            pending = copy.deepcopy(before)
            pending['pending'] = copy.deepcopy(correlation)
            save(self.root, pending)
            # A crash between these writes leaves explicit uncertainty. No replay/repair here.
            event = {'environment': 'FILE_SIMULATION', **copy.deepcopy(correlation),
                     'primitive': primitive, 'node': envelope['node'], 'task': envelope['task'],
                     'parameters': copy.deepcopy(envelope['values']), 'facts': facts,
                     'before_digest': digest(before), 'after_digest': digest(after),
                     'status_schema': SCHEMA, 'status': status}
            log = os.open(self.root / 'effects.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
            with os.fdopen(log, 'ab') as stream:
                stream.write(encoded(event) + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
            save(self.root, after)
            return {'status_schema': SCHEMA, 'status': status}
        finally:
            os.close(descriptor)

    def observe(self, sources):
        require(set(sources) <= SOURCES, 'undeclared source')
        state = self.state()
        values = {'ready': state['pending'] is None, 'sim/ready': state['pending'] is None,
                  'shelf.occupied': state['shelf_occupied'], 'shelf.stopped': state['shelf_stopped'],
                  'gripper.part_held': state['channels'][self.config['new_material_channel']]['holding'],
                  'ft.part_seated': bool(state['ft'] and state['ft']['seated']),
                  'vision.result_available': state['groove'] is not None,
                  'vision.groove_detected': bool(state['groove'] and state['groove']['found'])}
        # These are actual reads of current file-device state, not retimestamped camera samples.
        return {source: self.sdk.sample({'boolean': values[source]}) for source in sources}

    def custody(self):
        state = self.state()
        stable = state['shelf_occupied'] or state['channels'][self.config['new_material_channel']]['holding']
        complete = state['pending'] is None
        return {'no_pending_commands': complete, 'control_available': complete,
                'support_stable': stable, 'safe_to_drop': complete and stable and state['shelf_stopped']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--sdk')
    parser.add_argument('--initialize', action='store_true')
    parser.add_argument('mode', nargs='?')
    parser.add_argument('native_directory', nargs='?')
    args = parser.parse_args()
    config = configuration(args.config)
    if args.initialize:
        require(args.mode is None and args.native_directory is None, 'initialization cannot dispatch')
        initialize(config)
        return
    require(args.sdk is not None and args.mode in ('execute', 'lookup', 'observe')
            and args.native_directory is not None, 'Host-owned external SDK invocation required')
    spec = importlib.util.spec_from_file_location('rx_external_adapter', args.sdk)
    sdk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sdk)
    sdk.serve(Adapter(config, sdk))


if __name__ == '__main__':
    main()
