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

Built with **`MCPServer`** (`mcp.server.mcpserver.MCPServer`), on `mcp>=2`.

The earlier pin to `mcp<2` had to go in Problem 5: pydantic-ai's MCP client
requires the v2 SDK, and the agents and the server have to agree on a version.
The migration was small — v2 renamed `FastMCP` to `MCPServer` and switched the
wire-shaped `serverInfo`/`structuredContent` fields to snake_case — and the
Problem 4 smoke test still passes 21 of 21 field checks afterwards.

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

Connections are **read-only by default**. A tool that changes anything has to
ask for a writable handle explicitly, through `db.writing()`, which wraps the
whole change in one all-or-nothing transaction — so a read path cannot mutate
the shop by accident, and a payment cannot half-happen.

The shop's "today" is `desk.date_today` (**2026-08-31**), not the wall clock.
Every overdue test and delivery estimate below is measured from that field.

## The fourteen tools

Three read tools came from Problem 3. Problem 5 added seven more, plus the
approval board the agent team needs to work a ticket to resolution. Every one
of them reads or writes `data/campus_customs_new.db` and nothing else.

| Tool | Tables | Answers / does |
|---|---|---|
| `check_stock_by_size` | `inventory` | Can we fill this order from the shelf, and if not, by how much are we short? |
| `find_restock_vendors` | `vendors`, `invoices`, `desk` | Who can make up the gap, when would it land, and will they even ship? |
| `check_rent_due` | `leases`, `desk` | What is owed on the shop's space, and how soon? |
| `list_tickets` | `tickets`, `desk` | What has the shop been asked to deal with? |
| `get_cash_position` | `cash_accounts`, `desk` *(+ the approval board)* | What is in the bank, what is already promised, and what may still be committed? |
| `list_invoices` | `invoices`, `vendors`, `desk` | What do we owe each vendor, and how late is it? |
| `quote_discount` | `pricing`, `inventory`, `desk` | What does this bulk price do to the margin, and can the order even be filled? |
| `request_approval` | `invoices`, `leases`, `vendors`, `tickets`, `cash_accounts`, `desk` | Ask a human to approve a spend. Validates against the live record; moves no money. |
| `list_approvals` | *(approval board only)* | What has been asked for, and what did the human decide? |
| `pay_invoice` | `invoices`, `payments`, `cash_accounts`, `desk` | Settle a vendor bill against a signed approval, lifting that vendor's shipping block. |
| `pay_rent` | `leases`, `payments`, `cash_accounts`, `desk` | Pay rent against a signed approval and roll the lease to its next due date. |
| `update_ticket` | `tickets`, `desk` | Record the outcome and move the ticket along the board. |
| `draft_customer_message` | `tickets`, `desk` *(+ the board)* | Write a reply and file it. **Nothing is sent.** |
| `place_purchase_order` | `vendors`, `invoices`, `desk` *(+ the board)* | Order a restock, refusing while the vendor holds an unpaid bill. |

### The approval gate, and the verb that is missing

Spending is the one thing on this server that cannot be done by an agent
alone, and the guarantee is structural rather than a line in a prompt:

- `request_approval` writes a **pending** request. It validates against the
  live database first — the invoice must exist and still be open, and the
  amount must equal what is actually owed — so a request that could never be
  paid is refused when it is made, not discovered later.
- **No tool on this server approves anything.** The verb lives in
  `scripts/approve.py`, outside the MCP server, where no agent can reach it.
  An agent cannot approve its own spending because the action does not exist
  in its world. `tests/test_shop_tools.py::test_no_mcp_tool_can_approve`
  fails the build if an approving tool is ever added here.
- `pay_invoice` and `pay_rent` refuse — writing nothing at all — when the
  approval is missing, still pending, already spent, or for a different
  record, and when the balance will not cover the payment.

### What a payment moves, and why it is one transaction

A payment changes three things together: the cash balance, a new `payments`
row carrying the approver's name and `desk.date_today`, and the invoice status
or the lease's next due date. All three happen inside one `BEGIN IMMEDIATE`
transaction, so the books can never show cash gone with the bill still open.
`BEGIN IMMEDIATE` also takes the write lock up front, so two payments racing
for the same thin balance cannot both read it and both decide they fit.

### Two numbers for cash, and which one to use

`get_cash_position` returns `total_balance`, `approved_not_yet_paid` and
`uncommitted`, and the right one depends on the question:

- **Planning something new** → `uncommitted`. Planning against the raw balance
  is how two approved payments overdraw one account.
- **Executing an approval that already exists** → **not** `uncommitted`. That
  approval's amount is already inside `approved_not_yet_paid`, so
  `uncommitted` has subtracted the very money about to be spent. Pass
  `for_approval_id` and read `executing_approval.can_execute_now`.

This is not hypothetical: a live run read `uncommitted` while holding two
approvals and concluded they were in conflict, when $3,400 covered both the
$840 invoice and the $2,400 rent. The `for_approval_id` argument and a
regression test exist because of that run.

### What the tools deliberately will not do

- **Send anything.** There is no send or email tool, and the test suite asserts
  that none appears. `draft_customer_message` and `place_purchase_order` file
  their output on the board for a human; no customer or vendor is contacted.
- **Guess which vendor makes which SKU.** The schema does not record it, so
  `find_restock_vendors` returns each `specialty` verbatim and leaves the match
  to the agent, as a judgement it has to state out loud.
- **Add tables to the shop's database.** Approval requests, drafts and purchase
  orders have no home in the nine-table schema, so they live in
  `output/board/` as append-only JSON. No shop fact is stored there — only the
  shop's *intent*: who asked for what, who approved it, whether it is spent.

## Running it

Not required for this problem; the server is written, not launched.

```bash
python -m mcp_server.server     # stdio transport
```

## Layout

```
mcp_server/
  server.py   the MCPServer instance and all fourteen tool definitions
  db.py       path resolution, the seed guard, the shop's clock, transactions
  board.py    approval requests, drafts and POs -- the records the 9-table
              schema cannot hold. No shop facts live here.
  readme.md   this file
```

## Checking it still holds

```bash
python -m pytest tests/test_shop_tools.py -q   # 17 tests, no model, no network
python scripts/mcp_smoke.py                    # every tool over real MCP stdio
```

The test suite is where the rules are actually enforced. It calls the tool
functions directly and asserts every refusal — no approval, pending approval,
reused approval, redirected approval, insufficient funds, blocked vendor,
seed database — because a rule an agent can talk its way past is not a rule.
