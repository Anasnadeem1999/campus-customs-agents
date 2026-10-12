"""The human's half of the approval gate. Deliberately not an MCP tool.

Constraint 5 says every payment needs human approval. A prompt telling an
agent "do not approve your own spending" is a request; this is a guarantee.
The MCP server exposes `request_approval`, so an agent can ask -- and exposes
nothing at all that sets `status` to `approved`. The verb exists only here, in
a script an agent has no way to run.

Usage:
    python scripts/approve.py --list
    python scripts/approve.py --id 1 --by "Anas Nadeem"
    python scripts/approve.py --id 2 --reject --by "Anas Nadeem" --why "cash too thin"
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_server import board  # noqa: E402
from mcp_server.db import WORKING_DB, money  # noqa: E402


def shop_today() -> str:
    conn = sqlite3.connect(f"file:{WORKING_DB.as_posix()}?mode=ro", uri=True)
    try:
        return conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()[0]
    finally:
        conn.close()


def show(rows: list[dict]) -> None:
    if not rows:
        print("The approval board is empty.")
        return
    for r in rows:
        mark = {"pending": "[ ]", "approved": "[x]", "rejected": "[-]"}.get(r.get("status"), "[?]")
        spent = f"  spent on payment {r['consumed_by_payment_id']}" if r.get("consumed_by_payment_id") else ""
        print(f"{mark} #{r['id']}  {r['kind']} ref={r.get('ref_id')}  ${money(r.get('amount') or 0):,.2f}"
              f"  asked by {r.get('requested_by')}{spent}")
        print(f"      why: {r.get('reason')}")
        cash = r.get("cash_at_request_time") or {}
        if cash:
            print(f"      cash: {cash.get('total_balance')} on hand, "
                  f"{cash.get('uncommitted')} uncommitted, "
                  f"would leave {cash.get('would_leave_uncommitted')}")
        if r.get("status") == "rejected" and r.get("rejected_reason"):
            print(f"      rejected: {r['rejected_reason']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Approve or reject what the agents have asked for.")
    ap.add_argument("--list", action="store_true", help="show the board and exit")
    ap.add_argument("--id", type=int, help="approval request to decide")
    ap.add_argument("--by", help="your name -- recorded in payments.approved_by")
    ap.add_argument("--reject", action="store_true", help="reject instead of approve")
    ap.add_argument("--why", help="reason, when rejecting")
    args = ap.parse_args()

    if args.list or args.id is None:
        show(board.load_approvals())
        return 0

    if not (args.by or "").strip():
        ap.error("--by is required: an approval has to carry the name of the person giving it.")

    record = board.get_approval(args.id)
    if record.get("status") != "pending":
        print(f"Approval #{args.id} is already '{record['status']}'. Nothing to do.")
        return 1

    if args.reject:
        board.update_approval(
            args.id, status="rejected", approved_by=None,
            rejected_by=args.by, rejected_at=shop_today(), rejected_reason=args.why,
        )
        print(f"Rejected #{args.id} ({record['kind']} ref={record.get('ref_id')}).")
        return 0

    board.update_approval(args.id, status="approved", approved_by=args.by, approved_at=shop_today())
    print(f"Approved #{args.id}: {record['kind']} ref={record.get('ref_id')} "
          f"${money(record['amount']):,.2f}, by {args.by}.")
    print("The agent team can now act on it. Cash has not moved yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
