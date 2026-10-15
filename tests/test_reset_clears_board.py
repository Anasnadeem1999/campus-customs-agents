"""A reset must clear the approval board along with the database.

This is a regression test for a bug that produced wrong cash figures without
anything visibly failing. `reset_db.py` restored the database from the seed
but left `output/board/approvals.json` standing. The agents read both, so the
next run opened on a shop whose database said "no payments, $3,400 on hand"
and whose board said "rent already approved and paid". Ticket 102 was closed
as resolved on the strength of the board, and no rent payment was ever
written. The board showed three tickets done; the ledger showed the money
still sitting there.

The audit trail is checked to survive the same reset, because it is required
to append across runs rather than describe the shop's current state.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _run_reset() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/reset_db.py")],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_reset_empties_the_board(tmp_path: Path) -> None:
    board = REPO / "output/board"
    approvals, drafts = board / "approvals.json", board / "drafts.json"

    # Put something on the board that only makes sense against a spent-down
    # database: an approval already marked as having paid the rent.
    approvals.write_text(json.dumps([{
        "id": 1, "kind": "rent_payment", "ref_id": 1, "amount": 2400.0,
        "status": "approved", "approved_by": "test", "spent_on": "payment 1",
    }]), encoding="utf-8")
    drafts.write_text(json.dumps([{"id": 1, "ticket_id": 102, "body": "stale"}]),
                      encoding="utf-8")

    _run_reset()

    assert json.loads(approvals.read_text(encoding="utf-8")) == []
    assert json.loads(drafts.read_text(encoding="utf-8")) == []


def test_reset_leaves_the_audit_trail_alone() -> None:
    trail = REPO / "output/audit_trail.json"
    before = json.loads(trail.read_text(encoding="utf-8"))

    _run_reset()

    after = json.loads(trail.read_text(encoding="utf-8"))
    assert len(after["steps"]) == len(before["steps"])
    assert len(after["runs"]) == len(before["runs"])


def test_reset_restores_the_opening_cash_position() -> None:
    import sqlite3

    _run_reset()
    conn = sqlite3.connect(REPO / "data/campus_customs_new.db")
    balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()[0]
    payments = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    conn.close()

    # The board is empty and the ledger is untouched: the two agree that
    # nothing has been spent.
    assert balance == 3400.00
    assert payments == 0
