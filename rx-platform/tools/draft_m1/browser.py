"""Actual operator bundle -> P -> Executor -> external Host provider checks."""
from __future__ import annotations

import re
import time

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
        page.on('requestfailed', lambda request: diagnostics['failed_requests'].append({
            'path': request.url.split('?', 1)[0].removeprefix(site.origin),
            'error': request.failure, 'expected': (site.case == 'lost-start-response'
            and request.url.endswith('/api/v1/workflow-executions/start')) or (
                state_flags['read_loss'] and request.url.split('?', 1)[0].endswith('/api/v1/runtime-skill-result')) or (
                state_flags['navigating'] and request.method == 'GET' and request.failure == 'net::ERR_ABORTED')}))
        def reload_page():
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
            def terminal(receipt):
                result = receipt['result']
                if site.case == 'completion-loss':
                    return any(w['operation']['execution_knowledge'] == 'UNKNOWN' for w in result['work'])
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
                operation = work[0]['operation']
                if operation['execution_knowledge'] != 'UNKNOWN' or operation['disposition'] == 'RELEASED':
                    raise AssertionError('native completion loss did not preserve UNKNOWN custody')
                withheld = site.d.run('exec', site.services['h'], 'cat', '/data/material-alignment/withheld.jsonl')
                save(output / 'withheld-native-results.json', [json.loads(line) for line in withheld.splitlines()])
                time.sleep(1)
                again = inspect()
                if provider_effects(site) != effects or again['result']['work'][0]['operation']['operation_id'] != operation['operation_id']:
                    raise AssertionError('UNKNOWN inspection replayed work or replaced the operation')
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
                state_flags['read_loss'] = True
                page.route('**/api/v1/runtime-skill-result?*', lambda route: route.abort('failed'))
                expect(graph.get_by_role('status')).to_contain_text('Last retrieved results', timeout=20000)
                expect(actions.nth(0)).to_contain_text('UNKNOWN · original operation retained')
                expect(graph.get_by_text('Operation ' + original_id, exact=True)).to_be_visible()
                expect(execution.get_by_role('button', name='Run Task in simulation', exact=True)).to_have_count(0)
                page.screenshot(path=str(output / 'unknown-during-read-loss.png'), full_page=True)
                page.unroute('**/api/v1/runtime-skill-result?*')
                state_flags['read_loss'] = False
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
