/**
 * Who the five colleagues are, visually.
 *
 * The hardest thing to read on a busy board is *who is speaking*. A feed where
 * every entry looks alike forces you to read the name on every line, which is
 * exactly the work a dashboard is supposed to save you. So each agent gets a
 * fixed colour and a fixed two-letter monogram, used everywhere that agent
 * appears -- the feed, the summary, the delegation arrows.
 *
 * The colours are chosen to stay distinguishable rather than to be pretty in
 * isolation: the Boss is the Yale navy of the header because the Boss is the
 * shop speaking, and the four specialists take hues far enough apart on the
 * wheel to be told apart at a glance and in the common forms of colour
 * blindness. Colour is never the only signal -- the monogram and the name are
 * always there too.
 */

export type AgentId = 'boss' | 'inventory' | 'accounting' | 'facilities' | 'customer_service'

export type AgentFace = {
  id: AgentId
  name: string
  monogram: string
  colour: string
  tint: string
  owns: string
}

export const AGENTS: Record<AgentId, AgentFace> = {
  boss: {
    id: 'boss',
    name: 'Boss',
    monogram: 'BO',
    colour: '#00356b',
    tint: '#e8eff7',
    owns: 'Reads the ticket, decides who works it, makes the final call',
  },
  inventory: {
    id: 'inventory',
    name: 'Inventory',
    monogram: 'IN',
    colour: '#0f7b3f',
    tint: '#e7f4ec',
    owns: 'Stock by SKU and size, shortfalls, restock vendors',
  },
  accounting: {
    id: 'accounting',
    name: 'Accounting',
    monogram: 'AC',
    colour: '#8a5a00',
    tint: '#fbf1dd',
    owns: 'Cash, invoices, margins, preparing approvals',
  },
  facilities: {
    id: 'facilities',
    name: 'Facilities',
    monogram: 'FA',
    colour: '#6b3fa0',
    tint: '#f1ebf8',
    owns: 'The lease, rent, the landlord, the premises',
  },
  customer_service: {
    id: 'customer_service',
    name: 'Customer Service',
    monogram: 'CS',
    colour: '#a01b46',
    tint: '#fbe9ef',
    owns: 'Drafts what a customer will read',
  },
}

/** Unknown agent names must still render rather than crash the board. */
export function faceOf(agent: string): AgentFace {
  return (
    AGENTS[agent as AgentId] ?? {
      id: 'boss',
      name: agent,
      monogram: agent.slice(0, 2).toUpperCase(),
      colour: '#5b6670',
      tint: '#f0f2f5',
      owns: '',
    }
  )
}

/**
 * Agent output arrives as the JSON of a structured result. Showing raw JSON on
 * a desk someone is meant to sit at would be a failure of nerve -- the whole
 * point is that a human can follow what happened without reading a transcript.
 */
export function readableSays(says: string | null): string {
  if (!says) return ''
  const trimmed = says.trim()
  if (!trimmed.startsWith('{')) return trimmed
  try {
    const parsed = JSON.parse(trimmed)
    // Specialists answer with `answer`; the Boss answers with `decision`.
    return parsed.answer ?? parsed.decision ?? trimmed
  } catch {
    // A long output is trimmed in the audit trail, which leaves the JSON
    // unterminated and unparseable -- and those are exactly the steps worth
    // reading. Pull the field out textually rather than dumping the raw
    // object on a desk someone is meant to sit at.
    return extractField(trimmed, 'answer') ?? extractField(trimmed, 'decision') ?? trimmed
  }
}

/** Read one top-level string field out of JSON too truncated to parse. */
function extractField(source: string, field: string): string | null {
  const start = source.indexOf(`"${field}"`)
  if (start === -1) return null
  const open = source.indexOf('"', source.indexOf(':', start) + 1)
  if (open === -1) return null

  const ESCAPES: Record<string, string> = { n: '\n', t: '\t', '"': '"', '\\': '\\', '/': '/' }

  let out = ''
  for (let i = open + 1; i < source.length; i++) {
    const ch = source[i]
    if (ch === '\\') {
      // Honour the escape rather than ending the string early on an escaped
      // quote -- agents quote the shop's own wording often enough that this
      // is the difference between a readable sentence and a severed one.
      const next = source[i + 1] ?? ''
      if (next === 'u') {
        // \uXXXX, which is how the trail stores every curly quote, dash
        // and accent the agents write. Without this the backslash is
        // dropped and the digits are left on the page: a vendor's
        // "apparel reprint" came out as u201capparel reprintu201d.
        const hex = source.slice(i + 2, i + 6)
        if (/^[0-9a-fA-F]{4}$/.test(hex)) {
          out += String.fromCharCode(parseInt(hex, 16))
          i += 5
          continue
        }
      }
      out += ESCAPES[next] ?? next
      i++
      continue
    }
    if (ch === '"') return out
    out += ch
  }
  // Ran off the end: the field itself was cut mid-sentence. Say so, rather
  // than pretending the agent stopped talking there.
  return out.length ? `${out}…` : null
}

/** The figures an agent cited, so a number on screen can be traced to a tool. */
export function citedFigures(says: string | null): { label: string; value: string; from: string }[] {
  if (!says?.trim().startsWith('{')) return []
  try {
    const parsed = JSON.parse(says)
    const figures = parsed.figures
    if (!Array.isArray(figures)) return []
    return figures.map((f: { label: string; value: string; from_tool: string }) => ({
      label: f.label,
      value: f.value,
      from: (f.from_tool ?? '').replace('campus-customs_', ''),
    }))
  } catch {
    return []
  }
}
