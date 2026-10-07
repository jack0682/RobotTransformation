#!/usr/bin/env python3
"""Linux-only finite provider checks; not P/Executor/Host or UI acceptance evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import uuid


SOURCE = Path(__file__).resolve().parents[1] / 'examples/process/material-alignment'


def identifier():
    return str(uuid.uuid4())


@unittest.skipUnless(sys.platform == 'linux', 'isolated Linux simulation only')
class MaterialAlignment(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        spec = importlib.util.spec_from_file_location('material_alignment', SOURCE / 'adapter.py')
        self.provider = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.provider)
        self.config = json.loads((SOURCE / 'config.example.json').read_bytes())
        self.config['state_directory'] = str(self.root)
        config_path = self.root / 'config.json'
        config_path.write_text(json.dumps(self.config))
        self.config = self.provider.configuration(config_path)
        self.provider.initialize(self.config)
        self.adapter = self.provider.Adapter(self.config, types.SimpleNamespace(sample=lambda value: value))
        self.scenario = json.loads((SOURCE / 'scenario.json').read_bytes())
        self.selection = {
            'run': identifier(), 'part': identifier(), 'candidate': 0, 'slot': 0,
            'object': {'catalog': identifier(), 'id': identifier(), 'revision': '1', 'digest': 'a'*64},
            'publication': identifier(), 'policy_digest': 'b'*64,
            'configuration_digest': 'c'*64, 'object_values_digest': 'd'*64,
            'ordinal': '1', 'slot_ordinal': '1', 'authority_generation': '1',
        }
        self.values = {key: self.resolved(p['value_type'], p['unit'], p['default'])
                       for key, p in self.scenario['parameters'].items()}
        self.inputs = {'schema': 'rx.workflow-parameters.v2',
                       'inputs': {'schema_id': 'rx.execution-input-closure.v2', 'sha256': 'e'*64, 'size_bytes': '99'},
                       'templates_digest': 'f'*64, 'candidate': 0, 'slot': 0,
                       'task': 'material-alignment', 'values': self.values,
                       'on_failure': 'STOP', 'on_unknown': 'HOLD_AND_RECONCILE'}
        self.calls = []

    @staticmethod
    def resolved(kind, unit, value):
        data = {'kind': kind}
        if kind == 'NUMBER':
            data['range'] = {'min': value, 'max': value}
        elif kind == 'VECTOR':
            data['ranges'] = [{'min': number, 'max': number} for number in value]
        else:
            data['value'] = value
        return {'value': {'unit': unit, 'data': data}, 'frame': None}

    def override(self, key, value):
        p = self.scenario['parameters'][key]
        self.values[key] = self.resolved(p['value_type'], p['unit'], value)

    def request(self, primitive):
        envelope = copy.deepcopy(self.inputs)
        envelope.update(node=primitive, primitive=primitive,
                        done={'observation': self.provider.STEPS[primitive][2],
                              'equals': {'unit': 'unitless', 'data': {'kind': 'BOOLEAN', 'value': True}}})
        selected = {**copy.deepcopy(self.selection), 'node': primitive,
                    'parameter': {'schema_id': 'rx.workflow-parameters.v2',
                                  'sha256': self.provider.digest(envelope), 'size_bytes': '1'},
                    'intent_digest': '1'*64}
        correlation = {'operation': identifier(), 'invocation': identifier(), 'selection': selected}
        return envelope, correlation

    def execute(self, primitive):
        request = self.request(primitive)
        result = self.adapter.execute(*request)
        self.calls.append(request)
        return result

    def effects(self):
        path = self.root / 'effects.jsonl'
        return [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []

    def unchanged_rejection(self, callback):
        before = (self.root / 'state.json').read_bytes()
        effects = self.effects()
        with self.assertRaises(ValueError):
            callback()
        self.assertEqual(before, (self.root / 'state.json').read_bytes())
        self.assertEqual(effects, self.effects())

    def test_six_commands_preserve_material_channel_and_independent_correlation(self):
        original_other = copy.deepcopy(self.adapter.state()['channels']['other'])
        for step in self.scenario['steps']:
            self.assertEqual(self.execute(step['id']), {'status_schema': 'm1/alignment-result', 'status': 0})
            self.assertEqual(original_other, self.adapter.state()['channels']['other'])
        state, effects = self.adapter.state(), self.effects()
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertTrue(state['channels']['new-material']['holding'])
        self.assertFalse(state['shelf_occupied'])
        self.assertEqual(state['robot_orientation'], [0, 0, 0, 1])
        self.assertEqual(state['shelf_angle_deg'], 265)
        self.assertTrue(state['ft']['seated'])
        self.assertEqual(len(effects), 6)
        self.assertEqual([e['primitive'] for e in effects], list(self.provider.STEPS))
        for event, (envelope, correlation) in zip(effects, self.calls):
            self.assertEqual(event['operation'], correlation['operation'])
            self.assertEqual(event['invocation'], correlation['invocation'])
            self.assertEqual(event['selection'], correlation['selection'])
            self.assertEqual(event['parameters'], envelope['values'])
        for previous, following in zip(effects, effects[1:]):
            self.assertEqual(previous['after_digest'], following['before_digest'])
        self.assertEqual(effects[2]['facts']['source_detection_operation'], effects[1]['operation'])
        self.assertEqual(effects[2]['facts']['actuator'], 'ROTATING_SHELF')
        self.assertEqual(effects[4]['facts']['source_alignment_operation'], effects[3]['operation'])
        self.assertEqual(effects[-1]['after_digest'], self.provider.digest(state))

    def test_missed_groove_is_known_failure_with_shelf_occupied_no_downstream_effect(self):
        self.override('groove_found', False)
        self.execute('shelf-seat')
        self.assertEqual(self.execute('groove-detect')['status'], 10)
        state = self.adapter.state()
        self.assertEqual(state['phase'], 'KNOWN_FAILURE')
        self.assertTrue(state['shelf_occupied'])
        self.assertFalse(state['channels']['new-material']['holding'])
        self.assertTrue(self.adapter.custody()['support_stable'])
        self.unchanged_rejection(lambda: self.execute('shelf-rotate'))
        self.assertEqual(len(self.effects()), 2)
        self.assertFalse(self.effects()[-1]['facts']['found'])

    def test_wrong_object_channel_order_and_selection_are_rejected(self):
        self.unchanged_rejection(lambda: self.execute('groove-detect'))
        self.override('gripper_channel', 'other')
        self.unchanged_rejection(lambda: self.execute('shelf-seat'))
        self.override('gripper_channel', 'new-material')
        self.execute('shelf-seat')
        original = copy.deepcopy(self.selection)
        self.selection['object']['id'] = identifier()
        self.unchanged_rejection(lambda: self.execute('groove-detect'))
        self.selection = original
        self.selection['part'] = identifier()
        self.unchanged_rejection(lambda: self.execute('groove-detect'))

    def test_type_unit_equipment_and_nonconcrete_values_reject_without_effects(self):
        envelope, correlation = self.request('shelf-seat')
        invalid = copy.deepcopy(envelope)
        invalid['values']['ft_force_n']['value']['unit'] = 'mm'
        self.unchanged_rejection(lambda: self.adapter.execute(invalid, correlation))
        invalid = copy.deepcopy(envelope)
        invalid['values']['groove_angle_deg']['value']['data']['range']['max'] = 96
        self.unchanged_rejection(lambda: self.adapter.execute(invalid, correlation))
        invalid = copy.deepcopy(envelope)
        invalid['values']['robot_id']['value']['data']['value'] = 'other-robot'
        self.unchanged_rejection(lambda: self.adapter.execute(invalid, correlation))
        invalid = copy.deepcopy(envelope)
        invalid['values']['groove_found']['value']['data']['value'] = 1
        self.unchanged_rejection(lambda: self.adapter.execute(invalid, correlation))
        self.assertEqual(self.effects(), [])

    def test_changed_model_and_simulation_angle_are_consumed(self):
        self.override('material_model', 'sim/material-b')
        self.override('groove_angle_deg', 40)
        self.selection['candidate'] = self.inputs['candidate'] = 1
        for primitive in self.provider.STEPS:
            self.execute(primitive)
        self.assertEqual(self.adapter.state()['shelf_angle_deg'], 320)
        self.assertEqual(self.effects()[0]['parameters']['material_model']['value']['data']['value'], 'sim/material-b')

    def test_ft_failure_keeps_shelf_occupancy_and_original_object(self):
        self.override('ft_force_n', 1)
        for primitive in self.provider.STEPS:
            result = self.execute(primitive)
        self.assertEqual(result['status'], 12)
        state = self.adapter.state()
        self.assertEqual(state['phase'], 'KNOWN_FAILURE')
        self.assertTrue(state['shelf_occupied'])
        self.assertEqual(state['ft']['object'], self.selection['object'])
        self.assertTrue(state['channels']['new-material']['holding'])

    def test_alignment_failure_does_not_allow_regrasp(self):
        for primitive in ('shelf-seat', 'groove-detect', 'shelf-rotate'):
            self.execute(primitive)
        state = self.adapter.state()
        state['shelf_angle_deg'] = 0
        self.provider.save(self.root, state)  # Explicit simulated shelf-position fault.
        self.assertEqual(self.execute('alignment-check')['status'], 11)
        self.assertTrue(self.adapter.state()['shelf_occupied'])
        self.unchanged_rejection(lambda: self.execute('fixed-regrasp'))

    def test_original_operation_and_initialization_cannot_replay_or_reset(self):
        self.execute('shelf-seat')
        self.unchanged_rejection(lambda: self.adapter.execute(*self.calls[0]))
        self.unchanged_rejection(lambda: self.provider.initialize(self.config))

    def test_observation_is_passive_and_pending_state_is_not_repaired(self):
        before = (self.root / 'state.json').read_bytes()
        self.assertEqual(self.adapter.observe(['sim/ready']), {'sim/ready': {'boolean': True}})
        self.assertEqual(before, (self.root / 'state.json').read_bytes())
        self.assertEqual(self.effects(), [])
        state = self.adapter.state()
        state['pending'] = self.request('shelf-seat')[1]
        self.provider.save(self.root, state)  # Explicit crash-state injection, not product recovery.
        self.assertFalse(self.adapter.custody()['no_pending_commands'])
        self.assertFalse(self.adapter.observe(['sim/ready'])['sim/ready']['boolean'])
        self.unchanged_rejection(lambda: self.execute('shelf-seat'))


if __name__ == '__main__':
    unittest.main()
