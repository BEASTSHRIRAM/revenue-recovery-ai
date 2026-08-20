"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/lib/types";
import { formatCompactCurrency, formatDate } from "@/lib/format";

export function TrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm" style={{ color: "var(--muted)" }}>
        No case activity in this window yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="recoveredFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series-1)" stopOpacity={0.25} />
            <stop offset="100%" stopColor="var(--series-1)" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="atRiskFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series-2)" stopOpacity={0.2} />
            <stop offset="100%" stopColor="var(--series-2)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={(v: string) => formatDate(v)}
          tick={{ fill: "var(--chart-text)", fontSize: 12 }}
          axisLine={{ stroke: "var(--chart-grid)" }}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v: number) => formatCompactCurrency(v)}
          tick={{ fill: "var(--chart-text)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={64}
        />
        <Tooltip
          formatter={(value, name) => [formatCompactCurrency(Number(value)), String(name)]}
          labelFormatter={(v) => formatDate(String(v))}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "var(--chart-text)" }} />
        <Area
          type="monotone"
          dataKey="at_risk_cents"
          name="At risk"
          stroke="var(--series-2)"
          strokeWidth={2}
          fill="url(#atRiskFill)"
        />
        <Area
          type="monotone"
          dataKey="recovered_cents"
          name="Recovered"
          stroke="var(--series-1)"
          strokeWidth={2}
          fill="url(#recoveredFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
