"""Fill the Actual sections and the Cash tab of `output/desk_tickets.html`.

The Expected sections written in Problem 6 are **not touched**. That was the
point of writing them before the run: a prediction edited after the result is
not a prediction. This script only replaces the three empty `Actual` blocks
and the placeholder Cash tab.

Figures come from `output/resolved_tickets.json`, which is itself built from
the audit trail, the approval board and the working database -- so the page,
the JSON and the database cannot drift apart.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "output/desk_tickets.html"
DATA = REPO_ROOT / "output/resolved_tickets.json"

AGENT_NAMES = {
    "boss": "Boss",
    "inventory": "Inventory",
    "accounting": "Accounting",
    "facilities": "Facilities",
    "customer_service": "Customer Service",
}

#: How the run compared to the plan, per ticket. Written by reading the two
#: side by side -- the delegation lists themselves come from the trail.
VERDICTS = {
    101: {
        "matched": [
            "Boss called <strong>Inventory first</strong>, exactly as planned, and for the "
            "reason planned: the stock answer reframed the ticket before any money was discussed.",
            "Boss &rarr; Accounting second, once Inventory reported the vendor block.",
            "<strong>Facilities was not called</strong> &mdash; correctly, as predicted.",
        ],
        "diverged": [
            "<strong>Customer Service was never called.</strong> The plan had it third, drafting "
            "Tauhid a reply. It did not happen, so the one person actually waiting on this "
            "ticket was never written to. The shop ordered his tee and told him nothing. "
            "This is the clearest miss of the run.",
        ],
        "verdict": "2 of 3 planned delegations happened. The missing one was the customer.",
    },
    102: {
        "matched": [
            "Boss called <strong>Facilities first</strong>, as planned, and Facilities did the "
            "thing the plan existed for: it checked the landlord's claim against lease 1 rather "
            "than taking the notice at face value.",
            "<strong>Inventory and Customer Service were both left out</strong>, as predicted. "
            "No stock question, and the landlord is not a customer.",
        ],
        "diverged": [
            "<strong>The Facilities &rarr; Accounting hop did not happen.</strong> The plan "
            "expected a peer-to-peer delegation to check affordability. Instead Facilities and "
            "the Boss each called <code>get_cash_position</code> themselves. "
            "<em>This divergence is arguably the team being right and the plan being wrong:</em> "
            "shop rule 7 says not to delegate what a tool in front of you already answers, and "
            "asking a colleague would have cost a whole model call to return the same number.",
        ],
        "verdict": "1 of 2 planned delegations happened, and skipping the other was the better call.",
    },
    103: {
        "matched": [
            "Boss called <strong>Inventory first, not Accounting</strong> &mdash; the call the "
            "plan flagged as the one most likely to be got wrong, since the ticket is typed "
            "<code>price_override</code> and reads like a pricing question.",
            "Boss &rarr; Accounting second, with the 12-unit shortfall already in hand.",
            "Boss &rarr; Customer Service third, and a draft was actually filed.",
            "<strong>Facilities was not called</strong>, as predicted.",
        ],
        "diverged": [
            "Nothing. The run followed the plan step for step, including the optional "
            "<code>price_override</code> request the plan said it would not penalise either way.",
        ],
        "verdict": "3 of 3 planned delegations happened, in the planned order.",
    },
}


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def agent_rows(ticket: dict) -> str:
    rows = []
    for a in ticket["agents"]:
        asked = ", ".join(
            "the run" if b == "run" else AGENT_NAMES.get(b, b) for b in a["delegated_by"]
        )
        tools = " ".join(f"<code>{t}</code>" for t in a["tools_used"])
        rows.append(
            "<tr>"
            f"<td><strong>{AGENT_NAMES.get(a['agent'], a['agent'])}</strong></td>"
            f"<td>{a['turns']}</td>"
            f"<td>{asked}</td>"
            f"<td>{esc(a['contribution'])}</td>"
            f"<td class='toolcell'>{tools}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def approval_rows(ticket: dict) -> str:
    if not ticket["human_approvals"]:
        return "<tr><td colspan='5'>None raised for this ticket.</td></tr>"
    rows = []
    for a in ticket["human_approvals"]:
        mark = "approved" if a["decision"] == "approved" else "rejected"
        paid = f"paid as payment {a['paid_as_payment_id']}" if a["paid_as_payment_id"] else "no cash moved"
        rows.append(
            "<tr>"
            f"<td>#{a['approval_id']}</td>"
            f"<td>{a['kind'].replace('_', ' ')} (ref {a['ref_id']})</td>"
            f"<td>${a['amount']:,.2f}</td>"
            f"<td><span class='chip s-{'resolved' if mark == 'approved' else 'blocked'}'>{mark}</span> by {esc(a['decided_by'] or '-')}</td>"
            f"<td>{paid}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def actual_block(ticket: dict) -> str:
    tid = ticket["ticket_id"]
    v = VERDICTS[tid]
    status = ticket["final_status"]
    chip = "s-resolved" if status == "resolved" else "s-blocked"
    drafts = ticket["drafts_on_the_board"]
    drafts_html = (
        "<ul class='tight'>"
        + "".join(
            f"<li>{esc(d['type'].replace('_', ' '))} to <strong>{esc(d['to'])}</strong> "
            f"&mdash; {esc(d['subject'])} <em>({d['delivery_status'].replace('_', ' ')})</em></li>"
            for d in drafts
        )
        + "</ul>"
        if drafts
        else "<p class='note'>Nothing was filed on the board for this ticket.</p>"
    )

    return f"""  <h2>Actual &mdash; what the run did</h2>

  <div class="card">
    <div class="ticket-head">
      <h3 style="margin:0">Final status</h3>
      <span class="chip {chip}">{status.replace('_', ' ')}</span>
    </div>
    <p>{esc(ticket['outcome'])}</p>

    <h3>Who worked it, and with what</h3>
    <table>
      <thead><tr><th>Agent</th><th>Turns</th><th>Asked by</th><th>What they contributed</th><th>MCP tools used</th></tr></thead>
      <tbody>
{agent_rows(ticket)}
      </tbody>
    </table>

    <h3>Human approvals</h3>
    <table>
      <thead><tr><th>#</th><th>What</th><th>Amount</th><th>Decision</th><th>Effect</th></tr></thead>
      <tbody>
{approval_rows(ticket)}
      </tbody>
    </table>

    <h3>Left on the board</h3>
    {drafts_html}

    <h3>Cash effect</h3>
    <p>
      ${ticket['cash']['balance_before']:,.2f} &rarr;
      <strong>${ticket['cash']['balance_after']:,.2f}</strong>
      ({'no change' if ticket['cash']['change'] == 0 else f"{ticket['cash']['change']:+,.2f}"}).
      {esc(ticket['cash']['why'])}
    </p>
  </div>

  <h2>Expected vs actual</h2>

  <div class="card">
    <h3>Where the run followed the plan</h3>
    <ul class="tight">
{chr(10).join('      <li>' + m + '</li>' for m in v['matched'])}
    </ul>

    <h3>Where it diverged</h3>
    <ul class="tight">
{chr(10).join('      <li>' + m + '</li>' for m in v['diverged'])}
    </ul>

    <p class="note"><strong>Verdict:</strong> {v['verdict']}</p>
  </div>"""


def cash_tab(doc: dict) -> str:
    c = doc["cash"]
    rows = []
    for t in doc["tickets"]:
        cash = t["cash"]
        change = (
            "&mdash;" if cash["change"] == 0 else f"<strong>{cash['change']:+,.2f}</strong>"
        )
        rows.append(
            "<tr>"
            f"<td class='step'>#{t['ticket_id']}</td>"
            f"<td>{t['final_status'].replace('_', ' ')}</td>"
            f"<td class='num'>${cash['balance_before']:,.2f}</td>"
            f"<td class='num'>{change}</td>"
            f"<td class='num'>${cash['balance_after']:,.2f}</td>"
            f"<td>{esc(cash['why'])}</td>"
            "</tr>"
        )

    payments = "\n".join(
        "<tr>"
        f"<td>{p['id']}</td><td>{p['kind']}</td><td>{p['ref_id']}</td>"
        f"<td class='num'>${p['amount']:,.2f}</td><td>{p['paid_at']}</td>"
        f"<td>{esc(p['approved_by'])}</td>"
        "</tr>"
        for p in c["payments_written"]
    )

    match = c["matches_database"]
    verdict_class = "cash-ok" if match else "cash-bad"
    verdict = (
        "The computed ending balance matches <code>cash_accounts</code> exactly."
        if match
        else "MISMATCH &mdash; the arithmetic and the database disagree."
    )

    return f"""  <div class="card">
    <h2 style="margin-top:0">The money, start to finish</h2>
    <p>
      Shop date <strong>2026-08-31</strong>. The working database was reset from the
      pristine seed immediately before this run, so the opening balance is the
      seeded one.
    </p>

    <table>
      <thead>
        <tr><th>Ticket</th><th>Ended</th><th>Before</th><th>Change</th><th>After</th><th>Why</th></tr>
      </thead>
      <tbody>
        <tr class="opening">
          <td class="step">&mdash;</td><td>opening balance</td>
          <td class="num">&mdash;</td><td class="num">&mdash;</td>
          <td class="num"><strong>${c['starting_checking_balance']:,.2f}</strong></td>
          <td>Straight after <code>scripts/reset_db.py</code>.</td>
        </tr>
{chr(10).join(rows)}
        <tr class="closing">
          <td class="step">&mdash;</td><td><strong>closing balance</strong></td>
          <td class="num">&mdash;</td>
          <td class="num"><strong>&minus;{c['total_paid_out']:,.2f}</strong></td>
          <td class="num"><strong>${c['ending_checking_balance_computed']:,.2f}</strong></td>
          <td>Two payments left the shop.</td>
        </tr>
      </tbody>
    </table>

    <div class="{verdict_class}">
      <strong>Checked against the database.</strong>
      Computed closing balance <strong>${c['ending_checking_balance_computed']:,.2f}</strong>;
      <code>cash_accounts.balance</code> for <code>checking</code> reads
      <strong>${c['ending_checking_balance_in_database']:,.2f}</strong>. {verdict}
    </div>

    <h3>The arithmetic, in one line</h3>
    <p class="sum">
      $3,400.00 &minus; $840.00 (invoice 501) &minus; $2,400.00 (rent, lease 1)
      = <strong>$160.00</strong>
    </p>

    <h3>Payments actually written to the database</h3>
    <table>
      <thead><tr><th>#</th><th>Kind</th><th>Ref</th><th>Amount</th><th>Paid at</th><th>Approved by</th></tr></thead>
      <tbody>
{payments}
      </tbody>
    </table>

    <h3>What did <em>not</em> move the balance, and why</h3>
    <ul class="tight">
      <li>
        <strong>The $8 purchase order (ticket 101).</strong> Approved and placed with
        Bulldog Print Co, ETA 2026-09-05. A purchase order is a commitment, not a
        payment &mdash; cash leaves when the vendor invoices, which has not happened.
        Counting it here would show the shop $8 poorer than its own books.
      </li>
      <li>
        <strong>The $264 restock (ticket 103).</strong> Requested, and
        <strong>refused by the owner</strong>: $160 of uncommitted cash will not cover
        $264. It never became a payment, so it never touched the balance. This is the
        seeded cash squeeze landing &mdash; $840 + $2,400 = $3,240 against $3,400 leaves
        $160, and the third spend has to be refused.
      </li>
      <li>
        <strong>The $50 price override (ticket 103).</strong> A price, not a payment.
        Approving it moves nothing; it sets what the shop would charge for the 8 hoodies
        it actually has.
      </li>
    </ul>

    <p class="note">
      Revenue is not modelled in this homework &mdash; cash only goes out &mdash; so no
      sale appears on the credit side, including the 8 hoodies offered at $50.
    </p>
  </div>"""


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    doc = json.loads(DATA.read_text(encoding="utf-8"))

    if not doc["cash"]["matches_database"]:
        print("REFUSING to write: the cash arithmetic does not match the database.")
        return 1

    by_id = {t["ticket_id"]: t for t in doc["tickets"]}

    # Replace each ticket's Actual placeholder, section by section, so the two
    # identically-worded placeholders cannot be confused for one another.
    for tid in (101, 102, 103):
        marker = f'<section class="panel" id="t{tid}">'
        if tid == 101:
            marker = f'<section class="panel active" id="t{tid}">'
        start = html.index(marker)
        end = html.index("</section>", start)
        body = html[start:end]
        placeholder_start = body.index('<div class="actual">')
        placeholder_end = body.index("</div>", body.index("<p>", placeholder_start)) + len("</div>")
        new_body = body[:placeholder_start] + actual_block(by_id[tid]) + body[placeholder_end:]
        html = html[:start] + new_body + html[end:]

    # Replace the Cash tab placeholder.
    cash_start = html.index('<section class="panel" id="cash">')
    cash_end = html.index("</section>", cash_start)
    html = (
        html[:cash_start]
        + '<section class="panel" id="cash">\n'
        + cash_tab(doc)
        + "\n"
        + html[cash_end:]
    )

    # Styles the new blocks need.
    html = html.replace(
        "  footer { color: var(--muted);",
        """  td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  tr.opening td, tr.closing td { background: var(--ghost); }
  tr.closing td { border-top: 2px solid var(--yale); }
  .toolcell code { display: inline-block; margin: 1px 2px; font-size: 12px; }
  .cash-ok, .cash-bad {
    border-left: 4px solid var(--good); background: #eef7f1;
    padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 18px 0;
  }
  .cash-bad { border-left-color: var(--stop); background: #fbe9ea; }
  .sum { font-size: 17px; background: var(--ghost); padding: 12px 16px; border-radius: 8px; }
  footer { color: var(--muted);""",
    )

    # The Cash tab is no longer "later".
    html = html.replace(
        '<button role="tab" aria-selected="false" data-tab="cash">Cash<span class="sub">later</span></button>',
        '<button role="tab" aria-selected="false" data-tab="cash">Cash<span class="sub">$3,400 &rarr; $160</span></button>',
    )

    PAGE.write_text(html, encoding="utf-8")
    print(f"filled {PAGE.relative_to(REPO_ROOT)}")
    for tid in (101, 102, 103):
        print(f"  ticket {tid}: {by_id[tid]['final_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
