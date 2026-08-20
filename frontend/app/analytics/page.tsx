"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ByReasonRow, ChannelPerformanceRow, TrendPoint } from "@/lib/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { TrendChart } from "@/components/charts/TrendChart";
import { ByReasonChart } from "@/components/charts/ByReasonChart";
import { ChannelChart } from "@/components/charts/ChannelChart";

export default function AnalyticsPage() {
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [byReason, setByReason] = useState<ByReasonRow[]>([]);
  const [channels, setChannels] = useState<ChannelPerformanceRow[]>([]);

  useEffect(() => {
    api.trend(90).then(setTrend);
    api.byReason().then(setByReason);
    api.channelPerformance().then(setChannels);
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Recovery performance by reason, channel, and time.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recovered vs. at-risk, last 90 days</CardTitle>
        </CardHeader>
        <TrendChart data={trend} />
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Win rate by failure reason</CardTitle>
          </CardHeader>
          <ByReasonChart data={byReason} />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Messages sent by channel</CardTitle>
          </CardHeader>
          <ChannelChart data={channels} />
        </Card>
      </div>
    </div>
  );
}
