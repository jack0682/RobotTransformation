import { z } from './schema-runtime';
import { api } from './api';
import {
  artifactSchema,
  counter,
  installationSchema,
  operationSchema,
  runSchema,
  startCommandSchema,
  timeSchema,
  type Pending,
} from './schema';
import { definitionRefSchema, refKey } from './definition-schema';
import { stableDocument } from './draft-schema';
import { workflowRequestSchema, type WorkflowReceipt } from './workflow-schema';

export const executionBase = '/api/v1/workflow-executions/';
export type ExecutionRoute =
  '/api/v1/workflow-executions/runs' | '/api/v1/workflow-executions/objects';
export const executionMutation = (route: string) =>
  route === executionBase + 'runs' || route === executionBase + 'objects';
const same = (a: unknown, b: unknown) => stableDocument(a) === stableDocument(b);
const pinQuery = (pin: z.infer<typeof definitionRefSchema>) => new URLSearchParams(pin);
export const executionRunSchema = z.object({
  run: z.uuid(),
  cell: z.string(),
  publication: definitionRefSchema,
  policy: artifactSchema,
  configuration: artifactSchema,
  request: z.uuid(),
  actor: z.string(),
  slots: z.array(z.object({ ordinal: counter, slot_ordinal: counter, index: z.number().int() })),
  pools: z.array(z.object({ resource: definitionRefSchema, generation: counter })),
});
export const executionObjectSchema = z.object({
  run: z.uuid(),
  cell: z.string(),
  ordinal: counter,
  object: definitionRefSchema,
  model: definitionRefSchema,
  candidate: z.number().int().min(0),
  slot: z.number().int().min(0),
  request: z.uuid(),
  actor: z.string(),
});
export type ExecutionReceipt = {
  route: string;
  command: Record<string, unknown>;
  value: unknown;
};
export function validateExecutionReceipt(record: Pending, raw: unknown) {
  if (record.route === executionBase + 'runs') {
    const value = z
      .object({
        binding: executionRunSchema,
        state: z.literal('PREPARED'),
        operation_authorized: z.literal(false),
      })
      .parse(raw);
    if (
      value.binding.cell !== record.command.cell ||
      !same(value.binding.publication, record.command.publication) ||
      String(value.binding.slots.length) !== record.command.count ||
      value.binding.request !== record.request_key ||
      value.binding.actor !== record.principal
    )
      throw new Error('Run receipt differs from the original request');
    return value;
  }
  if (record.route !== executionBase + 'objects') throw new Error('Unsupported execution request');
  const value = executionObjectSchema.parse(raw);
  if (
    value.run !== record.command.run ||
    value.ordinal !== record.command.ordinal ||
    !same(value.object, record.command.object) ||
    value.request !== record.request_key ||
    value.actor !== record.principal
  )
    throw new Error('Material receipt differs from the original request');
  return value;
}
export const executionStartContextSchema = z.object({
  installation: installationSchema,
  cell: z.string(),
  cell_revision: counter,
  epoch: counter,
  scope_epochs: z.record(z.string(), counter),
  environment: z.literal('SIMULATION'),
  recipe: artifactSchema.extend({ schema_id: z.literal('rx.execution-plan.v2') }),
  run: runSchema,
  request: startCommandSchema,
  can_request: z.boolean(),
  blocking_reason: z.string().nullable(),
});
const publicationSchema = z.object({
  reference: definitionRefSchema,
  preview: definitionRefSchema,
  cell: z.string(),
  policy: artifactSchema,
});
const installedSchema = z.object({
  revision: counter,
  value: z.object({
    configuration: z.object({
      id: z.string(),
      environment: z.literal('SIMULATION'),
      execution: z.object({ publication: definitionRefSchema, policy: artifactSchema }),
    }),
  }),
});
const previewSchema = z.object({
  preview: z.object({ reference: definitionRefSchema, workflow: definitionRefSchema }),
  policy: z.object({
    schema: z.literal('rx.execution-policy.v2'),
    workflow: definitionRefSchema,
    candidates: z.array(z.object({ object_model: definitionRefSchema })),
  }),
});
export const inputClosureSchema = z.object({
  schema: z.literal('rx.execution-input-closure.v2'),
  workflow: definitionRefSchema,
  requests: z.array(workflowRequestSchema),
});
export function matchingCandidate(
  receipt: WorkflowReceipt,
  inputs: z.infer<typeof inputClosureSchema>,
) {
  if (
    !receipt.report.valid ||
    !receipt.report.concrete ||
    refKey(receipt.report.request.workflow) !== refKey(inputs.workflow)
  )
    throw new Error('Save a valid concrete configuration for this installed Task');
  const request = { ...receipt.report.request, slot_index: '0' };
  const matches = inputs.requests.flatMap((item, i) =>
    same({ ...item, slot_index: '0' }, request) ? [i] : [],
  );
  if (matches.length !== 1)
    throw new Error('These settings need installation and qualification before execution');
  return matches[0];
}
export async function installedTask(cell: string, receipt: WorkflowReceipt) {
  const current = installedSchema.parse(
    await api(`/api/v1/cell?${new URLSearchParams({ id: cell })}`),
  );
  if (current.value.configuration.id !== cell) throw new Error('Installed cell differs');
  const binding = current.value.configuration.execution;
  const publication = publicationSchema.parse(
    await api(`${executionBase}publication?${pinQuery(binding.publication)}`),
  );
  if (
    publication.cell !== cell ||
    refKey(publication.reference) !== refKey(binding.publication) ||
    !same(publication.policy, binding.policy)
  )
    throw new Error('Installed publication differs');
  const preview = previewSchema.parse(
    await api(`${executionBase}preview?${pinQuery(publication.preview)}`),
  );
  if (
    refKey(preview.preview.reference) !== refKey(publication.preview) ||
    refKey(preview.policy.workflow) !== refKey(receipt.report.request.workflow)
  )
    throw new Error('Installed Task version differs from saved settings');
  const params = pinQuery(publication.preview);
  params.set('artifact', 'inputs');
  const inputs = inputClosureSchema.parse(await api(`${executionBase}material?${params}`));
  const candidate = matchingCandidate(receipt, inputs);
  const model = preview.policy.candidates[candidate]?.object_model;
  if (!model) throw new Error('Installed material candidate is missing');
  return {
    cell,
    revision: current.revision,
    publication: publication.reference,
    policy: publication.policy,
    candidate,
    model,
  };
}
export type InstalledTask = Awaited<ReturnType<typeof installedTask>>;
const executionWorkSchema = z.object({
  part: z.uuid().nullable(),
  operation: operationSchema,
  invocation: z.uuid().nullable(),
  native_results: z
    .array(
      z.object({
        evidence: z.uuid(),
        invocation: z.uuid(),
        status_schema: z.string(),
        status: z.string().regex(/^-?(0|[1-9][0-9]*)$/),
        captured_at: timeSchema,
      }),
    )
    .default([]),
  resources: z.array(z.object({ revision: counter, value: z.object({}).passthrough() })),
  execution: z.object({
    operation: z.uuid(),
    publication: definitionRefSchema,
    policy: artifactSchema,
    selection: z.object({
      run: z.uuid(),
      node: z.string(),
      object: definitionRefSchema,
      candidate: z.number().int(),
      part: z.uuid(),
      ordinal: counter,
      slot: z.number().int().min(0),
    }),
  }),
});
export const executionResultSchema = z.object({
  schema: z.literal('rx.runtime-skill-result.v1'),
  result_owner: z.literal('PLATFORM'),
  installation: installationSchema,
  run: z.object({ revision: counter, value: runSchema }),
  details_truncated: z.boolean(),
  current_binding_matches: z.boolean(),
  work: z.array(executionWorkSchema),
});
export type ExecutionResult = z.infer<typeof executionResultSchema>;
export function validateExecutionResult(
  raw: unknown,
  binding: z.infer<typeof executionRunSchema>,
  material: z.infer<typeof executionObjectSchema> | null,
) {
  const result = executionResultSchema.parse(raw);
  if (
    result.run.value.id !== binding.run ||
    result.run.value.cell !== binding.cell ||
    result.work.some(
      (w) =>
        !material ||
        refKey(w.execution.selection.object) !== refKey(material.object) ||
        w.execution.selection.candidate !== material.candidate ||
        w.execution.selection.slot !== material.slot ||
        w.execution.selection.ordinal !== material.ordinal ||
        w.execution.selection.part !== w.part ||
        !result.run.value.part_ids.includes(w.execution.selection.part) ||
        w.native_results.some(
          (native) =>
            native.invocation !== w.invocation ||
            !w.operation.evidence_ids.includes(native.evidence),
        ) ||
        w.execution.selection.run !== binding.run ||
        w.execution.operation !== w.operation.operation_id ||
        refKey(w.execution.publication) !== refKey(binding.publication) ||
        !same(w.execution.policy, binding.policy),
    )
  )
    throw new Error('Execution result belongs to a different Task or operation');
  return result;
}
