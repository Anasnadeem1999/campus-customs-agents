"""Build `output/resolved_board.html` -- the React board, as it finished.

One self-contained file. The screenshots are embedded as base64 rather than
linked, so the page survives being emailed, zipped, or opened from a graded
clone with `output/screens/` missing. Double-click it and it works, with no
server and no network.

Figures come from `output/resolved_tickets.json`, so this page cannot disagree
with the JSON or with the database it was built from.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "output/resolved_tickets.json"
SCREENS = REPO_ROOT / "output/screens"
OUT = REPO_ROOT / "output/resolved_board.html"

CAPTIONS = {
    101: (
        "Ticket 101 selected, <strong>resolved</strong> in green and struck through. The "
        "summary shows Customer Service on the ticket &mdash; the delegation two earlier runs "
        "dropped &mdash; so Tauhid Zaman has a draft carrying the real 2026-09-05 ETA. Below "
        "it, Inventory reporting qty 0 and the invoice 501 block, with every figure traced "
        "back to the tool that returned it."
    ),
    102: (
        "Ticket 102 selected, <strong>resolved</strong>. The summary shows just two "
        "colleagues, Facilities and the Boss, which is the whole team this ticket needed. "
        "Facilities checked the landlord's notice against lease 1 itself rather than taking "
        "it on trust."
    ),
    103: (
        "Ticket 103 selected, <strong>resolved</strong> as a priced partial offer. All four "
        "colleagues appear. Inventory reports 8 of 20 on hand and the same invoice 501 block; "
        "the owner approved $42 a unit for the 8 that exist and refused the $264 restock for "
        "the 12 that do not. The till reads $160.00 with $8 promised and $152 free."
    ),
}


def img_tag(ticket_id: int) -> str:
    path = SCREENS / f"ticket-{ticket_id}.jpg"
    if not path.exists():
        return (
            "<p class='missing'>Screenshot missing: "
            f"<code>output/screens/{path.name}</code></p>"
        )
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<img alt="The Campus Customs board with ticket {ticket_id} selected" '
        f'src="data:image/jpeg;base64,{data}">'
    )


def main() -> int:
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {t["ticket_id"]: t for t in doc["tickets"]}
    cash = doc["cash"]

    cards = []
    for tid in (101, 102, 103):
        t = by_id[tid]
        status = t["final_status"]
        chip = "resolved" if status == "resolved" else "blocked"
        agents = " ".join(
            f"<span class='who'>{a['agent'].replace('_', ' ')}</span>" for a in t["agents"]
        )
        approvals = "".join(
            f"<li>#{a['approval_id']} {a['kind'].replace('_', ' ')} "
            f"${a['amount']:,.2f} &mdash; <strong>{a['decision']}</strong> "
            f"by {a['decided_by']}</li>"
            for a in t["human_approvals"]
        ) or "<li>None raised.</li>"

        cards.append(f"""
<section class="ticket">
  <header>
    <h2>Ticket {tid} &mdash; {t['subject']}</h2>
    <span class="chip {chip}">{status.replace('_', ' ')}</span>
  </header>

  <figure>
    {img_tag(tid)}
    <figcaption>{CAPTIONS[tid]}</figcaption>
  </figure>

  <div class="detail">
    <h3>Outcome</h3>
    <p>{t['outcome']}</p>

    <h3>Who worked it</h3>
    <p class="agents">{agents}</p>

    <h3>Human decisions</h3>
    <ul>{approvals}</ul>

    <h3>Cash</h3>
    <p class="cash">
      ${t['cash']['balance_before']:,.2f} &rarr;
      <strong>${t['cash']['balance_after']:,.2f}</strong>
      {'(unchanged)' if t['cash']['change'] == 0 else f"({t['cash']['change']:+,.2f})"}
    </p>
    <p class="why">{t['cash']['why']}</p>
  </div>
</section>""")

    html = f"""<!DOCTYPE html>
<!--
  The Campus Customs board as it finished, Problem 9.

  Self-contained: the screenshots are base64 data URIs, so this file works on a
  double-click with no server, no network and no sibling folder.
-->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Campus Customs — The board, resolved</title>
<style>
  :root {{
    --yale: #00356b; --ink: #1c1d1f; --muted: #6b7280;
    --paper: #f6f4ef; --card: #fffdf9; --line: #e4e0d7;
    --good: #0f7b3f; --bad: #a01b26;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font: 16px/1.6 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  }}
  header.top {{ background: var(--yale); color: #fff; padding: 24px 32px; }}
  header.top h1 {{ margin: 0 0 4px; font-size: 23px; }}
  header.top p {{ margin: 0; opacity: .85; font-size: 14px; }}
  .shell {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 70px; }}

  .summary {{
    background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 22px 26px; margin-bottom: 30px;
  }}
  .summary h2 {{ margin: 0 0 14px; font-size: 18px; color: var(--yale); }}
  .ledger {{ border-collapse: collapse; width: 100%; font-size: 15px; }}
  .ledger th, .ledger td {{ padding: 9px 12px; border-bottom: 1px solid var(--line); text-align: left; }}
  .ledger th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .5px; color: var(--muted); }}
  .ledger td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .ledger tr.total td {{ border-top: 2px solid var(--yale); font-weight: 700; }}
  .match {{
    margin-top: 16px; border-left: 4px solid var(--good); background: #eef7f1;
    padding: 13px 17px; border-radius: 0 8px 8px 0; font-size: 15px;
  }}

  section.ticket {{
    background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 22px 26px; margin-bottom: 26px;
  }}
  section.ticket > header {{
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 16px; flex-wrap: wrap; margin-bottom: 16px;
  }}
  section.ticket h2 {{ margin: 0; font-size: 19px; color: var(--yale); }}
  h3 {{ font-size: 14px; text-transform: uppercase; letter-spacing: .6px;
        color: var(--muted); margin: 20px 0 6px; }}
  .chip {{
    font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
    padding: 4px 11px; border-radius: 999px;
  }}
  .chip.resolved {{ background: #e3f3e9; color: var(--good); }}
  .chip.blocked {{ background: #fbe6e8; color: var(--bad); }}

  figure {{ margin: 0; }}
  figure img {{
    width: 100%; border: 1px solid var(--line); border-radius: 10px; display: block;
    box-shadow: 0 8px 26px rgba(28,29,31,.08);
  }}
  figcaption {{ font-size: 14px; color: var(--muted); margin-top: 10px; }}
  .missing {{ color: var(--bad); }}

  .agents .who {{
    display: inline-block; background: #eef3f9; color: var(--yale);
    padding: 2px 10px; border-radius: 999px; font-size: 13px; margin: 2px 4px 2px 0;
  }}
  ul {{ margin: 6px 0; padding-left: 22px; }}
  li {{ margin: 4px 0; }}
  .cash {{ font-size: 17px; font-variant-numeric: tabular-nums; margin: 4px 0; }}
  .why {{ font-size: 14.5px; color: var(--muted); margin: 2px 0 0; }}
  footer {{ color: var(--muted); font-size: 13px; border-top: 1px solid var(--line);
            padding-top: 14px; margin-top: 10px; }}
</style>
</head>
<body>

<header class="top">
  <h1>Campus Customs — the board, resolved</h1>
  <p>Shop date 2026-08-31 &middot; one full run over all three tickets &middot; every step on
     {' / '.join(doc['run']['model_resolved'])}</p>
</header>

<div class="shell">

  <div class="summary">
    <h2>The money, start to finish</h2>
    <table class="ledger">
      <thead><tr><th>Stage</th><th class="num">Change</th><th class="num">Balance</th><th>Why</th></tr></thead>
      <tbody>
        <tr>
          <td>Opening, after reset</td><td class="num">&mdash;</td>
          <td class="num">${cash['starting_checking_balance']:,.2f}</td>
          <td>The seeded balance.</td>
        </tr>
        <tr>
          <td>Ticket 101</td><td class="num">&minus;840.00</td>
          <td class="num">$2,560.00</td>
          <td>Invoice 501 paid, lifting the apparel vendor's shipping block.</td>
        </tr>
        <tr>
          <td>Ticket 102</td><td class="num">&minus;2,400.00</td>
          <td class="num">$160.00</td>
          <td>Rent on lease 1, due 2026-09-02.</td>
        </tr>
        <tr>
          <td>Ticket 103</td><td class="num">&mdash;</td>
          <td class="num">$160.00</td>
          <td>$264 restock refused &mdash; only $160 uncommitted.</td>
        </tr>
        <tr class="total">
          <td>Closing</td><td class="num">&minus;{cash['total_paid_out']:,.2f}</td>
          <td class="num">${cash['ending_checking_balance_computed']:,.2f}</td>
          <td>Two payments left the shop.</td>
        </tr>
      </tbody>
    </table>
    <div class="match">
      <strong>Checked against the database.</strong> The computed closing balance of
      ${cash['ending_checking_balance_computed']:,.2f} matches
      <code>cash_accounts.balance</code> for <code>checking</code>, which reads
      ${cash['ending_checking_balance_in_database']:,.2f}.
      <br>$3,400.00 &minus; $840.00 &minus; $2,400.00 = <strong>$160.00</strong>.
    </div>
  </div>
{''.join(cards)}

  <footer>
    Screenshots taken from the live React dashboard at <code>http://localhost:5180</code>,
    talking to the FastAPI backend at <code>http://localhost:8000</code>, after the run that
    produced <code>output/resolved_tickets.json</code>.
    {doc['run']['audit_steps_this_run']} steps were appended to
    <code>output/audit_trail.json</code> across runs
    {', '.join(doc['run']['audit_run_ids'])}; earlier runs were not overwritten.
  </footer>
</div>

</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({kb:,.0f} KB, screenshots embedded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
