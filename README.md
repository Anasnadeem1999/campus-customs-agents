# Campus Customs — a multi-agent operations desk

A five-agent team that runs a small Yale merchandise shop on Chapel Street.
Tickets land on a board, the agents work them, and **a human approves every
payment** before a cent moves.

Built for MGT 409 *AI Foundations for Managers*, Homework 5.

| Piece | Tech | Role |
|---|---|---|
| MCP server | Python + `mcp` | The only door to the database. Fourteen shop tools. |
| Backend | Python + FastAPI + PydanticAI | The agent team, plus the HTTP API. |
| Dashboard | React + Vite + TypeScript | Where a human watches the team and approves. |

Every agent runs on **`gpt-6-luna`** through the course Portkey gateway, and
the *resolved* model name is checked on every call.

---

## The shop, in one paragraph

It is **2026-08-31**. Checking holds **$3,400.00**. Three tickets are open:
Tauhid Zaman wants a tee in a size that is at zero; the landlord says rent is
due; the Yale AI Club wants 20 hoodies when 8 are on the shelf. Restocking
either garment means Bulldog Print Co — which holds an **$840 invoice, three
days overdue**, and will not ship until it is paid. Rent is **$2,400**.
$840 + $2,400 = $3,240 against $3,400, so two things can be paid and the
third has to be refused. That squeeze is the whole exercise.

---

## Setup

Requires **Python 3.13+** and **Node 20+**.

```bash
git clone <this repo>
cd HW5

python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cd frontend && npm install && cd ..
```

### The one thing you must do by hand

```bash
cp .env.example .env
```

Then open `.env` and put a real key in `PORTKEY_API_KEY`. **The real `.env` is
not in this repository and never will be** — only `.env.example`, which holds
placeholders.

Without a key the MCP server, the tests and the dashboard still work; only the
agent runs need the gateway.

### Point the MCP config at your machine

`.mcp.json` contains an absolute path to this project's virtualenv, which does
not survive a clone. Regenerate it:

```bash
python scripts/setup_mcp_config.py
```

---

## Copying the original database to the working copy

**Two database files ship in `data/`, and the distinction matters:**

| File | What it is |
|---|---|
| `data/campus_customs.db` | The **pristine seed**. Never written to, by anything, ever. |
| `data/campus_customs_new.db` | The **working copy**. Every agent write lands here. |

The working copy in this repository is **as the three-ticket run left it** —
$160 in checking, two payments written, invoice 501 paid, tickets 102 and 103
closed. That is deliberate: clone the repo, start the dashboard, and you see
the finished board without running anything.

**To copy the original over the working copy and start clean:**

```bash
python scripts/reset_db.py
```

That script clones the seed to the working copy, hashes the seed before and
after to prove it was not touched, clears stale WAL/SHM sidecars, and prints
the row counts, the shop date and the opening balance. The MCP server refuses
to open the seed at all — `db.connect()` raises rather than touch it, even if
the environment variable is pointed there by mistake.

### Reset before any full three-ticket run

```bash
python scripts/reset_db.py
rm -f output/board/approvals.json output/board/drafts.json   # clear the approval board too
```

Clearing the board matters: an approved request left pointing at an invoice
the reset has just reopened is a confusing half-state. `POST /api/reset` does
both for you.

---

## Running it

Three processes. Each in its own terminal.

### 1. The MCP server

Usually you do **not** start this by hand — the backend and the vibe coder
both launch it from `.mcp.json` over stdio. To run it directly:

```bash
python -m mcp_server.server
```

To prove it works end to end without a model:

```bash
python scripts/mcp_smoke.py       # speaks real MCP, checks every field against SQLite
```

### 2. The FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Serves the API at **http://localhost:8000**. Check it with
`curl http://localhost:8000/api/health`.

> Run it from `backend/` exactly as above. The repository root is added to
> `sys.path` at the top of `main.py` so that `main:app` works from that
> directory as well as `python -m backend.main` from the root.

### 3. The React board

```bash
cd frontend
npm run dev
```

Opens at **http://localhost:5173** and calls the backend at
`http://localhost:8000` directly. If 5173 is already in use, Vite moves to
5174 and prints the port it bound; the backend accepts any localhost origin,
so either works without touching CORS.

---

## Working the tickets

### From the dashboard

1. **Reset shop** in the header, for a clean board.
2. **Put the team on it** on a ticket. Agent cards stream into the middle
   column as the team works.
3. The team stops at the approval gate and the request appears under
   **Waiting on you**.
4. **Approve & pay** — the till drops. That click is the only thing in the
   whole system that moves money.
5. **Put the team on it** again so the team acts on your decision and closes
   the ticket out.

### From the command line

```bash
python -m backend.run_tickets                  # resets, then works every open ticket
python -m backend.run_tickets --ticket 102     # one ticket
python -m backend.run_tickets --no-reset       # continue after approving something
python -m backend.run_tickets --dry-run        # wiring check, no model calls

python scripts/approve.py --list               # read what the team asked for
python scripts/approve.py --id 1 --by "Your Name"
python scripts/approve.py --id 5 --reject --by "Your Name" --why "cannot fund it"
```

A full run is: **reset → run → approve → run again**.

---

## The approval gate

> **No agent can approve its own spending, and this is structural rather than
> a line in a prompt.**

`request_approval` lets an agent ask. **Nothing on the MCP server approves** —
the verb lives in `scripts/approve.py` and in one HTTP route, both outside
anything an agent can reach. An agent cannot approve a payment because the
action does not exist in its world.
`tests/test_shop_tools.py::test_no_mcp_tool_can_approve` fails the build if an
approving tool is ever added.

The payment tools refuse — writing nothing at all — when the approval is
missing, still pending, already spent, for a different record, or when the
balance will not cover it. A payment moves the cash balance, the `payments`
row and the invoice or lease status inside **one transaction**, or it does
none of them.

Nothing is ever sent to a customer or a vendor. There is no send tool, and a
test asserts that none appears.

---

## Tests

```bash
python -m pytest tests/ -q      # 38 tests
```

They run against the real MCP server and the real working database — a payment
rule tested only against a mock is not tested — and they use no model and no
network. The suite copies the shop before it starts and puts it back
afterwards, so running the tests does not disturb a completed run.

---

## What to look at

| File | What it holds |
|---|---|
| **`output/desk_tickets.html`** | **Open this first.** Per-ticket Expected (written before the run) vs Actual, a Cash tab reconciled against the database, and the Reflection. Double-click it. |
| `output/resolved_board.html` | The React board per ticket, screenshots embedded. Double-click it. |
| `output/harness.md` | The full working notes: tables, all 14 MCP tools with the tables each uses, the five agents, the API routes, the dashboard, the safety rules. |
| `output/design.md` | Why the dashboard looks the way it does. |
| `output/resolved_tickets.json` | Machine-readable run record: status, outcome, every agent's contribution, every human approval. |
| `output/audit_trail.json` | Every agent step ever run, appended never overwritten. |
| `AI_prompts.md` | Every prompt typed into the vibe coder, per problem. |
| `backend/prompts/` | The shop rules and the five role briefs. |

---

## Layout

```
AI_prompts.md            every prompt typed, per problem
requirements.txt
.env.example             placeholders only — the real .env is never committed
.gitignore
.mcp.json                MCP server registration (regenerate with scripts/setup_mcp_config.py)
README.md
data/
  campus_customs.db      the pristine seed — never written to
  campus_customs_new.db  the working copy — every agent write lands here
mcp_server/
  server.py              the MCPServer instance and all fourteen tools
  db.py                  path resolution, the seed guard, transactions
  board.py               approvals, drafts and POs the 9-table schema cannot hold
  readme.md
backend/
  main.py                FastAPI routes
  models.py              agent output types and audit records
  agent_team.py          the five agents, fully connected
  audit.py               the append-only audit trail
  model_config.py        the gpt-6-luna check
  run_tickets.py         CLI runner
  shop.py                the backend's MCP client
  prompts/
    shop_rules.md        loaded first by all five agents
    boss.md
    inventory.md
    accounting.md
    facilities.md
    customer_service.md
frontend/                React + Vite + TypeScript dashboard
scripts/
  reset_db.py            copy the seed over the working copy
  approve.py             the human half of the approval gate
  mcp_smoke.py           prove the MCP server over real stdio
tests/                   38 tests
output/
  harness.md             the working notes
  mcp_smoke.json         per-tool evidence, checked against SQLite
  desk_tickets.html      Expected vs Actual, Cash, Reflection
  design.md              dashboard design reasoning
  resolved_tickets.json  the run record
  resolved_board.html    board screenshots
  audit_trail.json       every agent step
  github_url.txt         this repository's URL
```

---

## The run this repository records

Reset to $3,400, then all three tickets worked with every payment put to the
owner as a question.

| Ticket | Final status | What happened |
|---|---|---|
| 101 Bulldog tee | `resolved` | Invoice 501 paid, vendor unblocked, tee ordered at its real $8 unit cost (ETA 2026-09-05), customer drafted a reply. |
| 102 Rent due | `resolved` | Notice checked against the lease, $2,400 paid, lease rolled to 2026-10-02. |
| 103 Bulk hoodies | `resolved` | Priced partial offer — 8 of 20 at the approved $42, the $264 restock refused, draft filed. |

```
$3,400.00  opening
  −840.00  invoice 501
−2,400.00  rent, lease 1
─────────
  $160.00  closing, and cash_accounts.balance reads $160.00
```

Five approval requests were put to the owner and five were answered — including
one **rejected**: Accounting asked for the tee's purchase order at $1.00 when
`pricing.unit_cost` is $8.00 for one unit. The team re-raised at the correct
figure. `request_approval` validates invoice and rent amounts against the
database but has nothing to check a purchase-order amount against, so the human
gate was the only control that caught it.

Ticket 101 is `resolved` because the *desk* is finished — paid, ordered,
customer told. The tee itself arrives 2026-09-05, and with these tools it never
actually will: there is no tool that receives stock and none that advances
`desk.date_today`. That limitation, and two others, are analysed in the
Reflection tab of `output/desk_tickets.html`.
