// Mirrors backend/app/schemas/*.py. Kept as one file since the API surface is
// small enough that a generated client would be overkill.

export type FailureClass =
  | "insufficient_funds"
  | "card_expired"
  | "card_invalid"
  | "do_not_honor"
  | "authentication_required"
  | "risk_blocked"
  | "technical_error"
  | "hard_decline"
  | "unknown";

export type CaseStatus =
  | "open"
  | "in_progress"
  | "awaiting_customer"
  | "recovered"
  | "lost"
  | "escalated";

export type MessageStatus = "draft" | "blocked" | "approved" | "sent" | "failed" | "bounced";
export type Channel = "email" | "sms" | "whatsapp";

export interface CaseListItem {
  id: string;
  status: CaseStatus;
  failure_class: FailureClass;
  recovery_score: number | null;
  amount_at_risk_cents: number;
  currency: string;
  attempt_count: number;
  opened_at: string;
  closed_at: string | null;
}

export interface RecoveryAttemptOut {
  id: string;
  kind: string;
  scheduled_at: string;
  executed_at: string | null;
  outcome: string;
}

export interface MessageOut {
  id: string;
  channel: Channel;
  status: MessageStatus;
  subject: string | null;
  body: string;
  generated_by: string;
  guardrail_flags: string[] | null;
  sent_at: string | null;
}

export interface AgentStepOut {
  id: string;
  node: string;
  reasoning: string | null;
  output: Record<string, unknown> | null;
  latency_ms: number | null;
  created_at: string;
}

export interface CaseDetail extends CaseListItem {
  failure_code: string | null;
  failure_reason: string | null;
  triage_rationale: string | null;
  score_confidence: number | null;
  strategy: Record<string, unknown> | null;
  attempts: RecoveryAttemptOut[];
  messages: MessageOut[];
  agent_steps: AgentStepOut[];
}

export interface RunCaseResponse {
  case_id: string;
  decisions: AgentDecision[];
  status: CaseStatus;
}

export interface AgentDecision {
  node: string;
  reasoning: string;
  latency_ms: number;
  output?: Record<string, unknown>;
}

export interface PlaybookOut {
  id: string;
  failure_class: FailureClass;
  retry_offsets_hours: number[];
  channel_ladder: string[];
  offer_policy: string | null;
  cases_closed: number;
  cases_recovered: number;
  win_rate: number | null;
}

export interface OverviewStats {
  recovered_mrr_cents: number;
  recovery_rate: number | null;
  at_risk_mrr_cents: number;
  open_cases: number;
  avg_days_to_recover: number | null;
}

export interface FunnelStage {
  stage: string;
  count: number;
}

export interface ByReasonRow {
  failure_class: string;
  total_cases: number;
  recovered_cases: number;
  win_rate: number | null;
  amount_at_risk_cents: number;
}

export interface ChannelPerformanceRow {
  channel: string;
  sent_count: number;
  opened_count: number;
  clicked_count: number;
}

export interface TrendPoint {
  date: string;
  recovered_cents: number;
  at_risk_cents: number;
}

export interface Capabilities {
  agent: { provider: string; model: string; live: boolean; mode: string; note: string | null };
  payments: { configured: string; effective: string; live: boolean; note: string | null };
  email: { configured: string; effective: string; live: boolean; note: string | null };
  database: { engine: string };
  guardrails: {
    max_messages_per_customer_per_week: number;
    max_retries_per_case: number;
    require_human_approval: boolean;
  };
}
