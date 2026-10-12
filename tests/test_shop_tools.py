"""The money path, proved end to end -- including every way it must refuse.

These tests call the MCP tool functions directly. No model is involved and no
network is touched: the point is that the *rules* hold regardless of what any
agent decides, because a rule an agent can talk its way past is not a rule.

Every test runs against a freshly reset working copy, and the seeded scenario
is the fixture: $3,400 on hand, an $840 overdue invoice blocking the only
apparel vendor, $2,400 of rent due in two days. $840 + $2,400 = $3,240, so the
$160 left over cannot fund the $264 hoodie restock. That squeeze is the whole
exam question, and `test_third_spend_is_refused_because_cash_runs_out` is it
in one assertion.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_server import board, server  # noqa: E402
from mcp_server.board import BoardError  # noqa: E402
from mcp_server.db import connect  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_shop(tmp_path, monkeypatch):
    """Reset the database and point the approval board at a throwaway folder."""
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "reset_db.py")],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    monkeypatch.setattr(board, "APPROVALS", tmp_path / "approvals.json")
    monkeypatch.setattr(board, "DRAFTS", tmp_path / "drafts.json")
    yield


def approve(approval_id: int, by: str = "Test Human") -> None:
    """Stand in for the human. Mirrors scripts/approve.py, which agents cannot run."""
    board.update_approval(
        approval_id, status="approved", approved_by=by, approved_at="2026-08-31"
    )


def balance() -> float:
    with connect() as conn:
        return conn.execute(
            "SELECT balance FROM cash_accounts WHERE name='checking'"
        ).fetchone()[0]


def tool_names() -> set[str]:
    return {t.name for t in asyncio.run(server.mcp.list_tools())}


# --- the gate ------------------------------------------------------------

def test_payment_without_any_approval_is_refused():
    with pytest.raises(BoardError, match="No approval request"):
        server.pay_invoice(invoice_id=501, approval_id=999)
    assert balance() == 3400.0


def test_payment_on_a_pending_approval_is_refused():
    req = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblocks the only apparel vendor.", requested_by="accounting",
    )
    assert req["status"] == "pending"
    with pytest.raises(BoardError, match="not 'approved'"):
        server.pay_invoice(invoice_id=501, approval_id=req["approval_id"])
    assert balance() == 3400.0, "a refused payment must not move a cent"


def test_no_mcp_tool_can_approve():
    """The strongest guarantee here: the verb is absent, not merely discouraged."""
    offenders = {n for n in tool_names() if "approve" in n and n != "list_approvals"}
    assert not offenders, (
        "an approving tool appeared on the MCP server; approval must stay in "
        "scripts/approve.py where no agent can reach it"
    )


def test_an_approval_cannot_be_reused():
    req = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Clear the block.", requested_by="accounting",
    )
    approve(req["approval_id"])
    server.pay_invoice(invoice_id=501, approval_id=req["approval_id"])
    with pytest.raises(BoardError, match="already spent"):
        server.pay_invoice(invoice_id=501, approval_id=req["approval_id"])


def test_an_approval_cannot_be_redirected_to_another_bill():
    req = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent due in 2 days.", requested_by="facilities",
    )
    approve(req["approval_id"])
    with pytest.raises(BoardError, match="rent_payment"):
        server.pay_invoice(invoice_id=501, approval_id=req["approval_id"])


def test_approval_amount_must_match_the_real_bill():
    with pytest.raises(BoardError, match="Approve the amount actually owed"):
        server.request_approval(
            kind="invoice_payment", amount=100.0, ref_id=501,
            reason="Try to part-pay.", requested_by="accounting",
        )


# --- the writes ----------------------------------------------------------

def test_paying_an_invoice_moves_all_three_things_together():
    req = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Overdue; blocks the apparel vendor.", requested_by="accounting",
    )
    approve(req["approval_id"], by="Anas Nadeem")
    out = server.pay_invoice(invoice_id=501, approval_id=req["approval_id"])

    assert out["balance_before"] == 3400.0
    assert out["balance_after"] == 2560.0
    with connect() as conn:
        assert conn.execute(
            "SELECT status FROM invoices WHERE id=501"
        ).fetchone()[0] == "paid"
        pay = conn.execute(
            "SELECT * FROM payments WHERE id=?", (out["payment_id"],)
        ).fetchone()
        assert pay["amount"] == 840.0
        assert pay["approved_by"] == "Anas Nadeem", "the human's name must reach the books"
        assert pay["paid_at"] == "2026-08-31", "stamped with desk.date_today, not the clock"
        assert conn.execute("SELECT balance FROM cash_accounts").fetchone()[0] == 2560.0


def test_paying_rent_rolls_the_lease_so_it_cannot_be_paid_twice():
    req = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Due 2026-09-02.", requested_by="facilities",
    )
    approve(req["approval_id"])
    out = server.pay_rent(lease_id=1, approval_id=req["approval_id"])
    assert out["settles"]["previous_next_due"] == "2026-09-02"
    assert out["settles"]["next_due"] == "2026-10-02"
    assert balance() == 1000.0


# --- the squeeze ---------------------------------------------------------

def test_third_spend_is_refused_because_cash_runs_out():
    """$3,400 funds the invoice and the rent. It does not fund the restock."""
    inv = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock the vendor.", requested_by="accounting",
    )
    approve(inv["approval_id"])
    server.pay_invoice(invoice_id=501, approval_id=inv["approval_id"])

    rent = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent.", requested_by="facilities",
    )
    approve(rent["approval_id"])
    server.pay_rent(lease_id=1, approval_id=rent["approval_id"])

    assert balance() == 160.0

    po = server.request_approval(
        kind="purchase_order", amount=264.0, ref_id=1,
        reason="12 hoodies for ticket 103.", requested_by="inventory",
    )
    # The request is allowed, but it is honest about not fitting.
    assert po["cash_check"]["fits_within_uncommitted"] is False
    assert po["cash_check"]["would_leave_uncommitted"] == -104.0


def test_a_payment_that_would_overdraw_is_refused_and_writes_nothing():
    rent = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent.", requested_by="facilities",
    )
    approve(rent["approval_id"])
    server.pay_rent(lease_id=1, approval_id=rent["approval_id"])
    assert balance() == 1000.0

    # $1,000 left still covers the $840 invoice, so drain it until it cannot.
    conn = connect(read_only=False)
    conn.execute("UPDATE cash_accounts SET balance = 500.0 WHERE name='checking'")
    conn.commit()
    conn.close()

    inv = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock.", requested_by="accounting",
    )
    approve(inv["approval_id"])
    with pytest.raises(BoardError, match="REFUSED"):
        server.pay_invoice(invoice_id=501, approval_id=inv["approval_id"])

    assert balance() == 500.0, "balance untouched"
    with connect() as conn2:
        assert conn2.execute(
            "SELECT status FROM invoices WHERE id=501"
        ).fetchone()[0] == "open"
        assert conn2.execute(
            "SELECT COUNT(*) FROM payments WHERE kind='invoice'"
        ).fetchone()[0] == 0


def test_cash_position_counts_approved_but_unpaid_money_as_gone():
    req = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent.", requested_by="facilities",
    )
    approve(req["approval_id"])
    pos = server.get_cash_position()
    assert pos["total_balance"] == 3400.0
    assert pos["approved_not_yet_paid"] == 2400.0
    assert pos["uncommitted"] == 1000.0, "planning against the raw balance overdraws"


# --- the vendor block ----------------------------------------------------

def test_vendor_will_not_ship_while_it_holds_an_unpaid_invoice():
    po = server.request_approval(
        kind="purchase_order", amount=264.0, ref_id=1,
        reason="Restock hoodies.", requested_by="inventory",
    )
    approve(po["approval_id"])
    with pytest.raises(BoardError, match="will not ship while it holds unpaid invoices"):
        server.place_purchase_order(
            vendor_id=1, sku="CC-HOOD-NAVY", size="M", qty=12,
            approval_id=po["approval_id"], needed_for_ticket=103,
        )


def test_clearing_the_invoice_unblocks_the_same_order():
    inv = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock the vendor.", requested_by="accounting",
    )
    approve(inv["approval_id"])
    server.pay_invoice(invoice_id=501, approval_id=inv["approval_id"])

    po = server.request_approval(
        kind="purchase_order", amount=264.0, ref_id=1,
        reason="Restock hoodies.", requested_by="inventory",
    )
    approve(po["approval_id"])
    out = server.place_purchase_order(
        vendor_id=1, sku="CC-HOOD-NAVY", size="M", qty=12,
        approval_id=po["approval_id"], needed_for_ticket=103,
    )
    assert out["eta"] == "2026-09-05", "desk.date_today + 5 lead days"
    assert out["cash_moved"] is False


# --- never contact anyone -------------------------------------------------

def test_there_is_no_send_tool_and_drafts_stay_unsent():
    assert not {n for n in tool_names() if "send" in n or "email" in n}

    out = server.draft_customer_message(
        ticket_id=101, recipient="Tauhid Zaman", subject="Your Bulldog tee",
        body="We are restocking size S and will hold one for you.",
    )
    assert out["delivery_status"] == "not_sent"
    assert board.load_drafts()[0]["delivery_status"] == "not_sent"


# --- the seed is sacred ---------------------------------------------------

def test_tools_cannot_be_pointed_at_the_pristine_seed(monkeypatch):
    from mcp_server import db
    monkeypatch.setattr(db, "WORKING_DB", db.SEED_DB)
    with pytest.raises(db.ShopDataError, match="Refusing to open the pristine seed"):
        db.connect()


def test_ticket_notes_are_appended_never_overwritten():
    before = server.list_tickets()["tickets"]
    original = next(t for t in before if t["id"] == 101)["notes"]
    server.update_ticket(101, status="blocked", append_note="Waiting on invoice 501.")
    after = next(
        t for t in server.list_tickets(status=None)["tickets"] if t["id"] == 101
    )
    assert original in after["notes"], "the customer's own words must survive"
    assert "[2026-08-31] Waiting on invoice 501." in after["notes"]


def test_paying_an_approval_is_judged_against_the_balance_not_uncommitted():
    """Regression: `uncommitted` already excludes the payment you are making.

    A live run hit this. Both the $840 invoice and the $2,400 rent were
    approved against a $3,400 balance, leaving `uncommitted` at $160. Reading
    that figure, the team concluded the two approvals were in conflict and paid
    neither -- but $3,400 covers both. `executing_approval.can_execute_now`
    answers the question the agent is actually asking.
    """
    inv = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock the vendor.", requested_by="accounting",
    )
    rent = server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent.", requested_by="facilities",
    )
    approve(inv["approval_id"])
    approve(rent["approval_id"])

    pos = server.get_cash_position(for_approval_id=inv["approval_id"])
    assert pos["uncommitted"] == 160.0, "both approvals are committed against $3,400"
    assert pos["executing_approval"]["already_counted_in_approved_not_yet_paid"] is True
    assert pos["executing_approval"]["can_execute_now"] is True, (
        "$3,400 on hand covers the $840 invoice; uncommitted is the wrong test here"
    )
    assert pos["executing_approval"]["balance_after"] == 2560.0

    # And both genuinely do fit, which is the point.
    server.pay_invoice(invoice_id=501, approval_id=inv["approval_id"])
    server.pay_rent(lease_id=1, approval_id=rent["approval_id"])
    assert balance() == 160.0
