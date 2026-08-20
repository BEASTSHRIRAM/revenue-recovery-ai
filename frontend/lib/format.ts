// Formatting helpers shared across the dashboard, case list, and analytics
// pages, so a currency or date never gets rendered two different ways.

export function formatCurrency(cents: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function formatCompactCurrency(cents: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(cents / 100);
}

export function formatPercent(ratio: number | null, digits = 0): string {
  if (ratio === null) return "—";
  return `${(ratio * 100).toFixed(digits)}%`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatRelative(iso: string): string {
  const diffMs = new Date(iso).getTime() - Date.now();
  const diffHours = Math.round(diffMs / (1000 * 60 * 60));
  if (Math.abs(diffHours) < 1) return "now";
  if (Math.abs(diffHours) < 24) return `${diffHours > 0 ? "in " : ""}${Math.abs(diffHours)}h${diffHours < 0 ? " ago" : ""}`;
  const diffDays = Math.round(diffHours / 24);
  return `${diffDays > 0 ? "in " : ""}${Math.abs(diffDays)}d${diffDays < 0 ? " ago" : ""}`;
}

const FAILURE_CLASS_LABELS: Record<string, string> = {
  insufficient_funds: "Insufficient funds",
  card_expired: "Card expired",
  card_invalid: "Card invalid",
  do_not_honor: "Do not honor",
  authentication_required: "Auth required",
  risk_blocked: "Risk blocked",
  technical_error: "Technical error",
  hard_decline: "Hard decline",
  unknown: "Unknown",
};

export function formatFailureClass(value: string): string {
  return FAILURE_CLASS_LABELS[value] ?? value;
}

const STATUS_LABELS: Record<string, string> = {
  open: "Open",
  in_progress: "In progress",
  awaiting_customer: "Awaiting customer",
  recovered: "Recovered",
  lost: "Lost",
  escalated: "Escalated",
};

export function formatStatus(value: string): string {
  return STATUS_LABELS[value] ?? value;
}
