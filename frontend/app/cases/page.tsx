"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CaseListItem } from "@/lib/types";
import { formatCurrency, formatDate, formatFailureClass, formatPercent, formatStatus } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { FailureClassBadge, StatusBadge } from "@/components/ui/Badge";

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In progress" },
  { value: "awaiting_customer", label: "Awaiting customer" },
  { value: "recovered", label: "Recovered" },
  { value: "lost", label: "Lost" },
  { value: "escalated", label: "Escalated" },
];

export default function CasesPage() {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listCases(status ? { status } : undefined)
      .then(setCases)
      .finally(() => setLoading(false));
  }, [status]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Recovery cases</h1>
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            {cases.length} case{cases.length === 1 ? "" : "s"} {status && `· ${formatStatus(status)}`}
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border p-1" style={{ borderColor: "var(--border)" }}>
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatus(f.value)}
              className="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
              style={{
                backgroundColor: status === f.value ? "var(--surface-muted)" : "transparent",
                color: status === f.value ? "var(--foreground)" : "var(--muted)",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase tracking-wide" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
              <th className="px-4 py-3 font-medium">Case</th>
              <th className="px-4 py-3 font-medium">Failure</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Amount at risk</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Opened</th>
            </tr>
          </thead>
          <tbody>
            {!loading && cases.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm" style={{ color: "var(--muted)" }}>
                  No cases match this filter.
                </td>
              </tr>
            )}
            {cases.map((c) => (
              <tr
                key={c.id}
                className="border-b last:border-0 hover:bg-[var(--surface-muted)]"
                style={{ borderColor: "var(--border)" }}
              >
                <td className="px-4 py-3">
                  <Link href={`/cases/${c.id}`} className="font-mono text-xs hover:underline" style={{ color: "var(--accent)" }}>
                    {c.id}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <FailureClassBadge value={c.failure_class} label={formatFailureClass(c.failure_class)} />
                </td>
                <td className="px-4 py-3">{c.recovery_score != null ? formatPercent(c.recovery_score) : "—"}</td>
                <td className="px-4 py-3 font-medium">{formatCurrency(c.amount_at_risk_cents, c.currency)}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={c.status} label={formatStatus(c.status)} />
                </td>
                <td className="px-4 py-3" style={{ color: "var(--muted)" }}>
                  {formatDate(c.opened_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
