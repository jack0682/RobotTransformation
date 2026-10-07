import type { WorkflowModel, WorkflowReceipt } from './workflow-schema';
import { refKey } from './definition-schema';
import type { ExecutionResult } from './workflow-execution-schema';

/** Display the server model's ordered steps; this component never advances work. */
export function WorkflowTaskGraph({
  model,
  receipt,
  selected,
  onSelect,
  execution,
  executionFresh,
}: {
  model: WorkflowModel;
  receipt: WorkflowReceipt | null;
  selected: string;
  onSelect: (node: string) => void;
  execution: ExecutionResult | null;
  executionFresh: boolean;
}) {
  const report =
    receipt && refKey(receipt.report.request.workflow) === refKey(model.reference)
      ? receipt.report
      : null;
  return (
    <section className="task-graph" aria-label="Task action graph">
      <h3>{model.label}</h3>
      <p className="muted">Select an action to inspect its settings and value sources.</p>
      {execution && !executionFresh && (
        <p role="status">
          Last retrieved results. Current execution state needs verification; original evidence and
          custody remain shown.
        </p>
      )}
      <ol>
        {model.spec.steps.map((step, index) => {
          const work = execution?.work.filter((w) => w.execution.selection.node === step.id) ?? [];
          const issues = report?.violations.filter(
            (v) => v.location === `nodes/${step.id}` || v.location.startsWith(`nodes/${step.id}/`),
          );
          return (
            <li key={step.id}>
              <button
                type="button"
                aria-pressed={selected === step.id}
                aria-label={`Action ${index + 1}: ${model.spec.tasks[step.task]?.label ?? step.id}`}
                onClick={() => onSelect(step.id)}
              >
                <span className="task-step-number">{index + 1}</span>
                <strong>{model.spec.tasks[step.task]?.label ?? step.id}</strong>
                <span className={issues?.length ? 'error' : 'muted'}>
                  {work.length
                    ? work
                        .map((w) =>
                          w.operation.integrity === 'DISPUTED'
                            ? 'DISPUTED · QUARANTINED'
                            : w.operation.execution_knowledge === 'UNKNOWN'
                              ? 'UNKNOWN · original operation retained'
                              : w.operation.outcome !== 'NONE'
                                ? w.operation.outcome
                                : w.operation.execution_knowledge,
                        )
                        .join(', ')
                    : issues?.length
                      ? 'Check settings'
                      : report?.valid
                        ? 'Values checked'
                        : 'Configure action'}
                </span>
              </button>
              {work.flatMap((w) =>
                w.native_results.map((native) => (
                  <p key={native.evidence} className="task-native-result">
                    Native result: {native.status_schema} / {native.status}
                  </p>
                )),
              )}
              {work.map((w) => (
                <details key={w.operation.operation_id}>
                  <summary>Operation evidence and custody</summary>
                  <p>Operation {w.operation.operation_id}</p>
                  <p>Invocation {w.invocation ?? 'No confirmed invocation'}</p>
                  <p>
                    {w.operation.phase} · {w.operation.disposition}
                  </p>
                  <p>Evidence: {w.operation.evidence_ids.join(', ') || 'No completion evidence'}</p>
                  <pre>{JSON.stringify(w.resources, null, 2)}</pre>
                </details>
              ))}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
