"""Receiving stock, advancing the clock, and the no-duplicates rule.

These cover shop rules 2, 7 and 8 -- the distinction between an order placed
and an order arrived, which is the thing the owner's rule 7 turns on.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_server import board, server  # noqa: E402
from mcp_server.board import BoardError  # noqa: E402
from mcp_server.db import ShopDataError, connect  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_shop(tmp_path, monkeypatch):
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "reset_db.py")],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    monkeypatch.setattr(board, "APPROVALS", tmp_path / "approvals.json")
    monkeypatch.setattr(board, "DRAFTS", tmp_path / "drafts.json")
    yield


def approve(approval_id: int, by: str = "Test Human") -> None:
    board.update_approval(
        approval_id, status="approved", approved_by=by, approved_at="2026-08-31"
    )


def stock(sku: str = "CC-TEE-WHITE", size: str = "S") -> int:
    with connect() as conn:
        return conn.execute(
            "SELECT qty FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()[0]


def place_the_tee_order() -> int:
    """Clear invoice 501, then order the one size-S tee. Returns the PO id."""
    inv = server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock the vendor.", requested_by="accounting",
    )
    approve(inv["approval_id"])
    server.pay_invoice(invoice_id=501, approval_id=inv["approval_id"])

    po = server.request_approval(
        kind="purchase_order", amount=8.0, ref_id=1,
        reason="One size-S tee for ticket 101.", requested_by="accounting",
    )
    approve(po["approval_id"])
    out = server.place_purchase_order(
        vendor_id=1, sku="CC-TEE-WHITE", size="S", qty=1,
        approval_id=po["approval_id"], needed_for_ticket=101,
    )
    return out["purchase_order_id"]


# --- rule 7: ordered is not arrived --------------------------------------

def test_placing_an_order_does_not_move_stock():
    """The whole point of rule 7, in one assertion."""
    assert stock() == 0
    place_the_tee_order()
    assert stock() == 0, "an order placed must not put anything on the shelf"


def test_stock_cannot_be_received_before_the_vendors_eta():
    po = place_the_tee_order()
    with pytest.raises(ShopDataError, match="not due until 2026-09-05"):
        server.receive_purchase_order(purchase_order_id=po)
    assert stock() == 0


def test_receiving_after_the_eta_puts_the_goods_on_the_shelf():
    po = place_the_tee_order()
    server.advance_shop_date(to_date="2026-09-05")

    out = server.receive_purchase_order(purchase_order_id=po)
    assert out["qty_before"] == 0 and out["qty_after"] == 1
    assert stock() == 1, "this is what lets ticket 101 honestly resolve"
    assert out["cash_moved"] is False, "receiving creates a debt, it does not spend"

    # The vendor is now owed for the goods, on a real invoice.
    with connect() as conn:
        bill = conn.execute(
            "SELECT amount, status, vendor_id FROM invoices WHERE id = ?",
            (out["vendor_invoice_id"],),
        ).fetchone()
    assert bill["amount"] == 8.0, "1 unit at pricing.unit_cost of $8.00"
    assert bill["status"] == "open" and bill["vendor_id"] == 1


def test_an_order_cannot_be_received_twice():
    po = place_the_tee_order()
    server.advance_shop_date(to_date="2026-09-05")
    server.receive_purchase_order(purchase_order_id=po)
    with pytest.raises(BoardError, match="already received"):
        server.receive_purchase_order(purchase_order_id=po)
    assert stock() == 1, "receiving twice would invent stock"


# --- the clock ------------------------------------------------------------

def test_the_shop_clock_only_moves_forward():
    with pytest.raises(ShopDataError, match="only moves forward"):
        server.advance_shop_date(to_date="2026-08-30")
    with pytest.raises(ShopDataError, match="only moves forward"):
        server.advance_shop_date(to_date="2026-08-31")


def test_advancing_the_clock_changes_what_is_overdue():
    """Rule 3: overdue is measured from desk.date_today, so moving it matters."""
    before = server.check_rent_due(lease_id=1)["leases"][0]
    assert before["days_until_due"] == 2 and before["is_overdue"] is False

    server.advance_shop_date(to_date="2026-09-05")
    after = server.check_rent_due(lease_id=1)["leases"][0]
    assert after["is_overdue"] is True, "rent due 2026-09-02 is late on 2026-09-05"


# --- rule 8: no duplicate orders -----------------------------------------

def test_the_same_restock_cannot_be_ordered_twice():
    place_the_tee_order()

    again = server.request_approval(
        kind="purchase_order", amount=8.0, ref_id=1,
        reason="Another tee.", requested_by="inventory",
    )
    approve(again["approval_id"])
    with pytest.raises(BoardError, match="already placed"):
        server.place_purchase_order(
            vendor_id=1, sku="CC-TEE-WHITE", size="S", qty=1,
            approval_id=again["approval_id"], needed_for_ticket=101,
        )


def test_receiving_creates_a_debt_that_blocks_the_vendor_until_it_is_paid():
    """Rules 2 and 8 compose, and the result is worth stating.

    Receiving goods bills the shop. That new invoice blocks the same vendor
    from shipping anything else until it is settled -- so a shop that keeps
    ordering without paying grinds itself to a halt. Clearing the bill frees
    the vendor again.
    """
    po = place_the_tee_order()
    server.advance_shop_date(to_date="2026-09-05")
    received = server.receive_purchase_order(purchase_order_id=po)
    new_invoice = received["vendor_invoice_id"]

    nxt = server.request_approval(
        kind="purchase_order", amount=8.0, ref_id=1,
        reason="Restock again.", requested_by="inventory",
    )
    approve(nxt["approval_id"])
    with pytest.raises(BoardError, match="will not ship while it holds unpaid invoices"):
        server.place_purchase_order(
            vendor_id=1, sku="CC-TEE-WHITE", size="S", qty=1,
            approval_id=nxt["approval_id"], needed_for_ticket=101,
        )

    # Settle the new bill and the same order goes through.
    pay = server.request_approval(
        kind="invoice_payment", amount=8.0, ref_id=new_invoice,
        reason="Clear the restock bill.", requested_by="accounting",
    )
    approve(pay["approval_id"])
    server.pay_invoice(invoice_id=new_invoice, approval_id=pay["approval_id"])

    out = server.place_purchase_order(
        vendor_id=1, sku="CC-TEE-WHITE", size="S", qty=1,
        approval_id=nxt["approval_id"], needed_for_ticket=101,
    )
    assert out["purchase_order_id"]
