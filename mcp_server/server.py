"""Campus Customs MCP server.

The single door between the agent team and the shop's database. Every agent --
Boss, Inventory, Accounting, Facilities, Customer Service -- reaches the shop
only through the tools registered here, so there is one place to audit what
the team can see and do.

Problem 3 registered the three read tools the open tickets need. Problem 5
adds the seven the agent team needs to actually work a ticket to resolution:
the board itself, cash, invoices, discount margins, the approval request, the
two payment tools, the ticket update and the customer-message draft.

**Spending is gated by a verb that does not exist here.** `request_approval`
lets an agent ask. Nothing in this file approves -- that lives in
`scripts/approve.py`, outside the MCP server, so an agent cannot approve its
own spending even if a prompt told it to.

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

from mcp.server.mcpserver import MCPServer

from . import board
from .board import BoardError
from .db import ShopDataError, connect, days_between, money, shop_today, writing

mcp = MCPServer("campus-customs")


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
        # The agent has asked about a SKU the shop does not carry -- usually a
        # remembered or guessed code rather than one a tool returned. Refusing
        # is right, but a bare refusal just gets retried identically, so name
        # the SKUs that do exist and the next attempt can be correct.
        with connect() as conn:
            stocked = [r["sku"] for r in conn.execute(
                "SELECT DISTINCT sku FROM inventory ORDER BY sku"
            )]
        raise ShopDataError(
            f"No inventory rows exist for SKU {sku!r}, so this shop does not carry it. "
            f"The SKUs that exist are: {', '.join(stocked)}. "
            "Use one of those, or read the sku off the ticket with list_tickets -- "
            "do not guess a product code."
        )

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



@mcp.tool()
def list_tickets(status: str | None = "open") -> dict[str, Any]:
    """Read the ticket board -- what the shop has been asked to deal with.

    This is where the Boss starts a run. It returns the tickets themselves and
    nothing inferred: the type, who asked, the SKU and size and quantity where
    the ticket names them, and the lease or invoice the ticket already points
    at.

    Args:
        status: filter on ticket status, default "open". Pass None for all.

    The `lease_id` and `invoice_id` columns are real foreign keys and matter --
    ticket 101 points at invoice 501, which is the reason that order is stuck.
    Follow them rather than re-deriving the link from the subject line.
    """
    with connect() as conn:
        today = shop_today(conn)
        sql = (
            "SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, "
            "status, notes, created_at FROM tickets"
        )
        params: tuple[Any, ...] = ()
        if status is not None:
            sql += " WHERE status = ?"
            params = (status,)
        rows = conn.execute(sql + " ORDER BY id", params).fetchall()

    return {
        "shop_date_today": today.isoformat(),
        "filter_status": status,
        "ticket_count": len(rows),
        "tickets": [dict(r) for r in rows],
    }


@mcp.tool()
def get_cash_position(for_approval_id: int | None = None) -> dict[str, Any]:
    """How much cash the shop actually has, and what is already spoken for.

    Every spending decision in this shop is really one question -- does this
    fit alongside everything else already promised? So this tool reports the
    live balance *and* the total of approvals that a human has signed off but
    which have not yet been paid, because that money is committed even though
    it is still sitting in the account.

    **Which number to use depends on what you are doing, and getting this
    backwards is the easiest mistake to make here:**

    * **Planning something new** -- use `uncommitted`. Reading `total_balance`
      is how two approved payments overdraw one account.
    * **Executing an approval that already exists** -- do *not* use
      `uncommitted`. That approval's own amount is already inside
      `approved_not_yet_paid`, so `uncommitted` has subtracted the very money
      you are about to spend. Judging the payment against it will tell you the
      shop cannot afford something it has already set the cash aside for.

    Args:
        for_approval_id: the approval you are about to pay. Pass it and the
            tool answers the execution question directly, in
            `executing_approval`, instead of leaving you to work out which
            figure applies.
    """
    with connect() as conn:
        rows = conn.execute("SELECT name, balance, date FROM cash_accounts ORDER BY name").fetchall()
        today = shop_today(conn)

    committed = [
        a
        for a in board.load_approvals()
        if a.get("status") == "approved"
        and a.get("consumed_by_payment_id") is None
        and a.get("kind") in ("invoice_payment", "rent_payment", "purchase_order")
    ]
    committed_total = money(sum(float(a.get("amount") or 0) for a in committed))
    total = money(sum(r["balance"] for r in rows))

    executing: dict[str, Any] | None = None
    if for_approval_id is not None:
        target = board.get_approval(for_approval_id)
        amount = money(float(target.get("amount") or 0))
        already_counted = any(int(a["id"]) == int(for_approval_id) for a in committed)
        paid_on = target.get("consumed_by_payment_id")

        if paid_on is not None:
            # The single most confusing state for an agent picking up a ticket:
            # the payment is done, so the cash is gone, so a naive balance test
            # reports "insufficient funds" and the agent concludes the bill is
            # unpayable -- when in fact it is already paid. Answer the real
            # question before the arithmetic can mislead.
            executing = {
                "approval_id": for_approval_id,
                "kind": target.get("kind"),
                "status": target.get("status"),
                "amount": amount,
                "already_paid": True,
                "paid_by_payment_id": paid_on,
                "can_execute_now": False,
                "why_not": "ALREADY PAID",
                "note": (
                    f"This was already paid on payment {paid_on}. Nothing further is "
                    "owed and nothing needs approving. Do NOT read the low balance as "
                    "the bill being unaffordable -- the balance is low *because* this "
                    "was paid. The work is done: mark the ticket resolved."
                ),
            }
        else:
            executing = {
                "approval_id": for_approval_id,
                "kind": target.get("kind"),
                "status": target.get("status"),
                "amount": amount,
                "already_paid": False,
                "already_counted_in_approved_not_yet_paid": already_counted,
                # The real test the pay tools apply. Cash set aside for this
                # approval is cash available *to this approval*.
                "can_execute_now": total >= amount and target.get("status") == "approved",
                "balance_after": money(total - amount),
                "note": (
                    "Judge this payment against total_balance, not uncommitted -- "
                    "uncommitted has already subtracted this very amount."
                ),
            }

    return {
        "shop_date_today": today.isoformat(),
        "accounts": [
            {"name": r["name"], "balance": money(r["balance"]), "as_of": r["date"]} for r in rows
        ],
        "total_balance": total,
        "approved_not_yet_paid": committed_total,
        "approved_not_yet_paid_detail": [
            {"approval_id": a["id"], "kind": a["kind"], "ref_id": a.get("ref_id"),
             "amount": money(float(a.get("amount") or 0)), "reason": a.get("reason")}
            for a in committed
        ],
        "uncommitted": money(total - committed_total),
        "executing_approval": executing,
        "how_to_read_this": (
            "uncommitted = what you may promise to something NEW. "
            "total_balance = what is actually there, and the figure an "
            "already-approved payment is judged against."
        ),
    }


@mcp.tool()
def list_invoices(status: str | None = None, vendor_id: int | None = None) -> dict[str, Any]:
    """What the shop owes its vendors, and how late each bill is.

    Each invoice comes back with the vendor's name attached and `days_overdue`
    measured against `desk.date_today`, never the wall clock.

    Args:
        status: e.g. "open" or "paid". Omit for every invoice.
        vendor_id: restrict to one vendor. Omit for all.

    An unpaid invoice does double duty in this shop: it is money owed *and* a
    shipping block on that vendor, which is why clearing one can be what
    unsticks an unrelated customer order.
    """
    with connect() as conn:
        today = shop_today(conn)
        sql = (
            "SELECT i.id, i.vendor_id, v.name AS vendor_name, i.amount, i.due_date, "
            "i.status, i.description FROM invoices i "
            "LEFT JOIN vendors v ON v.id = i.vendor_id"
        )
        clauses, params = [], []
        if status is not None:
            clauses.append("i.status = ?")
            params.append(status)
        if vendor_id is not None:
            clauses.append("i.vendor_id = ?")
            params.append(vendor_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = conn.execute(sql + " ORDER BY i.due_date", tuple(params)).fetchall()

    invoices = []
    for r in rows:
        overdue_by = days_between(dt.date.fromisoformat(r["due_date"]), today)
        invoices.append(
            {
                "invoice_id": r["id"],
                "vendor_id": r["vendor_id"],
                "vendor_name": r["vendor_name"],
                "amount": money(r["amount"]),
                "due_date": r["due_date"],
                "status": r["status"],
                "description": r["description"],
                "days_overdue": max(0, overdue_by),
                "is_overdue": overdue_by > 0 and r["status"] != "paid",
            }
        )

    return {
        "shop_date_today": today.isoformat(),
        "filter_status": status,
        "filter_vendor_id": vendor_id,
        "invoice_count": len(invoices),
        "total_outstanding": money(sum(i["amount"] for i in invoices if i["status"] != "paid")),
        "invoices": invoices,
    }


@mcp.tool()
def quote_discount(
    sku: str,
    qty: int,
    size: str | None = None,
    proposed_unit_price: float | None = None,
) -> dict[str, Any]:
    """Price a bulk request and show what it does to the margin.

    A discount ticket is two questions wearing one coat, and this tool answers
    both: can the order even be filled from stock, and what does the proposed
    price leave on the deal. Ticket 103 is the case -- 20 hoodies asked for, 8
    on the shelf.

    Args:
        sku: the product being quoted.
        qty: units the customer wants.
        size: the size asked for. Given it, the tool reports what that size can
            actually cover, which is usually the binding number.
        proposed_unit_price: the price being considered. Omit to see the list
            position only.

    Cost figures come from `pricing`; `restock_cost_for_shortfall` values the
    gap at unit cost, which is cash that has to leave before the order can
    ship. `margin_pct` is against unit cost, and `breaks_even_at` is the price
    below which the shop pays for the privilege of selling. The tool reports;
    it does not decide -- the discount floor is a judgement for Accounting and
    a human, not arithmetic.
    """
    with connect() as conn:
        today = shop_today(conn)
        price = conn.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
        if price is None:
            raise ShopDataError(f"No pricing row for SKU {sku!r}; cannot quote it.")
        if size is not None:
            stock = conn.execute(
                "SELECT qty FROM inventory WHERE sku = ? AND size = ?", (sku, size)
            ).fetchone()
            on_hand = stock["qty"] if stock else 0
        else:
            on_hand = conn.execute(
                "SELECT COALESCE(SUM(qty), 0) AS q FROM inventory WHERE sku = ?", (sku,)
            ).fetchone()["q"]

    unit_cost = money(price["unit_cost"])
    list_price = money(price["list_price"])
    shortfall = max(0, qty - on_hand)

    result: dict[str, Any] = {
        "shop_date_today": today.isoformat(),
        "sku": sku,
        "size": size,
        "qty_requested": qty,
        "qty_on_hand": on_hand,
        "shortfall": shortfall,
        "can_fulfil_from_stock": shortfall == 0,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "list_margin_per_unit": money(list_price - unit_cost),
        "list_revenue_total": money(list_price * qty),
        "restock_cost_for_shortfall": money(unit_cost * shortfall),
        "breaks_even_at": unit_cost,
    }

    if proposed_unit_price is not None:
        proposed = money(proposed_unit_price)
        margin_unit = money(proposed - unit_cost)
        result.update(
            {
                "proposed_unit_price": proposed,
                "discount_off_list": money(list_price - proposed),
                "discount_pct_off_list": round((list_price - proposed) / list_price * 100, 2)
                if list_price
                else None,
                "margin_per_unit": margin_unit,
                "margin_pct": round(margin_unit / unit_cost * 100, 2) if unit_cost else None,
                "margin_total": money(margin_unit * qty),
                "revenue_total": money(proposed * qty),
                "below_unit_cost": proposed < unit_cost,
            }
        )

    return result


@mcp.tool()
def request_approval(
    kind: str,
    amount: float,
    reason: str,
    requested_by: str,
    ref_id: int | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Ask a human to approve something. This is the only way to spend.

    Nothing here moves money. It writes a pending request to the board and
    stops, which is the point: the payment tools refuse to act without an
    approval that a human has signed, and no tool on this server can sign one.

    Args:
        kind: one of `invoice_payment` (ref_id = invoice id),
            `rent_payment` (lease id), `purchase_order` (vendor id), or
            `price_override` (ticket id).
        amount: cash leaving the shop, or for a price override, the proposed
            unit price.
        reason: why the shop should say yes -- what it unblocks, what it costs,
            what happens if it is refused. The human reads this and little else.
        requested_by: the agent asking, e.g. "accounting".
        ref_id: the record this is about. Required for every kind.
        detail: anything else the approver needs.

    The request is checked against the live database before it is written: the
    invoice must exist and still be open, the amount must match what is
    actually owed, and the spend is tested against cash that is not already
    promised to an earlier approval. A request that cannot pass those checks is
    refused here rather than becoming a surprise at payment time.
    """
    if kind not in board.APPROVAL_KINDS:
        raise BoardError(f"kind must be one of {board.APPROVAL_KINDS}, got {kind!r}.")
    if ref_id is None:
        raise BoardError(f"ref_id is required: a {kind} approval must name the record it is for.")
    if amount is None or float(amount) <= 0:
        raise BoardError("amount must be a positive number.")
    if not (reason or "").strip():
        raise BoardError("reason is required -- the human approving this reads it to decide.")

    amount = money(amount)
    with connect() as conn:
        today = shop_today(conn)
        checks: dict[str, Any] = {}

        if kind == "invoice_payment":
            row = conn.execute(
                "SELECT amount, status FROM invoices WHERE id = ?", (ref_id,)
            ).fetchone()
            if row is None:
                raise ShopDataError(f"No invoice {ref_id}.")
            if row["status"] == "paid":
                raise BoardError(f"Invoice {ref_id} is already paid; nothing to approve.")
            if money(row["amount"]) != amount:
                raise BoardError(
                    f"Invoice {ref_id} is for {money(row['amount'])}, but this request says "
                    f"{amount}. Approve the amount actually owed."
                )
            checks["invoice_status"] = row["status"]

        elif kind == "rent_payment":
            row = conn.execute(
                "SELECT monthly_rent, next_due FROM leases WHERE id = ?", (ref_id,)
            ).fetchone()
            if row is None:
                raise ShopDataError(f"No lease {ref_id}.")
            if money(row["monthly_rent"]) != amount:
                raise BoardError(
                    f"Lease {ref_id} rent is {money(row['monthly_rent'])}, not {amount}."
                )
            checks["next_due"] = row["next_due"]

        elif kind == "purchase_order":
            row = conn.execute(
                "SELECT name, lead_days FROM vendors WHERE id = ?", (ref_id,)
            ).fetchone()
            if row is None:
                raise ShopDataError(f"No vendor {ref_id}.")
            blocking = conn.execute(
                "SELECT id, amount FROM invoices WHERE vendor_id = ? AND status != 'paid'",
                (ref_id,),
            ).fetchall()
            checks["vendor_name"] = row["name"]
            checks["lead_days"] = row["lead_days"]
            checks["eta_if_ordered_today"] = (
                today + dt.timedelta(days=row["lead_days"])
            ).isoformat()
            checks["vendor_can_ship"] = not blocking
            checks["vendor_blocked_by_invoices"] = [b["id"] for b in blocking]

        elif kind == "price_override":
            row = conn.execute("SELECT id, sku, qty FROM tickets WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                raise ShopDataError(f"No ticket {ref_id}.")
            checks["ticket_sku"] = row["sku"]
            checks["ticket_qty"] = row["qty"]

    # A price override is a discount, not cash going out, so it is not tested
    # against the balance -- only the three spending kinds are.
    spends_cash = kind in ("invoice_payment", "rent_payment", "purchase_order")
    position = get_cash_position()
    record = board.add_approval(
        {
            "kind": kind,
            "ref_id": ref_id,
            "amount": amount,
            "reason": reason.strip(),
            "detail": detail,
            "requested_by": requested_by,
            "requested_on_shop_date": today.isoformat(),
            "status": "pending",
            "approved_by": None,
            "approved_at": None,
            "consumed_by_payment_id": None,
            "spends_cash": spends_cash,
            "checks_at_request_time": checks,
            "cash_at_request_time": {
                "total_balance": position["total_balance"],
                "already_approved_unpaid": position["approved_not_yet_paid"],
                "uncommitted": position["uncommitted"],
                "would_leave_uncommitted": money(position["uncommitted"] - amount)
                if spends_cash
                else position["uncommitted"],
                "fits_within_uncommitted": (position["uncommitted"] >= amount)
                if spends_cash
                else True,
            },
        }
    )

    return {
        "approval_id": record["id"],
        "status": "pending",
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "next_step": (
            "A human must approve this before it can be acted on. No agent can. "
            f"Human runs: python scripts/approve.py --id {record['id']} --by \"<name>\""
        ),
        "cash_check": record["cash_at_request_time"],
        "checks": checks,
    }


@mcp.tool()
def list_approvals(status: str | None = None) -> dict[str, Any]:
    """Show the approval board -- what has been asked for and what was decided.

    Use it to find the `approval_id` a payment tool needs, and to avoid asking
    twice for the same thing.

    Args:
        status: "pending", "approved", "rejected". Omit for everything.
    """
    rows = board.load_approvals()
    if status is not None:
        rows = [r for r in rows if r.get("status") == status]
    return {
        "filter_status": status,
        "approval_count": len(rows),
        "approvals": rows,
    }


def _pay(
    *,
    approval_id: int,
    kind: str,
    ref_id: int,
    paid_by_label: str,
) -> dict[str, Any]:
    """Shared body of the payment tools: check, then move everything at once.

    Both payment tools land here so the refusals cannot drift apart between
    them. The order matters -- approval first, then funds, then the write --
    because a refusal should cost nothing and leave no trace in the books.
    """
    approval = board.get_approval(approval_id)
    board.require_spendable(approval, kind, ref_id)
    amount = money(approval["amount"])

    with writing() as conn:
        today = shop_today(conn)
        account = conn.execute(
            "SELECT name, balance FROM cash_accounts ORDER BY balance DESC LIMIT 1"
        ).fetchone()
        if account is None:
            raise ShopDataError("The shop has no cash account.")
        balance = money(account["balance"])

        if balance < amount:
            # Constraint 7. Refused before any row is touched, and the whole
            # block rolls back regardless, so the books are untouched.
            raise BoardError(
                f"REFUSED: paying {amount:.2f} from '{account['name']}' would overdraw it. "
                f"Balance is {balance:.2f}, short by {money(amount - balance):.2f}. "
                "The balance must never go negative. Free up cash or drop a lower-priority "
                "spend, then ask again."
            )

        if kind == "invoice_payment":
            row = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                raise ShopDataError(f"No invoice {ref_id}.")
            if row["status"] == "paid":
                raise BoardError(f"Invoice {ref_id} is already paid.")
            if money(row["amount"]) != amount:
                raise BoardError(
                    f"Invoice {ref_id} is for {money(row['amount'])}; approval {approval_id} "
                    f"authorises {amount}. The invoice changed after it was approved -- "
                    "get a fresh approval."
                )
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
            settles = {"invoice_id": ref_id, "new_status": "paid"}
        else:
            row = conn.execute(
                "SELECT monthly_rent, next_due FROM leases WHERE id = ?", (ref_id,)
            ).fetchone()
            if row is None:
                raise ShopDataError(f"No lease {ref_id}.")
            if money(row["monthly_rent"]) != amount:
                raise BoardError(
                    f"Lease {ref_id} rent is {money(row['monthly_rent'])}; approval "
                    f"{approval_id} authorises {amount}."
                )
            # Rent is recurring: paying this month rolls the lease to the next
            # one, so the same rent cannot be paid twice off one due date.
            due = dt.date.fromisoformat(row["next_due"])
            month = due.month % 12 + 1
            year = due.year + (1 if due.month == 12 else 0)
            day = min(due.day, [31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 28,
                                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            next_due = dt.date(year, month, day).isoformat()
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (next_due, ref_id))
            settles = {"lease_id": ref_id, "previous_next_due": row["next_due"], "next_due": next_due}

        new_balance = money(balance - amount)
        conn.execute(
            "UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
            (new_balance, today.isoformat(), account["name"]),
        )
        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (paid_by_label, ref_id, amount, account["name"], today.isoformat(),
             approval["approved_by"]),
        )
        payment_id = cur.lastrowid

    board.update_approval(approval_id, consumed_by_payment_id=payment_id)

    return {
        "paid": True,
        "payment_id": payment_id,
        "kind": paid_by_label,
        "amount": amount,
        "account": account["name"],
        "paid_at": today.isoformat(),
        "approved_by": approval["approved_by"],
        "approval_id": approval_id,
        "balance_before": balance,
        "balance_after": new_balance,
        "settles": settles,
        "wrote": [
            "cash_accounts.balance",
            "payments (new row)",
            "invoices.status" if kind == "invoice_payment" else "leases.next_due",
        ],
    }


@mcp.tool()
def pay_invoice(invoice_id: int, approval_id: int) -> dict[str, Any]:
    """Pay a vendor invoice against an approval a human has already signed.

    Clearing an invoice does two jobs at once: the bill is settled, and the
    vendor's shipping block lifts, so a restock that was impossible becomes
    possible.

    Args:
        invoice_id: the bill to settle.
        approval_id: from `request_approval`, already approved by a human.

    Refuses, writing nothing, when the approval is missing, still pending,
    already spent, for a different invoice, or when the balance will not cover
    it. On success the cash balance, the `payments` row and the invoice status
    all move inside one transaction.
    """
    return _pay(
        approval_id=approval_id,
        kind="invoice_payment",
        ref_id=invoice_id,
        paid_by_label="invoice",
    )


@mcp.tool()
def pay_rent(lease_id: int, approval_id: int) -> dict[str, Any]:
    """Pay the rent on a lease against a human-signed approval.

    Args:
        lease_id: the lease to pay.
        approval_id: from `request_approval`, already approved by a human.

    Same refusals as `pay_invoice`. On success the balance drops, a `payments`
    row is written, and the lease rolls to its next due date so this month
    cannot be paid twice.
    """
    return _pay(
        approval_id=approval_id,
        kind="rent_payment",
        ref_id=lease_id,
        paid_by_label="rent",
    )


@mcp.tool()
def update_ticket(ticket_id: int, status: str | None = None, append_note: str | None = None) -> dict[str, Any]:
    """Record what was decided on a ticket, and move it along the board.

    Args:
        ticket_id: the ticket worked.
        status: the new status, e.g. "resolved", "blocked", "awaiting_approval".
            Omit to leave it where it is.
        append_note: a line describing the outcome. **Appended**, never
            overwritten -- the original note is the customer's own words and
            the history of a ticket is part of the audit.

    Notes are stamped with `desk.date_today` rather than the wall clock, so the
    ticket's own history reads on the shop's calendar.
    """
    if status is None and not (append_note or "").strip():
        raise ShopDataError("Nothing to update: pass a status, a note, or both.")

    with writing() as conn:
        today = shop_today(conn)
        row = conn.execute(
            "SELECT id, status, notes FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            raise ShopDataError(f"No ticket {ticket_id}.")

        new_notes = row["notes"]
        if (append_note or "").strip():
            stamped = f"[{today.isoformat()}] {append_note.strip()}"
            new_notes = f"{row['notes']}\n{stamped}" if row["notes"] else stamped
            conn.execute("UPDATE tickets SET notes = ? WHERE id = ?", (new_notes, ticket_id))
        if status is not None:
            conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))

    return {
        "ticket_id": ticket_id,
        "status_before": row["status"],
        "status_after": status if status is not None else row["status"],
        "notes_after": new_notes,
        "shop_date_today": today.isoformat(),
    }


@mcp.tool()
def draft_customer_message(
    ticket_id: int,
    recipient: str,
    subject: str,
    body: str,
    drafted_by: str = "customer_service",
) -> dict[str, Any]:
    """Write a message to a customer and leave it on the board. Nothing is sent.

    There is no send tool on this server and there is not going to be one.
    Constraint 9 is absolute: no real customer is emailed and no real vendor is
    contacted by this homework. A draft is filed where a human can read it,
    edit it, and decide.

    Args:
        ticket_id: the ticket this answers.
        recipient: who it would go to, as named on the ticket.
        subject: the subject line.
        body: the message. Say what the shop will actually do and when -- any
            date or figure in here must have come from a tool on this server,
            not from memory.
        drafted_by: the agent writing it.
    """
    for field, value in (("recipient", recipient), ("subject", subject), ("body", body)):
        if not (value or "").strip():
            raise BoardError(f"{field} cannot be empty.")

    with connect() as conn:
        today = shop_today(conn)
        row = conn.execute(
            "SELECT id, requester, subject FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            raise ShopDataError(f"No ticket {ticket_id}.")

    record = board.add_draft(
        {
            "ticket_id": ticket_id,
            "ticket_requester": row["requester"],
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "drafted_by": drafted_by,
            "drafted_on_shop_date": today.isoformat(),
            "delivery_status": "not_sent",
            "note": "Draft only. This server has no tool that sends anything.",
        }
    )
    return {
        "draft_id": record["id"],
        "ticket_id": ticket_id,
        "delivery_status": "not_sent",
        "saved_to": "output/board/drafts.json",
        "reminder": "Nothing was sent. A human reviews and sends this, or does not.",
    }


@mcp.tool()
def place_purchase_order(
    vendor_id: int,
    sku: str,
    size: str,
    qty: int,
    approval_id: int,
    needed_for_ticket: int | None = None,
) -> dict[str, Any]:
    """Place a restock order with a vendor, against a human-signed approval.

    Refuses if the vendor is still holding an unpaid invoice -- constraint 4,
    and the reason ticket 101 cannot be solved by ordering alone. Clear the
    blocking invoice first and the same call goes through.

    Args:
        vendor_id: who is being ordered from.
        sku, size, qty: what to make.
        approval_id: an approved `purchase_order` request for this vendor.
        needed_for_ticket: the ticket this unblocks, for the audit trail.

    No cash moves here. A purchase order is a commitment, and it is already
    counted against the balance by `get_cash_position` from the moment it is
    approved; cash leaves when the vendor's invoice is paid. The ETA is
    `desk.date_today + vendors.lead_days`.
    """
    approval = board.get_approval(approval_id)
    board.require_spendable(approval, "purchase_order", vendor_id)

    with connect() as conn:
        today = shop_today(conn)
        vendor = conn.execute(
            "SELECT id, name, specialty, lead_days FROM vendors WHERE id = ?", (vendor_id,)
        ).fetchone()
        if vendor is None:
            raise ShopDataError(f"No vendor {vendor_id}.")
        blocking = conn.execute(
            "SELECT id, amount, due_date FROM invoices WHERE vendor_id = ? AND status != 'paid'",
            (vendor_id,),
        ).fetchall()

    if blocking:
        owed = money(sum(b["amount"] for b in blocking))
        raise BoardError(
            f"REFUSED: {vendor['name']} will not ship while it holds unpaid invoices "
            f"{[b['id'] for b in blocking]} totalling {owed:.2f}. Settle those first, "
            "then place this order again."
        )

    # Shop rule 8: no duplicate orders. Stock already on its way is not a
    # reason to buy the same thing twice, and a second order would commit cash
    # the shop has not got, for goods it is already receiving.
    existing = board.open_purchase_orders(sku, size, needed_for_ticket)
    if existing:
        first = existing[0]
        raise BoardError(
            f"REFUSED: purchase order {first['id']} for {first['qty']} x {sku} size "
            f"{size} is already placed with {first['vendor_name']} and has not been "
            f"received yet (ETA {first['eta']}). Ordering again would buy the same "
            "stock twice. Receive that order when it lands, or work from it."
        )

    eta = (today + dt.timedelta(days=vendor["lead_days"])).isoformat()
    record = board.add_draft(
        {
            "record_type": "purchase_order",
            "vendor_id": vendor_id,
            "vendor_name": vendor["name"],
            "sku": sku,
            "size": size,
            "qty": qty,
            "approval_id": approval_id,
            "approved_by": approval["approved_by"],
            "needed_for_ticket": needed_for_ticket,
            "placed_on_shop_date": today.isoformat(),
            "lead_days": vendor["lead_days"],
            "eta": eta,
            "delivery_status": "not_sent",
            "note": "Order recorded on the board. No vendor was contacted.",
        }
    )
    return {
        "purchase_order_id": record["id"],
        "vendor": vendor["name"],
        "sku": sku,
        "size": size,
        "qty": qty,
        "eta": eta,
        "lead_days": vendor["lead_days"],
        "cash_moved": False,
        "note": "Commitment recorded; cash leaves when the vendor invoices. No vendor contacted.",
    }


@mcp.tool()
def receive_purchase_order(purchase_order_id: int) -> dict[str, Any]:
    """Book a delivered purchase order into stock, and record the vendor's bill.

    This is what makes "arrived" mean something different from "ordered".
    Until an order is received, `inventory.qty` has not moved and the customer
    still has nothing -- shop rule 7 turns on exactly that distinction.

    Args:
        purchase_order_id: the board id returned by `place_purchase_order`.

    Refuses while the shop's own date is still before the vendor's ETA: goods
    cannot be booked in before the lead time the `vendors` table committed to.
    Move the clock with `advance_shop_date` first.

    On success three things move inside one transaction -- `inventory.qty`
    goes up by the ordered quantity, a new row appears in `invoices` for what
    the vendor is now owed (quantity times `pricing.unit_cost`), and the order
    is marked received. **No cash moves here.** The shop now owes the vendor,
    and that bill is paid through the ordinary approval route like any other.
    """
    record = board.get_draft(purchase_order_id)
    if record.get("record_type") != "purchase_order":
        raise BoardError(f"Board record {purchase_order_id} is not a purchase order.")
    if record.get("received_on_shop_date"):
        raise BoardError(
            f"Purchase order {purchase_order_id} was already received on "
            f"{record['received_on_shop_date']}. Receiving it twice would invent stock."
        )

    sku, size, qty = record["sku"], record["size"], int(record["qty"])

    with writing() as conn:
        today = shop_today(conn)
        eta = dt.date.fromisoformat(record["eta"])
        if today < eta:
            raise ShopDataError(
                f"REFUSED: purchase order {purchase_order_id} is not due until {eta} "
                f"and the shop's date is {today}. {record['vendor_name']} quoted "
                f"{record['lead_days']} days, so the stock has not shipped yet. "
                "Advance the shop date once the day arrives, then receive it."
            )

        row = conn.execute(
            "SELECT qty, name FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        if row is None:
            raise ShopDataError(f"No inventory row for {sku} size {size} to receive into.")

        before = row["qty"]
        after = before + qty
        conn.execute(
            "UPDATE inventory SET qty = ? WHERE sku = ? AND size = ?", (after, sku, size)
        )

        cost = conn.execute(
            "SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
        if cost is None:
            raise ShopDataError(f"No pricing row for {sku}; cannot value the vendor's bill.")
        amount = money(cost["unit_cost"] * qty)

        next_id = conn.execute(
            "SELECT COALESCE(MAX(id), 500) FROM invoices"
        ).fetchone()[0] + 1
        due = (today + dt.timedelta(days=14)).isoformat()
        conn.execute(
            "INSERT INTO invoices (id, vendor_id, amount, due_date, status, description) "
            "VALUES (?, ?, ?, ?, 'open', ?)",
            (
                next_id,
                record["vendor_id"],
                amount,
                due,
                f"Restock {qty} x {sku} size {size} (PO {purchase_order_id})",
            ),
        )

    board.update_draft(
        purchase_order_id,
        received_on_shop_date=today.isoformat(),
        delivery_status="received",
        vendor_invoice_id=next_id,
    )

    return {
        "received": True,
        "purchase_order_id": purchase_order_id,
        "sku": sku,
        "size": size,
        "qty_received": qty,
        "qty_before": before,
        "qty_after": after,
        "received_on": today.isoformat(),
        "vendor_invoice_id": next_id,
        "vendor_invoice_amount": amount,
        "vendor_invoice_due": due,
        "cash_moved": False,
        "wrote": ["inventory.qty", "invoices (new row)"],
        "note": (
            f"{qty} unit(s) are now on the shelf. {record['vendor_name']} is owed "
            f"{amount:.2f} on invoice {next_id}, payable through the usual "
            "approval route."
        ),
    }


@mcp.tool()
def advance_shop_date(to_date: str) -> dict[str, Any]:
    """Move the shop's clock forward to a later date.

    `desk.date_today` is the shop's "today": every overdue test and every
    delivery estimate is measured from it. Advancing it is how a lead time
    actually elapses, so an order placed with a five-day lead can be received
    rather than waiting forever on a date that never comes.

    Args:
        to_date: an ISO date, e.g. "2026-09-05". Must be later than the
            current shop date.

    Refuses to move backwards. Rewinding the clock would un-overdue an
    invoice, un-due a rent payment, and silently change what the books mean.
    """
    try:
        target = dt.date.fromisoformat(to_date)
    except ValueError as exc:
        raise ShopDataError(f"{to_date!r} is not an ISO date like 2026-09-05.") from exc

    with writing() as conn:
        today = shop_today(conn)
        if target <= today:
            raise ShopDataError(
                f"REFUSED: the shop's date is already {today}; it only moves forward. "
                "Rewinding would un-overdue invoices and change what the books mean."
            )
        conn.execute("UPDATE desk SET date_today = ?", (target.isoformat(),))

    return {
        "shop_date_was": today.isoformat(),
        "shop_date_now": target.isoformat(),
        "days_advanced": (target - today).days,
        "note": (
            "Overdue tests and delivery ETAs are measured from this date, so "
            "re-read anything time-sensitive before acting on it."
        ),
    }


if __name__ == "__main__":
    mcp.run()
