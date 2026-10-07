"""Actual operator bundle -> P -> Executor -> external Host provider checks."""
from __future__ import annotations

import re
import time
from urllib.parse import parse_qs, urlsplit

from common import *
from commission import provider_effects
from cell_delivery.api import Rejected
from cell_delivery.commission import wait_for
from runtime_client import Terminal
from execution_client import ExecutionClient


def ref_key(ref):
    # Same identity formatting used by definition-schema.ts.
    return f"{ref['catalog']}/{ref['id']}/{ref['revision']}/{ref['digest']}"


def select_reference(locator, ref):
    # Select from rendered options using the actual definition UUID, never an invented DOM selector.
    locator.locator(f'option[value*="{ref["id"]}"]').wait_for(state='attached', timeout=30000)
    options = locator.locator('option').evaluate_all('(nodes) => nodes.map(n => ({value:n.value,text:n.textContent}))')
    matches = [option['value'] for option in options if ref['id'] in option['value']]
    if len(matches) != 1:
        raise AssertionError('exact pinned option missing or ambiguous')
    locator.select_option(matches[0])


def unknown_custody(receipt, initial_work, resources):
    """Check existing P records only; this helper issues no command or release."""
    result, binding = receipt['result'], receipt['binding']
    if len(result['work']) != 1:
        raise AssertionError('UNKNOWN admitted later work or lost the original operation')
    work = result['work'][0]
    original_id = initial_work['operation']['operation_id']
    selection = initial_work['execution']['selection']
    if (work['operation']['operation_id'] != original_id
            or work['invocation'] != initial_work['invocation']
            or work['execution'] != initial_work['execution']
            or work['part'] != selection['part'] or selection['node'] != 'shelf-seat'
            or work['operation']['execution_knowledge'] != 'UNKNOWN'
            or work['operation']['outcome'] != 'NONE'
            or work['operation']['phase'] != 'RECONCILING'
            or work['operation']['disposition'] != 'QUARANTINED'
            or work['operation']['integrity'] != 'VALID'
            or result['details_truncated'] or result['run']['value']['state'] == 'COMPLETED'
            or result['run']['value']['part_ids'] != [selection['part']]):
        raise AssertionError('UNKNOWN original identity or unfinished Part was not preserved')
    resource_values = {r['value']['id']: r['value'] for r in work['resources']}
    if (not resources or set(resource_values) != set(resources)
            or len(resource_values) != len(work['resources'])
            or any(r['holder'] != original_id for r in resource_values.values())):
        raise AssertionError('UNKNOWN lost an original P resource holder')
    parts = result['parts']
    if (len(parts) != 1 or parts[0]['value']['id'] != selection['part']
            or parts[0]['value']['disposition'] == 'CONFIRMED_COMPLETED'):
        raise AssertionError('UNKNOWN Part was completed, replaced or advanced')
    if binding['run'] != selection['run'] or len(binding['slots']) != 1:
        raise AssertionError('UNKNOWN Run slot binding differs')
    slot = binding['slots'][0]
    if (slot['index'] != selection['slot'] or slot['ordinal'] != selection['ordinal']
            or slot['slot_ordinal'] != selection['slot_ordinal']):
        raise AssertionError('UNKNOWN original slot identity differs')
    pins = {ref_key(pin['resource']): pin for pin in binding['pools']}
    pools = {ref_key(pool['resource']): pool for pool in receipt['slot_pools']}
    expected_hold = {'run': selection['run'], 'ordinal': selection['ordinal'],
        'slot_ordinal': selection['slot_ordinal'], 'part': selection['part'], 'consumed': False}
    if not pins or set(pins) != set(pools) or len(pools) != len(receipt['slot_pools']):
        raise AssertionError('UNKNOWN lost an original slot pool')
    for key, pool in pools.items():
        if (pool['generation'] != pins[key]['generation']
                or pool['layout_digest'] != pins[key]['layout_digest']
                or pool['holds'] != {str(selection['slot']): expected_hold}):
            raise AssertionError('UNKNOWN slot hold was released, consumed or reinitialized')
    return {'binding': binding, 'resources': resource_values, 'slot_pools': pools}


def completed_loss_audit(site):
    # A log row is complete only after its newline is present; an in-flight append
    # must not become either a failed proof or a fabricated completed loss.
    reader = r'''
import json,os,stat
from pathlib import Path
p=Path('/data/material-alignment/withheld.jsonl'); raw=b''
if p.exists():
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_size>1048576:
        raise ValueError('bounded owned test-link audit required')
    raw=p.read_bytes()
complete=not raw or raw.endswith(b'\n')
print(json.dumps([json.loads(line) for line in raw.splitlines()] if complete else []))
'''
    raw = site.d.run('exec', site.services['h'], '/opt/rx/python/python', '-I', '-S', '-B', '-c', reader)
    return json.loads(raw)


def verify_withheld_completion(site, work, effect, rows, output):
    """Join real loss audit and SDK durable capture by their original identities."""
    operation = work['operation']['operation_id']
    if str(uuid.UUID(operation)) != operation:
        raise AssertionError('original native operation is not a canonical UUID')
    if (not rows or any(row['mode'] not in ('execute', 'lookup')
            or row['operation'] != operation or row['invocation'] != work['invocation']
            or row['provider_exit'] != 0 or type(row['withheld_bytes']) is not int
            or not 0 < row['withheld_bytes'] <= 1048576
            or not re.fullmatch('[0-9a-f]{64}', row['request_sha256'])
            or not re.fullmatch('[0-9a-f]{64}', row['withheld_sha256']) for row in rows)):
        raise AssertionError('native result-loss audit lacks the original completed invocation')
    executions = [row for row in rows if row['mode'] == 'execute']
    if (len(executions) != 1 or executions[0]['native_entry_forwarded'] is not True
            or any(row['native_entry_forwarded'] is not False for row in rows if row['mode'] == 'lookup')):
        raise AssertionError('native result loss lacks one original forwarded entry')
    root = '/data/host/native-external/' + operation
    original = json.loads(site.d.run('exec', site.services['h'], 'cat', root + '/request.json'))
    completed = json.loads(site.d.run('exec', site.services['h'], 'cat', root + '/completion.json'))
    save(output / 'withheld-original-request.json', original)
    save(output / 'withheld-durable-completion.json', completed)
    dispatch = original['dispatch']
    capture = completed['capture']
    if (original['schema'] != 'rx.external-native-request.v1'
            or original['dispatch_digest'] != digest(encoded(dispatch))
            or completed['schema'] != 'rx.external-native-fact.v1' or completed['original'] != original
            or dispatch['operation'] != operation or dispatch['invocation'] != work['invocation']
            or dispatch['input']['binding'] != work['execution']
            or original['profile_digest'] != dispatch['intent']['profile_digest']
            or capture['native_id'] != work['invocation']
            or capture['device_session'] != dispatch['device_session']
            or capture['status_schema'] != effect['status_schema'] or capture['status'] != effect['status']
            or capture['status_schema'] != 'm1/alignment-result' or capture['status'] != 0
            or capture['captured_at']['clock_id'] != dispatch['admitted_at']['clock_id']
            or int(capture['captured_at']['ticks_ns']) < int(dispatch['admitted_at']['ticks_ns'])):
        raise AssertionError('withheld completion is not the actual original native capture')


def exercise(site):
    from playwright.sync_api import sync_playwright, expect
    output = site.evidence / 'browser'
    output.mkdir()
    diagnostics = {'page_errors': [], 'console_errors': [], 'failed_requests': [], 'http_errors': []}
    engineer = site.users['engineer']
    target_letter = 'b' if site.case == 'changed-material' else 'a'
    saved_receipts = []
    saved_requests = []
    state_flags = {'authenticated': False, 'navigating': False, 'read_loss': False}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True, viewport={'width': 1440, 'height': 1100},
            client_certificates=[{'origin': site.origin, 'certPath': str(site.final / site.browser['certificate']),
                                  'keyPath': str(site.final / site.browser['private_key'])}])
        page = context.new_page()
        page.on('pageerror', lambda error: diagnostics['page_errors'].append(str(error)))
        def console_message(message):
            if message.type != 'error':
                return
            path = message.location.get('url', '').split('?', 1)[0].removeprefix(site.origin)
            expected = (not state_flags['authenticated'] and path == '/api/v1/overview' and '401' in message.text) or (
                state_flags['read_loss'] and path == '/api/v1/runtime-skill-result' and 'ERR_FAILED' in message.text) or (
                path == '/api/v1/workflow-executions/objects' and '404' in message.text) or (
                site.case == 'lost-start-response' and path == '/api/v1/workflow-executions/start'
                and 'ERR_FAILED' in message.text)
            diagnostics['console_errors'].append({'path': path, 'text': message.text, 'expected': expected})
        page.on('console', console_message)
        def http_response(response):
            if response.status < 400:
                return
            path = response.url.split('?', 1)[0].removeprefix(site.origin)
            diagnostics['http_errors'].append({'path': path, 'status': response.status,
                'expected': (response.status == 404 and path == '/api/v1/workflow-executions/objects') or (
                    not state_flags['authenticated'] and response.status == 401 and path == '/api/v1/overview')})
        page.on('response', http_response)
        active_reads = set()
        superseded_reads = set()
        def request_started(request):
            if request.method == 'GET':
                active_reads.add(request)
        def request_finished(request):
            active_reads.discard(request)
            superseded_reads.discard(request)
        page.on('request', request_started)
        page.on('requestfinished', request_finished)
        def request_failed(request):
            superseded = request in superseded_reads
            diagnostics['failed_requests'].append({
                'path': request.url.split('?', 1)[0].removeprefix(site.origin),
                'error': request.failure, 'superseded_read': superseded,
                'expected': (site.case == 'lost-start-response'
                and request.url.endswith('/api/v1/workflow-executions/start')) or (
                    state_flags['read_loss'] and request.url.split('?', 1)[0].endswith('/api/v1/runtime-skill-result')) or (
                    (state_flags['navigating'] or superseded) and request.method == 'GET'
                    and request.failure == 'net::ERR_ABORTED')})
            request_finished(request)
        page.on('requestfailed', request_failed)
        def reload_page():
            # Cancellation events can arrive after navigation has already completed.
            superseded_reads.update(active_reads)
            state_flags['navigating'] = True
            try:
                page.reload(wait_until='networkidle')
            finally:
                state_flags['navigating'] = False
        try:
            page.goto(site.origin, wait_until='networkidle')
            page.get_by_label('Account', exact=True).fill('engineer')
            page.get_by_label('Password', exact=True).fill(site.browser['credentials']['engineer'])
            page.get_by_role('button', name='Sign in', exact=True).click()
            expect(page.get_by_role('button', name='Sign out', exact=True)).to_be_visible()
            state_flags['authenticated'] = True
            page.get_by_role('button', name='Workflow design', exact=True).click()
            expect(page.get_by_role('heading', name='Configure a Task', exact=True)).to_be_visible()
            page.get_by_label('Authoring catalog', exact=True).select_option(site.workflow['workflow']['catalog'])
            select_reference(page.get_by_label('Task library', exact=True), site.workflow['workflow'])
            expect(page.get_by_label('part context', exact=True)).to_be_enabled()

            def save_configuration():
                # Replacing the receipt disposes its original report-model read.
                superseded_reads.update(request for request in active_reads
                    if urlsplit(request.url).path == '/api/v1/workflow-model')
                with page.expect_response(lambda response: response.url.endswith('/api/v1/workflow-resolutions')
                                           and response.request.method == 'POST') as pending:
                    page.get_by_role('button', name='Save configuration and check values', exact=True).click()
                response = pending.value
                if not response.ok:
                    raise AssertionError('configuration save failed: ' + response.text())
                receipt = response.json()
                saved_requests.append(response.request.post_data_json)
                saved_receipts.append(receipt)
                return receipt

            # T02: server validation from a genuinely incomplete UI selection, before any Run.
            page.get_by_label('part context', exact=True).select_option('')
            invalid = save_configuration()
            if invalid['report']['valid'] is not False or provider_effects(site):
                raise AssertionError('missing material did not block before effects')
            select_reference(page.get_by_label('part context', exact=True), site.refs['material.a'])
            original = save_configuration()
            if original['report']['request'] != site.requests[0]:
                raise AssertionError('saved A configuration differs from approved candidate')
            # T08: a changed body cannot reuse the original, already committed save identity.
            conflict = json.loads(json.dumps(saved_requests[-1]))
            conflict['command']['slot_index'] = '1'
            try:
                engineer._request('/api/v1/workflow-resolutions', encoded(conflict))
            except Rejected as rejection:
                if rejection.status != 409 or rejection.body.get('code') != 'KEY_CONFLICT':
                    raise
                save(output / 'same-request-conflict.json', {'request': conflict,
                    'status': rejection.status, 'response': rejection.body})
            else:
                raise AssertionError('conflicting content replaced the original save request')
            if provider_effects(site):
                raise AssertionError('configuration conflict caused a native effect')
            selected = original
            if target_letter == 'b':
                select_reference(page.get_by_label('part context', exact=True), site.refs['material.b'])
                selected = save_configuration()
                if selected['report']['request'] != site.requests[1]:
                    raise AssertionError('saved B configuration differs from approved candidate')
                prior = engineer.get('/api/v1/workflow-resolution', catalog=original['reference']['catalog'], id=original['reference']['id'])
                if prior != original:
                    raise AssertionError('old saved configuration changed')
            page.screenshot(path=str(output / 'configured.png'), full_page=True)
            reload_page()
            page.get_by_role('button', name='Workflow design', exact=True).click()
            page.get_by_label('Authoring catalog', exact=True).select_option(site.workflow['workflow']['catalog'])
            page.get_by_text('Saved Task configurations', exact=True).click()
            page.get_by_role('button', name=re.compile(re.escape(selected['reference']['id']))).click()
            expect(page.get_by_role('heading', name='Run saved Task', exact=True)).to_be_visible()
            # The reopened receipt itself is read from P; no extra Save is needed to execute it.
            saved = engineer.get('/api/v1/workflow-resolution', catalog=selected['reference']['catalog'], id=selected['reference']['id'])
            if saved != selected:
                raise AssertionError('reopened configuration identity or values changed')
            execution = page.get_by_role('region', name='Run saved Task')
            execution.get_by_label('Simulation cell', exact=True).select_option(site.cell)
            with page.expect_response(lambda response: response.url.endswith('/api/v1/workflow-executions/runs')
                                       and response.request.method == 'POST') as pending:
                execution.get_by_role('button', name='Prepare execution', exact=True).click()
            creation = pending.value
            if not creation.ok:
                raise AssertionError('UI run preparation failed: ' + creation.text())
            bound = creation.json()['binding']
            site.run = bound['run']
            save(output / 'run-created.json', creation.json())
            expect(execution.get_by_label('Material to use', exact=True)).to_be_enabled()
            select_reference(execution.get_by_label('Material to use', exact=True), site.refs['object.' + target_letter])
            with page.expect_response(lambda response: response.url.endswith('/api/v1/workflow-executions/objects')
                                       and response.request.method == 'POST') as pending:
                execution.get_by_role('button', name='Confirm material', exact=True).click()
            if not pending.value.ok:
                raise AssertionError('UI material binding failed: ' + pending.value.text())
            starts = []
            if site.case == 'lost-start-response':
                def lose_reply(route):
                    starts.append(route.request.post_data_json)
                    reply = route.fetch()
                    if not reply.ok:
                        raise AssertionError(reply.text())
                    save(output / 'start-committed-discarded.json', reply.json())
                    route.abort('failed')
                page.route('**/api/v1/workflow-executions/start', lose_reply, times=1)
                execution.get_by_role('button', name='Run Task in simulation', exact=True).click()
                expect(page.get_by_role('button', name='Check original request', exact=True)).to_be_visible()
                reload_page()
                with page.expect_request(lambda req: req.url.endswith('/api/v1/workflow-executions/start')) as retry:
                    page.get_by_role('button', name='Check original request', exact=True).click()
                if retry.value.post_data_json != starts[0]:
                    raise AssertionError('lost browser reply caused a new start identity/body')
            else:
                with page.expect_response(lambda response: response.url.endswith('/api/v1/workflow-executions/start')
                                           and response.request.method == 'POST') as pending:
                    execution.get_by_role('button', name='Run Task in simulation', exact=True).click()
                if not pending.value.ok:
                    raise AssertionError('UI start failed: ' + pending.value.text())
                starts.append(pending.value.request.post_data_json)
            save(output / 'start-request.json', starts[0])
            client = ExecutionClient(Terminal(site.connections['engineer']), site.root / 'inspection-client')
            def inspect():
                return client.inspect_execution(site.run, reports=True)
            loss_operation = None
            prior_loss_custody = None
            def terminal(receipt):
                nonlocal loss_operation, prior_loss_custody
                result = receipt['result']
                if site.case == 'completion-loss':
                    if not result['work']:
                        return False
                    if len(result['work']) != 1:
                        raise AssertionError('completion loss admitted later work before the loss proof')
                    first = result['work'][0]
                    operation = first['operation']
                    if loss_operation is None:
                        loss_operation = operation['operation_id']
                    if operation['operation_id'] != loss_operation or operation['outcome'] != 'NONE':
                        raise AssertionError('completion loss replaced or settled its original operation')
                    if (operation['execution_knowledge'] != 'UNKNOWN'
                            or operation['phase'] != 'RECONCILING'
                            or operation['disposition'] != 'QUARANTINED'):
                        prior_loss_custody = None
                        return False
                    rows = completed_loss_audit(site)
                    if not any(row.get('mode') == 'execute' for row in rows):
                        prior_loss_custody = None
                        return False
                    applied = provider_effects(site)
                    if (len(applied) != 1 or applied[0]['operation'] != loss_operation
                            or applied[0]['invocation'] != first['invocation']
                            or applied[0]['selection'] != first['execution']['selection']):
                        raise AssertionError('completed loss audit lacks its one correlated native effect')
                    verify_withheld_completion(site, first, applied[0], rows, output)
                    current = unknown_custody(receipt, first,
                        site.templates['shelf-seat']['action']['intent']['resource_set'])
                    stable = current == prior_loss_custody
                    prior_loss_custody = current
                    return stable
                return result['run']['value']['state'] not in ('PREPARED', 'EXECUTING')
            receipt = wait_for(inspect, terminal, timeout=90)
            save(output / 'runtime-receipt.json', receipt)
            effects = provider_effects(site)
            save(output / 'provider-effects.json', effects)
            state = json.loads(site.d.run('exec', site.services['h'], 'cat', '/data/material-alignment/state.json'))
            save(output / 'provider-state.json', state)
            work = receipt['result']['work']
            expected_count = 1 if site.case == 'completion-loss' else 2 if site.case == 'groove-missing' else 6
            if len(effects) != expected_count or len({effect['operation'] for effect in effects}) != expected_count:
                raise AssertionError('unexpected or duplicate native effects')
            by_operation = {w['operation']['operation_id']: w for w in work}
            for effect in effects:
                linked = by_operation.get(effect['operation'])
                if linked is None or linked['execution']['selection'] != effect['selection']:
                    raise AssertionError('independent provider/P operation correlation differs')
                if effect['invocation'] != linked['invocation']:
                    raise AssertionError('provider/P invocation identity differs')
            expected_model = 'sim/material-' + target_letter
            if any(e['parameters']['material_model']['value']['data']['value'] != expected_model for e in effects):
                raise AssertionError('actual provider did not consume selected material')
            expected_angle = 120 if target_letter == 'b' else 95
            if any(e['parameters']['groove_angle_deg']['value']['data']['range'] != {
                    'min': expected_angle, 'max': expected_angle} for e in effects):
                raise AssertionError('actual provider did not consume the selected material angle')
            if site.case == 'groove-missing':
                failed = by_operation[effects[-1]['operation']]['operation']
                first = by_operation[effects[0]['operation']]['operation']
                if (effects[-1]['status'] != 10 or not state['shelf_occupied']
                        or failed['outcome'] != 'FAILED' or failed['execution_knowledge'] != 'ENDED'
                        or failed['phase'] != 'SETTLED' or first['outcome'] != 'SUCCEEDED'
                        or len(work) != 2 or {e['node'] for e in effects} != {'shelf-seat', 'groove-detect'}
                        or any(w['operation']['execution_knowledge'] == 'UNKNOWN' for w in work)):
                    raise AssertionError('known groove failure was hidden or changed to UNKNOWN')
            elif site.case == 'completion-loss':
                if len(work) != 1 or effects[0]['node'] != 'shelf-seat':
                    raise AssertionError('completion loss admitted work beyond the original A1')
                required_resources = site.templates['shelf-seat']['action']['intent']['resource_set']
                custody = unknown_custody(receipt, work[0], required_resources)
                save(output / 'unknown-original-custody.json', custody)
                loss_records = completed_loss_audit(site)
                save(output / 'withheld-native-results.json', loss_records)
                verify_withheld_completion(site, work[0], effects[0], loss_records, output)
                time.sleep(1)
                again = inspect()
                if provider_effects(site) != effects or unknown_custody(again, work[0], required_resources) != custody:
                    raise AssertionError('UNKNOWN inspection changed effects, identity or resource/slot custody')
                save(output / 'unknown-original-reinspection.json', again)
            else:
                if receipt['result']['run']['value']['state'] != 'COMPLETED' or state['shelf_occupied'] or not state['ft']['seated']:
                    raise AssertionError('normal Task lacks native final seating and clear shelf proof')
                if any(w['operation']['outcome'] != 'SUCCEEDED' for w in work):
                    raise AssertionError('normal Task contains a non-successful operation')
            def observed_sources():
                overview = engineer.get('/api/v1/overview')
                row = next(c for c in overview['cells'] if c['cell']['value']['id'] == site.cell)
                return {s['source']: s for s in row['diagnostics']['sources']}
            if site.case != 'completion-loss':
                actual = wait_for(observed_sources, lambda sources:
                    sources.get('shelf.occupied', {}).get('usable') is True
                    and sources['shelf.occupied']['observation']['value'] == {'boolean': state['shelf_occupied']})
                save(output / 'provider-observations-through-p.json', actual)
            # Restore original saved config/run after refresh and verify same graph result is visible.
            reload_page()
            page.get_by_role('button', name='Workflow design', exact=True).click()
            page.get_by_label('Authoring catalog', exact=True).select_option(site.workflow['workflow']['catalog'])
            page.get_by_text('Saved Task configurations', exact=True).click()
            page.get_by_role('button', name=re.compile(re.escape(selected['reference']['id']))).click()
            execution = page.get_by_role('region', name='Run saved Task')
            execution.get_by_label('Simulation cell', exact=True).select_option(site.cell)
            execution.get_by_label('Execution record', exact=True).select_option(site.run)
            graph = page.get_by_role('region', name='Task action graph')
            actions = graph.get_by_role('button', name=re.compile(r'^Action [0-9]+:'))
            expect(actions).to_have_count(6)
            if site.case == 'completion-loss':
                expect(actions.nth(0)).to_contain_text('UNKNOWN · original operation retained', timeout=20000)
                graph.locator('li').first.locator('summary').click()
                original_id = work[0]['operation']['operation_id']
                expect(graph.get_by_text('Operation ' + original_id, exact=True)).to_be_visible()
                expect(graph.get_by_role('status')).to_have_count(0, timeout=10000)
                delayed = []
                def delay_read(route):
                    if (route.request.method != 'GET'
                            or parse_qs(urlsplit(route.request.url).query) != {'run': [site.run]}):
                        raise AssertionError('delayed read does not name the original Run')
                    delayed.append((route, time.monotonic()))
                    # Leave this real browser request pending without fetching/fabricating a reply.
                page.route('**/api/v1/runtime-skill-result?*', delay_read, times=1)
                deadline = time.monotonic() + 10
                while not delayed and time.monotonic() < deadline:
                    page.wait_for_timeout(50)
                if len(delayed) != 1:
                    raise AssertionError('original result read was not intercepted for the delay check')
                expect(graph.get_by_role('status')).to_contain_text('Last retrieved results', timeout=3000)
                expect(actions.nth(0)).to_contain_text('UNKNOWN · original operation retained')
                expect(graph.get_by_text('Operation ' + original_id, exact=True)).to_be_visible()
                expect(execution.get_by_role('button', name='Run Task in simulation', exact=True)).to_have_count(0)
                page.screenshot(path=str(output / 'unknown-during-pending-read.png'), full_page=True)
                elapsed_ms = (time.monotonic() - delayed[0][1]) * 1000
                save(output / 'pending-result-read.json', {'run': site.run, 'operation': original_id,
                    'elapsed_ms': elapsed_ms, 'browser_api_timeout_ms': 15000,
                    'original_unknown_visible': True, 'last_retrieved_label_visible': True,
                    'request_still_withheld': True})
                if elapsed_ms >= 15000:
                    raise AssertionError('pending-read label was not verified before the existing API timeout')
                delayed[0][0].continue_()
                page.unroute('**/api/v1/runtime-skill-result?*', delay_read)
                expect(graph.get_by_role('status')).to_have_count(0, timeout=10000)
                state_flags['read_loss'] = True
                page.route('**/api/v1/runtime-skill-result?*', lambda route: route.abort('failed'))
                expect(graph.get_by_role('status')).to_contain_text('Last retrieved results', timeout=20000)
                expect(actions.nth(0)).to_contain_text('UNKNOWN · original operation retained')
                expect(graph.get_by_text('Operation ' + original_id, exact=True)).to_be_visible()
                expect(execution.get_by_role('button', name='Run Task in simulation', exact=True)).to_have_count(0)
                page.screenshot(path=str(output / 'unknown-during-read-loss.png'), full_page=True)
                page.unroute('**/api/v1/runtime-skill-result?*')
                state_flags['read_loss'] = False
                final_unknown = inspect()
                if (unknown_custody(final_unknown, work[0], required_resources) != custody
                        or provider_effects(site) != effects):
                    raise AssertionError('browser fault checks changed original UNKNOWN work or custody')
                save(output / 'unknown-after-browser-read-faults.json', final_unknown)
            elif site.case == 'groove-missing':
                expect(actions.nth(0)).to_contain_text('SUCCEEDED', timeout=20000)
                expect(actions.nth(1)).to_contain_text('FAILED')
                expect(execution.locator('[data-source="shelf.occupied"]')).to_contain_text('True')
                expect(execution.locator('[data-source="vision.result_available"]')).to_contain_text('True')
                expect(execution.locator('[data-source="vision.groove_detected"]')).to_contain_text('False')
                for index in range(2, 6):
                    expect(actions.nth(index)).not_to_contain_text('SUCCEEDED')
            else:
                expect(execution.get_by_role('status')).to_contain_text('COMPLETED', timeout=20000)
                for index in range(6):
                    expect(actions.nth(index)).to_contain_text('SUCCEEDED')
                expect(execution.locator('[data-source="shelf.occupied"]')).to_contain_text('False')
            page.screenshot(path=str(output / 'reopened-result.png'), full_page=True)
            if diagnostics['page_errors'] or any(not item['expected'] for key in (
                    'failed_requests', 'console_errors', 'http_errors') for item in diagnostics[key]):
                raise AssertionError('browser has unexpected page/network failures')
            save(output / 'saved-configurations.json', saved_receipts)
            save(output / 'result.json', {'status': 'PASS', 'case': site.case, 'run': site.run,
                'workflow': site.workflow['workflow'], 'publication': site.publication['reference'],
                'saved_configuration': selected['reference'], 'native_effects': len(effects),
                'owner_acceptance': 'USER_ACCEPTANCE_PENDING'})
        except Exception:
            page.screenshot(path=str(output / 'failure.png'), full_page=True)
            if state_flags['authenticated']:
                (output / 'failure-accessibility.txt').write_text(page.locator('body').aria_snapshot())
            raise
        finally:
            save(output / 'browser-diagnostics.json', diagnostics)
            browser.close()
