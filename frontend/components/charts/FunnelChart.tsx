"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FunnelStage } from "@/lib/types";
import { formatStatus } from "@/lib/format";

// Status-tone colors, matching the Badge components elsewhere in the app so
// a stage reads the same way in the table and in the chart.
const STAGE_COLOR: Record<string, string> = {
  open: "var(--info)",
  in_progress: "var(--info)",
  awaiting_customer: "var(--warning)",
  recovered: "var(--success)",
  lost: "var(--danger)",
  escalated: "var(--danger)",
};

export function FunnelChart({ data }: { data: FunnelStage[] }) {
  const chartData = data.map((d) => ({ ...d, label: formatStatus(d.stage) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="label"
          tick={{ fill: "var(--chart-text)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={110}
        />
        <Tooltip
          formatter={(value) => [Number(value), "Cases"]}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Bar dataKey="count" radius={[4, 4, 4, 4]} maxBarSize={28}>
          {chartData.map((entry) => (
            <Cell key={entry.stage} fill={STAGE_COLOR[entry.stage] ?? "var(--neutral)"} />
          ))}
          <LabelList dataKey="count" position="right" style={{ fill: "var(--foreground)", fontSize: 12 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
