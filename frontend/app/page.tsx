"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { FunnelStage, OverviewStats, TrendPoint } from "@/lib/types";
import { formatCompactCurrency, formatPercent } from "@/lib/format";
import { StatTile } from "@/components/ui/StatTile";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { TrendChart } from "@/components/charts/TrendChart";
import { FunnelChart } from "@/components/charts/FunnelChart";

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [funnel, setFunnel] = useState<FunnelStage[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.overview(), api.trend(30), api.funnel()])
      .then(([o, t, f]) => {
        setOverview(o);
        setTrend(t);
        setFunnel(f);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load dashboard data"));
  }, []);

  if (error) {
    return (
      <Card>
        <p className="text-sm" style={{ color: "var(--danger)" }}>
          Couldn&apos;t reach the API at {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}: {error}
        </p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Recovery overview</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          What the agent has recovered, and what&apos;s still at risk.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatTile
          label="Recovered MRR"
          value={overview ? formatCompactCurrency(overview.recovered_mrr_cents) : "—"}
        />
        <StatTile
          label="Recovery rate"
          value={overview ? formatPercent(overview.recovery_rate) : "—"}
        />
        <StatTile
          label="At-risk MRR"
          value={overview ? formatCompactCurrency(overview.at_risk_mrr_cents) : "—"}
        />
        <StatTile label="Open cases" value={overview ? overview.open_cases : "—"} />
        <StatTile
          label="Avg. days to recover"
          value={
            overview?.avg_days_to_recover != null ? overview.avg_days_to_recover.toFixed(1) : "—"
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recovered vs. at-risk, last 30 days</CardTitle>
          </CardHeader>
          <TrendChart data={trend} />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Cases by stage</CardTitle>
          </CardHeader>
          <FunnelChart data={funnel} />
        </Card>
      </div>
    </div>
  );
}
