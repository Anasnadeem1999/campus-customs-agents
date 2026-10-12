# Campus Customs MCP server

## What it is for

The single door between the Campus Customs agent team and the shop's data.

Five agents work the ticket board — Boss, Inventory, Accounting, Facilities
and Customer Service — and **none of them touches the database directly.**
Every lookup and, in later problems, every write goes through a tool
registered here. That buys two things the assignment needs: one place to audit
what the team is allowed to see and do, and a guarantee that no agent can
invent a price, a stock level or a due date, because the only numbers
available are the ones a tool read out of SQLite.

Built with **FastMCP** (`mcp.server.fastmcp.FastMCP`, pinned to `mcp<2` — v2
renamed the class to `MCPServer`).

## Which database it uses

**`data/campus_customs_new.db`** — the working copy, and only ever that.

The pristine seed `data/campus_customs.db` is the assignment's original data
and stays byte-for-byte untouched so a run can be restarted from a clean
slate. That isn't left to discipline: `db.connect()` compares the resolved
path against the seed and raises `ShopDataError` rather than opening it, even
if the `WORKING_DB_PATH` environment variable is pointed there by mistake.

Recreate the working copy at any time:

```bash
python scripts/reset_db.py
```

Connections are **read-only by default**. The three tools below only answer
questions; the tools that spend money or change a ticket arrive in later
problems and must ask for a writable handle explicitly, so a read path can
never mutate the shop by accident.

The shop's "today" is `desk.date_today` (**2026-08-31**), not the wall clock.
Every overdue test and delivery estimate below is measured from that field.

## The three tools

| Tool | Reads | Answers |
|---|---|---|
| `check_stock_by_size` | `inventory` | Can we fill this order from the shelf, and if not, by how much are we short? |
| `find_restock_vendors` | `vendors`, `invoices`, `desk` | Who can make up the gap, when would it land, and will they even ship? |
| `check_rent_due` | `leases`, `desk` | What is owed on the shop's space, and how soon? |

### `check_stock_by_size(sku, size, requested_qty=None)`

Stock is keyed by **(sku, size)**, so "do we have the Bulldog tee?" has no
answer — only "do we have it in S?" does. Returns the on-hand quantity and
aisle for that exact size, the quantities for the SKU's other sizes (so a
different size can be offered), and, when `requested_qty` is given, whether
the order fills from stock and the exact shortfall.

Distinguishes a size that is **stocked but at zero** from one the shop does
not carry at all — different problems with different answers.

### `find_restock_vendors(specialty_contains=None)`

For each vendor: lead time, the date an order placed today would arrive
(`desk.date_today + vendors.lead_days`), and whether it will ship.

A vendor holding any invoice whose status is not `paid` ships nothing new, so
`can_ship` is `false` and the blocking invoices are itemised with their
amounts and days overdue — which turns "we're out of stock" into the
actionable "we're out of stock *and here is the bill standing in the way*".

The database does not record which vendor supplies which SKU. The tool
therefore **does not guess** at that mapping: it returns each `specialty`
verbatim and leaves the match to the agent, with an optional case-insensitive
filter for narrowing.

### `check_rent_due(lease_id=None)`

Answers a rent notice from the lease itself rather than from the figure quoted
in the notice: landlord, monthly rent, next due date, and days until due
measured from `desk.date_today` (negative, with `is_overdue`, once past).

Reports only. It moves no money — payment requires human approval and a
separate tool.

## Running it

Not required for this problem; the server is written, not launched.

```bash
python -m mcp_server.server     # stdio transport
```

## Layout

```
mcp_server/
  server.py   FastMCP instance and the three tool definitions
  db.py       path resolution, the seed guard, and the shop's clock
  readme.md   this file
```

## Still to come

Later problems add tools for payments (human-approved, refusing any spend that
would drive cash negative), purchase orders, customer-message drafts, and
ticket status updates. They register in `server.py` alongside these three.
