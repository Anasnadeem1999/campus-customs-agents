# HW5 progress

Status of each problem, and the result of the final run. Earlier drafts and
superseded figures have been removed so that this file describes one thing:
the submission as it stands.

| # | Problem | Status |
|---|---|---|
| — | Setup: repo, data, reset script, model check | Done |
| 1 | Vibe coder prompts (`AI_prompts.md`) | Done |
| 2 | Study the database; start `output/harness.md` | Done |
| 3 | Build the MCP server | Done |
| 4 | Connect the MCP server; smoke-test each tool | Done |
| 5 | Agent team (5 agents, PydanticAI) + the tools they need | Done |
| 6 | Plan the three tickets (`output/desk_tickets.html`) | Done |
| 7 | Backend routes (FastAPI, `backend/main.py`) | Done |
| 8 | Agent dashboard (React + Vite + TypeScript) | Done |
| 9 | Resolve the tickets: full run, cash ledger, artefacts | Done |
| 10 | Reflection tab, written by the owner | Done |
| 11 | Submit to GitHub (public repo) | Done |
| A | *Follow-up:* full end-to-end audit and re-run | Done |
| B | *Follow-up:* the owner's shop rules, and the final run | Done |

---

## The final run

Reset from the pristine seed, then all three tickets worked with **every
payment and purchase order put to the owner as a question**. Three requests
were raised and three were answered; none was auto-approved.

| Ticket | Final status | What happened |
|---|---|---|
| **101** Bulldog tee | `resolved` | Invoice 501 paid → vendor unblocked → tee ordered at its real **$8.00** unit cost → shop clock advanced to the **2026-09-05** ETA → **order received, `inventory.qty` 0 → 1** → Tauhid drafted a reply saying it is ready. |
| **102** Rent due | `resolved` | Notice checked against lease 1, Accounting confirmed affordability, $2,400 paid, lease rolled to 2026-10-02. |
| **103** Bulk hoodies | `resolved` | Declined with an offer: 8 of 20 on hand, the $264 restock refused, Customer Service drafted the offer of the eight. |

### The money

| Stage | Change | Balance |
|---|---:|---:|
| Opening, after reset | — | **$3,400.00** |
| Ticket 101 — invoice 501 paid | −840.00 | $2,560.00 |
| Ticket 102 — rent on lease 1 | −2,400.00 | $160.00 |
| Ticket 103 — restock refused | — | $160.00 |
| **Closing** | **−3,240.00** | **$160.00** |

`cash_accounts.balance` reads **$160.00**. Checked rather than asserted:
`scripts/build_resolved.py` exits non-zero on a mismatch, and
`scripts/fill_desk_actuals.py` refuses to write the page at all.

Receiving the tee raised **invoice 502 for $8.00** from Bulldog Print Co — a
liability the shop now owes, not cash that has left the account, and
deliberately absent from the closing balance.

### Cost

| Ticket | Agent turns | Tokens |
|---|---:|---:|
| 101 | 11 | 619,229 |
| 102 | 6 | 258,145 |
| 103 | 7 | 371,465 |
| **Total** | **24** | **1,248,839** |

Every step resolved to `gpt-6-luna-2026-09-22`, checked against what the
gateway reported rather than what was requested.

---

## How the plans compared

The Expected Plans in `output/desk_tickets.html` are the owner's own, and the
Actual sections are filled separately from the run. In the final run **all
three tickets matched the plan**: the planned first call was made on each
(Inventory, Facilities, Inventory), every planned delegation happened, and
every agent the plan excluded stayed out.

The plan's one blind spot, found by running it: it stopped at *"order placed,
ETA 2026-09-05"* and treated that as finished. The owner's shop rule 7 says
placing an order is not the product arriving, which is why the shop now has
tools to advance the clock and receive stock.

---

## What the rules were worth

The same three tickets were run before and after the shop rules were rewritten
in the owner's words:

| | Before the rules | After |
|---|---:|---:|
| Ticket 103 | 995,949 tokens, unresolved | resolved |
| Ticket 101 | "resolved" with the shelf empty | resolved with stock on hand |

Same model, same tools, same data. A clear definition of *done* changed the
outcome more than any change to the architecture would have.

---

## Verification

- **50 tests** pass, with no model and no network. They assert every refusal
  the shop depends on: no approval, pending approval, reused approval,
  redirected approval, wrong amount, insufficient funds, blocked vendor,
  duplicate order, receiving before the ETA, the clock running backwards, the
  seed database, and the absence of any send or approving tool.
- **MCP smoke test** passes 8 of 8 read tools, each cross-checked against
  independently written SQL on a disposable clone of the seed.
- **Seed database untouched** — sha256 `23686a90d698f7fa`, zero payments,
  shop date still 2026-08-31.
- `.env` has never been committed on any branch, and the real key appears in
  no tracked file.

## A note on the audit trail

`output/audit_trail.json` holds **191 steps across 33 runs**, going back to
Problem 5. That is deliberate: Problem 5 requires the file to append rather
than be wiped, so the development history is evidence of compliance rather
than clutter. The file opens with a `submission` block naming the final run —
**steps 168–191** — with its outcomes, cash and token figures, so there is no
ambiguity about which run is being submitted.
