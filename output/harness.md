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
