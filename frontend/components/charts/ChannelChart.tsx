"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ChannelPerformanceRow } from "@/lib/types";

// Channels are distinct identities (email/sms/whatsapp), so this is a
// categorical encoding — fixed hue order, slots 1-3, never reassigned by sort
// order or filtering.
const CHANNEL_COLOR: Record<string, string> = {
  email: "var(--series-1)",
  sms: "var(--series-2)",
  whatsapp: "var(--series-3)",
};

const CHANNEL_LABEL: Record<string, string> = {
  email: "Email",
  sms: "SMS",
  whatsapp: "WhatsApp",
};

export function ChannelChart({ data }: { data: ChannelPerformanceRow[] }) {
  const chartData = data.map((d) => ({ ...d, label: CHANNEL_LABEL[d.channel] ?? d.channel }));

  if (chartData.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm" style={{ color: "var(--muted)" }}>
        No messages sent yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: "var(--chart-text)", fontSize: 12 }}
          axisLine={{ stroke: "var(--chart-grid)" }}
          tickLine={false}
        />
        <YAxis tick={{ fill: "var(--chart-text)", fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          formatter={(value) => [Number(value), "Sent"]}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Bar dataKey="sent_count" radius={[4, 4, 0, 0]} maxBarSize={64}>
          {chartData.map((entry) => (
            <Cell key={entry.channel} fill={CHANNEL_COLOR[entry.channel] ?? "var(--neutral)"} />
          ))}
          <LabelList dataKey="sent_count" position="top" style={{ fill: "var(--foreground)", fontSize: 12 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
