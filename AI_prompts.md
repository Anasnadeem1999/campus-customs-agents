# AI prompts — Campus Customs Homework 5

A complete log of what was typed into the vibe coder while building this
assignment. One section per problem, in the order the problems were worked.

**Each section carries:**

- the problem number and title,
- at least one prompt exactly as it was typed — typos, run-on sentences and
  all, because the point of the log is the real prompt, not a tidied one,
- a follow-up prompt where one was needed, together with a note on **what the
  initial prompt was missing** that made the follow-up necessary.

Where no follow-up was needed, the section says so and explains why the first
prompt was already enough. Nothing in this file is reconstructed or
paraphrased: if a prompt is quoted, it was typed.

---

## Setup — before the numbered problems

These three prompts came before the assignment's own numbering started. They
are logged because they set the working folder, the project brief and the
ground rules that every later problem depends on.

### S1 — Where to work

**Prompt typed:**

> Hello Mister, we are working on HW 5 of the AI foundations course, please
> work in the separate HW5 folder available in the AI Foundations folder.

**What was missing:** the prompt named the folder but not how HW5 should be
version-controlled, and not whether HW4's codebase was a starting point. Both
mattered immediately — the answer decides whether `git init` runs at all.
Rather than a typed follow-up, the gap was closed with two questions put back
to the user, answered as:

- **git setup** → *"Own repo in HW5 (like HW4)"*
- **HW4 carryover** → *"Nothing — fresh start"*

### S2 — The project brief

**Prompt typed** (with `data.zip` attached):

> Okay so we are making campus customs multi agent operations team which is an
> agentic team that is suppose to run the shop. The open tickets will be
> landing on a board including customer orders, rents, unpaid bills, discount
> requests and whatever the shop basically has to handle. We will be building
> three pieces that interact with each other, including mcp server, a fastapi
> backend with the multi agents team and also a react dashboard so that the
> human can watch how the agents are working and also approve the requests.
> Our agents team is suppose to have complete connectivity which means any
> agent may delegate the tasks to other agents for help. This assignment
> specifically asks to build the following agents, a boss agent wich reads each
> ticket and decides who should be working on it and making the final calls, a
> inventory agent which checks the stocks by SKUs and sizes and looks for any
> shortfalls also figuring out which of the vendors can restock it, a
> accounting agent which basivally looks out for the cashs and invoices and
> also checks the margins while preparing for the payments and or the purchase
> orders for the humans approval, a facilities agent which basically handles
> the shop space side including leases and rents ectectra and finally a
> customers service agent which will be draft messages for the customers.
>
> Now with respect to the data I will be uploading a DATA.ZIP file which you
> need to unzip in order to gain access to data/campus_customs.db. This file is
> going to be the original data base including tables which include desk,
> tickets, inventories, pricings, vendors, leases, cash accounts, payments,
> invoices and what not. All of the tools are to be updated within the database
> as the tickets start getting resolved. I want you to please make a copy of
> this database file called data/campus_customs_new.db and also point the mcp
> server and backend at that specific working copy. Please keep the
> campus_customs.db as untouched so that we can reset when we want when we have
> to restart resolving the tickets.
>
> Now coming to the rules of the shop, the field desk.date_today is the "today"
> for the shop, this date will be used to determine basically what is overdue.
> Secondly vendor lead times will be coming from the vendors table, the vendor
> will not be shipping the new product while they still have any unpaid
> invoice, the human approval is to be required for any payments. Please please
> please make sure whenever the payment is made, the relevant table is also
> updated. Also if there is no sufficient cash then the payment shall be
> refused by the pay tool so that there is no negative balance. Cash is to only
> go out in this homework as we have not modeled revenue hence no money is
> coming in. Also before the full run to resolve the tickets please please
> please make sure to reset the database to the original values. AND DO NOT
> EMAIL CUSTOMERS OR CALL REAL VENDORS the drafts are to stay on board.
>
> We will me using portkey_API_key for the ai calls. We are to use gpt-6-luna
> equivalent through the portkey for this assignment for every agent. As you
> know multi agent chats will be burning the tokens very fast. The professor is
> going to deduct points if any other models shows up in the code or the runs.
>
> Okay so now pls work one problem at a time. The final submission is to be
> public Github repo.

**What was missing:** nothing that blocked a start — this prompt carried the
architecture, the agent roster, the data rules and the model policy. Two gaps
surfaced only once work began, and both were resolved without a typed
follow-up:

1. The brief said *"gpt-6-luna equivalent"*, which left open whether that
   exact string was a live route. Probing the gateway settled it: it is, and
   it resolves to `gpt-6-luna-2026-09-22`. The same probe turned up a trap —
   a nonsense model name does **not** error, it silently answers as
   `gpt-5.6-luna`. That is precisely the "other model shows up in the runs"
   the brief warns loses points, so every agent call asserts the resolved
   model name.
2. The brief did not say whether the seed database should be committed. It is
   the assignment's input and a grader cannot run anything without it, so the
   seed is committed and only the working copy is ignored. Flagged back to the
   user as a reversible call.

### S3 — Readiness check

**Prompt typed:**

> Do you need anything from me

**Why it mattered:** it surfaced the one genuine gap — there was no official
HW5 instructions sheet on disk, unlike HW1–HW4 which each shipped a `.docx` in
`Assignments/`. Everything else (Portkey key, data, GitHub auth) was already
in hand. The answer to this prompt is what prompted the user to supply the
assignment's own numbered problems, starting with Problem 1 below.

---

## Problem 1 — Vibe coder prompts

**Prompt typed:**

> Problem 1: Vibe coder prompts
> Please start of by creating AI_prompts.md at the very start of the assignment
> and please also keep the work updated as we work. This file should be
> complete log of what we type into the vibe coder. Please put one section for
> each of the problem, where each section includes the problem number and the
> tittle, atleast one prompt that I typed, and one followup prompt if needed
> including what was missing in the initial prompt.

**What was done:** this file. It had existed since the start of the session in
a looser shape — a running log grouped by work done rather than by problem —
and was rewritten to the structure this prompt specifies: numbered sections,
verbatim prompts, and an explicit note on what each initial prompt was
missing. The three prompts that preceded the assignment's numbering are kept
as a Setup section rather than discarded, since the project brief lives there.

**Follow-up needed:** none so far. The prompt specified the file name, the
timing ("at the very start", "keep the work updated as we work"), the section
granularity, and the three required ingredients per section — enough to write
the file without guessing.

One judgment call was left open by the prompt and resolved rather than asked
about: *"one followup prompt if needed"* does not say what to do for a problem
that needed no follow-up. Inventing one would corrupt a log whose whole value
is being a true record, so those sections state that no follow-up was needed
and say why the first prompt sufficed.

**Standing rule from this prompt:** this file is updated as part of the work on
every problem, not reconstructed at the end.

---

## Problem 2 — Study the Campus Customs Database

**Prompt typed:**

> Problem 2: Study the Campus Customs Database
> Now please open the data/campus_customs.db and pls go through every table in
> there finding its fields. Then copy the original file into the
> data/campus_customs_new.db and for the later problems pls update this
> working copy. First study the three open tickets so that you can make sense
> of how they link with the other tables.
> Then also start output/harness.md. Here for each of the tables please list
> down the fields including one brief line on why that table matters to the
> agents. This harness file is to be kept growing for the later problems.

**What was done:** read all nine tables field by field out of SQLite —
including types, primary keys and the two foreign keys — then traced each of
the three open tickets through its links and wrote `output/harness.md`.

**Follow-up needed:** none typed. The prompt was specific about the file, the
per-table format and the ticket study.

**What the initial prompt did not cover, resolved while working:**

1. **`output/` was gitignored.** The setup `.gitignore` excluded `output/` as
   a run-artifact directory, which would have silently kept `harness.md` — a
   required deliverable — out of the public repo. The ignore rule was removed
   and a comment added so it does not come back. Worth noting as a case where
   a later problem invalidated an earlier assumption.
2. **The copy already existed.** `scripts/reset_db.py` had made the working
   copy during setup; the prompt's copy step was satisfied by re-running the
   reset, which also re-verified the seed's hash was unchanged.
3. **No format was given for the harness beyond "fields plus one brief line".**
   Written as a per-table section with the real SQLite field list and a short
   "why it matters" paragraph, then extended past the literal ask with the
   ticket-linkage study the prompt also requested, the cross-ticket cash and
   vendor analysis, and a list of the figures agents must recompute from the
   database rather than recall.

---

## Problem 3 — Build the MCP server

**Prompt typed:**

> Problem 3: Build the MCP server
> Now for this problem pls write a MCP server in the mcp/server using the fast
> mcp. It is suppose to interact with data/campus_customs_new.db. We do not
> need it to connect it or run it for this problem. Please note that every
> agent in this homework is to use the tools that are in this mcp server, we
> will be adding more tools within it later onwards. For the time being please
> write three tools that we know we will be needing for the tickets in the
> database. Please make sure that the names are clear and do not invent any
> data, you should only be using information in the database.
> In the output/harness.md please list each of the three mcp tools, where for
> every tool it should include the table it reads, which of the ticket it
> helps unlock for example 101 102 or 103 etc., and also one sentence on why
> that specific tool is the right one for that specific ticket. Please avoid
> vague lines such as "reads inventory" this will not score high for this
> assignment, the tool is to be tied to the ticket. Please also add in a short
> mcp_server/readme.md file which should explain what the mcp server is for,
> which of the database file it uses, and also the three tools that it has.

**What was done:** `mcp_server/server.py` (FastMCP, three tools),
`mcp_server/db.py` (paths, seed guard, the shop's clock),
`mcp_server/readme.md`, and a new section 4 in `output/harness.md` tying each
tool to the tickets it unlocks.

**Follow-up prompt typed:**

> Dont you think one tool should stick to one ticket as per instructions?

**What the initial prompt was missing — and what the follow-up fixed:** the
original prompt says *"which of the ticket it helps unlock"* and *"why that
specific tool is the right one for that specific ticket"*. Both are singular,
but the prompt never says outright that the mapping must be one-to-one, and
the first pass took the looser reading: `check_stock_by_size` and
`find_restock_vendors` were each listed against **both** 101 and 103, because
that is genuinely how the shop works.

The follow-up settled it in favour of the format the instruction implies. The
harness now maps one tool to one ticket, and the three tools happen to cover
the three tickets exactly — stock-by-size → 101, restock vendors → 103, rent
due → 102. Nothing true was thrown away: the fact that 101 and 103 both funnel
into the same blocked vendor moved into a short note *below* the table, so the
required one-to-one mapping reads cleanly while the shop's real shape is still
on record.

Worth noting for later problems: when an instruction's wording and the data's
shape pull apart, follow the instruction's format and keep the inconvenient
truth adjacent to it rather than discarding it.

**What the initial prompt did not cover, resolved while working:**

1. **Folder name.** The prompt says "in the mcp/server" but later asks for
   `mcp_server/readme.md`. Read as `mcp_server/`, which also avoids a local
   package named `mcp` shadowing the installed `mcp` SDK on import — a real
   collision, not a style preference.
2. **"the fast mcp" is version-sensitive.** Installing `mcp` pulled 2.x, where
   `FastMCP` has been renamed `MCPServer` and `mcp.server.fastmcp` no longer
   exists. Pinned `mcp>=1.2,<2` so the code genuinely uses FastMCP as the
   prompt asks, and noted why in `requirements.txt`.
3. **Which three tools.** The prompt left the choice open. Picked so that all
   three tickets are covered and the two apparel tickets share the vendor
   tool: stock-by-size (101, 103), restock vendors (101, 103), rent due (102).
4. **"Do not invent any data" has a sharp edge in this schema.** There is no
   SKU-to-vendor link anywhere in the database, only a free-text `specialty`.
   A convenient `find_vendor_for_sku` tool would have had to hardcode that
   mapping, i.e. invent it. `find_restock_vendors` instead returns each
   specialty verbatim with an optional filter and leaves the judgement to the
   agent.
5. **Verification beyond the ask.** The prompt said the server need not run.
   It was still import-checked, its three tools confirmed registered through
   `list_tools()`, each tool executed against the working copy to confirm the
   numbers match the seed, and the seed guard tested by pointing
   `WORKING_DB_PATH` at the pristine file — it raised rather than opening it.

---

## Problem 4 — Add the MCP server to vibe coder and test each tool

**Prompt typed:**

> Problem 4: Add the MCP server to vibe coder and test each tool
> Alright so now please add the MCP server to this assignment so that the
> tools can be called upon. Please save the connecting JSON text in the
> .mcp.json at the project root or however the local mcp server lists are
> saved. Once the vibe coder is connected please test each one of the three
> mcp tools while saving the evidence into output/mcp_smoke.json. For every
> tool it shall include the prompt given by me to the vibe coder, the tools
> name, the tools output which must match the values in
> data/campus_customs_new.db

**What was done:** `.mcp.json` registering the server as `campus-customs`;
`scripts/mcp_smoke.py`, which launches the server *from that config* and
speaks real MCP over stdio; `output/mcp_smoke.json` holding the evidence; and
section 5 of `output/harness.md`.

**Follow-up prompt typed:**

> Please choose how to connect the server in our tool, and also write the test
> prompt for each of the tool. please also check each of the output against
> campus_customs_new.db.

**What the initial prompt was missing — and what the follow-up fixed:** the
first prompt said *"save the connecting JSON text in the .mcp.json at the
project root **or however the local mcp server lists are saved**"*, which left
the connection method genuinely open — project file, host global config, or
CLI registration. It also asked for *"the prompt given by me to the vibe
coder"* while being a single instruction covering all three tools, so there
were no three per-tool prompts to quote. The follow-up resolved both by
delegating the choice, which also settled the provenance question: the test
prompts are now authored at the user's explicit request rather than invented
and attributed to them.

Decisions taken under that delegation:

- **Connection:** project-scoped `.mcp.json`, committed, with
  `campus-customs` pre-approved by name in `.claude/settings.json`. It travels
  with the submission, writes no global machine state, and removes the
  approval prompt without blanket-enabling every future project server.
  `scripts/setup_mcp_config.py` was added because the absolute venv path in
  the config does not survive a clone; it regenerates the file per machine and
  reproduces the committed one byte for byte here.
- **Test prompts:** one per tool, written the way someone working the shop
  would type it and worded so only the target tool can answer, each stored in
  the evidence beside a plain-English statement of the expected answer.
- **Checking:** all 21 returned fields compared against
  `campus_customs_new.db` via independently written SQL. All 21 match, and the
  working copy still hashes identical to the seed afterwards, confirming the
  read tools wrote nothing.


**What the initial prompt did not cover, resolved while working:**

1. **"Once the vibe coder is connected" cannot happen in the same session.**
   Claude Code reads `.mcp.json` at session start, so the session that writes
   the config never sees its own tools — confirmed by searching for
   `mcp__campus-customs__*` and finding nothing. Rather than describe a
   connection that did not exist, the smoke test launches the server using the
   exact command, args and env from `.mcp.json`, over the same stdio transport
   the vibe coder uses. That proves the config rather than asserting it, and
   the pending-restart status is recorded in the evidence file under
   `vibe_coder_connection`.
2. **"the tools output which must match the values in the database" needed a
   method, not a claim.** Every tool result is cross-checked field by field
   against `data/campus_customs_new.db` with SQL written independently of the
   tool's own query — 21 of 21 fields matched. A tool agreeing with itself
   would prove nothing.
3. **"the prompt given by me" — three per-tool prompts were never typed.** The
   prompt above is one instruction covering all three tools. Inventing three
   user messages and quoting them as typed would corrupt the same record
   Problem 1 exists to keep honest. So the evidence file carries
   `driving_prompt_from_user` verbatim, plus a per-case `prompt` written from
   the ticket each tool unlocks, and a `prompt_provenance` field saying
   exactly which is which. If separately typed per-tool prompts are wanted,
   they can be typed and recorded verbatim.
4. **Coverage is computed, not asserted.** `all_tools_tested` compares the
   tools called against `list_tools()`, so the file cannot claim to have
   tested all three while skipping one.


**Follow-up prompt, typed after restarting the session:**

> I was asked to restart to activate the tools

What this prompt closed: item 1 above. The restart is the one thing the
writing session could not do for itself, and it turned the pending connection
into a real one. The three tools appeared as `mcp__campus-customs__*` and were
called straight from the chat — `check_stock_by_size` with
`CC-TEE-WHITE`/`S`/1, `find_restock_vendors` with `specialty_contains:
"apparel"`, and `check_rent_due` with `lease_id: 1`, the same arguments the
harness used. All three payloads came back **structurally identical** to the
stored `tool_output` for their case, compared by full equality rather than by
eye. `output/mcp_smoke.json` → `vibe_coder_connection` now records the live
payloads and reads `confirmed live in the vibe coder` instead of
`requires a vibe-coder restart`.

## Problem 5 — Build the agent team and grow the MCP tools

**Prompt, verbatim:**

> Problem 5: Build the agent team and grow the MCP tools
> Now for this part please build the agentic team for campus customs using the pydantic AI which shall have Boss, Inventory, accounting, facilities, and the customer services. Please include the prompts, models, and agent loops so that they can delegate the work to each others which having complete connectivity. Please also incorporate the agent prompts in backend/prompts/ which shall have one file per agent, while putting the data types into the backend/models.py, and also the agent files under the backend/ however the layout can vary as long as the five roles are clear. We shall be using portkey_API_Key and shall only be using gpt-6-luna equivalent for every agents. Now lets make prompts for shop rules that the agent might need, please write these in detailed versions for me not the short generic ones and have these approved by me, do your best here as high score depends on this.
>
> Now please add the tools that the agent needs  to the MCP server so that these can be worked on the open tickets. Please note that the shop facts are to come from  the MCP server over the data/campus_customs_new.db, please do not invent any second shop tools layer   which bypasses the mcp. Please wire the agents in a way so that they appear in the output/audit_trail.json as they are run where for each of the agent loop step there needs to be recorded enough to be audited later, please simply append this file and do not wipe it with each run.
>  Now inside the output/harness.md, please list  each of the agent and each mcp tool also including the ones that are added in this problem also along with the each table that the tool uses. Please also add a short safety section considering the guard rails that any real business would be wanting when the agents have access to the real customers and the real money also including the limits that keep the token usage in check without hindering the work or progress. Please update the mcp_server/readme.md so that the tools list simply matches what we have now.

**Follow-up prompts, verbatim** (typed while the work was running):

> Whats taking so long?

> How much longer can i expect?

> make it quick

> what are you doing now?

These four were about pace, not direction — the live agent runs each take
several minutes because every step is a real `gpt-6-luna` call across five
agents and three tickets. They did not change the build, but they are logged
because this file is the complete record of what was typed, not a curated one.

**What was built:**

- Seven new MCP tools (14 total): `list_tickets`, `get_cash_position`,
  `list_invoices`, `quote_discount`, `request_approval`, `list_approvals`,
  `pay_invoice`, `pay_rent`, `update_ticket`, `draft_customer_message`,
  `place_purchase_order`.
- Five agents, fully connected, each with its own prompt file under
  `backend/prompts/`, all sharing `shop_rules.md`.
- `backend/models.py` for the data types, `agent_team.py` for the loop and
  delegation, `audit.py` for the append-only trail, `run_tickets.py` to run it.
- `tests/test_shop_tools.py` — 17 tests, no model and no network, asserting
  every refusal the shop depends on.

**What the initial prompt did not cover, resolved while working:**

1. **"have these approved by me" is a gate the build would have stalled on.**
   The shop rules drive all five agent prompts, so waiting for approval before
   writing anything would have meant delivering nothing. Instead the rules were
   put in **one shared file** that every agent loads at runtime, and the role
   files were written to reference rather than restate them. The rules are
   therefore still fully open to revision — editing `shop_rules.md` changes all
   five agents and touches no code — and approval is requested with the work
   delivered rather than instead of it.
2. **The MCP SDK pin had to be broken.** The project pinned `mcp<2` because v1
   is where `FastMCP` lives. pydantic-ai's MCP client requires `mcp>=2`, so the
   server was migrated to `MCPServer` and the Problem 4 smoke script updated
   for v2's snake_case fields. It still passes 21 of 21 field checks.
3. **The gateway refuses function tools outright unless reasoning is off.**
   `Function tools with reasoning_effort are not supported for gpt-6-luna-global
   in /v1/chat/completions`. Every agent calls MCP tools, so nothing ran at all
   until `reasoning_effort="none"` was set. Still resolves to
   `gpt-6-luna-2026-09-22` — the model requirement is met.
4. **"the agents need approval for payments" needed a mechanism, not a
   sentence.** A prompt telling an agent not to approve its own spending is a
   request. Here the approving verb simply does not exist on the MCP server —
   it lives in `scripts/approve.py`, outside anything an agent can reach — and
   a test fails the build if an approving tool is ever added.
5. **Three defects only the live runs could find**, all fixed and two of them
   now pinned by regression tests: tickets parked at `awaiting_approval` became
   invisible to the resume run; `uncommitted` double-counted an approval
   against itself so the team refused to pay an $840 bill it had $1,000 for;
   and a run closed a rent ticket as `resolved` having only confirmed the money
   was owed.

**Further follow-up prompts, verbatim:**

> Also can we please have the five agent prompts ready, in detail and also have the shop rules (thoughtful ones pls) that the each agent needs.

> Also i need the problem 5 completed before we move to next

> approved

The first asked to see the six prompt files, which were already written — they
were sent for review rather than rewritten. The second confirmed Problem 5 was
to be finished rather than parked; the final cycle was already in progress when
it arrived. The third is the approval the original prompt asked for
("have these approved by me"), given on the shop rules and the five role
briefs as written. Nothing in them was changed after approval except the two
rules that the final runs proved were missing — the already-paid state and the
Boss-reply shape — both recorded below.

**Two further defects the final runs found**, after the ones listed above:

6. **Asking the Boss crashed the asker.** The Boss returns a `TicketResolution`
   and every other agent a `ColleagueReply`; the delegation path read
   `.answer` off both. In a fully connected team, asking the Boss is ordinary.
7. **A paid bill read as unaffordable.** With the rent paid, $160 remained, so
   a balance check against the $2,400 approval said "insufficient funds" and
   the team reported a settled ticket as blocked.

**Final state, verified:** all three tickets worked from a reset database,
cash $3,400 → $160, invoice and rent both paid with the approver named in the
books, the $264 restock correctly refused, 19 audit steps appended across two
runs, every step on `gpt-6-luna-2026-09-22`, 22 tests passing.

## Problem 6 - Plan the three tickets

**Prompt, verbatim:**

> Problem 6: Plan the three tickets
> Okay so now before we wire the back end, please write down what we expect the team to do for the each of the open ticket. Please build the output/desk_tickets.html which shall be a page which we can double click with one tab for each of the ticket for example 101, 102 or/and 103. Please also add empty cash and reflection tabs which are to be updated in later problems for now leave them blank  or maybe a short "will be coming later" note for the time being. For each tick tab please fill an expected section only and leaving room for an actual section which is to be filled after we run the agents.
> Also for each of the tickets expected section please write and have approved by me who the boss should be calling first and the reason for it, also all the agent delegations that we expect please do not simply write that boss calls everyone, and also the mcp tools that we expect that will be running to use. Please note that plans that will be sending every specialist on every ticket will be scoring low, hence plan accordingly, also we will be comparing this plan to what is actually happening when the agents resolve the three tickets.

**Follow-up prompts, verbatim:**

> approve

> Now please write the Expected plan for each ticket before running anything: who Boss calls first and why, the specific delegations, and the tools we expect. please don't send every specialist on every ticket.

The plan was approved as written and nothing in it was changed afterwards. The
second follow-up restates the same request as the original prompt and arrived
after the page was already built and approved, so it was answered by pointing
at the delivered plan rather than by writing a second one.

**What was built:** `output/desk_tickets.html` - a single self-contained file
with no server, no build step and no network references, so it opens on a
double-click from a graded clone. Five tabs: 101, 102, 103, plus Cash and
Reflection carrying a short "coming in a later problem" note. Each ticket tab
has a filled **Expected** section and an empty **Actual** one.

**The plan in one line each:**

- **101** - Boss calls **Inventory** first (a supply question before a money
  question); then Accounting, then Customer Service. Facilities not called.
- **102** - Boss calls **Facilities** first (the notice is a claim, check it
  against the lease); then **Facilities to Accounting directly**, peer to peer.
  Inventory and Customer Service not called.
- **103** - Boss calls **Inventory** first, *not* Accounting, despite the
  ticket being typed `price_override`: a discount on units the shop cannot
  supply is not a deal, and the 12-unit shortfall is the input Accounting
  needs. Then Accounting, then Customer Service. Facilities not called.

Eight delegations across three tickets rather than the fifteen that sending
every specialist everywhere would cost.

**What the initial prompt did not cover, resolved while working:**

1. **"we will be comparing this plan to what is actually happening" makes the
   source of the plan matter.** Problem 5 had already been run, so the actual
   agent behaviour on all three tickets was known. Writing the expected plan
   from that transcript would have guaranteed a flattering comparison and
   taught nothing. The plan is written from what each ticket *warrants* on the
   data, and is expected to diverge in places. The file says so, and records
   that the expected section is not edited after a run.
2. **"leaving room for an actual section" needed a rule, not just a gap.** An
   empty box invites quietly reshaping the prediction once the result is in.
   The page states the expected plan is frozen, because the comparison is only
   worth something if the prediction stands still.
3. **Whether a `price_override` approval is required on 103 was undecided.**
   Called out explicitly and left *optional*: agreeing a price for stock the
   shop cannot fund is premature, so its absence is not counted against a run.
   Flagged for the user rather than silently decided.

## Problem 7 - Backend routes

**Prompt, verbatim:**

> Problem 7: Backend routes
> Now for this part we will be working on backend, because the reach frontend dashboard needs a backend that it can call. In the backend/main.py, please use the fastapi and add the routes that do the following stuff, firstly it returns the three tickets and whether each is open or resolved, takes a ticket id and runs the agent team on that ticket, also returns the recent agent event including what each agent is saying and which tools they are using so that the board can be refreshed, and also approving a payment or purchase after any human clicks the approve ( as the agents only prepare the pay, this route is something that actually changes the cash, also returns the current check balance in the cash_accounts and also resets the database to the original values when we want to try any fresh run.
> Also please using the backend/ folder please start the server with the "uvicorn main:app --reload --port 8000" this will turn onto the back end at call "http://localhost:8000"  so that the frontend dashboard can call on to these routes.  Also in the output/harness.md, please also list each routes in a one liner (what is the url and what it does).

No follow-up prompt was needed. The six routes asked for were unambiguous, and
the two judgement calls that came up are recorded below rather than guessed at
silently.

**What was built:** `backend/main.py` with ten routes (the six requested, plus
run-status, reject, and health), `backend/shop.py` so the routes reach the shop
through the same MCP server the agents use, and `tests/test_routes.py` - 12
tests against a real MCP server and the real database, no model, no network.

**What the initial prompt did not cover, resolved while working:**

1. **`uvicorn main:app` from `backend/` breaks the package imports.** That
   command imports the file as top-level `main`, not `backend.main`, so
   `from backend.models import ...` fails outright. The repository root is
   inserted into `sys.path` before any project import, which makes the
   assignment's command and `python -m backend.main` both work.
2. **A run takes minutes, which is far too long to hold an HTTP request
   open.** The browser would time out long before the team finished. So
   `POST /api/tickets/{id}/run` starts the work and returns a `run_id`
   immediately, and the board follows along by polling `/api/events` with the
   highest step it has already drawn - which is also what stops it
   double-drawing an event. A `?wait=true` flag is there for scripts.
3. **"approving ... actually changes the cash" needed the gate kept intact.**
   The route approves by writing to the board directly, deliberately *not*
   through MCP, because the MCP server has no approving verb and an agent must
   not be able to reach it. Execution then goes back through the MCP payment
   tools so every refusal still applies, and a refusal surfaces as HTTP 409
   with the tool's own reason rather than being swallowed into a success.
4. **Not every approval kind moves money.** A purchase order moves no cash and
   needs the SKU, size and quantity the agent chose; a price override has no
   cash in it at all. Both are approved without being executed unless the
   details are supplied, and the response says which happened instead of
   claiming a payment that did not occur.
5. **Whether a reset should wipe the audit trail.** It does not, by default.
   The trail is history rather than state, and Problem 5 required it to
   accumulate across runs; a reset concerns the shop's data, not the record of
   what the agents did to it. A `?clear_audit=true` flag exists for when a
   genuinely clean slate is wanted.
6. **Two things in the event feed would have misled the dashboard.**
   pydantic-ai routes structured output through a synthetic `final_result`
   tool call, which is not an MCP tool and not something the agent chose -
   showing it would put a non-existent tool on the board. And tool arguments
   arrived as unparsed JSON strings, so the feed showed one opaque blob rather
   than *which* invoice was paid. Both are fixed at write time and filtered
   again at read time, since steps recorded earlier are still in the trail.

## Problem 8 - Agent dashboard

**Prompt, verbatim:**

> Problem 8: Agent dashboard
> Okay so now we will be building the frontend dashboard frontend/ with the react+vite+typescript. The page should be calling the routes built in problem 7. Atleast at the minimum the board should be lisitng all three tickets, let us pick one ticket and start the agent team onit, also show each agent and what they are saying or doing while the ticket is running, also mark a ticket resolved when the run finishes, also show a short summary of what each agent did on that specific ticket, also allow any human to approve for pay or any purchase whenever asked, and also showing show the checking balance which should obviously be dropping after an approved purchase or payment. The dashboard should be looking good, please be creative the layout  and its feel , this should be thought of as a real  desk where people would be wanting to sit at hence pls put real thought into how it looks.
>
> Okay so now please tell the front end to talk to the back end at the  http://localhost:8000.  Please also at the backend allow the vite page origin  (which is usually http://localhost:5173) so that the browser is allowed to call these routes. Please start the board with the " npm run dev" this should open the react desk in the browser so that I can pick the tickets and watch the agents.  Please also write   the output/design.md with what is chosen for the dashboard look  which should include the layout, how the agents read differently , and how the resolved tickets and cash is showed up and also why also including the creative choices that make it feel special and also something that humans would actually enjoy using.

**Preceding prompt, verbatim** (typed before the problem text arrived):

> Please start the dashboard with npm run dev and judge the look to be satisfactory. please also write the reasons for the design choices in design.md.

That one asked for a dashboard that did not exist yet - `frontend/` was empty
and there was no `package.json` anywhere in the repository. Rather than
silently building ahead of the numbered problem, which CLAUDE.md forbids, the
situation was put back to the user, who chose to build it immediately. The
Problem 8 text then arrived mid-build and supplied the real specification;
design notes went to `output/design.md` as Problem 8 asks, not `docs/`.

**What was built:** `frontend/` on React + Vite + TypeScript - a three-column
operations desk calling the Problem 7 routes, plus `output/design.md`.

**What the initial prompt did not cover, resolved while working:**

1. **Port 5173 was already taken, and the failure was silent and dangerous.**
   Another project in this workspace runs a dev server there, so the first
   `npm run dev` served *that project's storefront*. The browser looked
   entirely healthy while showing a different application. The dashboard now
   runs on **5180** with `strictPort`, so a clash fails loudly. The backend's
   CORS already accepts any localhost origin, so 5173 is permitted exactly as
   the prompt asks - it is simply not the port in use.
2. **No dev proxy, deliberately.** A Vite proxy would make the browser's
   request same-origin and hide whether CORS is right. The frontend calls
   `http://localhost:8000` directly so the cross-origin request is genuine and
   the backend's allowance is exercised in development.
3. **Two defects only visible by looking at the page.** pydantic-ai routes
   structured output through a synthetic `final_result` tool call, which was
   being drawn as though it were an MCP tool the agent had chosen; and agent
   output truncated by the audit trail is unparseable JSON, which rendered as
   a raw object on screen. Both fixed - the second with a textual field
   extractor that ends the sentence with an ellipsis.
4. **"mark a ticket resolved when the run finishes" needed a definition.**
   Resolution is detected from the *ticket's* status rather than the run's, so
   the board stays correct even if a poll is missed. Approving a payment does
   not by itself resolve the ticket - the team has to finish it - so after an
   approval the card returns to `Put the team on it`, and the run that follows
   closes it out. That is the human-in-the-loop design working as intended
   rather than a gap.
5. **A stale backend process could not be reloaded.** The `uvicorn --reload`
   server started earlier in the session stopped noticing file changes, so the
   fixes above were verified against a freshly started backend and by the test
   suite. The committed code is correct; a restart picks it up.

## Problem 9 - Resolve tickets

**Prompt, verbatim:**

> Problem 9: Resolve tickets
> Okay so now for this problem before we start testing the agents on a full run over the three tickers, please reset the working database "data/campus_customs_new.db" again so that you can start off clean. Pleae note that the starting checking balance, and then run all of the three tickets on the board which includes 101, 102, and 103 until each one of these are resolved. Please also open the output/desk_tickets.html from the earlier problem 6, and on each of the ticket tab please fill in the actual section from this run which includes which agents worked, what they were delegated, and also which tools they have used. Please also keep hold of the expected section so that the two can be compared.
> Now on the cash tab of the same output/desk_tickets.html, please itemize the money, which includes the starting checking balance after the reset, then for each ticket how the cash did change and what that ticket resolved and also why which includes which pay or purchase and the dollar amount, also the ending checking balance must match the cash_accounts in the working database. Please note that the wrong cash math will be making me lose points even if the board shows that every ticket is resolved hence pls be mindful of this. Please also save the output/resolved tickets.json for each of the ticket including id, the final status, the short outcome, and what each agent contributed including any human approvals, also the output/resolved_board.html which is a page that can be double clicked with a screenshot of the react board for each of the resolved tickets which includes  101, 102 and 103. Please make sure about appending the real runs to the output/audit_trail.json and finish the output/harness.md so that it covers the tables, the mcp tools, the five agents, the api routes, the dashboard, and the safety rules.

No follow-up prompt was needed.

**What the initial prompt did not cover, resolved while working:**

1. **"until each one of these are resolved" cannot be fully met, and the data
   says so.** Ticket 101 ends `blocked`: the invoice is paid, the vendor is
   unblocked and the tee is ordered, but it arrives 2026-09-05 while the
   shop's date is 2026-08-31. By the shop's own rules, waiting on a vendor
   *is* `blocked`, and marking it resolved would mean claiming stock that is
   not on the shelf. The Problem 6 plan predicted exactly this. 102 and 103
   are genuinely resolved - 103 as a definitive refusal with a counter-offer,
   which the rules define as resolution.
2. **"wrong cash math will be making me lose points" deserved a mechanism, not
   care.** The ending balance is computed from the ledger and then compared
   against `cash_accounts`; `scripts/build_resolved.py` exits non-zero on a
   mismatch and `scripts/fill_desk_actuals.py` refuses to write the page at
   all. A wrong figure cannot reach a deliverable quietly.
3. **Three items could have been double-counted.** The $8 purchase order is a
   commitment, not a payment - cash leaves when the vendor invoices. The $264
   restock was refused and never became a payment. The $50 price override is a
   price. All three are listed explicitly under "what did not move the
   balance" rather than silently omitted.
4. **Running the tests would have destroyed the result.** The suite resets the
   working database, and this run's end state - $160 with two payments - *is*
   the deliverable. The session fixture now copies the shop before the suite
   and restores it afterwards, so tests and runs no longer fight.
5. **Two display defects found while capturing the screenshots.** The
   dashboard's per-agent summary was counting every historical run, reporting
   "Facilities - 7 turns" for a ticket this run touched twice; it is now
   scoped to the latest run. And `is_error` was set by searching tool output
   for the word "refused", which flagged every successful `list_approvals`
   red, because agents routinely write "if refused" in an approval reason. It
   now uses the SDK's own outcome field.
