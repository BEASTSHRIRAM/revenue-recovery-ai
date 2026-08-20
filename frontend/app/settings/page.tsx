"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Capabilities } from "@/lib/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function SettingsPage() {
  const [caps, setCaps] = useState<Capabilities | null>(null);

  useEffect(() => {
    api.capabilities().then(setCaps);
  }, []);

  if (!caps) return <p className="text-sm" style={{ color: "var(--muted)" }}>Loading…</p>;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          What&apos;s live vs. running in local/demo mode. Add credentials in the backend&apos;s{" "}
          <code>.env</code> to upgrade any of these.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <CapabilityCard
          title="Agent"
          live={caps.agent.live}
          rows={[
            ["Provider", "Groq"],
            ["Model", caps.agent.model],
            ["Mode", caps.agent.mode],
          ]}
          note={caps.agent.note}
        />
        <CapabilityCard
          title="Payments"
          live={caps.payments.live}
          rows={[
            ["Configured", caps.payments.configured],
            ["Effective", caps.payments.effective],
          ]}
          note={caps.payments.note}
        />
        <CapabilityCard
          title="Email"
          live={caps.email.live}
          rows={[
            ["Configured", caps.email.configured],
            ["Effective", caps.email.effective],
          ]}
          note={caps.email.note}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Guardrail limits</CardTitle>
        </CardHeader>
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt style={{ color: "var(--muted)" }}>Max messages / customer / week</dt>
            <dd className="text-lg font-semibold">{caps.guardrails.max_messages_per_customer_per_week}</dd>
          </div>
          <div>
            <dt style={{ color: "var(--muted)" }}>Max retries / case</dt>
            <dd className="text-lg font-semibold">{caps.guardrails.max_retries_per_case}</dd>
          </div>
          <div>
            <dt style={{ color: "var(--muted)" }}>Human approval required</dt>
            <dd className="text-lg font-semibold">{caps.guardrails.require_human_approval ? "Yes" : "No"}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Database</CardTitle>
        </CardHeader>
        <p className="text-sm">Engine: {caps.database.engine}</p>
      </Card>
    </div>
  );
}

function CapabilityCard({
  title,
  live,
  rows,
  note,
}: {
  title: string;
  live: boolean;
  rows: [string, string][];
  note: string | null;
}) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{title}</h3>
        <Badge tone={live ? "success" : "warning"}>{live ? "Live" : "Demo mode"}</Badge>
      </div>
      <dl className="flex flex-col gap-1 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-2">
            <dt style={{ color: "var(--muted)" }}>{label}</dt>
            <dd className="text-right">{value}</dd>
          </div>
        ))}
      </dl>
      {note && (
        <p className="text-xs" style={{ color: "var(--warning)" }}>
          {note}
        </p>
      )}
    </Card>
  );
}
