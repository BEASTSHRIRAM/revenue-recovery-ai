"use client";

import type { AgentStepOut } from "@/lib/types";
import { formatDateTime } from "@/lib/format";

const NODE_LABEL: Record<string, string> = {
  ingest: "Ingest",
  triage: "Triage",
  enrich: "Enrich",
  score: "Score",
  plan_retries: "Plan retries",
  plan_action_required: "Plan (action required)",
  compose: "Compose",
  guardrail: "Guardrail",
  execute: "Execute",
  escalate: "Escalate",
};

export function DecisionTrace({ steps }: { steps: AgentStepOut[] }) {
  if (steps.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        The agent hasn&apos;t run on this case yet.
      </p>
    );
  }

  return (
    <ol className="flex flex-col gap-3">
      {steps.map((step, i) => (
        <li key={step.id} className="relative flex gap-3">
          <div className="flex flex-col items-center">
            <span
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold"
              style={{ backgroundColor: "var(--info-bg)", color: "var(--info)" }}
            >
              {i + 1}
            </span>
            {i < steps.length - 1 && (
              <span className="mt-1 w-px flex-1" style={{ backgroundColor: "var(--border)" }} />
            )}
          </div>
          <div className="flex-1 pb-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">{NODE_LABEL[step.node] ?? step.node}</span>
              <span className="text-xs" style={{ color: "var(--muted)" }}>
                {step.latency_ms != null ? `${step.latency_ms}ms` : ""} · {formatDateTime(step.created_at)}
              </span>
            </div>
            {step.reasoning && (
              <p className="mt-0.5 text-sm" style={{ color: "var(--foreground)" }}>
                {step.reasoning}
              </p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
