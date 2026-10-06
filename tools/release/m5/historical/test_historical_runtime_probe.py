"""Pure fixtures only: does not import or execute preserved consumer code."""
import copy
from pathlib import Path
import tempfile
import unittest
import uuid
import historical_runtime_probe as p

HERE = Path(__file__).resolve().parent
REQUEST = 'a2084aa1-f414-4d68-81a9-19f92c0303d1'


def composition():
    draft = str(uuid.uuid5(uuid.UUID(REQUEST), 'rx.runtime-skill.draft'))
    return {'status': 'DRAFT_READY_FOR_COMPILER', 'execution_authorized': False,
            'request_id': REQUEST, 'draft_id': draft,
            'compile_input': {'draft': draft, 'cell': 'cell/a', 'source_revision': '1',
                              'binding_revision': '1', 'catalog_digest': '0' * 64,
                              'source': {'schema': 'rx.process-source.v1', 'process': 'historical-client-check'},
                              'bindings': {'skill/1': {'intent': {}}}}}


class HistoricalProbeTests(unittest.TestCase):
    def test_saved_resolved_binding_and_candidate_must_match(self):
        value = composition()
        action = {'host': 'host/a', 'intent': {'target': 'target/a', 'kind': 'PROGRAM', 'resource_set': ['r/a']}}
        value['compile_input']['bindings'] = {'skill/1': action}
        body = value['compile_input']
        saved = {'complete': True, 'missing': [], 'selections': {'skill/1': 'step/a'},
                 'draft': body['draft'], 'cell': 'cell/a', 'source_revision': '1', 'revision': '1',
                 'catalog_digest': '0' * 64, 'origins': {'skill/1': '1' * 64}, 'resolved': body['bindings']}
        catalog = {'catalog_digest': '0' * 64, 'candidates': [{'step': 'step/a', 'step_digest': '1' * 64,
                   'host': 'host/a', 'target': 'target/a', 'kind': 'PROGRAM', 'resources': ['r/a']}]}
        p.binding_receipt(value, saved, catalog, 'step/a')
        for field, replacement in [('complete', False), ('missing', ['skill/1']),
                                   ('selections', {'skill/1': 'step/b'}), ('origins', {'skill/1': '2' * 64}),
                                   ('resolved', {'skill/1': {}}), ('revision', '2')]:
            changed = copy.deepcopy(saved)
            changed[field] = replacement
            with self.assertRaises(ValueError): p.binding_receipt(value, changed, catalog, 'step/a')
        wrong = copy.deepcopy(value)
        wrong['compile_input']['bindings']['skill/1']['host'] = 'wrong'
        changed = copy.deepcopy(saved)
        changed['resolved'] = wrong['compile_input']['bindings']
        with self.assertRaises(ValueError): p.binding_receipt(wrong, changed, catalog, 'step/a')

    def test_same_request_recovery_and_scope(self):
        value = composition()
        p.same_recovery(value, copy.deepcopy(value), REQUEST, 'cell/a', 'step/a')
        for field, replacement in [('source_revision', '2'), ('binding_revision', '2'),
                                   ('catalog_digest', '1' * 64), ('cell', 'cell/b')]:
            changed = copy.deepcopy(value)
            changed['compile_input'][field] = replacement
            with self.assertRaises(ValueError):
                p.same_recovery(value, changed, REQUEST, 'cell/a', 'step/a')

    def test_authority_and_new_uuid_refused(self):
        for field, replacement in [('execution_authorized', True), ('request_id', str(uuid.uuid4())),
                                   ('draft_id', str(uuid.uuid4())), ('status', 'COMPLETED')]:
            value = composition()
            value[field] = replacement
            with self.assertRaises(ValueError):
                p.positive_composition(value, REQUEST, 'cell/a', 'step/a')

    def test_noncanonical_revision_refused(self):
        for replacement in ['0', '01', 1, True, str(2**64)]:
            value = composition()
            value['compile_input']['source_revision'] = replacement
            with self.assertRaises(ValueError):
                p.positive_composition(value, REQUEST, 'cell/a', 'step/a')

    def test_idle_observation_rejects_truncation_and_activity(self):
        value = {'installation': {'id': 'one'}, 'cells': [{'cell': {'value': {'id': 'cell/a'}},
                  'runs': [], 'work': [], 'runs_truncated': False, 'work_truncated': False}]}
        p.idle_cell(value, 'cell/a')
        for field, replacement in [('runs', [{}]), ('work', [{}]), ('runs_truncated', True), ('work_truncated', True)]:
            changed = copy.deepcopy(value)
            changed['cells'][0][field] = replacement
            with self.assertRaises(ValueError):
                p.idle_cell(changed, 'cell/a')

    def test_negative_cannot_admit_or_enter_mutation(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            state = Path(folder)
            p.assert_no_negative_mutation({}, {}, state, REQUEST)
            with self.assertRaises(ValueError):
                p.assert_no_negative_mutation({}, {'new': {}}, state, REQUEST)
            (state / REQUEST).mkdir()
            (state / REQUEST / 'compose-source.request.json').write_text('{}')
            with self.assertRaises(ValueError):
                p.assert_no_negative_mutation({}, {}, state, REQUEST)

    def test_pagination_complete_and_loop_refused(self):
        class Terminal:
            def __init__(self, loop): self.loop, self.calls = loop, 0
            def get(self, route, **query):
                self.calls += 1
                return {'cell': 'cell/a', 'drafts': [] if self.loop else [{'id': str(self.calls), 'cell': 'cell/a'}],
                        'next': 'same' if self.loop or self.calls == 1 else None}
        self.assertEqual(len(p.draft_inventory(Terminal(False), 'cell/a')), 2)
        with self.assertRaises(ValueError): p.draft_inventory(Terminal(True), 'cell/a')


if __name__ == '__main__':
    unittest.main(verbosity=2)
