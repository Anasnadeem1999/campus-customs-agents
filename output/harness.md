# Campus Customs — agent harness

Working notes on the shop the agent team has to run. Started at Problem 2 and
**grown with each later problem** — tools, agents, runs and results get
appended here as they are built.

| | |
|---|---|
| Seed database | `data/campus_customs.db` — pristine, **never written to** |
| Working copy | `data/campus_customs_new.db` — every agent write lands here |
| Reset | `python scripts/reset_db.py` (re-clones the seed; verifies its hash) |
| Shop "today" | `desk.date_today` = **2026-08-31** — not the wall clock |
| Cash on hand | `checking` = **$3,400.00** |
| Model | `gpt-6-luna` via Portkey, every agent, no exceptions |

---

## 1. The tables

Nine tables. For each: the fields as they really are in SQLite, and one line on
why the agent team cares.

### `desk` — 1 row

| Field | Type | |
|---|---|---|
| `date_today` | TEXT | `2026-08-31` — the shop's clock |
| `notes` | TEXT | null |

**Why it matters:** this single field defines "today". Every overdue
calculation, every lead-time ETA, every "due in N days" is measured from here.
An agent that reaches for the real system date will mis-rank the whole board,
because the real date is years off from the shop's.

### `tickets` — 3 rows

| Field | Type | |
|---|---|---|
| `id` | INTEGER | PK — 101, 102, 103 |
| `type` | TEXT | `customer_order`, `rent_notice`, `price_override` |
| `requester` | TEXT | who is asking — a customer, a landlord, a student org |
| `subject` | TEXT | one-line headline |
| `sku` | TEXT | nullable — set only when the ticket is about a product |
| `size` | TEXT | nullable — pairs with `sku` to hit `inventory`'s composite key |
| `qty` | INTEGER | nullable — how many units are being asked for |
| `lease_id` | INTEGER | nullable → `leases.id` |
| `invoice_id` | INTEGER | nullable → `invoices.id` |
| `status` | TEXT | all three are `open` |
| `notes` | TEXT | the free-text detail that carries the actual ask |
| `created_at` | TEXT | ISO 8601 with `-04:00` offset |

**Why it matters:** this is the board. It is the agents' only inbox, and its
nullable foreign keys are what tell the Boss which specialist a ticket belongs
to — a `lease_id` means Facilities, an `invoice_id` means Accounting, a
`sku`+`size` means Inventory.

### `inventory` — 10 rows

| Field | Type | |
|---|---|---|
| `sku` | TEXT | PK part 1 |
| `size` | TEXT | PK part 2 — `S`/`M`/`L`/`XL`, or `OS` for one-size goods |
| `name` | TEXT | human name, repeated on every size row |
| `qty` | INTEGER | units on hand |
| `location` | TEXT | `Aisle A`–`Aisle D` |

**Why it matters:** stock is keyed by **(sku, size)**, not by sku. "Do we have
the Bulldog tee?" has no answer — only "do we have it in S?" does, and that is
the difference between fulfilling ticket 101 and not. Two rows sit at qty 0.

### `pricing` — 4 rows

| Field | Type | |
|---|---|---|
| `sku` | TEXT | PK — one row per sku, **not** per size |
| `unit_cost` | REAL | what the shop pays |
| `list_price` | REAL | what the shop charges |

**Why it matters:** the Accounting agent's margin floor. A discount request is
only answerable against `unit_cost`, and restock cost is `unit_cost × qty`.
Note the grain mismatch with `inventory`: price is per sku, stock is per size.

### `vendors` — 3 rows

| Field | Type | |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | TEXT | Bulldog Print Co, Elm City Gifts, QuickShip CT |
| `specialty` | TEXT | `apparel reprint`, `mugs and small goods`, `local courier` |
| `lead_days` | INTEGER | 5, 3, 1 |

**Why it matters:** two independent gates on any restock. `specialty` decides
*who can even make the item*, and `lead_days` decides *when it lands* —
`date_today + lead_days`. Lead times are read from this table, never assumed.

### `invoices` — 1 row

| Field | Type | |
|---|---|---|
| `id` | INTEGER | PK — 501 |
| `vendor_id` | INTEGER | → `vendors.id` |
| `amount` | REAL | 840.00 |
| `due_date` | TEXT | 2026-08-28 |
| `status` | TEXT | `open` |
| `description` | TEXT | "Rush reprint CC-TEE-WHITE S" |

**Why it matters:** an unpaid invoice is a **shipping blocker**, not just a
bill. Under the shop rules a vendor ships nothing new while it holds an open
invoice, so this table gates Inventory's restock options as much as
Accounting's payment queue.

### `leases` — 1 row

| Field | Type | |
|---|---|---|
| `id` | INTEGER | PK — 1 |
| `space_name` | TEXT | Chapel Street shop |
| `landlord` | TEXT | Elm City Properties |
| `monthly_rent` | REAL | 2400.00 |
| `next_due` | TEXT | 2026-09-02 |
| `notes` | TEXT | null |

**Why it matters:** the Facilities agent's ledger, and the largest single claim
on cash. `next_due` against `date_today` is what makes rent urgent, and
`monthly_rent` is the figure Accounting has to reserve cash for.

### `cash_accounts` — 1 row

| Field | Type | |
|---|---|---|
| `name` | TEXT | PK — `checking` |
| `balance` | REAL | 3400.00 |
| `date` | TEXT | 2026-08-31 |

**Why it matters:** the hard ceiling on everything. Cash only ever goes **out**
in this homework — no revenue is modelled — so this number is monotonically
decreasing and the pay tool must refuse any payment that would drive it
negative.

### `payments` — 0 rows

| Field | Type | |
|---|---|---|
| `id` | INTEGER | PK |
| `kind` | TEXT | what was paid — e.g. an invoice or a rent charge |
| `ref_id` | INTEGER | nullable — the `invoices.id` or `leases.id` paid |
| `amount` | REAL | |
| `account` | TEXT | → `cash_accounts.name` |
| `paid_at` | TEXT | stamped from `desk.date_today`, not the wall clock |
| `approved_by` | TEXT | **NOT NULL** — who the human approver was |

**Why it matters:** starts empty; the agents fill it. `approved_by` being NOT
NULL is the schema enforcing the shop rule — a payment cannot be written at
all without naming a human approver. Every paid row must move in lockstep with
a `cash_accounts.balance` decrease and the invoice or lease status.

---

## 2. The three open tickets, and how they link up

All three are `open` as of 2026-08-31. They are not independent — they compete
for one $3,400 pot, and two of them run through the same blocked vendor.

### Ticket 101 — `customer_order` — Tauhid Zaman, "Bulldog tee"

*Wants `CC-TEE-WHITE` size **S**, qty 1. Also carries `invoice_id = 501`.*

```
tickets.101 ──sku+size──> inventory(CC-TEE-WHITE, S)  qty = 0     ← cannot fulfil
            └─invoice_id─> invoices.501  $840, due 2026-08-28, open
                              └─vendor_id─> vendors.1 Bulldog Print Co
                                            apparel reprint, lead 5d
```

The chain is the whole puzzle. The customer wants a tee the shop does not
have — size S is the one size at zero (M/L/XL hold 5/3/2). Restocking means
an apparel reprint, and **Bulldog Print Co is the only apparel vendor**. But
that vendor holds invoice 501, **3 days overdue**, so under the shop rules it
will not ship. The ticket links the invoice directly, which is the dataset
telling the agents the bill and the order are one problem: pay 501, then the
reprint can be ordered, landing `2026-08-31 + 5d = 2026-09-05`.

Margin is comfortable — cost $8 against a $28 list, 71.4%.

### Ticket 102 — `rent_notice` — Elm City Properties, "Rent due"

*`lease_id = 1`. No sku, no invoice.*

```
tickets.102 ──lease_id──> leases.1  Chapel Street shop
                          rent $2,400, next_due 2026-09-02  ← 2 days out
```

The simplest chain and the biggest number. Facilities owns it, Accounting
funds it, and it needs human approval like any payment.

### Ticket 103 — `price_override` — Yale AI Club, "Bulk hoodie discount"

*Wants 20 × `CC-HOOD-NAVY` size **M**. No invoice, no lease.*

```
tickets.103 ──sku+size──> inventory(CC-HOOD-NAVY, M)  qty = 8    ← short by 12
            └─sku───────> pricing(CC-HOOD-NAVY)  cost $22 / list $58
```

It reads like a pricing question but it is **two** questions. The discount is
Accounting's — 20 at list is $1,160 revenue on $440 of cost, 62.1% margin, so
there is room to move. The quieter problem is Inventory's: only 8 are on hand,
so 12 must be reprinted, and that again means Bulldog Print Co, again blocked
by invoice 501.

### What the three tickets do to each other

**The vendor bottleneck.** Vendor 1 is the only `apparel reprint` supplier.
Vendors 2 and 3 do mugs and courier work. So neither the tee nor the hoodie
has an alternative source — clearing invoice 501 is the single unlock for both
101 and 103.

**The cash squeeze.** Everything draws on one $3,400 balance, and nothing
refills it:

| Claim | Amount | Running balance |
|---|---|---|
| Opening `checking` | | **3,400.00** |
| Invoice 501 — unblocks vendor 1 | −840.00 | 2,560.00 |
| Rent, due 2026-09-02 | −2,400.00 | **160.00** |
| Restock 12 hoodies @ $22 | −264.00 | **−104.00 → must be refused** |

Both bills fit; the hoodie restock does not. The pay tool refusing on
insufficient cash is therefore **on the main path of this dataset**, not an
edge case — and ticket 103 cannot be fully granted as asked. The honest
outcome is a partial offer (8 now) or a deferral, drafted by Customer Service,
with the restock held until cash allows.

**Order matters.** Pay rent first and $1,000 remains — still enough for the
$840 invoice. Either order clears both. But any agent that commits to the
hoodie restock before the two bills breaks the shop.

---

## 3. Facts the agents must compute, never recall

The numbers above are this document's reading of the seed data, written down
so a human can check the agents' work. The agents themselves must read every
figure from `data/campus_customs_new.db` at the moment they need it, because
the working copy changes as tickets resolve.

- **Overdue** = `desk.date_today` − `due_date` / `next_due`. Never the wall clock.
- **Restock ETA** = `desk.date_today` + `vendors.lead_days`.
- **Can this vendor ship?** No, if it has any invoice whose status is not paid.
- **Can we afford this?** Re-read `cash_accounts.balance`; refuse if the
  payment would take it below zero.
- **Margin** = (`list_price` − `unit_cost`) / `list_price`, from `pricing`.
- **Do we have it?** Always by **(sku, size)**, never by sku alone.

---

## 4. The MCP tools (Problem 3)

Built with FastMCP in `mcp_server/server.py`, against the working copy only.
Every agent on the team reaches the shop through these tools and nothing else,
so no agent can quote a price, a stock level or a due date that did not come
out of SQLite.

One tool, one ticket — the three tools cover the three open tickets exactly.

| Tool | Table it reads | Ticket it unlocks |
|---|---|---|
| `check_stock_by_size` | `inventory` | **101** — customer order, Bulldog tee |
| `find_restock_vendors` | `vendors`, `invoices`, `desk` | **103** — bulk hoodie request |
| `check_rent_due` | `leases`, `desk` | **102** — rent notice |

### `check_stock_by_size(sku, size, requested_qty=None)`

**Reads:** `inventory` — the `(sku, size)` row, plus the SKU's other sizes.

**Unlocks ticket 101.**

> Ticket 101 asks for `CC-TEE-WHITE` in size **S**, and S is the single size
> sitting at zero while M, L and XL hold 5, 3 and 2 — so a SKU-level stock
> check would report ten tees in the building and tell Tauhid Zaman yes when
> the correct answer is no.

Verified against the working copy: `qty_on_hand: 0`, `shortfall: 1`,
`other_sizes: {S:0, M:5, L:3, XL:2}`.

### `find_restock_vendors(specialty_contains=None)`

**Reads:** `vendors` (lead times), `invoices` (the shipping block), `desk` (to
date the ETA).

**Unlocks ticket 103.**

> Ticket 103 wants 20 hoodies against 8 on hand, and this is the tool that
> decides whether the missing 12 can be made at all — it finds that Bulldog
> Print Co is the only vendor whose specialty is apparel reprint, that it is
> blocked by an $840 invoice already 3 days overdue, and that even once freed
> the reprint would not land until 2026-09-05.

Verified: filtering on `"apparel"` returns exactly one vendor —
`can_ship: false`, `blocked_amount: 840.0`, `days_overdue: 3`,
`eta_if_ordered_today: 2026-09-05`.

### `check_rent_due(lease_id=None)`

**Reads:** `leases` (the obligation), `desk` (to measure urgency).

**Unlocks ticket 102.**

> Ticket 102 is a landlord's email asserting that rent is due in two days, and
> this tool is the right one precisely because it does not take the email's
> word for it — it answers from lease 1 itself: **$2,400**, due
> **2026-09-02**, two days out from `desk.date_today`.

Verified: `amount_due: 2400.0`, `days_until_due: 2`, `is_overdue: false`.

### A note on overlap, kept out of the table above

The mapping above is each tool's ticket. The tools are not *fenced* to that
ticket, and one overlap matters to the run: ticket 101 also reaches
`find_restock_vendors` once its shortfall of 1 is known, and ticket 103 also
reaches `check_stock_by_size` to learn it is short by 12 in the first place.

That overlap is the dataset's point rather than an accident. Both apparel
tickets funnel into the same blocked vendor, so **101 and 103 are not two
restock problems but one unpaid invoice** — clearing invoice 501 is the single
action that unblocks both. Recorded here so the one-tool-one-ticket table
stays readable without the shop's actual shape being lost.

### Design decisions worth recording

- **The tools refuse to guess a vendor–SKU mapping.** The schema has no link
  from a SKU to a vendor; only a free-text `specialty`. Rather than hardcode
  "tees come from vendor 1", `find_restock_vendors` returns each specialty
  verbatim and lets the agent judge. Inventing that mapping would be inventing
  data.
- **Read-only by default.** `db.connect()` opens the file `mode=ro` unless a
  caller explicitly asks to write, so the three question-answering tools
  cannot mutate the shop even by accident. The payment and ticket-update
  tools in later problems will have to ask.
- **The seed is guarded in code, not by convention.** Pointing
  `WORKING_DB_PATH` at `data/campus_customs.db` raises `ShopDataError`
  instead of opening it. Tested.
- **A stocked-but-empty size is distinguished from a size never carried.**
  `(CC-TEE-WHITE, S)` exists at qty 0, which is a restock; a size with no row
  at all is a different conversation with the customer.

---

## 5. Connecting and smoke-testing the server (Problem 4)

`.mcp.json` at the project root registers the server under the key
**`campus-customs`**, following the same shape the workspace already uses for
its other local server: an absolute path to this project's venv interpreter,
then the module to run.

```json
{
  "mcpServers": {
    "campus-customs": {
      "command": ".../HW5/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": ".../HW5",
        "WORKING_DB_PATH": "data/campus_customs_new.db",
        "SEED_DB_PATH": "data/campus_customs.db"
      }
    }
  }
}
```

`PYTHONPATH` is set rather than relying on a working directory, so the package
imports no matter where the host launches it from. The two DB paths are passed
explicitly so the working copy is named in the config itself, not just
defaulted in code.

### The evidence: `output/mcp_smoke.json`

Produced by `scripts/mcp_smoke.py`, which **reads `.mcp.json` and launches the
server from it** — same interpreter, same args, same env — then speaks real
MCP over stdio: initialize, `list_tools`, `call_tool`. It imports nothing from
`mcp_server`, so a config that would fail in the vibe coder fails here too.

For each of the three tools the file records the prompt, the tool name, the
arguments, the full tool output, and a **field-by-field cross-check against
`data/campus_customs_new.db` using SQL written separately from the tool's own
query**. A tool agreeing with itself proves nothing; agreeing with an
independent `SELECT` is evidence.

| Ticket | Tool | Fields checked vs SQL | Result |
|---|---|---|---|
| 101 | `check_stock_by_size` | 4 | PASS |
| 103 | `find_restock_vendors` | 10 | PASS |
| 102 | `check_rent_due` | 7 | PASS |

**21 of 21 fields matched**, including the derived ones that are easiest to
get wrong — `shortfall: 1`, `days_overdue: 3`, `eta_if_ordered_today:
2026-09-05`, `days_until_due: 2`. `all_tools_tested` is computed by comparing
the tools actually called against `list_tools()`, so the file cannot claim
full coverage while silently skipping one. No model calls were made; this is
transport and data, not inference.

### How the server is connected — and why this way

**Project-scoped `.mcp.json`, committed to the repo, with the server
pre-approved in `.claude/settings.json`.**

Three reasons this beats the alternatives:

- **It travels with the submission.** The config is a file in the repo, so a
  clone gets the server with no manual setup. Registering the server in the
  host's global config would leave the public repo describing a connection the
  grader does not have.
- **It writes no global machine state.** Nothing outside this folder changes.
- **It removes the approval prompt without over-granting.**
  `.claude/settings.json` lists `campus-customs` under
  `enabledMcpjsonServers` — this one server by name, rather than
  `enableAllProjectMcpServers`, which would wave through any server a future
  config happens to add.

The one real weakness is portability: `command` is an absolute path to this
project's venv, which does not survive a clone onto another machine. Hence
`scripts/setup_mcp_config.py`, which rewrites `.mcp.json` for whatever machine
it runs on — `--check` reports drift without writing. Run on this machine it
reproduces the committed file byte for byte.

### Connection status, stated plainly

The tools are **not** live in the session that wrote the config. Claude Code
reads `.mcp.json` when a session starts, so `mcp__campus-customs__*` appears
only after a restart. That limitation is recorded in the evidence file under
`vibe_coder_connection` rather than papered over. What *is* proven is the
config: the smoke test launches the server through it, over the same stdio
transport the vibe coder uses, and all three tools answer correctly.

### The test prompts

Written for this smoke test at the user's instruction, one per tool, each
phrased the way someone working the shop would type it and worded so that only
its target tool can answer it.

| Ticket | Tool | Test prompt |
|---|---|---|
| 101 | `check_stock_by_size` | *"Ticket 101 just came in: Tauhid Zaman wants one Bulldog tee, SKU CC-TEE-WHITE, in size S. Check the shelf for that exact size — how many do we have, and if we cannot fill it, how many are we short?"* |
| 103 | `find_restock_vendors` | *"Ticket 103: the Yale AI Club wants 20 navy hoodies in size M and we only hold 8. Find me a vendor who could reprint the missing 12 — give me their lead time, whether anything is stopping them from shipping, and the date an order placed today would land."* |
| 102 | `check_rent_due` | *"Ticket 102: Elm City Properties emailed claiming the shop rent is due in two days. Do not take the email's word for it — pull the lease itself and tell me the landlord, the amount owed, the due date, and how many days away that is."* |

Each prompt is stored in `output/mcp_smoke.json` beside the tool's actual
output and the SQL cross-check, along with a plain-English statement of the
answer expected before the call was made.

### Every returned field, checked against `campus_customs_new.db`

**21 of 21 match.**

| Ticket | Field | Database | Tool |
|---|---|---|---|
| 101 | `qty_on_hand` | 0 | 0 |
| 101 | `location` | Aisle B | Aisle B |
| 101 | `product_name` | Classic Bulldog Tee | Classic Bulldog Tee |
| 101 | `shortfall` | 1 | 1 |
| 103 | `vendor_count` | 1 | 1 |
| 103 | `vendor_id` | 1 | 1 |
| 103 | `name` | Bulldog Print Co | Bulldog Print Co |
| 103 | `specialty` | apparel reprint | apparel reprint |
| 103 | `lead_days` | 5 | 5 |
| 103 | `eta_if_ordered_today` | 2026-09-05 | 2026-09-05 |
| 103 | `can_ship` | false | false |
| 103 | `blocked_amount` | 840.0 | 840.0 |
| 103 | `blocking_invoice_ids` | [501] | [501] |
| 103 | `days_overdue` | 3 | 3 |
| 102 | `lease_id` | 1 | 1 |
| 102 | `space_name` | Chapel Street shop | Chapel Street shop |
| 102 | `landlord` | Elm City Properties | Elm City Properties |
| 102 | `amount_due` | 2400.0 | 2400.0 |
| 102 | `next_due` | 2026-09-02 | 2026-09-02 |
| 102 | `days_until_due` | 2 | 2 |
| 102 | `is_overdue` | false | false |

The "Database" column is not the tool's own answer echoed back — it is a
separate `SELECT` written independently in `scripts/mcp_smoke.py`. The derived
values are the ones worth watching: `shortfall`, `days_overdue`,
`eta_if_ordered_today` and `days_until_due` are all computed from
`desk.date_today`, so they would drift immediately if any tool reached for the
wall clock.

After the run, `campus_customs_new.db` still hashes identical to the seed —
confirming the three read tools changed nothing.

---

## Appendix — verified data integrity

Checked against the seed at Problem 2; no surprises to code around.

- Every `pricing` sku exists in `inventory`, and vice versa — 4 SKUs each side.
- `tickets.invoice_id` → 501 and `tickets.lease_id` → 1 both resolve.
- `invoices.vendor_id` → 1 resolves.
- Zero-stock rows: `(CC-TEE-WHITE, S)` and `(CC-MUG-CREST, OS)`. Only the
  first has a ticket against it; the empty mug shelf is unclaimed.
- `payments` is empty, as expected — the agents write the first row.
- Vendor shipping status at seed: **1 Bulldog Print Co — BLOCKED** ($840 open);
  2 Elm City Gifts — clear; 3 QuickShip CT — clear.
- Status vocabulary in the seed is narrow: tickets are all `open`, the invoice
  is `open`. The tools will have to introduce whatever further values they
  need (e.g. `paid`, `resolved`) rather than finding them pre-defined.
