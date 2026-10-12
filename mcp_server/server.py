"""Campus Customs MCP server.

The single door between the agent team and the shop's database. Every agent --
Boss, Inventory, Accounting, Facilities, Customer Service -- reaches the shop
only through the tools registered here, so there is one place to audit what
the team can see and do.

This problem registers the three read tools the three open tickets need.
Payment, purchase-order and ticket-update tools arrive in later problems.

Two rules hold for every tool in this file:

* **The working copy only.** All reads hit `data/campus_customs_new.db`.
  `db.connect()` refuses the pristine seed outright.
* **No invented data.** A tool returns what the database says and nothing
  more. Where the schema simply does not record a fact -- which vendor makes
  which SKU, for instance -- the tool surfaces the raw fields and leaves the
  judgement to the agent rather than guessing on its behalf.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from mcp.server.fastmcp import FastMCP

from .db import ShopDataError, connect, days_between, shop_today

mcp = FastMCP("campus-customs")


@mcp.tool()
def check_stock_by_size(sku: str, size: str, requested_qty: int | None = None) -> dict[str, Any]:
    """Look up how many units of one SKU are on hand in one specific size.

    Stock in this shop is keyed by **(sku, size)**, so "do we have the Bulldog
    tee?" has no answer -- only "do we have it in S?" does. Pass
    `requested_qty` and the tool also reports the shortfall, which is the
    number that has to be restocked.

    Args:
        sku: e.g. "CC-TEE-WHITE".
        size: e.g. "S", "M", "L", "XL", or "OS" for one-size goods.
        requested_qty: units the ticket asks for. Optional.

    Returns the on-hand quantity and aisle for that exact size, the quantities
    for the SKU's other sizes (useful when a different size could be offered),
    and -- when `requested_qty` is given -- whether the order can be filled
    from stock and by how much it falls short.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()

        siblings = conn.execute(
            "SELECT size, qty FROM inventory WHERE sku = ? ORDER BY size",
            (sku,),
        ).fetchall()

    if not siblings:
        raise ShopDataError(f"No inventory rows exist for SKU {sku!r}.")

    if row is None:
        # The SKU is real but this size is not stocked at all -- a different
        # situation from a size that is stocked and sitting at zero.
        return {
            "sku": sku,
            "size": size,
            "size_is_stocked": False,
            "qty_on_hand": 0,
            "location": None,
            "other_sizes": {r["size"]: r["qty"] for r in siblings},
            "requested_qty": requested_qty,
            "can_fulfil_from_stock": False if requested_qty else None,
            "shortfall": requested_qty if requested_qty else None,
            "note": f"SKU {sku} has no row for size {size}; it is not carried in that size.",
        }

    on_hand = row["qty"]
    result: dict[str, Any] = {
        "sku": row["sku"],
        "product_name": row["name"],
        "size": row["size"],
        "size_is_stocked": True,
        "qty_on_hand": on_hand,
        "location": row["location"],
        "other_sizes": {r["size"]: r["qty"] for r in siblings},
        "requested_qty": requested_qty,
    }

    if requested_qty is not None:
        shortfall = max(0, requested_qty - on_hand)
        result["can_fulfil_from_stock"] = shortfall == 0
        result["shortfall"] = shortfall
        result["qty_available_now"] = min(on_hand, requested_qty)

    return result


@mcp.tool()
def find_restock_vendors(specialty_contains: str | None = None) -> dict[str, Any]:
    """List the vendors, with each one's lead time and whether it will ship.

    Use this once `check_stock_by_size` shows a shortfall, to find out who
    could make up the gap and when it would land.

    Two gates decide whether a vendor is usable, and both are read live:

    * **Unpaid invoices block shipping.** A vendor holding any invoice whose
      status is not `paid` ships nothing new until that bill is cleared, so
      `can_ship` is false and the blocking invoices are itemised.
    * **Lead time** comes from `vendors.lead_days`, never from assumption.
      `eta_if_ordered_today` is `desk.date_today + lead_days`.

    Args:
        specialty_contains: optional case-insensitive filter on the vendor's
            `specialty` text, e.g. "apparel".

    The database does not record which vendor supplies which SKU, so this tool
    does **not** guess at that mapping. It returns each vendor's `specialty`
    verbatim and leaves the match to the calling agent.
    """
    with connect() as conn:
        today = shop_today(conn)
        vendors = conn.execute(
            "SELECT id, name, specialty, lead_days FROM vendors ORDER BY id"
        ).fetchall()
        unpaid = conn.execute(
            "SELECT id, vendor_id, amount, due_date, status, description "
            "FROM invoices WHERE status != 'paid' ORDER BY due_date"
        ).fetchall()

    blocking: dict[int, list[dict[str, Any]]] = {}
    for inv in unpaid:
        due = dt.date.fromisoformat(inv["due_date"])
        overdue_by = days_between(due, today)
        blocking.setdefault(inv["vendor_id"], []).append(
            {
                "invoice_id": inv["id"],
                "amount": inv["amount"],
                "due_date": inv["due_date"],
                "status": inv["status"],
                "description": inv["description"],
                "days_overdue": overdue_by if overdue_by > 0 else 0,
                "is_overdue": overdue_by > 0,
            }
        )

    results = []
    for vendor in vendors:
        if specialty_contains and specialty_contains.lower() not in vendor["specialty"].lower():
            continue
        holds = blocking.get(vendor["id"], [])
        results.append(
            {
                "vendor_id": vendor["id"],
                "name": vendor["name"],
                "specialty": vendor["specialty"],
                "lead_days": vendor["lead_days"],
                "eta_if_ordered_today": (today + dt.timedelta(days=vendor["lead_days"])).isoformat(),
                "can_ship": not holds,
                "blocking_invoices": holds,
                "blocked_amount": round(sum(h["amount"] for h in holds), 2),
            }
        )

    return {
        "shop_date_today": today.isoformat(),
        "filter_specialty_contains": specialty_contains,
        "vendor_count": len(results),
        "vendors": results,
    }


@mcp.tool()
def check_rent_due(lease_id: int | None = None) -> dict[str, Any]:
    """Report what rent is owed on the shop's space, and how soon.

    Answers a rent notice with the lease's own figures rather than the ones
    quoted in the notice: the landlord, the monthly rent, the next due date,
    and how many days away that is measured from `desk.date_today`.

    Args:
        lease_id: a specific lease. Omit to get every lease the shop holds.

    `days_until_due` is negative once a lease is past due, and `is_overdue`
    says so outright. The amount returned here is what an approved payment
    would be for -- this tool only reports; it moves no money.
    """
    with connect() as conn:
        today = shop_today(conn)
        sql = "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases"
        params: tuple[Any, ...] = ()
        if lease_id is not None:
            sql += " WHERE id = ?"
            params = (lease_id,)
        leases = conn.execute(sql + " ORDER BY next_due", params).fetchall()

    if lease_id is not None and not leases:
        raise ShopDataError(f"No lease exists with id {lease_id}.")

    results = []
    for lease in leases:
        due = dt.date.fromisoformat(lease["next_due"])
        days = days_between(today, due)
        results.append(
            {
                "lease_id": lease["id"],
                "space_name": lease["space_name"],
                "landlord": lease["landlord"],
                "amount_due": lease["monthly_rent"],
                "next_due": lease["next_due"],
                "days_until_due": days,
                "is_overdue": days < 0,
                "notes": lease["notes"],
            }
        )

    return {
        "shop_date_today": today.isoformat(),
        "lease_count": len(results),
        "leases": results,
    }


if __name__ == "__main__":
    mcp.run()
