/**
 * The Campus Customs desk.
 *
 * Laid out the way the work actually flows, left to right: the tickets you
 * could pick up, the team working the one you picked, and the decisions
 * waiting on you. The cash sits in the header because it is the one number
 * that matters on every ticket and must never be more than a glance away.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, type AgentEvent, type Approval, type Cash, type Ticket } from './api'
import { AGENTS, citedFigures, faceOf, readableSays } from './agents'

const APPROVER = 'Anas Nadeem'
const POLL_MS = 2000

type Toast = { id: number; text: string; tone: 'good' | 'bad' }

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [shopDate, setShopDate] = useState('')
  const [cash, setCash] = useState<Cash | null>(null)
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [running, setRunning] = useState<Set<number>>(new Set())
  const [toasts, setToasts] = useState<Toast[]>([])
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState<number | null>(null)

  // Tracked in a ref rather than state: the poller reads it on every tick and
  // putting it in state would restart the interval on each poll.
  const sinceRef = useRef(0)
  // One poll makes four requests, which can easily outlast the two-second
  // interval. Without this guard a second poll starts with the same `since`
  // as the first and both append the same events, which React reports as
  // duplicate keys and the reader sees as the team saying everything twice.
  const inFlight = useRef(false)
  const prevCash = useRef<number | null>(null)
  const [cashFlash, setCashFlash] = useState(false)

  const say = useCallback((text: string, tone: Toast['tone'] = 'good') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, text, tone }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 6000)
  }, [])

  const poll = useCallback(async () => {
    if (inFlight.current) return
    inFlight.current = true
    try {
      const [t, c, a, e] = await Promise.all([
        api.tickets(),
        api.cash(),
        api.approvals(),
        api.events(sinceRef.current),
      ])
      setOffline(false)
      setTickets(t.tickets)
      setShopDate(t.shop_date_today)

      // Flash the balance only when it actually changes, so the eye is drawn
      // to money moving rather than to the poll ticking.
      if (prevCash.current !== null && prevCash.current !== c.checking_balance) {
        setCashFlash(true)
        setTimeout(() => setCashFlash(false), 1600)
      }
      prevCash.current = c.checking_balance
      setCash(c)
      setApprovals(a.approvals)

      if (e.events.length) {
        sinceRef.current = Math.max(sinceRef.current, e.latest_step)
        setEvents((prev) => {
          // Merge on step number rather than trusting `since` alone. The
          // backend reset route rewinds the trail, and a stale response can
          // still land after a newer one -- in both cases the step number is
          // the only reliable identity an event has.
          const seen = new Set(prev.map((x) => x.step))
          const fresh = e.events.filter((x) => !seen.has(x.step))
          return fresh.length ? [...prev, ...fresh] : prev
        })
      }
    } catch {
      setOffline(true)
    } finally {
      inFlight.current = false
    }
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, POLL_MS)
    return () => clearInterval(id)
  }, [poll])

  // A run is finished when the board stops reporting the ticket as running and
  // the backend has moved its status on. Watching the ticket rather than the
  // run keeps the two in step even if a poll is missed.
  useEffect(() => {
    setRunning((prev) => {
      if (!prev.size) return prev
      const next = new Set(prev)
      for (const id of prev) {
        const ticket = tickets.find((t) => t.id === id)
        if (ticket && ticket.status !== 'open') {
          next.delete(id)
          say(`Ticket ${id} finished — ${ticket.status.replace('_', ' ')}`)
        }
      }
      return next.size === prev.size ? prev : next
    })
  }, [tickets, say])

  const ticketEvents = useMemo(
    () => events.filter((e) => selected === null || e.ticket_id === selected),
    [events, selected],
  )

  /** What each agent did on this ticket — the per-agent summary.
   *
   * Scoped to the ticket's **most recent run**, not its whole history. The
   * audit trail accumulates across every run ever made, so summing all of it
   * reported "Facilities — 7 turns" for a ticket this run touched twice,
   * silently folding in work from days ago. The question a desk is asking is
   * "what just happened", so the summary answers that one.
   */
  const latestRunEvents = useMemo(() => {
    if (!ticketEvents.length) return ticketEvents
    const lastRun = ticketEvents[ticketEvents.length - 1].run_id
    return ticketEvents.filter((e) => e.run_id === lastRun)
  }, [ticketEvents])

  const perAgent = useMemo(() => {
    const byAgent = new Map<string, { steps: number; tools: Set<string>; last: AgentEvent }>()
    for (const e of latestRunEvents) {
      const entry = byAgent.get(e.agent) ?? { steps: 0, tools: new Set<string>(), last: e }
      entry.steps += 1
      entry.last = e
      for (const t of e.tools_used) entry.tools.add(t.tool.replace('campus-customs_', ''))
      byAgent.set(e.agent, entry)
    }
    return [...byAgent.entries()]
  }, [latestRunEvents])

  const pending = approvals.filter((a) => a.status === 'pending')

  async function runTicket(id: number) {
    setBusy(id)
    try {
      await api.runTicket(id)
      setSelected(id)
      setRunning((r) => new Set(r).add(id))
      say(`The team is working ticket ${id}`)
    } catch (err) {
      say(String(err instanceof Error ? err.message : err), 'bad')
    } finally {
      setBusy(null)
    }
  }

  async function decide(id: number, yes: boolean) {
    setBusy(-id)
    try {
      if (yes) {
        const r = await api.approve(id, APPROVER)
        say(r.cash_moved ? `Paid. Checking is now $${r.checking_balance.toLocaleString()}` : r.note)
      } else {
        await api.reject(id, APPROVER)
        say(`Request ${id} rejected`)
      }
      await poll()
    } catch (err) {
      // A refused payment explains itself; that explanation is the single most
      // useful thing on the screen, so it is shown in full rather than summarised.
      say(String(err instanceof Error ? err.message : err), 'bad')
    } finally {
      setBusy(null)
    }
  }

  async function resetShop() {
    setBusy(-9999)
    try {
      await api.reset()
      setEvents([])
      sinceRef.current = 0
      setSelected(null)
      setRunning(new Set())
      prevCash.current = null
      say('Shop reset to the original figures')
      await poll()
    } catch (err) {
      say(String(err instanceof Error ? err.message : err), 'bad')
    } finally {
      setBusy(null)
    }
  }

  const selectedTicket = tickets.find((t) => t.id === selected) ?? null

  return (
    <div className="desk">
      <header className="masthead">
        <div className="brand">
          <div className="crest">CC</div>
          <div>
            <h1>Campus Customs</h1>
            <p className="sub">Operations desk {shopDate && <>&middot; shop date {shopDate}</>}</p>
          </div>
        </div>

        <div className="header-right">
          <div className={`till ${cashFlash ? 'flash' : ''}`}>
            <span className="till-label">Checking</span>
            <span className="till-amount">
              ${cash ? cash.checking_balance.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '—'}
            </span>
            {cash && cash.approved_not_yet_paid > 0 && (
              <span className="till-note">
                ${cash.approved_not_yet_paid.toLocaleString()} promised &middot; $
                {cash.uncommitted.toLocaleString()} free
              </span>
            )}
          </div>
          <button className="ghost" onClick={resetShop} disabled={busy === -9999}>
            {busy === -9999 ? 'Resetting…' : 'Reset shop'}
          </button>
        </div>
      </header>

      {offline && (
        <div className="offline">
          Can’t reach the backend at <code>http://localhost:8000</code>. Start it with{' '}
          <code>cd backend &amp;&amp; uvicorn main:app --reload --port 8000</code>.
        </div>
      )}

      <main className="columns">
        {/* ── the board ───────────────────────────────────────────── */}
        <section className="col board">
          <h2 className="col-title">The board</h2>
          {!tickets.length && <p className="empty">No tickets loaded.</p>}
          {tickets.map((t) => {
            const isRunning = running.has(t.id)
            return (
              <article
                key={t.id}
                className={[
                  'ticket',
                  t.is_resolved ? 'resolved' : '',
                  selected === t.id ? 'selected' : '',
                  isRunning ? 'running' : '',
                ].join(' ')}
                onClick={() => setSelected(t.id)}
              >
                <div className="ticket-top">
                  <span className="ticket-id">#{t.id}</span>
                  <StatusChip status={t.status} running={isRunning} />
                </div>
                <h3>{t.subject}</h3>
                <p className="requester">{t.requester}</p>
                <p className="ask">
                  {t.sku ? (
                    <>
                      {t.qty} &times; <code>{t.sku}</code> {t.size && <>size {t.size}</>}
                    </>
                  ) : (
                    t.type.replace('_', ' ')
                  )}
                </p>
                <button
                  className="run"
                  disabled={isRunning || busy === t.id}
                  onClick={(e) => {
                    e.stopPropagation()
                    runTicket(t.id)
                  }}
                >
                  {isRunning ? 'Team is working…' : busy === t.id ? 'Starting…' : 'Put the team on it'}
                </button>
              </article>
            )
          })}
        </section>

        {/* ── the feed ────────────────────────────────────────────── */}
        <section className="col feed">
          <h2 className="col-title">
            {selectedTicket ? `Ticket #${selectedTicket.id} — the team at work` : 'The team at work'}
          </h2>

          {selectedTicket && perAgent.length > 0 && (
            <div className="summary">
              <h4>What each colleague did — latest run</h4>
              {perAgent.map(([agent, info]) => {
                const face = faceOf(agent)
                return (
                  <div key={agent} className="summary-row">
                    <Monogram agent={agent} />
                    <div>
                      <strong style={{ color: face.colour }}>{face.name}</strong>
                      <span className="muted">
                        {' '}
                        — {info.steps} turn{info.steps === 1 ? '' : 's'}
                        {info.tools.size > 0 && <>, {[...info.tools].join(', ')}</>}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {!ticketEvents.length && (
            <p className="empty">
              {selectedTicket
                ? 'Nothing yet. Put the team on this ticket and their work appears here as it happens.'
                : 'Pick a ticket to watch the team work it.'}
            </p>
          )}

          {ticketEvents.map((e) => {
            const face = faceOf(e.agent)
            const figures = citedFigures(e.says)
            return (
              <article key={e.step} className="event" style={{ borderLeftColor: face.colour }}>
                <div className="event-head">
                  <Monogram agent={e.agent} />
                  <div className="who">
                    <strong style={{ color: face.colour }}>{face.name}</strong>
                    {e.delegated_by && (
                      <span className="asked-by">asked by {faceOf(e.delegated_by).name}</span>
                    )}
                  </div>
                  <span className="step-no">#{e.step}</span>
                </div>

                {e.error ? (
                  <p className="err">{e.error}</p>
                ) : (
                  <p className="says">{readableSays(e.says)}</p>
                )}

                {e.tools_used.length > 0 && (
                  <div className="tools">
                    {e.tools_used.map((t, i) => (
                      <span key={i} className={`tool ${t.is_error ? 'tool-err' : ''}`}>
                        {t.tool.replace('campus-customs_', '')}
                      </span>
                    ))}
                  </div>
                )}

                {figures.length > 0 && (
                  <div className="figures">
                    {figures.map((f, i) => (
                      <span key={i} className="figure" title={`read from ${f.from}`}>
                        {f.label} <b>{f.value}</b>
                      </span>
                    ))}
                  </div>
                )}

                {e.blocked_on && <p className="blocked">Blocked on: {e.blocked_on}</p>}

                <div className="event-foot">
                  {e.model && (
                    <span className={e.model_ok ? 'ok' : 'notok'}>
                      {e.model_ok ? '✓' : '✗'} {e.model}
                    </span>
                  )}
                  {e.tokens != null && <span>{e.tokens.toLocaleString()} tokens</span>}
                  {e.duration_seconds != null && <span>{e.duration_seconds.toFixed(1)}s</span>}
                </div>
              </article>
            )
          })}
        </section>

        {/* ── your decisions ──────────────────────────────────────── */}
        <section className="col inbox">
          <h2 className="col-title">
            Waiting on you {pending.length > 0 && <span className="count">{pending.length}</span>}
          </h2>

          {!pending.length && (
            <p className="empty">
              Nothing to decide. The team asks here before any money moves — it can’t approve
              anything itself.
            </p>
          )}

          {pending.map((a) => (
            <article key={a.id} className="approval">
              <div className="approval-top">
                <span className="kind">{a.kind.replace('_', ' ')}</span>
                <span className="amount">${a.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <p className="why">{a.reason}</p>
              {a.cash_at_request_time && (
                <p className="leaves">
                  Leaves ${a.cash_at_request_time.would_leave_uncommitted.toLocaleString()} free
                  {!a.cash_at_request_time.fits_within_uncommitted && (
                    <strong className="tight"> — tight</strong>
                  )}
                </p>
              )}
              <p className="asked-by-line">asked by {faceOf(a.requested_by).name}</p>
              <div className="decide">
                <button className="yes" disabled={busy === -a.id} onClick={() => decide(a.id, true)}>
                  {busy === -a.id ? 'Working…' : 'Approve & pay'}
                </button>
                <button className="no" disabled={busy === -a.id} onClick={() => decide(a.id, false)}>
                  Decline
                </button>
              </div>
            </article>
          ))}

          <div className="roster">
            <h4>The team</h4>
            {Object.values(AGENTS).map((a) => (
              <div key={a.id} className="roster-row">
                <Monogram agent={a.id} />
                <div>
                  <strong style={{ color: a.colour }}>{a.name}</strong>
                  <p className="muted">{a.owns}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <div className="toasts">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.tone}`}>
            {t.text}
          </div>
        ))}
      </div>
    </div>
  )
}

function Monogram({ agent }: { agent: string }) {
  const face = faceOf(agent)
  return (
    <span className="monogram" style={{ background: face.tint, color: face.colour }}>
      {face.monogram}
    </span>
  )
}

function StatusChip({ status, running }: { status: string; running: boolean }) {
  if (running) return <span className="chip working">working</span>
  const label = status.replace('_', ' ')
  return <span className={`chip s-${status}`}>{label}</span>
}
