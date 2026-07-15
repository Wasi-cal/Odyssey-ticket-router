// Typed client for the Smart Ticket Router backend.
//
// The frontend talks to these endpoints (proxied via /api/* to the FastAPI
// backend — see next.config.ts). /tickets* endpoints require a JWT, sent as
// `Authorization: Bearer <token>` (see lib/auth.ts):
//
//   POST /auth/register                body: { email, password }
//   POST /auth/login                   body: { email, password }
//   POST /tickets                      body: { text }
//   GET  /tickets                      -> TicketSummary[]
//   GET  /tickets/{ticket_ref}         -> TicketDetail

import { getToken } from "./auth";

export type TicketSummary = {
  ticket_ref: string;
  title: string;
  priority: string; // "High" | "Medium" | "Low"
  status: string; // e.g. "Open" | "In Progress" | "Resolved" | "Closed"
  category: string; // human-readable label, e.g. "Billing"
  updated_at: string; // ISO timestamp
  reasoning: string | null; // one-line rationale for the classification
  assigned_to: string | null; // assignee's name (a person, never a team/role)
  reports_to: string | null; // team manager's name (always set once assigned, even if the manager is the assignee)
};

export type TicketDetail = TicketSummary & {
  description: string;
  role: string | null; // assignee's role
  estimated_time: string | null; // e.g. "4h"
  created_at?: string;
};

const API_BASE = "/api";

// Thrown when the server rejects the request as unauthenticated/expired, so
// callers can redirect to /login instead of showing a generic error.
export class AuthError extends Error {}

async function request(
  path: string,
  init?: RequestInit,
  auth = false,
): Promise<unknown> {
  const headers = new Headers(init?.headers);
  if (auth) {
    headers.set("Authorization", `Bearer ${getToken()}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new Error("Could not reach the server. Is the backend running?");
  }
  if (!res.ok) {
    const message = await extractError(res);
    if (res.status === 401) throw new AuthError(message);
    throw new Error(message);
  }
  return res.json();
}

// FastAPI errors arrive as {detail: string} or {detail: [{msg: ...}, ...]}.
async function extractError(res: Response): Promise<string> {
  const fallback = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) => (typeof d?.msg === "string" ? d.msg : null))
        .filter(Boolean);
      if (msgs.length) return msgs.join("; ");
    }
  } catch {
    // non-JSON body — fall through
  }
  return fallback;
}

// Classification-only call for the AI-vs-manual comparison page. Runs the
// same LLM pipeline as createTicket but never persists a ticket row.
export type ClassifyResult = {
  category: string;
  priority: string;
  team: string;
  reasoning: string;
  title: string;
  estimated_time: string;
  used_fallback: boolean;
};

export async function classifyTicket(text: string): Promise<ClassifyResult> {
  const data = await request("/classify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return data as ClassifyResult;
}

export type AuthResponse = { access_token: string; token_type: string };

export async function register(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const data = await request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return data as AuthResponse;
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const data = await request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return data as AuthResponse;
}

export async function createTicket(text: string): Promise<TicketDetail> {
  const data = await request(
    "/tickets",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    },
    true,
  );
  return normalizeTicket(data);
}

export async function fetchTickets(): Promise<TicketSummary[]> {
  const data = await request("/tickets", undefined, true);
  const list = Array.isArray(data)
    ? data
    : Array.isArray((data as { tickets?: unknown[] })?.tickets)
      ? (data as { tickets: unknown[] }).tickets
      : [];
  return list.map(normalizeTicket);
}

export async function fetchTicket(ticket_ref: string): Promise<TicketDetail> {
  const data = await request(
    `/tickets/${encodeURIComponent(ticket_ref)}`,
    undefined,
    true,
  );
  return normalizeTicket(data);
}

// The backend response shape may drift slightly as it's built out (e.g.
// category label vs category_id, nested assignee object vs flat fields).
// Normalize here so the pages can rely on one flat shape.
function normalizeTicket(raw: unknown): TicketDetail {
  const t = (raw ?? {}) as Record<string, unknown>;
  const assignee = (
    typeof t.assigned_to === "object" && t.assigned_to !== null
      ? t.assigned_to
      : {}
  ) as Record<string, unknown>;

  return {
    ticket_ref: str(t.ticket_ref) ?? "",
    title: str(t.title) ?? "(untitled)",
    priority: str(t.priority) ?? "Medium",
    status: str(t.status) ?? "Open",
    category: str(t.category) ?? str(t.category_label) ?? str(t.category_id) ?? "—",
    updated_at: str(t.updated_at) ?? str(t.created_at) ?? "",
    reasoning: str(t.reasoning) ?? null,
    assigned_to: str(t.assigned_to) ?? str(assignee.name) ?? null,
    description: str(t.description) ?? str(t.text) ?? "",
    role: str(t.role) ?? str(assignee.role) ?? null,
    reports_to: str(t.reports_to) ?? str(assignee.reports_to) ?? null,
    estimated_time:
      str(t.estimated_time) ?? num(t.estimated_time)?.toString() ?? null,
    created_at: str(t.created_at),
  };
}

function str(v: unknown): string | undefined {
  return typeof v === "string" && v !== "" ? v : undefined;
}

function num(v: unknown): number | undefined {
  return typeof v === "number" ? v : undefined;
}
