"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PlaybookOut } from "@/lib/types";
import { formatFailureClass, formatPercent } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<PlaybookOut[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    api.listPlaybooks().then(setPlaybooks);
  }, []);

  async function save(pb: PlaybookOut) {
    setSaving(pb.id);
    const offer_policy = editing[pb.id] ?? pb.offer_policy ?? "";
    const updated = await api.updatePlaybook(pb.id, { offer_policy });
    setPlaybooks((prev) => prev.map((p) => (p.id === pb.id ? updated : p)));
    setSaving(null);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Playbooks</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Retry timing and channel ladder per failure class. Win rates are computed live from closed cases.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {playbooks.map((pb) => (
          <Card key={pb.id} className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">{formatFailureClass(pb.failure_class)}</h3>
              <span
                className="text-sm font-semibold"
                style={{ color: pb.win_rate != null && pb.win_rate > 0.5 ? "var(--success)" : "var(--muted)" }}
              >
                {formatPercent(pb.win_rate)} win rate
              </span>
            </div>

            <div className="text-sm" style={{ color: "var(--muted)" }}>
              {pb.cases_recovered}/{pb.cases_closed} cases recovered
            </div>

            <div>
              <span className="text-xs font-medium uppercase" style={{ color: "var(--muted)" }}>
                Retry offsets (hours)
              </span>
              <p className="text-sm">
                {pb.retry_offsets_hours.length > 0 ? pb.retry_offsets_hours.join(", ") : "None — outreach only"}
              </p>
            </div>

            <div>
              <span className="text-xs font-medium uppercase" style={{ color: "var(--muted)" }}>
                Channel ladder
              </span>
              <p className="text-sm">{pb.channel_ladder.join(" → ")}</p>
            </div>

            <div>
              <span className="text-xs font-medium uppercase" style={{ color: "var(--muted)" }}>
                Offer policy
              </span>
              <textarea
                className="mt-1 w-full rounded-md border p-2 text-sm"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--surface-muted)" }}
                rows={2}
                value={editing[pb.id] ?? pb.offer_policy ?? ""}
                onChange={(e) => setEditing((prev) => ({ ...prev, [pb.id]: e.target.value }))}
              />
            </div>

            <Button onClick={() => save(pb)} disabled={saving === pb.id} className="self-start">
              {saving === pb.id ? "Saving…" : "Save"}
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
