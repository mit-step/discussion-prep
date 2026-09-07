import type { Evaluation, HistoryEntry, Reading, RespondResult, TranscriptDetail } from "../types";

export const BASE = "/discussion-prep";
const USER_ID_KEY = "discussion-prep:user_id";

export function getStoredUserId(): string | null {
  return localStorage.getItem(USER_ID_KEY);
}

export function setStoredUserId(userId: string): void {
  localStorage.setItem(USER_ID_KEY, userId);
}

export function clearStoredUserId(): void {
  localStorage.removeItem(USER_ID_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const userId = getStoredUserId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (userId) headers["X-User-Id"] = userId;

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  login: (name: string, email: string) =>
    request<{ user_id: string; name: string; email: string }>(`${BASE}/api/auth/login`, {
      method: "POST",
      body: JSON.stringify({ name, email }),
    }),

  listReadings: () => request<Reading[]>(`${BASE}/api/readings`),

  searchReadings: (q: string) =>
    request<Reading[]>(`${BASE}/api/readings/search?q=${encodeURIComponent(q)}`),

  readingHistory: (docUuid: string) =>
    request<HistoryEntry[]>(`${BASE}/api/readings/${docUuid}/history`),

  createSession: (docUuid: string) =>
    request<{ session_id: string; rounds_total: number; reading_title: string }>(`${BASE}/api/session`, {
      method: "POST",
      body: JSON.stringify({ doc_uuid: docUuid }),
    }),

  submitArgument: (sessionId: string, argumentText: string) =>
    request<RespondResult>(`${BASE}/api/session/${sessionId}/argument`, {
      method: "POST",
      body: JSON.stringify({ argument_text: argumentText }),
    }),

  submitResponse: (sessionId: string, responseText: string) =>
    request<RespondResult>(`${BASE}/api/session/${sessionId}/respond`, {
      method: "POST",
      body: JSON.stringify({ response_text: responseText }),
    }),

  getTranscript: (sessionId: string) => request<TranscriptDetail>(`${BASE}/api/transcripts/${sessionId}`),
};

export function readingPdfUrl(docUuid: string): string {
  return `${BASE}/readings-pdf/${docUuid}.pdf`;
}

export type { Evaluation };
