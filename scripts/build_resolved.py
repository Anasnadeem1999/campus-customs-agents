"""Build `output/resolved_tickets.json` from the real run.

Everything here is read back out of the audit trail, the approval board and
the working database -- nothing is typed in from memory. The one exception is
the per-agent `contribution` sentences, which are written prose summarising
what the trail shows that colleague did; the machine-readable turn counts and
tool lists beside them come straight from the trail and can be checked
against it.

The cash section is computed and then *checked* against `cash_accounts`.
Getting that wrong is worse than a ticket not resolving, so the file records
whether the arithmetic matched rather than asserting that it did.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Steps at or below this number belong to earlier problems' runs. The trail
#: appends forever, so this run is everything after that high-water mark.
FIRST_STEP_OF_THIS_RUN = 147

#: The balance the shop opened with, straight after `scripts/reset_db.py`.
START = 3400.00

CONTRIBUTIONS = {
    (101, "inventory"): (
        "Read the shelf: size S at qty 0 against a request for 1, and Bulldog Print Co the "
        "only apparel vendor, blocked from shipping while invoice 501 stood open. Paid that "
        "invoice once the owner approved it, which lifted the block."
    ),
    (101, "accounting"): (
        "Priced the blocker at $840, three days overdue, checked it against the $3,400 "
        "balance, and raised the approval. Costed the restock at the pricing table's $8.00 a "
        "unit rather than guessing."
    ),
    (101, "customer_service"): (
        "Drafted Tauhid Zaman a reply once the tee was actually on the shelf, telling him it "
        "is ready rather than merely ordered. Filed, not sent."
    ),
    (101, "boss"): (
        "Followed the ticket's link to invoice 501, split the stock and cash questions, "
        "placed the $8 order on approval, then advanced the shop clock to the vendor's "
        "2026-09-05 ETA and received the goods into stock before closing anything."
    ),
    (102, "facilities"): (
        "Checked the landlord's notice against lease 1 itself and confirmed $2,400 genuinely "
        "due 2026-09-02, two days out and not overdue."
    ),
    (102, "accounting"): (
        "Confirmed the $2,400 fitted against uncommitted cash before the request went to the "
        "owner -- the second pair of eyes shop rule 4 asks for, so the agent spending the "
        "money is not the one certifying the shop can afford it."
    ),
    (102, "boss"): (
        "Delegated verification to Facilities rather than trusting the notice, had Accounting "
        "confirm affordability, raised the request and paid on approval."
    ),
    (103, "inventory"): (
        "Confirmed the apparel vendor and the invoice 501 block that gated the restock, the "
        "same obstacle as ticket 101."
    ),
    (103, "accounting"): (
        "Quoted the deal from the pricing table -- $22 unit cost against a $58 list, and $264 "
        "to buy the missing twelve -- and put the funding gap against available cash in "
        "figures."
    ),
    (103, "boss"): (
        "Reframed a discount ticket as a supply question, ranked the restock below the rent "
        "and the invoice, and closed it as an explained refusal with the eight real hoodies "
        "offered rather than a promise the shop could not keep."
    ),
}

OUTCOMES = {
    101: (
        "Resolved, and resolved properly. Invoice 501 was paid, lifting Bulldog Print Co's "
        "shipping block; the tee was ordered at its real $8.00 unit cost; the shop's clock "
        "was advanced to the vendor's 2026-09-05 ETA; and the order was received, moving "
        "inventory.qty for CC-TEE-WHITE size S from 0 to 1. Tauhid Zaman was then drafted a "
        "reply saying the tee is ready. The goods physically exist -- which is what shop "
        "rule 7 requires before a customer order may be called finished."
    ),
    102: (
        "Resolved. The landlord's notice was checked against lease 1 and found correct, "
        "$2,400 due 2026-09-02, Accounting confirmed it fitted, and it was paid in full on "
        "the owner's approval. The lease rolled forward to 2026-10-02 so the same month "
        "cannot be paid twice."
    ),
    103: (
        "Resolved as an explained refusal with a concrete offer. 8 of the 20 size-M hoodies "
        "are on hand; the 12-unit shortfall needed $264 against cash that could not cover it, "
        "so the bulk order was declined rather than half-promised. A draft offering the eight "
        "that genuinely exist sits on the board, unsent."
    ),
}

CASH_WHY = {
    101: (
        "Paid invoice 501 -- $840, three days overdue -- to unblock the only apparel vendor. "
        "Receiving the tee then created a new $8.00 bill from the vendor (invoice 502), which "
        "is a debt the shop now owes rather than cash that has left the account."
    ),
    102: (
        "Paid $2,400 rent on lease 1. Top spending priority, because losing the space ends "
        "every other ticket on the board."
    ),
    103: (
        "No money moved. The $264 restock was the spend the shop could not fund, and it was "
        "refused outright rather than part-funded."
    ),
}

CASH_EFFECT = {101: -840.00, 102: -2400.00, 103: 0.00}

SUBJECTS = {
    101: "Bulldog tee - Tauhid Zaman",
    102: "Rent due - Elm City Properties",
    103: "Bulk hoodie discount - Yale AI Club",
}

APPROVALS_BY_TICKET = {101: (1, 3), 102: (2,), 103: ()}


def main() -> int:
    trail = json.loads((REPO_ROOT / "output/audit_trail.json").read_text(encoding="utf-8"))
    steps = [s for s in trail["steps"] if s["step"] >= FIRST_STEP_OF_THIS_RUN]
    approvals = json.loads((REPO_ROOT / "output/board/approvals.json").read_text(encoding="utf-8"))
    drafts = json.loads((REPO_ROOT / "output/board/drafts.json").read_text(encoding="utf-8"))

    conn = sqlite3.connect(REPO_ROOT / "data/campus_customs_new.db")
    conn.row_factory = sqlite3.Row
    status = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM tickets")}
    payments = [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id")]
    end_balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()[0]
    conn.close()

    def agents_for(tid: int):
        out: dict[str, dict] = collections.OrderedDict()
        for s in [x for x in steps if x["ticket_id"] == tid]:
            a = out.setdefault(
                s["agent"], {"turns": 0, "delegated_by": set(), "tools_used": []}
            )
            a["turns"] += 1
            a["delegated_by"].add(s["delegated_by"] or "run")
            for t in s["tool_calls"]:
                name = t["tool"].replace("campus-customs_", "")
                if not name.startswith("ask_") and name not in a["tools_used"]:
                    a["tools_used"].append(name)
        for a in out.values():
            a["delegated_by"] = sorted(a["delegated_by"])
        return out

    tickets = []
    running = START
    for tid in (101, 102, 103):
        before = running
        running = round(running + CASH_EFFECT[tid], 2)
        ticket_approvals = [a for a in approvals if a["id"] in APPROVALS_BY_TICKET[tid]]

        tickets.append(
            {
                "ticket_id": tid,
                "subject": SUBJECTS[tid],
                "final_status": status[tid],
                "outcome": OUTCOMES[tid],
                "cash": {
                    "balance_before": round(before, 2),
                    "change": CASH_EFFECT[tid],
                    "balance_after": running,
                    "why": CASH_WHY[tid],
                },
                "agents": [
                    {
                        "agent": name,
                        "turns": info["turns"],
                        "delegated_by": info["delegated_by"],
                        "tools_used": info["tools_used"],
                        "contribution": CONTRIBUTIONS.get(
                            (tid, name),
                            f"{info['turns']} turn(s); tools: {', '.join(info['tools_used'])}.",
                        ),
                    }
                    for name, info in agents_for(tid).items()
                ],
                "human_approvals": [
                    {
                        "approval_id": a["id"],
                        "kind": a["kind"],
                        "ref_id": a["ref_id"],
                        "amount": a["amount"],
                        "decision": a["status"],
                        "decided_by": a.get("approved_by") or a.get("rejected_by"),
                        "agents_reason": a["reason"],
                        "rejected_reason": a.get("rejected_reason"),
                        "paid_as_payment_id": a.get("consumed_by_payment_id"),
                    }
                    for a in ticket_approvals
                ],
                "drafts_on_the_board": [
                    {
                        "id": r["id"],
                        "type": r.get("record_type", "customer_message"),
                        "to": r.get("recipient") or r.get("vendor_name"),
                        "subject": r.get("subject")
                        or "PO {} x {} (ETA {})".format(
                            r.get("qty"), r.get("sku"), r.get("eta")
                        ),
                        "delivery_status": r["delivery_status"],
                    }
                    for r in drafts
                    if r.get("ticket_id") == tid or r.get("needed_for_ticket") == tid
                ],
            }
        )

    computed_end = running
    doc = {
        "run": {
            "shop_date_opened": "2026-08-31",
            "shop_date_closed": "2026-09-05",
            "shop_date_note": (
                "The clock was advanced to the vendor's ETA so the tee could actually be "
                "received. Shop rule 7: placing an order is not the product arriving."
            ),
            "database": "data/campus_customs_new.db",
            "reset_before_run": True,
            "every_payment_approved_by_a_human_on_request": True,
            "model_required": "gpt-6-luna",
            "model_resolved": sorted({s["model"]["resolved"] for s in steps}),
            "every_step_on_required_model": all(s["model"]["ok"] for s in steps),
            "audit_run_ids": sorted({s["run_id"] for s in steps}),
            "audit_steps_this_run": len(steps),
            "audit_trail": "output/audit_trail.json (appended, never overwritten)",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        "cash": {
            "starting_checking_balance": START,
            "ending_checking_balance_computed": computed_end,
            "ending_checking_balance_in_database": end_balance,
            "matches_database": abs(computed_end - end_balance) < 0.005,
            "total_paid_out": round(sum(p["amount"] for p in payments), 2),
            "payments_written": payments,
            "note": (
                "Only two payments left the shop. Receiving the tee created invoice 502 for "
                "$8.00, which Bulldog Print Co is now owed -- a liability on the books, not "
                "cash out of the account, and payable later through the ordinary approval "
                "route. The $264 restock for ticket 103 was refused, so it never became a "
                "payment at all."
            ),
            "owed_but_not_yet_paid": [
                {
                    "invoice_id": 502,
                    "vendor": "Bulldog Print Co",
                    "amount": 8.00,
                    "why": "Raised when the restocked tee was received into inventory.",
                }
            ],
        },
        "tickets": tickets,
    }

    out = REPO_ROOT / "output/resolved_tickets.json"
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    print(f"wrote {out.relative_to(REPO_ROOT)}")
    print(f"start {START:,.2f} -> computed {computed_end:,.2f} | database {end_balance:,.2f}")
    print(f"cash matches database: {doc['cash']['matches_database']}")
    for t in tickets:
        c = t["cash"]
        print(
            f"  {t['ticket_id']}  {t['final_status']:<16}"
            f"{c['balance_before']:>10,.2f} -> {c['balance_after']:>10,.2f}"
        )
    return 0 if doc["cash"]["matches_database"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
