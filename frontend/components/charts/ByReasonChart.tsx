"use client";

import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ByReasonRow } from "@/lib/types";
import { formatFailureClass, formatPercent } from "@/lib/format";

// Win rate is a magnitude, so it gets the sequential single hue rather than
// a categorical color per failure class (those aren't distinct identities
// being compared side by side here — they're all measured on the same scale).
export function ByReasonChart({ data }: { data: ByReasonRow[] }) {
  const chartData = data
    .map((d) => ({ ...d, label: formatFailureClass(d.failure_class), win_rate_pct: (d.win_rate ?? 0) * 100 }))
    .sort((a, b) => b.total_cases - a.total_cases);

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 36)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 32, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="label"
          tick={{ fill: "var(--chart-text)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={130}
        />
        <Tooltip
          formatter={(value, _name, entry) => [
            `${Number(value).toFixed(0)}% (${entry.payload.recovered_cases}/${entry.payload.total_cases})`,
            "Win rate",
          ]}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Bar dataKey="win_rate_pct" fill="var(--series-1)" radius={[4, 4, 4, 4]} maxBarSize={20}>
          <LabelList
            dataKey="win_rate_pct"
            position="right"
            formatter={(v) => formatPercent(Number(v) / 100)}
            style={{ fill: "var(--foreground)", fontSize: 12 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
