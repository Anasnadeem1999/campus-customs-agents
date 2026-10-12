# HW5 progress

The assignment hands over its problems one at a time, so this table grows as
each new problem arrives rather than being planned out in advance.

| # | Problem | Status |
|---|---|---|
| — | Setup: repo, data, reset script, model check | Done |
| 1 | Vibe coder prompts (`AI_prompts.md`) | Done |
| 2 | Study the database; start `output/harness.md` | Done |
| 3 | Build the MCP server (FastMCP, three tools) | Done |
| 4 | Connect the MCP server; smoke-test each tool | Done |
| 5 | Agent team (5 agents, PydanticAI) + 7 new MCP tools | Done |
| 6 | *awaiting the next problem from the user* | — |

## Setup — repo, data, reset script, model check

Done before the numbered problems began.

- Unzipped the supplied archive to `data/campus_customs.db` (53 KB, 9 tables).
- `scripts/reset_db.py` copies the seed to `data/campus_customs_new.db`,
  hashes the seed before and after to prove it was not touched, clears stale
  WAL/SHM sidecars, and prints row counts plus cash and `date_today`.
- `.gitignore` excludes `.env`, the working DB copy, `.venv/`, `output/`.
  The seed DB *is* committed — it is the assignment's input and the grader
  needs it to run anything.
- `.env.example` carries placeholders only.
- **Model verified against the live gateway:** `gpt-6-luna` resolves to
  `gpt-6-luna-2026-09-22`. A deliberately wrong name did *not* error — it
  silently answered as `gpt-5.6-luna-2026-07-09`. Hence the runtime assertion
  on `response.model` recorded in CLAUDE.md.

## 1 — Vibe coder prompts

`AI_prompts.md` is the complete log of prompts typed into the vibe coder, in
the format the problem specifies: one section per problem, carrying the
problem number and title, at least one verbatim prompt, and a follow-up prompt
with a note on what the initial prompt was missing.

- Rewrote the file from its earlier shape (grouped by work done) into the
  required per-problem structure.
- The three prompts that preceded the assignment's own numbering — working
  folder, project brief, readiness check — are kept as a **Setup** section, so
  the brief and the ground rules stay in the log.
- Sections with no follow-up say so and explain why the first prompt was
  enough, rather than inventing a prompt that was never typed.
- The file is updated as part of each problem's work, not reconstructed at the
  end.

## 2 — Study the database; start `output/harness.md`

- Read all nine tables field by field (types, PKs, the two FKs on `tickets`,
  the FK on `invoices`), and refreshed `data/campus_customs_new.db` from the
  seed.
- `output/harness.md` now carries a section per table — real field list plus a
  line on why the agent team cares — followed by the three-ticket linkage
  study, the cross-ticket analysis, and the list of figures agents must
  recompute rather than recall. It is the file that grows each problem.
- **Fixed a trap from setup:** `.gitignore` had excluded `output/`, which
  would have kept the harness deliverable out of the public repo. Rule
  removed, comment left in its place.

### What the data actually says

- Vendor 1 (Bulldog Print Co) is the **only** apparel vendor, and it is
  blocked by invoice 501 — $840, 3 days overdue. Tickets 101 *and* 103 both
  need an apparel reprint, so that one invoice gates both.
- Ticket 103 is short by **12** hoodies, not merely a discount question.
- Cash is the binding constraint: $3,400 covers the $840 invoice and the
  $2,400 rent with **$160** left, so the $264 hoodie restock cannot be funded.
  The pay tool's insufficient-funds refusal sits on the main path.

## 3 — Build the MCP server

- `mcp_server/server.py` — FastMCP instance plus three read tools:
  `check_stock_by_size`, `find_restock_vendors`, `check_rent_due`.
- `mcp_server/db.py` — resolves the working copy, raises if asked to open the
  seed, and reads the shop's clock from `desk.date_today`.
- `mcp_server/readme.md` — purpose, database file, the three tools.
- `output/harness.md` section 4 — one tool to one ticket (stock-by-size → 101,
  restock vendors → 103, rent due → 102), each with the table it reads and a
  one-sentence reason tied to that ticket. Revised from an earlier many-to-many
  listing after the user pointed out the instruction reads singular; the
  101/103 overlap is kept as a note below the table.
- Pinned `mcp>=1.2,<2`: the 2.x SDK renamed `FastMCP` to `MCPServer`.

Verified without running the server: all three tools register through
`list_tools()`; each returns the right figures off the working copy (101 →
shortfall 1, 103 → shortfall 12 with 8 available, apparel vendor
`can_ship: false` blocked by $840, rent $2,400 due in 2 days); and pointing
`WORKING_DB_PATH` at the seed raises `ShopDataError` instead of opening it.

## 4 — Connect the MCP server; smoke-test each tool

- `.mcp.json` registers the server as `campus-customs` (venv interpreter,
  `-m mcp_server.server`, `PYTHONPATH` and both DB paths in `env`).
- `scripts/mcp_smoke.py` reads that config, launches the server from it, and
  speaks real MCP over stdio — initialize, `list_tools`, `call_tool`.
- `output/mcp_smoke.json` records, per tool: the prompt, the tool name, the
  arguments, the full output, and a field-by-field cross-check against the
  working database using independently written SQL.
- **21 of 21 fields matched; overall PASS.** No model calls.
- **Connection method chosen:** project-scoped `.mcp.json`, committed, with
  `campus-customs` pre-approved by name in `.claude/settings.json` — it
  travels with the submission and writes no global state.
  `scripts/setup_mcp_config.py` regenerates the config per machine, since the
  absolute venv path does not survive a clone.
- **Test prompts written**, one per tool, each stored in the evidence next to
  the expected answer in plain English.
- The tools are not live in the session that wrote the config — Claude Code
  reads `.mcp.json` at startup. Noted in the evidence under
  `vibe_coder_connection`; a restart makes them callable.


### Connection confirmed live (after a session restart)

The restart Problem 4 said was needed has happened, so the caveat above is
settled: the vibe coder now exposes `mcp__campus-customs__check_stock_by_size`,
`find_restock_vendors` and `check_rent_due`, and all three were called from the
chat with the harness's own arguments. Each payload is structurally identical
to the stored `tool_output` for its case — checked by equality, not by eye.
`output/mcp_smoke.json` → `vibe_coder_connection` carries the live payloads and
now reads `confirmed live in the vibe coder`.

## 5 — The agent team, and the tools it needs

**Five agents, fully connected**, each with its own prompt file under
`backend/prompts/` and all loading the shared `shop_rules.md` first. Boss,
Inventory, Accounting, Facilities, Customer Service; any agent may ask any
other, and the delegation is real — Customer Service can ask Accounting without
routing through the Boss.

**Seven new MCP tools, 14 in total.** `list_tickets`, `get_cash_position`,
`list_invoices`, `quote_discount`, `request_approval`, `list_approvals`,
`pay_invoice`, `pay_rent`, `update_ticket`, `draft_customer_message`,
`place_purchase_order`. All nine tables are now reachable, and nothing in
`backend/` touches SQLite — the shop is reached only through MCP.

**The approval gate is structural, not a prompt instruction.** `request_approval`
lets an agent ask; nothing on the MCP server approves. The verb lives in
`scripts/approve.py`, outside anything an agent can reach, and a test fails the
build if an approving tool is ever added.

**`output/audit_trail.json` appends.** Run headers and steps in separate lists
joined by `run_id`. Each step carries the agent, who delegated to it, the task,
every tool call *with its arguments* and result, the conclusion, the resolved
model, tokens and timings. Failures are appended too.

### Verified against the live gateway

- Full human-in-the-loop cycle on ticket 102: team raised a $2,400 approval and
  stopped → approved → resume run paid it. Cash $3,400 → $1,000, `payments` row
  stamped `Anas Nadeem` and `2026-08-31`, lease rolled to 2026-10-02.
- Invoice path likewise: approval → payment → cash $3,400 → $2,560, invoice 501
  `paid`, which lifts Bulldog Print Co's shipping block.
- `tests/test_shop_tools.py` — **17 passing**, no model, no network. Every
  refusal: no approval, pending, reused, redirected, wrong amount, insufficient
  funds, blocked vendor, seed database, no send tool.

### Five things the live runs forced

1. **`mcp<2` pin removed.** pydantic-ai's MCP client needs v2, so the server
   moved to `MCPServer` and the Problem 4 smoke script was updated for v2's
   snake_case fields. Still 21 of 21.
2. **`reasoning_effort="none"` is mandatory.** The gateway refuses function
   tools outright otherwise; every agent calls tools, so nothing ran at all.
   Still resolves to `gpt-6-luna-2026-09-22`.
3. **`awaiting_approval` tickets were invisible to resume runs** — the team
   parked a ticket at the gate and the run meant to finish it could not see it.
4. **`uncommitted` double-counted an approval against itself**, so the team
   called two approvals a conflict and paid neither when $3,400 covered both.
   `get_cash_position(for_approval_id=...)` now answers it; regression test added.
5. **An agent turn could hang with no bound.** Token and request limits do not
   bound time; a turn sat for ten minutes with no error. Per-turn wall-clock
   timeout added, written to the trail as a failed step.

### The full cycle, verified end to end

Shop rules and the five agent prompts **approved by the user**, then one clean
cycle run from a reset database:

| Ticket | Outcome | What actually happened |
|---|---|---|
| 101 | `blocked` | Invoice 501 paid under approval 1, lifting the vendor's shipping block. Blocked pending a purchase-order approval for the size-S tee. |
| 102 | `resolved` | Rent paid in full under approval 2. |
| 103 | `blocked` | 8 of 20 hoodies on hand; the $264 restock cannot be funded from $160 uncommitted. Customer draft filed, not sent. |

Database after the run — the seeded squeeze, exactly as predicted:

- cash **$3,400 → $160** ($840 + $2,400 = $3,240 out)
- invoice 501 `paid`; lease rolled 2026-09-02 → 2026-10-02
- two `payments` rows, both `approved_by: "Anas Nadeem"`, both `paid_at: 2026-08-31`
- the third spend, the $264 restock, is correctly refused for want of cash

Audit trail: **19 steps across 2 runs, appended not wiped**, 146 tool calls
recorded with their arguments, all five agents exercised, every step resolving
to `gpt-6-luna-2026-09-22`, 827,321 tokens total.

### Two more defects the final runs found

6. **Asking the Boss crashed the asker.** The Boss returns a
   `TicketResolution` and everyone else a `ColleagueReply`; the delegation
   path read `.answer` off both and raised `AttributeError`, losing the turn.
   In a fully connected team, asking the Boss is ordinary — now handled
   explicitly and covered by `tests/test_agent_wiring.py`.
7. **A paid bill was reported as unaffordable.** Once the rent was paid, $160
   remained, so a balance check against the $2,400 approval said "insufficient
   funds" and the team called a settled ticket blocked — which would send the
   owner chasing money they had already spent. `get_cash_position` now answers
   `already_paid` before the arithmetic can mislead.

Also raised the per-turn token ceiling from 120,000 to 250,000: a real Boss
turn on ticket 101 measured 120,980 and was killed just short of finishing,
which costs the whole turn and buys nothing.

### Open

Nothing outstanding on Problem 5. Awaiting the next problem.
