import type { ApiResult, ChatRequest, FullPlan, SseEvent } from "./types";
import { parseSseStream } from "./sse";

const API_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 30_000;

interface RequestOptions extends Omit<RequestInit, "signal"> {
  /** Abort the request after this many milliseconds. Defaults to 30s. */
  timeoutMs?: number;
}

/**
 * Single fetch wrapper. Returns a discriminated `ApiResult` so callers
 * never have to wrap calls in try/catch. Includes a hard timeout so a
 * stuck backend doesn't lock up the UI.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResult<T>> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, headers, ...rest } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const url = path.startsWith("http") ? path : `${API_URL}${path}`;
    const response = await fetch(url, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...headers,
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return {
        ok: false,
        error: text || `Request failed with status ${response.status}`,
        status: response.status,
      };
    }

    const data = (await response.json()) as T;
    return { ok: true, data };
  } catch (err) {
    const message =
      err instanceof DOMException && err.name === "AbortError"
        ? `Request timed out after ${timeoutMs}ms`
        : err instanceof Error
          ? err.message
          : "Unknown network error";
    return { ok: false, error: message };
  } finally {
    clearTimeout(timeoutId);
  }
}

/** Fetch a fully-synthesized plan by id. */
export async function getPlan(planId: string): Promise<ApiResult<{ plan: FullPlan }>> {
  return apiFetch<{ plan: FullPlan }>(`/api/plan/${encodeURIComponent(planId)}`);
}

interface PlanVersionsResponse {
  versions: Array<{
    id: string;
    version_num: number;
    notes: string | null;
    created_at: string;
  }>;
}

/** Fetch all versions for a plan. */
export async function getPlanVersions(planId: string): Promise<ApiResult<PlanVersionsResponse>> {
  return apiFetch<PlanVersionsResponse>(`/api/plan/${encodeURIComponent(planId)}/versions`);
}

interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  intent: string | null;
  created_at: string;
}

interface ConversationResponse {
  messages: ConversationMessage[];
}

/** Fetch conversation history for a plan. */
export async function getConversation(planId: string): Promise<ApiResult<ConversationResponse>> {
  return apiFetch<ConversationResponse>(`/api/plan/${encodeURIComponent(planId)}/conversation`);
}

interface PlanSummary {
  id: string;
  title: string;
  status: string;
  total_cost_usd: number;
  created_at: string;
  updated_at: string;
}

interface PlansListResponse {
  plans: PlanSummary[];
}

/** Fetch all plans for the current user. */
export async function getPlans(): Promise<ApiResult<PlansListResponse>> {
  return apiFetch<PlansListResponse>('/api/plans');
}

/**
 * Open the streaming chat endpoint. Yields SSE events as they arrive.
 * The caller is responsible for handling each event type appropriately.
 */
export async function* streamChat(
  body: ChatRequest,
  options: { signal?: AbortSignal } = {},
): AsyncGenerator<SseEvent, void, unknown> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(`Chat stream failed with status ${response.status}`);
  }

  yield* parseSseStream(response);
}
