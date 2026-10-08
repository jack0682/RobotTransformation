import { expect, it } from 'vitest';
import { validateExecutionReceipt, validateExecutionResult } from './workflow-execution-schema';
import type { Pending } from './schema';
const id = (n: string) =>
  `${n.repeat(8)}-${n.repeat(4)}-4${n.repeat(3)}-8${n.repeat(3)}-${n.repeat(12)}`;
const pin = { catalog: id('1'), id: id('2'), revision: '1', digest: 'a'.repeat(64) };
const artifact = { schema_id: 'rx.execution-policy.v2', sha256: 'b'.repeat(64), size_bytes: '123' };
const binding = {
  run: id('3'),
  cell: 'cell/sim',
  publication: pin,
  policy: artifact,
  configuration: artifact,
  request: id('4'),
  actor: 'operator',
  slots: [{ ordinal: '1', slot_ordinal: '1', index: 0 }],
  pools: [],
};
const pending: Pending = {
  request_key: id('4'),
  route: '/api/v1/workflow-executions/runs',
  principal: 'operator',
  installation: id('5'),
  store_generation: id('6'),
  label: 'Prepare task',
  command: { cell: 'cell/sim', publication: pin, expected_cell: '1', count: '1' },
};
it('requires a run receipt for the exact original actor, request, publication and count', () => {
  const result = { binding, state: 'PREPARED', operation_authorized: false };
  expect(validateExecutionReceipt(pending, result)).toEqual(result);
  for (const altered of [
    { request: id('7') },
    { actor: 'other' },
    { publication: { ...pin, revision: '2' } },
    { slots: [] },
  ]) {
    expect(() =>
      validateExecutionReceipt(pending, { ...result, binding: { ...binding, ...altered } }),
    ).toThrow();
  }
  expect(() =>
    validateExecutionReceipt(pending, { ...result, operation_authorized: true }),
  ).toThrow();
});
it('preserves UNKNOWN with custody and refuses cross-run result attribution', () => {
  const op = {
    operation_id: id('7'),
    revision: '2',
    phase: 'RECONCILING',
    execution_knowledge: 'UNKNOWN',
    outcome: 'NONE',
    integrity: 'VALID',
    disposition: 'HELD',
    evidence_ids: [],
  };
  const result = {
    schema: 'rx.runtime-skill-result.v1',
    result_owner: 'PLATFORM',
    installation: {
      id: id('5'),
      store_generation: id('6'),
      runtime_boot: id('8'),
      clock_id: 'clock',
    },
    run: {
      revision: '2',
      value: {
        id: binding.run,
        cell: binding.cell,
        state: 'RECOVERY_REQUIRED',
        purpose: 'PRODUCTION',
        budget: { unit: 'PART_ATTEMPT', limit: '1', revision: '1', consumptions: [] },
        recipe_digest: 'a'.repeat(64),
        envelope_digest: 'b'.repeat(64),
        part_ids: [id('a')],
      },
    },
    details_truncated: false,
    current_binding_matches: true,
    work: [
      {
        part: id('a'),
        operation: op,
        invocation: id('8'),
        resources: [],
        execution: {
          operation: op.operation_id,
          publication: pin,
          policy: artifact,
          selection: {
            run: binding.run,
            node: 'groove-detect',
            object: pin,
            candidate: 0,
            part: id('a'),
            ordinal: '1',
            slot: 0,
          },
        },
      },
    ],
  };
  const material = {
    run: binding.run,
    cell: binding.cell,
    ordinal: '1',
    object: pin,
    model: pin,
    candidate: 0,
    slot: 0,
    request: id('4'),
    actor: 'operator',
  };
  expect(
    validateExecutionResult(result, binding, material).work[0].operation.execution_knowledge,
  ).toBe('UNKNOWN');
  for (const changed of [
    { run: id('9') },
    { candidate: 1 },
    { slot: 1 },
    { part: id('b') },
    { object: { ...pin, id: id('c') } },
  ]) {
    const wrong = structuredClone(result);
    Object.assign(wrong.work[0].execution.selection, changed);
    expect(() => validateExecutionResult(wrong, binding, material)).toThrow();
  }
  expect(() => validateExecutionResult(result, binding, null)).toThrow();
});
