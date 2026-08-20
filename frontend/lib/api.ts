// Thin typed fetch wrapper over the FastAPI backend. Every page/component
// calls through here rather than calling `fetch` directly, so the base URL
// and error handling live in exactly one place.

import type {
  ByReasonRow,
  Capabilities,
  CaseDetail,
  CaseListItem,
  ChannelPerformanceRow,
  FunnelStage,
  OverviewStats,
  PlaybookOut,
  RunCaseResponse,
  TrendPoint,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(response.status, body || response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  capabilities: () => request<Capabilities>("/capabilities"),

  listCases: (params?: { status?: string; failure_class?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<CaseListItem[]>(`/api/cases${query ? `?${query}` : ""}`);
  },
  getCase: (id: string) => request<CaseDetail>(`/api/cases/${id}`),
  runCase: (id: string) =>
    request<RunCaseResponse>(`/api/cases/${id}/run`, { method: "POST" }),
  approveMessage: (caseId: string, messageId: string) =>
    request<{ status: string }>(`/api/cases/${caseId}/messages/${messageId}/approve`, {
      method: "POST",
    }),

  listPlaybooks: () => request<PlaybookOut[]>("/api/playbooks"),
  updatePlaybook: (id: string, body: Partial<PlaybookOut>) =>
    request<PlaybookOut>(`/api/playbooks/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  overview: () => request<OverviewStats>("/api/analytics/overview"),
  funnel: () => request<FunnelStage[]>("/api/analytics/funnel"),
  byReason: () => request<ByReasonRow[]>("/api/analytics/by-reason"),
  channelPerformance: () => request<ChannelPerformanceRow[]>("/api/analytics/channels"),
  trend: (days = 30) => request<TrendPoint[]>(`/api/analytics/trend?days=${days}`),
};

export function agentStreamUrl(caseId: string): string {
  return `${BASE_URL}/api/agent/cases/${caseId}/stream`;
}
