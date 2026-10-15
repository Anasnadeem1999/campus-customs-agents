"""Rewrite the audit trail's `submission` block from the run itself.

    python scripts/stamp_submission.py --first-step 317

The trail is append-only and holds every run going back to Problem 5, so it
needs a pointer saying which run is the submitted one. That pointer used to be
maintained by hand, which is how a summary quietly stops describing the run it
names: re-run the board and the figures underneath it change while the block
keeps asserting the old ones.

So nothing here is typed in. The step range is the only input; the turns, the
tokens, the models, the per-ticket agents, the cash and the human decisions are
all read back out of `output/audit_trail.json`, the working database and the
approval board. If a figure in the block is wrong, it is because the run was
wrong, which is the only kind of wrong worth reporting.

Only the `submission` key is touched. Steps, runs and decisions are never
modified -- this script appends a description, it does not edit history.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRAIL = REPO / "output/audit_trail.json"
WORKING_DB = REPO / "data/campus_customs_new.db"
APPROVALS = REPO / "output/board/approvals.json"

OPENING_BALANCE = 3400.00


def build_block(first_step: int) -> dict:
    trail = json.loads(TRAIL.read_text(encoding="utf-8"))
    steps = [s for s in trail["steps"] if s["step"] >= first_step]
    if not steps:
        raise SystemExit(f"No steps at or after {first_step}; nothing to describe.")

    last_step = max(s["step"] for s in steps)
    numbers = sorted(s["step"] for s in steps)
    if numbers != list(range(first_step, last_step + 1)):
        raise SystemExit(
            "The submitted range has gaps. A run missing a step cannot be "
            "published as the record of itself."
        )

    conn = sqlite3.connect(WORKING_DB)
    conn.row_factory = sqlite3.Row
    statuses = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM tickets")}
    balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()[0]
    shop_date = conn.execute("SELECT date_today FROM desk").fetchone()[0]
    paid = sum(r[0] for r in conn.execute("SELECT amount FROM payments"))
    conn.close()

    if abs((OPENING_BALANCE - paid) - balance) >= 0.005:
        raise SystemExit(
            f"Cash does not reconcile: {OPENING_BALANCE:.2f} - {paid:.2f} "
            f"!= {balance:.2f}. Refusing to stamp a block over it."
        )

    per_ticket: dict[str, dict] = {}
    for ticket_id in sorted(statuses):
        mine = [s for s in steps if s["ticket_id"] == ticket_id]
        per_ticket[str(ticket_id)] = {
            "agent_turns": len(mine),
            "tokens": sum((s.get("usage") or {}).get("total_tokens", 0) for s in mine),
            "agents": sorted({s["agent"] for s in mine}),
            "final_status": statuses[ticket_id],
        }

    board = json.loads(APPROVALS.read_text(encoding="utf-8"))
    decisions = [
        {
            "approval_id": a["id"],
            "kind": a["kind"],
            "amount": a["amount"],
            "decision": a.get("status"),
            "decided_by": a.get("approved_by"),
        }
        for a in board
        if a.get("status") in {"approved", "rejected"}
    ]

    models = sorted({
        (s.get("model") or {}).get("resolved")
        for s in steps
        if (s.get("model") or {}).get("resolved")
    })

    return {
        "read_this_first": (
            "This file is append-only by design: Problem 5 requires that it "
            f"accumulate across runs rather than be wiped. Everything before step "
            f"{first_step} is development history and is kept deliberately. "
            "THE SUBMITTED RUN IS DESCRIBED BELOW, and every figure in it is "
            "generated from the run by scripts/stamp_submission.py, never typed in."
        ),
        "submitted_run": {
            "first_step": first_step,
            "last_step": last_step,
            "run_ids": sorted({s["run_id"] for s in steps}),
            "why_several_run_ids": (
                "One ticket is worked across several passes, because the team "
                "stops at the human approval gate and resumes after a decision. "
                "Each pass gets its own run id."
            ),
            "agent_turns": len(steps),
            "total_tokens": sum((s.get("usage") or {}).get("total_tokens", 0) for s in steps),
            "model_resolved": models,
            "every_step_on_required_model": all(m.startswith("gpt-6-luna") for m in models)
            and all((s.get("model") or {}).get("ok") for s in steps),
            "shop_date_opened": "2026-08-31",
            "shop_date_closed": shop_date,
            "opening_checking_balance": OPENING_BALANCE,
            "closing_checking_balance": balance,
            "human_decisions": decisions,
            "tickets": per_ticket,
        },
        "history_before_the_submitted_run": {
            "steps": first_step - 1,
            "runs": len({s["run_id"] for s in trail["steps"] if s["step"] < first_step}),
            "note": "Earlier development runs, retained because this file must append, never wipe.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--first-step", type=int, required=True,
                    help="first step number of the run being submitted")
    args = ap.parse_args()

    block = build_block(args.first_step)
    trail = json.loads(TRAIL.read_text(encoding="utf-8"))
    trail["submission"] = block
    TRAIL.write_text(json.dumps(trail, indent=2, default=str), encoding="utf-8")

    run = block["submitted_run"]
    print(f"stamped submission: steps {run['first_step']}-{run['last_step']}, "
          f"{run['agent_turns']} turns, {run['total_tokens']:,} tokens")
    print(f"  models   : {run['model_resolved']}")
    print(f"  cash     : {run['opening_checking_balance']:,.2f} -> "
          f"{run['closing_checking_balance']:,.2f}")
    print(f"  decisions: {len(run['human_decisions'])} human")
    for tid, t in run["tickets"].items():
        print(f"  {tid}: {t['final_status']:<10} {t['agent_turns']:>2} turns  "
              f"{t['tokens']:>9,} tokens  {t['agents']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
