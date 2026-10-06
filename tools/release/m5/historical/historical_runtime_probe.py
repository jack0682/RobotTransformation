#!/usr/bin/env python3
"""Linux CI oracle for the exact published old runtime facade, never a new SDK alias.

Local tests exercise pure assertions. Product API calls require --execute, Linux,
and CI=true. No run/start/compile/activation API is called by this probe.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

LOCK_SHA256 = 'e4e416530d4dee347afd7c1acbe6d36b8baf3807f2eed2588250f1ca6b4a810f'
FILES = {
    'image_identity.py': 'd6b8ba9a3a0ba0dfdb4c5c1d5f8338eb8b3958259c4fc9c9f43a30b20bf8ad75',
    'python_environment.py': 'b1fb5f488dcfd34453f3143ef3d543393d33ff411a80c17ff636a8b75bdf4006',
    'runtime_client.py': '161514ed9afac8699dabafd5bdf24659c451d1dce4223df6fa0d2597af33616f',
    'rx': '5f7b565cab21e3b6258dafd1d295bab8f426d1d2b43983603e4e44a7aeb77bf0',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular(path):
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path
            and path.is_file() and not path.is_symlink(), 'Canonical regular file required')
    return path


def fresh(path):
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path
            and not path.exists() and not path.is_symlink() and path.parent.is_dir(),
            'Fresh canonical path with existing parent required')
    return path


def pinned_client(client, lock):
    require(client.is_absolute() and client.resolve() == client and client.is_dir(),
            'Canonical historical client directory required')
    require(sha(regular(lock)) == LOCK_SHA256, 'Historical consumer lock changed')
    require({p.name for p in client.iterdir()} == set(FILES), 'Historical client file set differs')
    actual = {name: sha(regular(client / name)) for name in FILES}
    require(actual == FILES, 'Historical client substituted or edited')
    return actual


def positive_composition(value, request, cell, step):
    draft = str(uuid.uuid5(uuid.UUID(request), 'rx.runtime-skill.draft'))
    require(value['status'] == 'DRAFT_READY_FOR_COMPILER'
            and value['execution_authorized'] is False, 'Draft must not authorize execution')
    require(value['request_id'] == request and value['draft_id'] == draft, 'Original request/draft changed')
    body = value['compile_input']
    require(body['draft'] == draft and body['cell'] == cell, 'Compile input scope differs')
    for field in ('source_revision', 'binding_revision'):
        number = body[field]
        require(isinstance(number, str) and number.isascii() and number.isdecimal()
                and str(int(number)) == number and 0 < int(number) < 2**64,
                'Canonical positive revision required')
    require(isinstance(body['catalog_digest'], str) and len(body['catalog_digest']) == 64
            and set(body['catalog_digest']) <= set('0123456789abcdef'), 'Catalog digest differs')
    require(set(body['bindings']) == {'skill/1'}, 'Exactly one authored binding required')
    require(body['source']['schema'] == 'rx.process-source.v1'
            and body['source']['process'] == 'historical-client-check', 'Wrong authored source')
    # The old client's public returned compile input is authoritative for the rest
    # of each binding's schema. Its saved request is checked separately below.
    return {key: body[key] for key in ('draft', 'cell', 'source_revision', 'binding_revision',
                                      'catalog_digest', 'source', 'bindings')}



def binding_receipt(value, saved, catalog, step):
    body = value['compile_input']
    candidates = [candidate for candidate in catalog['candidates'] if candidate['step'] == step]
    require(len(candidates) == 1, 'One selected public candidate required')
    selected = candidates[0]
    require(saved['complete'] is True and saved['missing'] == []
            and saved['selections'] == {'skill/1': step}, 'Saved binding selection is incomplete or differs')
    require(saved['draft'] == body['draft'] and saved['cell'] == body['cell']
            and saved['source_revision'] == body['source_revision']
            and saved['revision'] == body['binding_revision'], 'Saved binding revision differs')
    require(saved['catalog_digest'] == body['catalog_digest'] == catalog['catalog_digest']
            and saved['origins'] == {'skill/1': selected['step_digest']}, 'Selected candidate origin differs')
    require(saved['resolved'] == body['bindings'], 'Exported ActionBinding differs from saved resolution')
    action = saved['resolved']['skill/1']
    require(action['host'] == selected['host']
            and action['intent']['target'] == selected['target']
            and action['intent']['kind'] == selected['kind']
            and action['intent']['resource_set'] == selected['resources'], 'Resolved public candidate fields differ')
    return saved


def same_recovery(first, recovered, request, cell, step):
    expected = positive_composition(first, request, cell, step)
    require(positive_composition(recovered, request, cell, step) == expected,
            'Recovery changed original source/binding identity')
    return expected


def idle_cell(overview, cell):
    selected = [x for x in overview['cells'] if x['cell']['value']['id'] == cell]
    require(len(selected) == 1, 'Exactly one visible target cell required')
    value = selected[0]
    require(value['runs_truncated'] is False and value['work_truncated'] is False,
            'Truncated execution observation cannot prove absence')
    require(value['runs'] == [] and value['work'] == [], 'Target cell must have no run/work')
    return {'installation': overview['installation'], 'runs': value['runs'], 'work': value['work']}


def draft_inventory(terminal, cell):
    result, seen, after = {}, set(), None
    for _ in range(100):
        query = {'cell': cell}
        if after is not None:
            query['after'] = after
        page = terminal.get('/api/v1/process-drafts', **query)
        require(page['cell'] == cell and isinstance(page['drafts'], list), 'Draft page scope differs')
        for item in page['drafts']:
            require(item['cell'] == cell and item['id'] not in result, 'Duplicate or cross-cell draft')
            result[item['id']] = item
        after = page['next']
        if after is None:
            return result
        require(isinstance(after, str) and after not in seen, 'Draft pagination did not advance')
        seen.add(after)
    raise ValueError('Draft pagination exceeds fixture scope')


def assert_no_negative_mutation(before, after, state, request):
    require(after == before, 'Invalid-step request changed admitted drafts')
    for name in ('compose-source.request.json', 'compose-source.reply.json',
                 'compose-bindings.request.json', 'compose-bindings.reply.json'):
        require(not (state / request / name).exists(), 'Invalid step entered a draft mutation')


def cli(args, action, label, logs, expected_failure=False):
    command = [sys.executable, '-E', '-s', '-B', str(args.client / 'rx'), 'runtime',
               '--connection', str(args.connection), '--state-dir', str(args.state), *action]
    env = {key: value for key, value in os.environ.items() if not key.startswith('PYTHON')}
    (logs / (label + '.command.json')).write_text(json.dumps(command) + '\n')
    try:
        completed = subprocess.run(command, env=env, cwd=args.state.parent,
                                   capture_output=True, timeout=150)
    except subprocess.TimeoutExpired as error:
        (logs / (label + '.stdout')).write_bytes(error.stdout or b'')
        (logs / (label + '.stderr')).write_bytes(error.stderr or b'')
        raise
    (logs / (label + '.stdout')).write_bytes(completed.stdout)
    (logs / (label + '.stderr')).write_bytes(completed.stderr)
    record = {'argv': command, 'exit_code': completed.returncode,
              'stdout_sha256': hashlib.sha256(completed.stdout).hexdigest(),
              'stderr_sha256': hashlib.sha256(completed.stderr).hexdigest()}
    if expected_failure:
        require(completed.returncode == 1 and b'installed steps not found:' in completed.stderr,
                'Invalid step did not produce the old client refusal')
        return record
    require(completed.returncode == 0, 'Historical client failed: ' + label)
    return json.loads(completed.stdout), record


def execute(args, receipt, logs):
    receipt['before_file_sha256'] = pinned_client(args.client, args.lock)
    regular(args.connection)
    fresh(args.state)
    # Load only the already byte-verified old module, never a current source tree.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('rx_verified_historical_client', args.client / 'runtime_client.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == args.client / 'runtime_client.py', 'Wrong observer module')
    receipt['observer_module'] = str(module.__file__)
    terminal = module.Terminal(args.connection)
    before = idle_cell(terminal.get('/api/v1/overview'), args.cell)
    receipt['public_before'] = before
    catalog, command = cli(args, ['skills'], 'skills', logs)
    receipt['commands'].append(command)
    require(catalog['schema'] == 'rx.runtime-skill-catalog.v1' and catalog['truncated'] is False,
            'Complete old runtime catalog required')
    require(catalog['installation'] == before['installation'], 'Catalog installation changed')
    steps, command = cli(args, ['steps', '--cell', args.cell], 'steps', logs)
    receipt['commands'].append(command)
    available = [item['step'] for item in steps['candidates']]
    require(steps['cell'] == args.cell and args.step in available, 'Requested step unavailable')
    request = str(uuid.uuid4())
    receipt['request_id'] = request
    first, command = cli(args, ['compose', 'historical-client-check', '--cell', args.cell,
                                '--step', args.step, '--request-id', request], 'compose', logs)
    receipt['commands'].append(command)
    positive_composition(first, request, args.cell, args.step)
    saved = json.loads((args.state / request / 'compose-bindings.request.json').read_bytes())
    require(saved['body']['command']['selections'] == {'skill/1': args.step}, 'Wrong step composed')
    saved_binding = json.loads((args.state / request / 'compose-bindings.reply.json').read_bytes())
    receipt['saved_binding'] = binding_receipt(first, saved_binding, steps, args.step)
    saved_binding_sha = sha(args.state / request / 'compose-bindings.reply.json')
    saved_requests = {p.name: sha(p) for p in (args.state / request).glob('*.request.json')}
    recovered, command = cli(args, ['compose-recover', request], 'recover', logs)
    receipt['commands'].append(command)
    receipt['composition'] = same_recovery(first, recovered, request, args.cell, args.step)
    binding_receipt(recovered, saved_binding, steps, args.step)
    require(sha(args.state / request / 'compose-bindings.reply.json') == saved_binding_sha,
            'Recovery rewrote the admitted binding reply')
    require({p.name: sha(p) for p in (args.state / request).glob('*.request.json')} == saved_requests,
            'Recovery rewrote original mutation requests')
    receipt['request_files_sha256'] = saved_requests
    before_negative = draft_inventory(terminal, args.cell)
    require(first['draft_id'] in before_negative, 'Composed draft absent from public inventory')
    negative = str(uuid.uuid4())
    missing = 'historical/missing/' + negative
    require(missing not in available, 'Negative step unexpectedly exists')
    command = cli(args, ['compose', 'historical-invalid-step', '--cell', args.cell,
                         '--step', missing, '--request-id', negative], 'invalid-step', logs, True)
    receipt['commands'].append(command)
    after_negative = draft_inventory(terminal, args.cell)
    assert_no_negative_mutation(before_negative, after_negative, args.state, negative)
    receipt['negative'] = {'request_id': negative, 'step': missing, 'refused': True,
                           'admitted_drafts_unchanged': True, 'before': before_negative, 'after': after_negative}
    after = idle_cell(terminal.get('/api/v1/overview'), args.cell)
    require(after == before, 'Installation or target-cell execution observation changed')
    receipt['public_after'] = after
    receipt['after_file_sha256'] = pinned_client(args.client, args.lock)
    receipt['status'] = 'PASS_FOR_REPORTED_SCOPE'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('client', 'lock', 'connection', 'state', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--cell', required=True)
    parser.add_argument('--step', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    require(args.execute and os.environ.get('CI') == 'true' and sys.platform == 'linux',
            'Only explicit fresh Linux CI execution is allowed')
    fresh(args.output)
    logs = fresh(args.output.with_suffix('.logs'))
    logs.mkdir()
    receipt = {'schema': 'rx.historical-runtime-consumer-probe.v1', 'status': 'FAIL',
               'classification': 'PUBLISHED_INSTALLED_RUNTIME_CLIENT', 'lock_sha256': LOCK_SHA256,
               'scope': 'Catalog, draft compose and same-request recovery; no execution authorization',
               'not_observed': ['rxclpy/rxclcpp SDK ABI', 'Execution v2 completion', 'native effects (caller must observe)', 'physical operation'],
               'python': sys.version, 'platform': platform.platform(), 'commands': []}
    try:
        execute(args, receipt, logs)
    except Exception as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        try:
            receipt['final_file_sha256'] = pinned_client(args.client, args.lock)
        except Exception as error:
            receipt['status'] = 'FAIL'
            receipt['final_pin_error'] = str(error)
        args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    require(receipt['status'] == 'PASS_FOR_REPORTED_SCOPE', 'Historical client final pins failed')
    print(json.dumps({'status': receipt['status'], 'receipt': str(args.output)}))


if __name__ == '__main__':
    main()
