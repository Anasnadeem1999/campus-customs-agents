/**
 * The backend, typed.
 *
 * Every call goes to the FastAPI routes from Problem 7. Nothing in the
 * frontend knows anything about the shop that a route did not return -- no
 * cached prices, no remembered balances, no hard-coded ticket list. The
 * dashboard is a window onto the database, not a second copy of it.
 *
 * The backend is addressed directly at http://localhost:8000, which is what
 * makes this a genuine cross-origin call from the Vite page on :5173 -- and
 * therefore what the backend's CORS allowance actually has to permit. A dev
 * proxy would hide that same-origin, and the first deploy would discover it.
 *
 * Override with VITE_API_BASE if the backend is moved.
 */

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

export type Ticket = {
  id: number
  type: string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  lease_id: number | null
  invoice_id: number | null
  status: string
  notes: string | null
  created_at: string
  is_open: boolean
  is_resolved: boolean
}

export type TicketsResponse = {
  shop_date_today: string
  ticket_count: number
  open_count: number
  resolved_count: number
  tickets: Ticket[]
}

export type ToolUse = {
  tool: string
  arguments: Record<string, unknown>
  is_error: boolean
}

export type AgentEvent = {
  step: number
  run_id: string
  ticket_id: number | null
  agent: string
  delegated_by: string | null
  task: string | null
  says: string | null
  tools_used: ToolUse[]
  blocked_on: string | null
  needs_human: string | null
  model: string | null
  model_ok: boolean | null
  tokens: number | null
  duration_seconds: number | null
  started_at: string | null
  error: string | null
}

export type EventsResponse = {
  since: number
  returned: number
  latest_step: number
  events: AgentEvent[]
}

export type Approval = {
  id: number
  kind: string
  ref_id: number | null
  amount: number
  reason: string
  requested_by: string
  status: string
  approved_by: string | null
  consumed_by_payment_id: number | null
  cash_at_request_time?: {
    total_balance: number
    uncommitted: number
    would_leave_uncommitted: number
    fits_within_uncommitted: boolean
  }
}

export type Cash = {
  shop_date_today: string
  checking_balance: number
  approved_not_yet_paid: number
  uncommitted: number
}

/** Throws with the backend's own message, so a refusal reaches the screen intact. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      // FastAPI puts the reason in `detail`; a refused payment explains itself
      // there, and that explanation is the most useful thing on the screen.
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* non-JSON error body -- keep the status line */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  tickets: () => request<TicketsResponse>('/tickets'),
  cash: () => request<Cash>('/cash'),
  events: (since: number) => request<EventsResponse>(`/events?since=${since}&limit=200`),
  approvals: () => request<{ approvals: Approval[] }>('/approvals'),

  runTicket: (id: number) =>
    request<{ run_id: string; ticket_id: number; status: string }>(`/tickets/${id}/run`, {
      method: 'POST',
    }),

  approve: (id: number, approvedBy: string) =>
    request<{ cash_moved: boolean; checking_balance: number; note: string }>(
      `/approvals/${id}/approve`,
      { method: 'POST', body: JSON.stringify({ approved_by: approvedBy }) },
    ),

  reject: (id: number, approvedBy: string) =>
    request<{ status: string }>(`/approvals/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ approved_by: approvedBy }),
    }),

  reset: () => request<{ checking_balance: number }>('/reset', { method: 'POST' }),
}
