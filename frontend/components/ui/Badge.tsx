import { ReactNode } from "react";

export type BadgeTone = "success" | "warning" | "danger" | "info" | "neutral";

const TONE_VARS: Record<BadgeTone, { fg: string; bg: string }> = {
  success: { fg: "var(--success)", bg: "var(--success-bg)" },
  warning: { fg: "var(--warning)", bg: "var(--warning-bg)" },
  danger: { fg: "var(--danger)", bg: "var(--danger-bg)" },
  info: { fg: "var(--info)", bg: "var(--info-bg)" },
  neutral: { fg: "var(--neutral)", bg: "var(--neutral-bg)" },
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  const { fg, bg } = TONE_VARS[tone];
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{ color: fg, backgroundColor: bg }}
    >
      {children}
    </span>
  );
}

const STATUS_TONE: Record<string, BadgeTone> = {
  open: "info",
  in_progress: "info",
  awaiting_customer: "warning",
  recovered: "success",
  lost: "danger",
  escalated: "danger",
};

export function StatusBadge({ status, label }: { status: string; label: string }) {
  return <Badge tone={STATUS_TONE[status] ?? "neutral"}>{label}</Badge>;
}

const FAILURE_CLASS_TONE: Record<string, BadgeTone> = {
  insufficient_funds: "warning",
  card_expired: "neutral",
  card_invalid: "neutral",
  do_not_honor: "danger",
  authentication_required: "info",
  risk_blocked: "danger",
  technical_error: "info",
  hard_decline: "danger",
  unknown: "neutral",
};

export function FailureClassBadge({ value, label }: { value: string; label: string }) {
  return <Badge tone={FAILURE_CLASS_TONE[value] ?? "neutral"}>{label}</Badge>;
}
