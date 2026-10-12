# Campus Customs — Homework 5

A **multi-agent operations team** that runs the Campus Customs shop. Open
tickets land on a board — customer orders, rent notices, unpaid bills,
discount requests — and a team of agents works them to resolution while a
human watches and approves.

**This homework is independent of HW4.** Nothing carries over: not the file
layout, not the conventions, not the assumptions. HW4 was a customer-facing
storefront; HW5 is an internal operations console. Everything here comes from
the HW5 brief and the HW5 problem prompts only.

Work **one problem at a time**.

## The three pieces

| Piece | Tech | Role |
|---|---|---|
| MCP server | Python + `mcp` | The only door to the database. Exposes shop tools. |
| Backend | Python + FastAPI + PydanticAI | The agent team, plus the HTTP/stream API. |
| Dashboard | React + Vite + TypeScript | Human watches the agents work and approves requests. |

## The agents

Fully connected team — **any agent may delegate to any other agent.**

| Agent | Owns |
|---|---|
| **Boss** | Reads each ticket, decides who works it, makes the final call. |
| **Inventory** | Stock by SKU and size, shortfalls, which vendor can restock. |
| **Accounting** | Cash, invoices, margins; prepares payments and POs for approval. |
| **Facilities** | Shop space: leases, rent, landlord matters. |
| **Customer Service** | Drafts messages to customers. |

## Hard constraints (from the user)

1. **`data/campus_customs.db` is read-only, forever.** It is the pristine seed.
   All agent writes go to **`data/campus_customs_new.db`**; the MCP server and
   backend point only at that working copy.
2. **Reset the database before any full ticket-resolution run** —
   `python scripts/reset_db.py`.
3. **`desk.date_today` is "today"** for the shop. Overdue is measured against
   that field, never against the wall clock.
4. **Vendor lead times come from the `vendors` table.** A vendor will not ship
   anything new while it still has an unpaid invoice.
5. **Every payment needs human approval.** No agent pays anything on its own.
6. **A payment must write through to the database** — the cash account, the
   `payments` row, and the invoice/lease status all move together.
7. **The pay tool refuses when cash is insufficient.** The balance must never
   go negative.
8. **Cash only goes out.** Revenue is not modelled in this homework.
9. **Never email a customer or contact a real vendor.** Drafts stay on the board.
10. **Never commit `.env`.** Ship `.env.example` with placeholders only.
11. Final submission is a push to a **public** GitHub repo.

## Model policy — strict

Every agent runs on **`gpt-6-luna`** through the course Portkey gateway.
Points are deducted if any other model appears in the code or in a run.

> **Gotcha, verified 2026-10-11:** the Portkey gateway does *not* error on an
> unknown model name — it silently falls back to `gpt-5.6-luna`. A typo would
> therefore cost points without any visible failure. Every call must assert
> that the **resolved** `response.model` starts with `gpt-6-luna`, and the
> resolved name is recorded in the audit trail.

## Database (`data/campus_customs.db`, 9 tables)

| Table | Shape |
|---|---|
| `desk` | `date_today`, `notes` — the shop's clock |
| `tickets` | `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at` |
| `inventory` | PK (`sku`, `size`) → `name`, `qty`, `location` |
| `pricing` | `sku` → `unit_cost`, `list_price` |
| `vendors` | `id`, `name`, `specialty`, `lead_days` |
| `leases` | `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes` |
| `invoices` | `id`, `vendor_id`, `amount`, `due_date`, `status`, `description` |
| `payments` | `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by` |
| `cash_accounts` | `name` → `balance`, `date` |

### The seeded scenario

Shop date is **2026-08-31**; checking holds **$3,400.00**. Three open tickets:

- **101 — customer_order.** Tauhid Zaman wants `CC-TEE-WHITE` size S, qty 1.
  That size is at **qty 0**. Restocking means Bulldog Print Co (apparel
  reprint, 5-day lead) — but that vendor holds **invoice 501 for $840, due
  2026-08-28, still open**, so it is overdue and the vendor will not ship.
- **102 — rent_notice.** Chapel Street shop rent **$2,400 due 2026-09-02**.
- **103 — price_override.** Yale AI Club wants 20 × `CC-HOOD-NAVY` size M at a
  bulk discount. Only **8** are in stock; unit cost $22 against a $58 list.

Note the cash squeeze: $840 + $2,400 = $3,240 against $3,400 on hand. Both can
be paid, but only $160 survives — so any third spend has to be refused.

## Working notes

- `AI_prompts.md` — **required deliverable (Problem 1).** The complete log of
  prompts typed into the vibe coder. One section per problem, each carrying
  the problem number and title, at least one prompt quoted verbatim, and a
  follow-up prompt where one was needed plus a note on what the initial prompt
  was missing. Update it **as part of each problem's work**, never
  reconstructed afterwards. Prompts are quoted exactly as typed — never
  invent, tidy, or paraphrase one; if a problem needed no follow-up, say so
  and explain why the first prompt sufficed.
- `docs/progress.md` — status of each problem.
- The assignment arrives one numbered problem at a time. Don't pre-build files
  a problem hasn't asked for yet, and don't guess at the numbering ahead.
