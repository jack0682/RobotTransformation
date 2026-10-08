"""Author the bounded M1 model and A/B input domain through public P APIs."""
from __future__ import annotations

import copy
import shutil

from common import *
from definitions_client import Definitions
from workflow_client import Workflows
from runtime_client import Terminal, RuntimeClient
from execution_client import ExecutionClient


def quantity(kind, unit, value):
    if kind == 'NUMBER':
        data = {'kind': kind, 'range': {'min': value, 'max': value}}
    elif kind == 'VECTOR':
        data = {'kind': kind, 'ranges': [{'min': v, 'max': v} for v in value]}
    else:
        data = {'kind': kind, 'value': value}
    return {'unit': unit, 'data': data}


def definition_value(kind, value):
    return {dict(NUMBER='number', VECTOR='vector', BOOLEAN='boolean', TEXT='text')[kind]: value}


def generate(scenario, case):
    """Definitions are fresh per installation; the shelf has one declared custody slot."""
    catalog = uid()
    definitions = []
    def ref(key):
        return {'$ref': key}
    def add(key, body, label=None):
        definitions.append({'key': key, 'id': uid(), 'expected': None,
                            'label': label or key + ' · SIMULATION', 'body': body})
    def prop(key, kind, unit, length=None, category='RESOURCE'):
        add('property.' + key, {'kind': 'PROPERTY', 'specification': {
            'value_type': kind, 'category': category, 'constraint_scope': None, 'unit': unit,
            'minimum': None, 'maximum': None, 'choices': [], 'vector_length': length,
            'overridable': False, 'parameter_mapping': {}}})
    parameters = scenario['parameters']
    equipment = {'robot': 'robot_id', 'gripper': 'gripper_channel', 'shelf': 'shelf_id',
                 'vision': 'vision_id', 'ft': 'ft_id'}
    for key, p in parameters.items():
        prop(key, p['value_type'], p['unit'], len(p['default']) if p['value_type'] == 'VECTOR' else None,
             'RESOURCE' if key in equipment.values() else 'OBJECT')
    for key, kind, unit, length in [('done', 'BOOLEAN', 'unitless', None),
            ('implementation', 'TEXT', 'unitless', None), ('version', 'TEXT', 'unitless', None),
            ('origin', 'VECTOR', 'mm', 3), ('frame', 'TEXT', 'unitless', None),
            ('orientation', 'VECTOR', 'unitless', 4),
            ('count', 'NUMBER', 'unitless', None), ('pitch', 'NUMBER', 'mm', None)]:
        prop(key, kind, unit, length)
    material_fields = [key for key in parameters if key not in equipment.values()]
    add('type.material', {'kind': 'OBJECT_TYPE', 'parent': None, 'fields': {
        key: {'property': ref('property.' + key), 'required': True} for key in material_fields}})
    for letter, model, angle in [('a', 'sim/material-a', 95), ('b', 'sim/material-b', 120)]:
        values = {key: definition_value(parameters[key]['value_type'], parameters[key]['default'])
                  for key in material_fields}
        values['material_model'] = {'text': model}
        values['groove_angle_deg'] = {'number': angle}
        values['groove_found'] = {'boolean': case != 'groove-missing'}
        add('material.' + letter, {'kind': 'OBJECT_MODEL', 'object_type': ref('type.material'),
                                  'values': values}, 'Material ' + letter.upper() + ' · SIMULATION')
        add('object.' + letter, {'kind': 'OBJECT_INSTANCE', 'base': ref('material.' + letter), 'values': {}},
            'Material ' + letter.upper() + ' · identified simulation object')
    for slot, field in equipment.items():
        fields = {field: {'property': ref('property.' + field), 'required': True}}
        values = {field: definition_value('TEXT', parameters[field]['default'])}
        if slot == 'shelf':
            for key, kind, value in [('origin', 'VECTOR', [0, 0, 0]), ('frame', 'TEXT', 'SIMULATION/shelf'),
                                     ('orientation', 'VECTOR', [0, 0, 0, 1]),
                                     ('count', 'NUMBER', 1), ('pitch', 'NUMBER', 1)]:
                fields[key] = {'property': ref('property.' + key), 'required': True}
                values[key] = definition_value(kind, value)
        add('type.' + slot, {'kind': 'RESOURCE_TYPE', 'parent': None, 'fields': fields})
        add('model.' + slot, {'kind': 'RESOURCE_MODEL', 'resource_type': ref('type.' + slot), 'values': values})
        add('resource.' + slot, {'kind': 'RESOURCE_INSTANCE', 'base': ref('model.' + slot), 'values': {}})
    add('type.provider', {'kind': 'RESOURCE_TYPE', 'parent': None, 'fields': {
        key: {'property': ref('property.' + propkey), 'required': True}
        for key, propkey in [('can_align', 'done'), ('implementation', 'implementation'), ('version', 'version')]}})
    add('resource.provider', {'kind': 'RESOURCE_MODEL', 'resource_type': ref('type.provider'), 'values': {
        'can_align': {'boolean': True}, 'implementation': {'text': scenario['implementation']},
        'version': {'text': scenario['version']}}})
    add('pattern.shelf', {'kind': 'POINT_PATTERN', 'resource_type': ref('type.shelf'),
        'orientation': 'orientation',
        'origin': 'origin', 'frame': 'frame', 'axes': [{'count': 'count', 'pitch': 'pitch', 'direction': [1, 0, 0]}]},
        'Single simulation shelf seat custody slot')
    contexts = {'part': {'label': 'Material', 'kind': 'OBJECT', 'accepted_types': [ref('type.material')],
                        'required': True, 'multiple': False}}
    defaults = {'part': [ref('material.a')]}
    for slot in [*equipment, 'provider']:
        contexts[slot] = {'label': slot.capitalize(), 'kind': 'RESOURCE',
                         'accepted_types': [ref('type.' + slot)], 'required': True, 'multiple': False}
        defaults[slot] = [ref('resource.' + slot)]
    properties = {}
    for key in parameters:
        slot = next((slot for slot, field in equipment.items() if field == key), 'part')
        properties[key] = {'property': ref('property.' + key),
            'sources': [{'kind': 'CONTEXT', 'slot': slot, 'field': key, 'index': 0}], 'default': None}
    # Existing execution-v2 requires a pattern resource. This is one shelf seat, not a tray cycle.
    properties['shelf_position'] = {'property': ref('property.origin'),
        'sources': [{'kind': 'PATTERN', 'slot': 'shelf', 'rule': ref('pattern.shelf'), 'component': 'POSITION'}],
        'default': None}
    tasks = {}
    for step in scenario['steps']:
        tasks[step['id']] = {'label': step['label'], 'contexts': list(contexts), 'properties': properties,
            'constraints': [], 'capabilities': [{'name': 'align', 'slot': 'provider', 'field': 'can_align'}],
            'skills': [{'capability': 'align', 'slot': 'provider', 'implementation_field': 'implementation',
                        'version_field': 'version', 'primitive': step['id'], 'parameters': {k: k for k in parameters}}],
            'timeout_property': 'timeout_s', 'done': {'observation': step['done'], 'property': ref('property.done'),
                                                    'equals': quantity('BOOLEAN', 'unitless', True)},
            'on_failure': 'STOP', 'on_unknown': 'HOLD_AND_RECONCILE'}
    model = {'schema': 'rx.workflow-model-package.v1', 'catalog': catalog, 'id': uid(), 'expected': None,
        'label': 'Material alignment and regrasp · SIMULATION', 'spec': {
            'schema': 'rx.workflow-model.v1', 'contexts': contexts, 'defaults': defaults,
            'property_sets': [], 'rules': {}, 'constraints': {}, 'tasks': tasks,
            'steps': [{'id': s['id'], 'task': s['id']} for s in scenario['steps']]}}
    return {'schema': 'rx.definition-package.v1', 'catalog': catalog,
            'title': 'M1 material alignment · SIMULATION', 'definitions': definitions}, model


def author(site):
    terminal = Terminal(site.connections['engineer'])
    journal = site.root / 'authoring-client'
    definitions, model = generate(site.scenario, site.case)
    save(site.evidence / 'definitions-input.json', definitions)
    request = uid()
    save(site.evidence / 'definitions-request-identity.json', {'request_id': request, 'catalog': definitions['catalog']})
    try:
        refs = Definitions(terminal, journal).apply(definitions, {}, request)['references']
    except Exception:
        # Preserve the original identity and inspect only; never replay a failed setup mutation.
        for entry in definitions['definitions']:
            if entry['body']['kind'] == 'POINT_PATTERN':
                try:
                    current = terminal.get('/api/v1/definition', catalog=definitions['catalog'], id=entry['id'])
                    save(site.evidence / 'failed-definition-readback.json', current)
                except Exception as error:
                    save(site.evidence / 'failed-definition-readback-error.json', {'error': str(error)})
        raise
    workflow = Workflows(terminal, journal).apply(model, refs, uid())
    saved_model = Workflows(terminal, journal).model(workflow['workflow'])
    requests = []
    for key in ('a', 'b'):
        request = {'workflow': workflow['workflow'],
                   'contexts': {**saved_model['spec']['defaults'], 'part': [refs['material.' + key]]},
                   'property_sets': [], 'overrides': {}, 'inputs': {}, 'slot_index': '0'}
        report = Workflows(terminal, journal).resolve(request, uid())
        save(site.evidence / ('resolution-' + key + '.json'), report)
        if report['report']['valid'] is not True or report['report']['concrete'] is not True:
            raise ValueError('M1 input domain is not concrete: ' + str(report['report']['violations']))
        requests.append(request)
    execution = ExecutionClient(terminal, journal)
    preview = execution.command('preview', {'id': uid(), 'candidates': [
        {'key': key, 'object_model': refs['material.' + key], 'request': request}
        for key, request in zip(('a', 'b'), requests)], 'slots': 1,
        'templates': {k: v['action'] for k, v in site.templates.items()},
        'node_contracts': {k: v['contract'] for k, v in site.templates.items()}}, uid())
    execution.export(preview, site.root / 'material')
    api = site.users['engineer']
    context = api.get('/api/v1/package-intake-context', cell=site.cell)
    intake = api.mutate('template-intake', '/api/v1/package-intakes', {'id': uid(), 'cell': site.cell,
        'title': 'M1 external simulation provider', 'relative_path': 'templates',
        'object': {'manifest': sha(site.author / 'package/manifest.json'),
                   'signature': sha(site.author / 'package/manifest.sig.json')},
        'configuration_digest': context['configuration_digest'],
        'policy_generation': context['registration']['generation']})
    publication = execution.command('publish', {'id': uid(), 'preview': preview['reference'], 'cell': site.cell,
        'bindings': {k: {'intake': intake['id'], 'template': k} for k in site.templates}}, uid())
    composition = RuntimeClient(terminal, journal).compose(uid(), 'm1/material-alignment', site.cell,
        ['step/' + step['id'] for step in site.scenario['steps']])
    site.workflow, site.refs, site.requests = workflow, refs, requests
    site.preview, site.publication = preview, publication
    site.compile_input = composition['compile_input']
    save(site.evidence / 'workflow.json', workflow)
    save(site.evidence / 'preview.json', preview)
    save(site.evidence / 'publication.json', publication)
    save(site.evidence / 'compile-input.json', site.compile_input)
    return site
