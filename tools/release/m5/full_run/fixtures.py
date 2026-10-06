"""Public JSON authoring inputs and acceptance predicates; no runtime imports."""
import copy
import hashlib
import json
import uuid


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def pin(raw, schema):
    return {'schema_id': schema, 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': str(len(raw))}


def fresh_definitions(catalog, contract):
    rows = []
    def ref(key): return {'$ref': key}
    def add(key, body):
        rows.append({'key': key, 'id': str(uuid.uuid4()), 'expected': None, 'label': key, 'body': body})
    def prop(key, kind, category, unit='unitless', minimum=None, maximum=None):
        add(key, {'kind': 'PROPERTY', 'specification': {'value_type': kind, 'category': category,
            'constraint_scope': None, 'unit': unit, 'minimum': minimum, 'maximum': maximum,
            'choices': [], 'vector_length': None, 'overridable': False, 'parameter_mapping': {}}})
    prop('increment', 'NUMBER', 'EXECUTION', minimum=1, maximum=1)
    prop('timeout', 'NUMBER', 'EXECUTION', 's', 1, 30)
    prop('done', 'BOOLEAN', 'RESOURCE')
    prop('cap_count', 'BOOLEAN', 'RESOURCE')
    prop('implementation', 'TEXT', 'RESOURCE')
    prop('version', 'TEXT', 'RESOURCE')
    prop('object_tag', 'TEXT', 'OBJECT')
    add('counter_type', {'kind': 'RESOURCE_TYPE', 'parent': None, 'fields': {
        k: {'property': ref(k), 'required': True} for k in ['cap_count', 'implementation', 'version']}})
    add('counter', {'kind': 'RESOURCE_MODEL', 'resource_type': ref('counter_type'), 'values': {
        'cap_count': {'boolean': True}, 'implementation': {'text': contract['implementation']},
        'version': {'text': contract['version']}}})
    add('object_type', {'kind': 'OBJECT_TYPE', 'parent': None,
        'fields': {'tag': {'property': ref('object_tag'), 'required': True}}})
    add('object_model', {'kind': 'OBJECT_MODEL', 'object_type': ref('object_type'),
        'values': {'tag': {'text': 'M5_EXTERNAL_ADAPTER_SIMULATION_COUNTER'}}})
    add('object_instance', {'kind': 'OBJECT_INSTANCE', 'base': ref('object_model'), 'values': {}})
    quantity = lambda n, unit='unitless': {'unit': unit, 'data': {'kind': 'NUMBER', 'range': {'min': n, 'max': n}}}
    workflow = {'schema': 'rx.workflow-model-package.v1', 'catalog': catalog, 'id': str(uuid.uuid4()),
        'expected': None, 'label': 'M5 fresh one-node counter EXTERNAL_ADAPTER_SIMULATION', 'spec': {
            'schema': 'rx.workflow-model.v1',
            'contexts': {
                'part': {'label': 'part', 'kind': 'OBJECT', 'accepted_types': [ref('object_type')], 'required': True, 'multiple': False},
                'counter': {'label': 'counter', 'kind': 'RESOURCE', 'accepted_types': [ref('counter_type')], 'required': True, 'multiple': False}},
            'defaults': {'part': [ref('object_model')], 'counter': [ref('counter')]}, 'property_sets': [],
            'tasks': {'count': {'label': 'Increment exactly once', 'contexts': ['part', 'counter'],
                'properties': {k: {'property': ref(k), 'sources': [{'kind': 'DEFAULT'}], 'default': v}
                               for k, v in [('increment', quantity(1)), ('timeout', quantity(10, 's'))]},
                'constraints': [], 'capabilities': [{'name': 'count', 'slot': 'counter', 'field': 'cap_count'}],
                'skills': [{'capability': 'count', 'slot': 'counter', 'implementation_field': 'implementation',
                    'version_field': 'version', 'primitive': 'count', 'parameters': {'increment': 'increment'}}],
                'timeout_property': 'timeout', 'done': {'observation': 'done', 'property': ref('done'),
                    'equals': {'unit': 'unitless', 'data': {'kind': 'BOOLEAN', 'value': True}}},
                'on_failure': 'STOP', 'on_unknown': 'HOLD_AND_RECONCILE'}},
            'rules': {}, 'constraints': {}, 'steps': [{'id': 'count', 'task': 'count'}]}}
    return {'schema': 'rx.definition-package.v1', 'catalog': catalog, 'title': 'M5 counter fixture', 'definitions': rows}, workflow


def execution_target(initial, resolved, publication):
    root = resolved['root']
    nodes = root['body'].get('children', [root])
    if len(nodes) != 1 or nodes[0]['body']['kind'] != 'OPERATION':
        raise ValueError('Exactly one authored operation is required')
    binding = {'schema': 'rx.workflow-execution-binding.v2', 'publication': publication['reference'],
               'policy': publication['policy'], 'nodes': {nodes[0]['id']: 'count'}}
    plan = {'schema': 'rx.execution-plan.v2', 'binding': binding, 'process': resolved}
    target = copy.deepcopy(initial)
    step = copy.deepcopy(initial['steps'][0])
    action = resolved['bindings'][nodes[0]['body']['binding']]
    if step['host'] != action['host'] or step['intent'] != action['intent']:
        raise ValueError('Compiler changed the initial allowed action')
    step.update(id=nodes[0]['id'], predecessors=[])
    target.update(process=resolved, execution=binding, recipe=pin(encoded(plan), 'rx.execution-plan.v2'), steps=[step])
    return target, plan


def assert_identity(receipt, expected_run=None):
    if receipt.get('environment') != 'SIMULATION' or receipt['result']['details_truncated']:
        raise AssertionError('Complete SIMULATION receipt required')
    run = receipt['binding']['run']
    if expected_run is not None and run != expected_run:
        raise AssertionError('Original Run identity changed')
    if receipt['result']['run']['value']['id'] != run or len(receipt['result']['work']) != 1:
        raise AssertionError('Exactly one original P-owned operation required')
    work = receipt['result']['work'][0]
    if not work.get('execution') or not work.get('invocation'):
        raise AssertionError('Execution-v2 binding and native invocation required')
    return run, work


def assert_success(receipt, effects, expected_run=None):
    run, work = assert_identity(receipt, expected_run)
    if receipt['result']['run']['value']['state'] != 'COMPLETED' or receipt['result']['current_binding_matches'] is not True:
        raise AssertionError('The Run is not completed under the current binding')
    op = work['operation']
    if (op['outcome'] != 'SUCCEEDED' or op['phase'] != 'SETTLED' or op['disposition'] != 'RELEASED'
            or op['integrity'] != 'VALID' or op['execution_knowledge'] != 'ENDED'):
        raise AssertionError('P has not settled and released the successful operation')
    if len(receipt['result']['parts']) != 1:
        raise AssertionError('Exactly one actual Part is required')
    part=receipt['result']['parts'][0]['value']
    if (part['disposition']!='CONFIRMED_COMPLETED' or part['id']!=work.get('part') or part['run']!=run
            or part['ordinal']!='1' or receipt['result']['run']['value']['part_ids']!=[part['id']]):
        raise AssertionError('The one actual Part is not completed under its original Run membership')
    if (not work['resources'] or len({r['value']['id'] for r in work['resources']})!=len(work['resources'])
            or any(r['value']['holder'] is not None for r in work['resources'])):
        raise AssertionError('Successful operation retains resources')
    assert_effect_identity(work, effects, 1)
    if effects[0].get('increment')!=1 or effects[0].get('count_before')!=0 or effects[0].get('count_after')!=1:
        raise AssertionError('Fresh counter did not increment exactly from zero to one')
    return run


def assert_effect_identity(work, effects, expected):
    if len(effects) != expected:
        raise AssertionError(f'Expected {expected} effects, got {len(effects)}')
    for effect in effects:
        if effect['operation'] != work['operation']['operation_id'] or effect['invocation'] != work['invocation']:
            raise AssertionError('Effect belongs to a different operation/invocation')
        if encoded(effect['selection']) != encoded(work['execution']['selection']):
            raise AssertionError('Effect selection differs from P-bound execution')


def assert_unknown_held(receipt, before, effects, expected_effects):
    run, work = assert_identity(receipt, before['binding']['run'])
    old = before['result']['work'][0]
    if (work['operation']['operation_id'], work['invocation'], work['execution'],work.get('part')) != (old['operation']['operation_id'], old['invocation'], old['execution'],old.get('part')):
        raise AssertionError('Cold restart changed the original execution identity')
    operation=work['operation']
    if (operation['execution_knowledge']!='UNKNOWN' or operation['disposition'] not in ('HELD','QUARANTINED')
            or operation['outcome'] not in ('NONE','UNRESOLVED')
            or operation['phase']=='SETTLED' and operation['outcome']!='UNRESOLVED'):
        raise AssertionError('Unsupported cold recovery must remain UNKNOWN without a known terminal result')
    if receipt['result']['run']['value']['state'] not in ('EXECUTING','PAUSED','RECOVERY_REQUIRED'):
        raise AssertionError('The original uncertain Run was terminated or rewound')
    old_parts=before['result']['parts'];parts=receipt['result']['parts']
    part_key=lambda p:(p['value']['id'],p['value']['run'],p['value']['ordinal'])
    if len(old_parts)!=1 or len(parts)!=1 or part_key(parts[0])!=part_key(old_parts[0]):
        raise AssertionError('The original one Part identity/ordinal was lost or replaced')
    if (parts[0]['value']['run']!=run or work.get('part')!=parts[0]['value']['id']
            or parts[0]['value']['disposition'] not in ('IN_PROGRESS','UNRESOLVED')):
        raise AssertionError('The UNKNOWN Part was completed, discarded or detached')
    if (receipt['result']['run']['value']['part_ids']!=before['result']['run']['value']['part_ids']
            or receipt['result']['run']['value']['part_ids']!=[parts[0]['value']['id']]):
        raise AssertionError('Run Part membership changed')
    old_resources={r['value']['id']:r['value'] for r in old['resources']}
    resources={r['value']['id']:r['value'] for r in work['resources']}
    if (not old_resources or len(old_resources)!=len(old['resources']) or len(resources)!=len(work['resources'])
            or set(resources)!=set(old_resources)
            or any(r['holder']!=operation['operation_id'] for r in [*resources.values(),*old_resources.values()])):
        raise AssertionError('Original P-owned resource identities/holds were lost or replaced')
    assert_effect_identity(work, effects, expected_effects)
    return run


def accepted_start(stdout, returncode, request_id, run):
    # The shipped CLI exits 2 for a valid but non-COMPLETED Run receipt.
    if returncode not in (0, 2):
        raise ValueError('Installed start failed before a correlated receipt')
    value=json.loads(stdout)
    if (value.get('schema')!='rx.execution-cli-receipt.v2' or value.get('request_id')!=request_id
            or value['binding']['run']!=run or not value.get('start_attempt')):
        raise ValueError('Start receipt does not match the original request and Run')
    return value


def assert_native_snapshot(snapshot, work, profile_digest, program_digest, expected_intent, has_completion):
    """Verify immutable SDK native facts against the exact public P operation binding."""
    def raw(name):
        item=snapshot['files'][name];value=bytes.fromhex(item['raw_hex'])
        if hashlib.sha256(value).hexdigest()!=item['sha256'] or len(value)!=item['bytes']:
            raise AssertionError('Native snapshot bytes differ from their inventory')
        return value
    expected_files={'installation','device_session','request'}|({'completion'} if has_completion else set())
    if set(snapshot['files'])!=expected_files:raise AssertionError('Unexpected or missing native immutable facts')
    installation=json.loads(raw('installation'))
    native=installation['native']
    if installation.get('native_directory') is not None or native['kind']!='EXTERNAL_PROCESS':
        raise AssertionError('Only the fresh external native generation is in scope')
    session=raw('device_session').decode()
    if str(uuid.UUID(session))!=session or session!=native['device_session'] or native['program_digest']!=program_digest:
        raise AssertionError('Native generation/program differs from installed public closure')
    request=json.loads(raw('request'));dispatch=request['dispatch']
    if (set(request)!={'schema','dispatch','profile_digest','dispatch_digest'}
            or set(dispatch)!={'operation','invocation','intent','input','device_session','admitted_at','expires_at'}
            or set(dispatch['input'])!={'binding','parameters'}):
        raise AssertionError('Native SDK original request shape differs')
    if (request['schema']!='rx.external-native-request.v1' or request['profile_digest']!=profile_digest
            or dispatch['device_session']!=session or dispatch['operation']!=work['operation']['operation_id']
            or dispatch['invocation']!=work['invocation'] or encoded(dispatch['input']['binding'])!=encoded(work['execution'])):
        raise AssertionError('Native request does not match P operation/invocation/binding/profile/session')
    parameters=bytes(dispatch['input']['parameters']);parameter=work['execution']['selection']['parameter']
    if (parameter['schema_id']!='rx.workflow-parameters.v2' or len(parameters)!=int(parameter['size_bytes'])
            or hashlib.sha256(parameters).hexdigest()!=parameter['sha256']):
        raise AssertionError('Native parameter bytes differ from the approved parameter pin')
    if {r['value']['id'] for r in work['resources']}!=set(dispatch['intent']['resource_set']):
        raise AssertionError('Observed resources differ from the original native intent')
    actual_dispatch_digest=hashlib.sha256(encoded(dispatch)).hexdigest()
    if request['dispatch_digest']!=actual_dispatch_digest:
        raise AssertionError('Native SDK dispatch digest differs')
    intent=copy.deepcopy(expected_intent)
    intent['body']['program']['parameter_set']=work['execution']['selection']['parameter']
    if (encoded(dispatch['intent'])!=encoded(intent) or dispatch['intent']['profile_digest']!=profile_digest
            or work['execution']['selection']['intent_digest']!=work['operation']['intent_digest']):
        raise AssertionError('Native intent differs from selected public template and parameter pin')
    if ('completion' in snapshot['files'])!=has_completion:
        raise AssertionError('Native durable completion presence differs from the injected boundary')
    if has_completion:
        completion=json.loads(raw('completion'));capture=completion['capture']
        if (completion['schema']!='rx.external-native-fact.v1' or encoded(completion['original'])!=encoded(request)
                or capture['native_id']!=work['invocation'] or capture['device_session']!=session
                or capture['status_schema']!=intent['completion_rule'] or type(capture['status']) is not int
                or capture['status']!=0):
            raise AssertionError('Native completion does not belong to the original request tuple')
    return {'operation':dispatch['operation'],'invocation':dispatch['invocation'],'profile_digest':profile_digest,
        'program_digest':program_digest,'device_session':session,'dispatch_digest':actual_dispatch_digest,
        'file_sha256':{name:item['sha256'] for name,item in snapshot['files'].items()},
        'dispatch_digest_scheme':'SHA256 of released external SDK encoded(dispatch), not P domain-separated identity'}
