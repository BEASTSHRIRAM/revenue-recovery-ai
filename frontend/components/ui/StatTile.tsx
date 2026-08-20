import { ReactNode } from "react";
import { Card } from "./Card";

export function StatTile({
  label,
  value,
  hint,
  trend,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  trend?: { direction: "up" | "down" | "flat"; label: string };
}) {
  return (
    <Card className="flex flex-col gap-1.5">
      <span className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--muted)" }}>
        {label}
      </span>
      <span className="text-2xl font-semibold tracking-tight" style={{ color: "var(--foreground)" }}>
        {value}
      </span>
      {(hint || trend) && (
        <div className="flex items-center gap-2 text-xs" style={{ color: "var(--muted)" }}>
          {trend && (
            <span
              style={{
                color:
                  trend.direction === "up"
                    ? "var(--success)"
                    : trend.direction === "down"
                    ? "var(--danger)"
                    : "var(--muted)",
              }}
            >
              {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"} {trend.label}
            </span>
          )}
          {hint && <span>{hint}</span>}
        </div>
      )}
    </Card>
  );
}
