"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { agentStreamUrl, api } from "@/lib/api";
import type { AgentDecision, CaseDetail } from "@/lib/types";
import {
  formatCurrency,
  formatDateTime,
  formatFailureClass,
  formatPercent,
  formatStatus,
} from "@/lib/format";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, FailureClassBadge, StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DecisionTrace } from "@/components/agent-trace/DecisionTrace";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [liveDecisions, setLiveDecisions] = useState<AgentDecision[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const load = useCallback(() => {
    api
      .getCase(caseId)
      .then(setCaseDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "failed to load case"));
  }, [caseId]);

  useEffect(() => {
    load();
    return () => eventSourceRef.current?.close();
  }, [load]);

  function runAgentLive() {
    setRunning(true);
    setLiveDecisions([]);
    const source = new EventSource(agentStreamUrl(caseId));
    eventSourceRef.current = source;

    source.onmessage = (event) => {
      const decision = JSON.parse(event.data) as AgentDecision;
      setLiveDecisions((prev) => [...prev, decision]);
    };
    source.addEventListener("done", () => {
      source.close();
      setRunning(false);
      load();
    });
    source.onerror = () => {
      source.close();
      setRunning(false);
      load();
    };
  }

  async function approve(messageId: string) {
    await api.approveMessage(caseId, messageId);
    load();
  }

  if (error) {
    return (
      <Card>
        <p className="text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      </Card>
    );
  }

  if (!caseDetail) {
    return <p className="text-sm" style={{ color: "var(--muted)" }}>Loading…</p>;
  }

  const liveNodes = new Set(liveDecisions.map((d) => d.node));

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-sm" style={{ color: "var(--muted)" }}>
              {caseDetail.id}
            </h1>
            <StatusBadge status={caseDetail.status} label={formatStatus(caseDetail.status)} />
            <FailureClassBadge value={caseDetail.failure_class} label={formatFailureClass(caseDetail.failure_class)} />
          </div>
          <p className="mt-1 text-2xl font-semibold tracking-tight">
            {formatCurrency(caseDetail.amount_at_risk_cents, caseDetail.currency)} at risk
          </p>
          {caseDetail.recovery_score != null && (
            <p className="text-sm" style={{ color: "var(--muted)" }}>
              Recovery score: {formatPercent(caseDetail.recovery_score)}
              {caseDetail.score_confidence != null && ` · confidence ${formatPercent(caseDetail.score_confidence)}`}
            </p>
          )}
        </div>
        <Button variant="primary" onClick={runAgentLive} disabled={running}>
          {running ? "Running…" : "Run agent"}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Agent decision trace</CardTitle>
          </CardHeader>
          {running || liveDecisions.length > 0 ? (
            <DecisionTrace
              steps={liveDecisions.map((d, i) => ({
                id: `live-${i}`,
                node: d.node,
                reasoning: d.reasoning,
                output: d.output ?? null,
                latency_ms: d.latency_ms,
                created_at: new Date().toISOString(),
              }))}
            />
          ) : (
            <DecisionTrace steps={caseDetail.agent_steps} />
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Facts</CardTitle>
          </CardHeader>
          <dl className="flex flex-col gap-2 text-sm">
            <Row label="Failure code" value={caseDetail.failure_code ?? "—"} />
            <Row label="Failure reason" value={caseDetail.failure_reason ?? "—"} />
            <Row label="Triage rationale" value={caseDetail.triage_rationale ?? "—"} />
            <Row label="Attempts used" value={String(caseDetail.attempt_count)} />
            <Row label="Opened" value={formatDateTime(caseDetail.opened_at)} />
            {caseDetail.closed_at && <Row label="Closed" value={formatDateTime(caseDetail.closed_at)} />}
          </dl>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Messages</CardTitle>
          </CardHeader>
          <div className="flex flex-col gap-3">
            {caseDetail.messages.length === 0 && (
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                No drafts yet.
              </p>
            )}
            {caseDetail.messages.map((m) => (
              <div key={m.id} className="rounded-lg border p-3" style={{ borderColor: "var(--border)" }}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold uppercase" style={{ color: "var(--muted)" }}>
                    {m.channel}
                  </span>
                  <MessageStatusBadge status={m.status} />
                </div>
                {m.subject && <p className="mt-1 text-sm font-medium">{m.subject}</p>}
                <p className="mt-1 whitespace-pre-wrap text-sm" style={{ color: "var(--muted)" }}>
                  {m.body}
                </p>
                {m.guardrail_flags && m.guardrail_flags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.guardrail_flags.map((f) => (
                      <Badge key={f} tone="danger">
                        {f}
                      </Badge>
                    ))}
                  </div>
                )}
                {(m.status === "draft" || m.status === "blocked") && (
                  <Button className="mt-2" onClick={() => approve(m.id)}>
                    Approve &amp; send
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Retry / outreach schedule</CardTitle>
          </CardHeader>
          <div className="flex flex-col gap-2">
            {caseDetail.attempts.length === 0 && (
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                No attempts scheduled yet.
              </p>
            )}
            {caseDetail.attempts.map((a) => (
              <div key={a.id} className="flex items-center justify-between text-sm">
                <span>{a.kind === "retry_charge" ? "Retry charge" : "Outreach"}</span>
                <span style={{ color: "var(--muted)" }}>{formatDateTime(a.scheduled_at)}</span>
                <OutcomeBadge outcome={a.outcome} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs" style={{ color: "var(--muted)" }}>
        {label}
      </dt>
      <dd>{value}</dd>
    </div>
  );
}

function MessageStatusBadge({ status }: { status: string }) {
  const tone = status === "sent" ? "success" : status === "blocked" || status === "failed" ? "danger" : "neutral";
  return <Badge tone={tone}>{status}</Badge>;
}

function OutcomeBadge({ outcome }: { outcome: string }) {
  const tone = outcome === "succeeded" ? "success" : outcome === "failed" ? "danger" : "neutral";
  return <Badge tone={tone}>{outcome}</Badge>;
}
