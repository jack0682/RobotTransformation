import { useEffect, useRef, useState } from 'react';
import { api, ApiFailure, explain } from './api';
import { formatValue } from './conditions';
import {
  definitionPageSchema,
  definitionViewSchema,
  refKey,
  type DefinitionRef,
} from './definition-schema';
import type { Overview, Pending } from './schema';
import type { WorkflowReceipt } from './workflow-schema';
import {
  executionBase,
  executionObjectSchema,
  executionRunSchema,
  executionStartContextSchema,
  installedTask,
  validateExecutionResult,
  type ExecutionReceipt,
  type ExecutionResult,
  type InstalledTask,
} from './workflow-execution-schema';
import type { z } from './schema-runtime';

export function WorkflowExecution({
  data,
  receipt,
  locked,
  cell,
  onSelectCell,
  selectedRun,
  onSelectRun,
  onSubmit,
  latest,
  onResult,
  onFresh,
  canExecute,
}: {
  data: Overview;
  receipt: WorkflowReceipt;
  locked: boolean;
  cell: string;
  onSelectCell: (cell: string) => void;
  selectedRun: string;
  onSelectRun: (run: string) => void;
  onSubmit: (request: Pending) => Promise<void>;
  latest: ExecutionReceipt | null;
  onResult: (result: ExecutionResult | null) => void;
  onFresh: (fresh: boolean) => void;
  canExecute: boolean;
}) {
  const [installed, setInstalled] = useState<InstalledTask | null>(null);
  const [objects, setObjects] = useState<Array<{ reference: DefinitionRef; label: string }>>([]);
  const [object, setObject] = useState('');
  const [bound, setBound] = useState<z.infer<typeof executionRunSchema> | null>(null);
  const [material, setMaterial] = useState<z.infer<typeof executionObjectSchema> | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [resultFresh, setResultFresh] = useState(false);
  const resultKey = useRef('');
  const selectedCell = data.cells.find((c) => c.cell.value.id === cell);
  useEffect(() => {
    let cancelled = false;
    setInstalled(null);
    setObjects([]);
    setObject('');
    setError('');
    if (!cell) return;
    setBusy(true);
    void (async () => {
      const value = await installedTask(cell, receipt);
      const choices: Array<{ reference: DefinitionRef; label: string }> = [];
      let after: string | null = null;
      do {
        const params = new URLSearchParams({ catalog: value.model.catalog, archived: 'false' });
        if (after) params.set('after', after);
        const page = definitionPageSchema.parse(await api(`/api/v1/definitions?${params}`));
        for (const item of page.definitions.filter((d) => d.kind === 'OBJECT_INSTANCE')) {
          const pin = item.reference;
          const detail = definitionViewSchema.parse(
            await api(
              `/api/v1/definition?${new URLSearchParams({ catalog: pin.catalog, id: pin.id, revision: pin.revision })}`,
            ),
          );
          const definition = detail.version.definition;
          if (refKey(definition.reference) !== refKey(pin))
            throw new Error('Material revision differs');
          if (
            definition.body.kind === 'OBJECT_INSTANCE' &&
            refKey(definition.body.base) === refKey(value.model)
          )
            choices.push(item);
        }
        after = page.next;
      } while (after && !cancelled);
      if (!cancelled) {
        setInstalled(value);
        setObjects(choices);
      }
    })()
      .catch((e) => {
        if (!cancelled) setError(explain(e));
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cell, receipt, reload]);
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const key = JSON.stringify([
      selectedRun,
      receipt.reference,
      data.installation.id,
      data.installation.store_generation,
    ]);
    if (resultKey.current !== key) {
      resultKey.current = key;
      setBound(null);
      setMaterial(null);
      setResult(null);
      onResult(null);
    }
    setResultFresh(false);
    onFresh(false);
    if (!selectedRun || !installed) return;
    const inspect = async () => {
      // Preserve the last evidence while this new read is still unverified.
      setResultFresh(false);
      onFresh(false);
      try {
        const binding = executionRunSchema.parse(
          await api(`${executionBase}runs?${new URLSearchParams({ run: selectedRun })}`),
        );
        if (binding.cell !== cell || refKey(binding.publication) !== refKey(installed.publication))
          throw new Error('Selected run uses a different installed Task');
        if (
          binding.slots.length !== 1 ||
          String(binding.slots[0].index) !== receipt.report.request.slot_index
        )
          throw new Error('Selected run slot differs from saved settings');
        let assigned = null;
        try {
          assigned = executionObjectSchema.parse(
            await api(
              `${executionBase}objects?${new URLSearchParams({ run: selectedRun, ordinal: '1' })}`,
            ),
          );
          if (
            assigned.run !== selectedRun ||
            assigned.candidate !== installed.candidate ||
            refKey(assigned.model) !== refKey(installed.model)
          )
            throw new Error('Selected run material differs from saved settings');
        } catch (e) {
          if (!(e instanceof ApiFailure && e.status === 404)) throw e;
        }
        const status = validateExecutionResult(
          await api(`/api/v1/runtime-skill-result?${new URLSearchParams({ run: selectedRun })}`),
          binding,
          assigned,
        );
        if (
          status.installation.id !== data.installation.id ||
          status.installation.store_generation !== data.installation.store_generation
        )
          throw new Error('Execution belongs to a different installation');
        if (!cancelled) {
          setBound(binding);
          setMaterial(assigned);
          setResult(status);
          onResult(status);
          setResultFresh(true);
          onFresh(true);
          setError('');
          timer = setTimeout(() => void inspect(), 1500);
        }
      } catch (e) {
        if (!cancelled) {
          setError(explain(e));
          setResultFresh(false);
          onFresh(false);
          timer = setTimeout(() => void inspect(), 1500);
        }
      }
    };
    void inspect();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [
    selectedRun,
    installed,
    latest,
    reload,
    cell,
    receipt,
    data.installation.id,
    data.installation.store_generation,
    onResult,
    onFresh,
  ]);
  function request(
    route: Pending['route'],
    command: Record<string, unknown>,
    label: string,
    review?: Pending['start_review'],
  ) {
    if (!canExecute || locked || busy) return Promise.resolve();
    return onSubmit({
      route,
      command,
      label,
      request_key: crypto.randomUUID(),
      principal: data.user.principal,
      installation: data.installation.id,
      store_generation: data.installation.store_generation,
      ...(review ? { start_review: review } : {}),
    });
  }
  async function start() {
    if (!bound || !material || !installed) return;
    setBusy(true);
    setError('');
    try {
      const context = executionStartContextSchema.parse(
        await api(
          `${executionBase}start-context?${new URLSearchParams({ cell, run: bound.run, purpose: 'PRODUCTION', budget_limit: '1' })}`,
        ),
      );
      if (!context.can_request || context.blocking_reason)
        throw new Error(context.blocking_reason ?? 'Start conditions require review');
      if (
        context.cell !== cell ||
        context.run.id !== bound.run ||
        context.request.run !== bound.run ||
        context.request.budget_limit !== '1' ||
        context.installation.id !== data.installation.id ||
        context.installation.store_generation !== data.installation.store_generation ||
        context.installation.runtime_boot !== data.installation.runtime_boot
      )
        throw new Error('Start context changed');
      await request(
        '/api/v1/workflow-executions/start',
        context.request,
        'Run configured simulation Task',
        {
          cell,
          epoch: context.epoch,
          scope_epochs: context.scope_epochs,
          recipe_digest: context.recipe.sha256,
          runtime_boot: context.installation.runtime_boot,
        },
      );
      setReload((n) => n + 1);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  }
  const selectedObject = objects.find((o) => refKey(o.reference) === object);
  return (
    <section className="inset" aria-label="Run saved Task">
      <h3>Run saved Task</h3>
      {!data.user.roles.includes('OPERATOR') && (
        <p>An Operator role is required to execute this Task.</p>
      )}
      {!data.user.terminal && <p>Use a registered terminal to execute this Task.</p>}
      <label>
        Simulation cell
        <select
          aria-label="Simulation cell"
          value={cell}
          disabled={locked || busy || !!selectedRun}
          onChange={(e) => onSelectCell(e.target.value)}
        >
          <option value="">Select a cell</option>
          {data.cells
            .filter((c) => c.cell.value.environment === 'SIMULATION')
            .map((c) => (
              <option key={c.cell.value.id} value={c.cell.value.id}>
                {c.cell.value.id}
              </option>
            ))}
        </select>
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {installed && (
        <>
          <p>
            These saved settings match an installed candidate. Current start conditions are checked
            again before execution.
          </p>
          <label>
            Execution record
            <select
              aria-label="Execution record"
              value={selectedRun}
              disabled={locked || busy}
              onChange={(e) => onSelectRun(e.target.value)}
            >
              <option value="">Prepare a new execution</option>
              {selectedRun && !selectedCell?.runs.some((r) => r.value.id === selectedRun) && (
                <option value={selectedRun}>{selectedRun}</option>
              )}
              {selectedCell?.runs.map((r) => (
                <option key={r.value.id} value={r.value.id}>
                  {r.value.state} · {r.value.id}
                </option>
              ))}
            </select>
          </label>
          {!selectedRun && (
            <button
              disabled={locked || busy || !canExecute || !data.user.terminal}
              onClick={() =>
                void request(
                  '/api/v1/workflow-executions/runs',
                  {
                    cell,
                    publication: installed.publication,
                    expected_cell: installed.revision,
                    count: '1',
                  },
                  'Prepare configured Task execution',
                )
              }
            >
              Prepare execution
            </button>
          )}
          {bound && !material && (
            <>
              <label>
                Material to use
                <select
                  aria-label="Material to use"
                  value={object}
                  disabled={locked || busy}
                  onChange={(e) => setObject(e.target.value)}
                >
                  <option value="">Select the actual material</option>
                  {objects.map((o) => (
                    <option key={refKey(o.reference)} value={refKey(o.reference)}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                disabled={locked || busy || !canExecute || !resultFresh || !selectedObject}
                onClick={() =>
                  selectedObject &&
                  void request(
                    '/api/v1/workflow-executions/objects',
                    { run: bound.run, ordinal: '1', object: selectedObject.reference },
                    'Confirm selected material',
                  )
                }
              >
                Confirm material
              </button>
            </>
          )}
          {material && result?.run.value.state === 'PREPARED' && (
            <button
              className="primary"
              disabled={locked || busy || !canExecute || !resultFresh || !data.user.terminal}
              onClick={() => void start()}
            >
              Run Task in simulation
            </button>
          )}
          {result && (
            <p role="status">
              {resultFresh ? 'Execution' : 'Last retrieved execution'} {result.run.value.state}
              {!result.current_binding_matches ? ' · installation has changed' : ''}
              {result.details_truncated ? ' · partial result list' : ''}
            </p>
          )}
          {selectedCell && (
            <section aria-label="Last reported device observations">
              <h4>Last reported device observations</h4>
              <dl className="facts">
                {selectedCell.diagnostics.sources.map((source) => (
                  <div key={source.source} data-source={source.source}>
                    <dt>{source.source}</dt>
                    <dd>
                      {source.observation ? formatValue(source.observation.value) : 'UNKNOWN'}
                      {' · '}
                      {source.usable
                        ? 'Usable at the last read'
                        : 'Current value needs verification'}
                      {source.issues.length ? ` (${source.issues.join(', ')})` : ''}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </>
      )}
      <button disabled={locked || busy} onClick={() => setReload((n) => n + 1)}>
        Refresh execution records
      </button>
    </section>
  );
}
