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

---

## 6. The agent team (Problem 5)

Five agents, **fully connected** — any agent may delegate to any other. The
connectivity is literal, not nominal: Customer Service can ask Accounting
directly without routing through the Boss, and Inventory can ask the Boss.
Each agent is built the same way — the shop rules, then its own role brief,
then the MCP toolset, then one `ask_<colleague>` tool per other member.

| Agent | Owns | Prompt file | Delegates to |
|---|---|---|---|
| **Boss** | Reads each ticket, decides who works it, ranks priorities across tickets, makes the final call | `backend/prompts/boss.md` | all four |
| **Inventory** | Stock by SKU **and size**, shortfalls, which vendor can restock and when | `backend/prompts/inventory.md` | all four |
| **Accounting** | Cash, invoices, margins; prepares payments and POs for approval | `backend/prompts/accounting.md` | all four |
| **Facilities** | The lease, rent, the landlord, the premises | `backend/prompts/facilities.md` | all four |
| **Customer Service** | Drafts what a customer will read | `backend/prompts/customer_service.md` | all four |

Every agent runs on **`gpt-6-luna`** through the Portkey gateway, and the
*resolved* model name is checked on every single step (section 6.4).

### 6.1 Where the prompts live

`backend/prompts/shop_rules.md` is loaded first by all five agents, then the
role file. Order is deliberate: the rules outrank the role, and the rules say
so. Keeping the rules in one shared file means a change to shop policy is one
edit, not five, and the role briefs stay about the role.

The rules cover: the shop's clock, facts-from-tools-only, the approval gate,
the vendor block, how to rank spending when cash is short, never contacting
anyone, how to delegate, telling the truth when the answer is no, finishing the
ticket, keeping turns cheap, and the model policy.

### 6.2 Every tool, and the tables behind it

Fourteen tools: the three from Problem 3, seven added in Problem 5, plus
`list_approvals`, `list_tickets` and `get_cash_position` that the team needs to
see its own board.

| Tool | Problem | Tables read | Tables written |
|---|---|---|---|
| `check_stock_by_size` | 3 | `inventory` | — |
| `find_restock_vendors` | 3 | `vendors`, `invoices`, `desk` | — |
| `check_rent_due` | 3 | `leases`, `desk` | — |
| `list_tickets` | 5 | `tickets`, `desk` | — |
| `get_cash_position` | 5 | `cash_accounts`, `desk` | — |
| `list_invoices` | 5 | `invoices`, `vendors`, `desk` | — |
| `quote_discount` | 5 | `pricing`, `inventory`, `desk` | — |
| `request_approval` | 5 | `invoices`, `leases`, `vendors`, `tickets`, `cash_accounts`, `desk` | — *(board only)* |
| `list_approvals` | 5 | — *(board only)* | — |
| `pay_invoice` | 5 | `invoices`, `cash_accounts`, `desk` | `invoices`, `payments`, `cash_accounts` |
| `pay_rent` | 5 | `leases`, `cash_accounts`, `desk` | `leases`, `payments`, `cash_accounts` |
| `update_ticket` | 5 | `tickets`, `desk` | `tickets` |
| `draft_customer_message` | 5 | `tickets`, `desk` | — *(board only)* |
| `place_purchase_order` | 5 | `vendors`, `invoices`, `desk` | — *(board only)* |

All nine tables are now reachable. The four that only a Problem 5 tool touches
— `pricing`, `payments`, `cash_accounts`, `tickets` — are exactly the ones a
team that *resolves* tickets needs and a team that only *reports* did not.

**Approval requests, drafts and purchase orders are not in the database.** The
nine-table schema has no room for them, and adding tables to the assignment's
own input would be editing the question. They live in `output/board/` as
append-only JSON. Nothing in there is a shop fact — no price, balance or
quantity — only the shop's intent: who asked for what, who approved it, and
whether it has been spent.

### 6.3 The audit trail

`output/audit_trail.json`, **appended, never wiped**. Two lists joined by
`run_id`: `runs` (one header per run, written before any agent is invoked, so a
crashed run still leaves a record that it was attempted) and `steps`.

One step is one agent turn, and carries enough to audit the decision without
the transcript:

`step` · `run_id` · `ticket_id` · `agent` · `delegated_by` · `task` ·
`tool_calls` (name, **arguments**, returned payload, error flag) · `output` ·
`blocked_on` · `needs_human` · `model` (requested, **resolved**, ok) · `usage`
(tokens) · `started_at` · `finished_at` · `duration_seconds` · `error`

`delegated_by` is what makes the delegation graph readable after the fact: a
step with `delegated_by: "boss"` is the Boss asking, and `null` means the run
itself invoked that agent. Recording the tool **arguments** alongside the
result is what makes the trail auditable rather than merely descriptive — a
reviewer can replay the exact call and check whether the agent's conclusion
followed from what it actually got back.

Failures are appended too. A step that threw is written with its error rather
than dropped, because the run where something went wrong is the run you most
want the record of.

### 6.4 The model check, on every step

The gateway does **not** error on an unknown model name — it silently answers
as `gpt-5.6-luna`. So the requested name proves nothing. Every step reads the
model the gateway says it actually used, compares it against `gpt-6-luna` as a
strict prefix (the dated suffix `gpt-6-luna-2026-09-22` is allowed; a different
family is not), and records both. Any step failing the check makes the whole
run **void**, reported loudly and last so it cannot be missed.

**One gateway constraint had to be worked around.** Asked for function tools
with reasoning left on, the gateway refuses the entire call:

> `azure-openai error: Function tools with reasoning_effort are not supported
> for gpt-6-luna-global in /v1/chat/completions. To use function tools, use
> /v1/responses or set reasoning_effort to 'none'.`

Every agent here calls MCP tools, so every agent hit it. Setting
`reasoning_effort="none"` fixes it and still resolves to `gpt-6-luna-2026-09-22`
— verified live. The model requirement is met; nothing is substituted.

### 6.5 The human-in-the-loop cycle, demonstrated

```bash
python -m backend.run_tickets                 # resets, works the board, stops at the gate
python scripts/approve.py --list              # read what the team asked for
python scripts/approve.py --id 1 --by "Anas Nadeem"
python -m backend.run_tickets --no-reset      # team acts on the approval and finishes
```

**Verified end to end over the whole board**, from a reset database: the team
worked all three tickets, raised two approvals and stopped; both were approved;
the resume run paid both and finished what it could.

| Ticket | Outcome | What happened |
|---|---|---|
| 101 | `blocked` | Invoice 501 paid, lifting the vendor's shipping block. Waiting on a purchase-order approval. |
| 102 | `resolved` | Rent paid in full. |
| 103 | `blocked` | 8 of 20 on hand; the $264 restock will not fit in $160. Draft filed, not sent. |

The database moved exactly as constraints 6 and 7 require — cash **$3,400 →
$160**, invoice 501 `paid`, the lease rolled 2026-09-02 → 2026-10-02 so the
same month cannot be paid twice, and two `payments` rows each stamped
`approved_by: "Anas Nadeem"` and `paid_at: 2026-08-31` (the shop's clock, not
the wall clock).

That $160 is the seeded squeeze landing: $840 + $2,400 = $3,240 against $3,400,
so the third spend — the $264 hoodie restock — is refused for want of cash, and
the team says so in figures rather than quietly dropping it.

Audit trail from that cycle: **19 steps across 2 runs, appended not wiped**,
146 tool calls recorded with their arguments, all five agents exercised, every
step resolving to `gpt-6-luna-2026-09-22`.

### 6.6 Three defects the live runs found

Worth recording, because none of them would have shown up in a test that
mocked the model:

1. **Tickets parked at `awaiting_approval` vanished from the resume run.** The
   runner read only `status="open"`, so the moment the team correctly parked a
   ticket at the approval gate, the run that was supposed to finish it could no
   longer see it. Fixed by treating `open`, `awaiting_approval` and `blocked`
   as unfinished work.
2. **`uncommitted` double-counted an approval against itself.** With both the
   $840 invoice and the $2,400 rent approved against $3,400, `uncommitted`
   reads $160 — so the team concluded the two approvals were in conflict and
   paid neither, when the balance covered both. `get_cash_position` now takes
   `for_approval_id` and answers the execution question directly, and a
   regression test pins it.
3. **Investigating was being mistaken for resolving.** A run closed the rent
   ticket as `resolved` having only confirmed the amount was genuinely owed —
   landlord unpaid, ticket shut, nobody looking for it. The rules now set an
   explicit bar: `resolved` means the thing asked for actually happened.

---

## 7. Safety and guard rails

What a real business would want in place before letting agents near its
customers and its bank account — and what is actually implemented here.

### 7.1 Money

| Guard rail | How it is enforced |
|---|---|
| **No agent can approve spending** | The verb does not exist on the MCP server. Approval lives in `scripts/approve.py`, outside anything an agent can call. A test fails the build if an approving tool ever appears. |
| **Every payment names a human** | `payments.approved_by` is written from the approval record, so the books say who authorised it. |
| **The balance cannot go negative** | The pay tools compare against the live balance and refuse, writing nothing. |
| **A payment is all-or-nothing** | Cash, the `payments` row and the invoice/lease status move in one `BEGIN IMMEDIATE` transaction. No state where cash is gone and the bill is still open. |
| **One approval, one payment** | A consumed approval is dead. Stops the same bill being paid twice across resume runs. |
| **An approval cannot be redirected** | Kind and `ref_id` must both match. Rent money approved is rent money. |
| **The amount must match the real bill** | Checked against the database at request time *and* again at payment time, in case the record moved in between. |
| **Committed money is visibly gone** | `get_cash_position` separates what is in the bank from what is already promised, so two agents cannot each spend the same dollar. |
| **Races cannot both win** | `BEGIN IMMEDIATE` takes the write lock before reading the balance. |

What a real business would add beyond this homework: per-agent and per-day
spending ceilings, dual approval above a threshold, a vendor allow-list so
money can only go to known counterparties, and alerting on any refusal — a
refused payment is a signal, not just a non-event.

### 7.2 Customers and the outside world

- **There is no send tool, and the test suite asserts none appears.** Drafts
  are filed for a human; no customer is emailed, no vendor contacted.
- Drafts must carry only figures a tool returned this run, and must say
  "pending approval" where a human has not yet decided.
- Ticket notes are **appended, never overwritten**, so the customer's own words
  and the decision history both survive.
- Real-world additions: PII minimisation in prompts and logs, a review queue
  before any outbound send, and retention limits on the audit trail.

### 7.3 Data

- The seed database is never opened. `db.connect()` raises rather than touching
  it even if the environment variable is pointed there by mistake.
- Reads are read-only by default; writing is explicit and transactional.
- Agents cannot reach SQLite at all — only MCP tools, so the tool list *is* the
  permission list.
- The gateway key is read from `.env`, never logged, never committed.

### 7.4 Keeping the agents honest

- No shop figure may be stated that did not come from a tool this run. The
  `FigureCited` output type makes an agent name the tool behind each number, so
  a fabricated figure is visible rather than buried in prose.
- Model identity is verified on every call, not assumed from what was asked for.
- Every step is on disk with its tool arguments, so a decision can be replayed.

### 7.5 Token and cost limits — tight enough to matter, loose enough to work

A fully connected team is a loop waiting to happen: A asks B, B asks A, and
neither thinks it is doing anything wrong. Four limits bound the cost, and each
is set from what the seeded tickets actually need rather than guessed.

| Limit | Value | Why that number |
|---|---|---|
| Delegation depth | **3** | The deepest real chain here is Boss → Inventory → Accounting. A fourth hop is a loop, not work. |
| Agent turns per ticket | **14** | Observed runs finish a ticket in 2–4 turns. 14 leaves headroom for a hard ticket and still stops a spiral. |
| Requests per agent turn | **12** | Enough for a genuine chain of tool calls and a considered answer. |
| Tokens per agent turn | **250,000** | Measured, not guessed: a real Boss turn on ticket 101 came in at 120,980 and a 120,000 ceiling killed it just short of finishing. A limit that stops a turn before it completes costs the whole turn and buys nothing, so this sits well clear of the real maximum and catches genuine runaways. |
| Tool retries | **3** | The tools refuse with *actionable* text, so an agent can usually correct its arguments. The default of 1 turned a recoverable correction into a dead run. |
| Wall-clock per agent turn | **240s** | Tokens and requests do not bound *time*. A run was seen sitting on one turn for ten minutes with no new step and no error — indistinguishable from slow progress. The turn is abandoned, the timeout is written to the trail, and the run moves to the next ticket instead of taking the board down. |

**The limits return a usable message rather than an exception wherever they
can.** An agent told "you are too deep — answer from what you have and say
what you could not find out" still produces a result; one that gets an
exception produces nothing, and the ticket is lost. That is the difference
between a limit that controls cost and one that destroys work.

The prompts pull in the same direction: call a tool once per fact per turn and
reuse the result, ask for the subset you need rather than filtering a full
table in your head, think in proportion to the stakes, and stop when the
question is answered. Section 10 of the shop rules also gives the agent its own
stopping rule — more than a dozen steps on one ticket, or the same tool called
three times with identical arguments, means hand back what you have.

Real-world additions: a per-run cost ceiling in dollars rather than tokens,
caching of read-only tool results within a run, and a smaller model for the
routine lookups with `gpt-6-luna` reserved for judgement — not available here,
since the assignment requires one model throughout.

---

---

## 8. Backend routes (Problem 7)

`backend/main.py`, FastAPI. Started from the `backend/` folder exactly as the
assignment specifies, which serves the API at `http://localhost:8000`:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Every route, one line each

| Method | URL | What it does |
|---|---|---|
| `GET` | `/api/tickets` | Returns all three tickets with each one's status and whether it is open or resolved. |
| `POST` | `/api/tickets/{id}/run` | Runs the agent team on that ticket; returns a `run_id` at once and works it in the background. |
| `GET` | `/api/runs/{run_id}` | Reports how one agent run is going — running, finished or failed. |
| `GET` | `/api/events` | The board's refresh feed: recent agent steps, what each agent said and which MCP tools it called. |
| `GET` | `/api/approvals` | Lists what the agents have asked a human to approve, filterable by status. |
| `POST` | `/api/approvals/{id}/approve` | **The human's click, and the only thing in the backend that moves cash** — approves, then carries the payment out. |
| `POST` | `/api/approvals/{id}/reject` | Says no, recording who refused it. |
| `GET` | `/api/cash` | Returns the current checking balance, plus what is already approved but unpaid. |
| `POST` | `/api/reset` | Resets the working database to the pristine seed for a fresh run. |
| `GET` | `/api/health` | Confirms the backend is up and can reach the MCP server. |

### Why `main:app` needs a `sys.path` insert

`uvicorn main:app` run from `backend/` imports this file as the top-level
module `main`, not as `backend.main`, so `from backend.models import ...`
would fail outright. The repository root is inserted into `sys.path` before
any project import, which makes both entry points work — the assignment's
command and `python -m backend.main` — with neither as a special case.

### The one route that spends money

Everywhere else agents prepare and humans decide. `POST
/api/approvals/{id}/approve` is where the deciding happens, so it is the only
route that causes cash to leave the shop. It does two things in order:

1. **Approves**, by writing to the approval board directly — deliberately
   *not* through MCP, because the MCP server has no approving verb and an
   agent must not be able to reach this even if a prompt told it to. Same
   action as `scripts/approve.py`, exposed for the dashboard's button.
2. **Executes**, through the MCP payment tools, so every rule still applies.
   A refusal — insufficient cash, approval already spent, amount no longer
   matching the bill — comes back as HTTP 409 with the tool's own reason,
   rather than being swallowed into a success.

Purchase orders are approved but not placed unless the SKU, size and quantity
are supplied, because placing one moves no cash. Price overrides are approved
and nothing is executed — there is no cash in them.

### Everything else reads through MCP

No route opens SQLite. `backend/shop.py` launches the same `campus-customs`
server from the same committed `.mcp.json` the agents use, so the dashboard
and the team see one database through one door. The single exception is
`POST /api/reset`, which runs `scripts/reset_db.py` — a file copy of the
database rather than a question about the shop.

`POST /api/reset` keeps the audit trail by default. The trail is history
rather than state, and a reset concerns the shop's data, not the record of
what the agents did to it.

### Verified live

Started with the assignment's own command and exercised end to end:

- `POST /api/reset` → cash back to **$3,400**, all three tickets `open`.
- `POST /api/tickets/102/run` → returned a `run_id` immediately; the team
  raised a $2,400 rent approval in the background.
- `POST /api/approvals/1/approve` → **cash $3,400 → $1,000**, `payments` row
  stamped `Anas Nadeem`, lease rolled 2026-09-02 → 2026-10-02.
- Refusals all behave: re-approving a paid request **409**, unknown approval
  **404**, blank approver **422**, unknown ticket **404**, and a payment the
  balance cannot cover **409 with nothing written**.

`tests/test_routes.py` pins this — 12 tests against a real MCP server and the
real database, with no model and no network.

---

---

## 9. The dashboard (Problem 8)

`frontend/` — React + Vite + TypeScript. Start it from that folder:

```bash
npm run dev          # http://localhost:5180
```

It calls the backend directly at `http://localhost:8000`. There is no dev
proxy, deliberately: a proxy would make the request same-origin and hide
whether CORS is configured correctly, so the browser makes a genuine
cross-origin request and the backend's allowance is exercised every time.

**Port 5180, not Vite's default 5173.** Another project in this workspace
already holds 5173, and the first run of this dashboard served *that project's
storefront* — the browser looked perfectly healthy while showing an entirely
different application. `strictPort` now makes a clash fail loudly.

### Layout

A fixed, full-height three-column workspace, ordered the way the work flows:

| Column | Holds |
|---|---|
| **The board** | The three tickets, each with status and a *Put the team on it* button |
| **The team at work** | Per-agent summary for the latest run, then the live agent feed |
| **Waiting on you** | Approvals needing a human decision, then the team roster |

Cash sits in the masthead, because it constrains every ticket rather than one
panel, and it is the largest number on the page.

### How the agents read apart

Each of the five carries **three** consistent signals — a fixed colour as a
spine down its event cards, a two-letter monogram, and its name — so the feed
is followable by colour without reading a name on every line, and still works
in greyscale. Each event card shows who asked them, what they said as prose,
which MCP tools they called, **the figures they cited with the source tool in
the tooltip**, what blocked them, and a footer carrying the resolved model,
tokens and seconds.

That figures row is the quiet centrepiece: the shop rules forbid stating a
number that did not come from a tool, and the row is that rule made visible.

### Resolved tickets and cash

A resolved ticket **recedes rather than disappears** — green spine, `RESOLVED`
chip, 62% opacity, strikethrough. It is still part of the day but has stopped
asking for attention. `working` pulses amber and is the only animated element
on the page; `blocked` is red; `awaiting approval` is amber.

The till **flashes only when the balance actually changes**, never on the
two-second poll, so the one time it catches the eye is the time money moved.
Below it, when anything is approved but unpaid, a second line separates what is
in the bank from what is already spoken for.

Full reasoning, including what was deliberately left out, is in
**`output/design.md`**.

---

## 10. The full run (Problem 9)

One run over all three tickets, from a database reset immediately beforehand.
Opening balance **$3,400.00**, shop date **2026-08-31**.

### Outcomes

| Ticket | Final status | What happened |
|---|---|---|
| **101** Bulldog tee | `blocked` | Invoice 501 paid, lifting the vendor's shipping block; the one size-S tee ordered for $8, ETA **2026-09-05**. Blocked on that delivery — everything in the shop's power is done, but the tee is not on the shelf on 2026-08-31. |
| **102** Rent due | `resolved` | Notice checked against lease 1 and found correct; $2,400 paid; lease rolled to 2026-10-02 so the month cannot be paid twice. |
| **103** Bulk hoodies | `resolved` | Declined with a counter-offer. 8 of 20 on hand; the $264 restock refused against $160 uncommitted; $50/unit approved and a draft filed, unsent. |

### The money

| Stage | Change | Balance |
|---|---:|---:|
| Opening, after reset | — | **$3,400.00** |
| Ticket 101 — invoice 501 paid | −840.00 | $2,560.00 |
| Ticket 102 — rent on lease 1 | −2,400.00 | $160.00 |
| Ticket 103 — restock refused | — | $160.00 |
| **Closing** | **−3,240.00** | **$160.00** |

`$3,400.00 − $840.00 − $2,400.00 = $160.00`, and `cash_accounts.balance` for
`checking` reads **$160.00**. Checked, not asserted —
`scripts/build_resolved.py` exits non-zero if the two disagree, and
`scripts/fill_desk_actuals.py` refuses to write the page at all.

Three things deliberately did **not** move the balance: the $8 purchase order
(a commitment; cash leaves when the vendor invoices), the $264 restock
(refused, so it never became a payment), and the $50 price override (a price,
not a payment).

### Human decisions

Five approval requests, decided by a human outside anything an agent can reach:

| # | What | Amount | Decision |
|---|---|---:|---|
| 1 | invoice payment, invoice 501 | $840.00 | approved → paid |
| 2 | rent payment, lease 1 | $2,400.00 | approved → paid |
| 3 | purchase order, 1 tee | $8.00 | approved → placed, no cash |
| 4 | price override, ticket 103 | $50.00/unit | approved, no cash |
| 5 | purchase order, 12 hoodies | $264.00 | **rejected** — $160 will not cover it |

Request 5 is the seeded cash squeeze landing exactly where the data said it
would, and being refused out loud rather than part-funded or quietly dropped.

### Plan versus run

The expected plans were written in Problem 6 **before** this run and were not
edited afterwards. Side by side in `output/desk_tickets.html`:

- **Ticket 103 — 3 of 3.** The run followed the plan step for step, including
  calling Inventory rather than Accounting first on a ticket typed
  `price_override`, which the plan had flagged as the call most likely to be
  got wrong.
- **Ticket 102 — 1 of 2, and the miss was the plan's fault.** The expected
  `Facilities → Accounting` hop did not happen; both agents read
  `get_cash_position` themselves instead. Shop rule 7 says not to delegate what
  a tool in front of you already answers, so the team was right and the plan
  was wrong.
- **Ticket 101 — 2 of 3, and the miss matters.** Customer Service was never
  called, so **Tauhid Zaman was never written to**. The shop ordered his tee
  and told him nothing. The clearest failure of the run, and only visible
  because the plan existed to compare against.

### Provenance

- **25 steps appended** to `output/audit_trail.json` across four run ids —
  earlier runs were not overwritten, and the file now holds every run since
  Problem 5.
- **Every step resolved to `gpt-6-luna-2026-09-22`**, checked against what the
  gateway reported rather than what was requested.
- Artefacts: `output/resolved_tickets.json`, `output/desk_tickets.html`
  (Expected and Actual side by side, plus the Cash tab),
  `output/resolved_board.html` (board screenshots, self-contained).

---

## 11. What this harness covers

| Piece | Where |
|---|---|
| The nine tables | §1, with the three tickets' linkage in §2 |
| Facts agents must compute, never recall | §3 |
| The MCP tools — all fourteen, with the tables each uses | §4 (the first three) and §6.2 (the full table) |
| Connecting and smoke-testing the server | §5 |
| The five agents, their prompts and the delegation graph | §6 |
| The audit trail and the model check | §6.3, §6.4 |
| Safety and guard rails, including token limits | §7 |
| The API routes, one line each | §8 |
| The dashboard | §9, with full design reasoning in `output/design.md` |
| The full three-ticket run and its cash | §10 |

### The rules, in one place

1. The seed database is never opened — `db.connect()` raises rather than touch it.
2. Every shop fact comes from the MCP server; nothing else reads SQLite.
3. `desk.date_today` is "today"; the wall clock is never consulted for shop logic.
4. A vendor holding an unpaid invoice ships nothing.
5. **No agent can approve spending** — the verb does not exist on the MCP server.
6. A payment moves cash, the `payments` row and the invoice or lease together, or not at all.
7. The balance may never go negative; the pay tools refuse and write nothing.
8. Cash only goes out — revenue is not modelled.
9. Nothing is ever sent to a customer or a vendor; there is no send tool.
10. `.env` is never committed; `.env.example` carries placeholders.
11. Every agent runs on `gpt-6-luna`, and the **resolved** name is checked on every call.

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
