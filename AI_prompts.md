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

**Follow-up needed:** none typed.

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

