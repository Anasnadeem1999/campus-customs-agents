# The desk — design notes

What the dashboard looks like, and why each choice was made.

The brief was to build something that feels like *a real desk people would
want to sit at*. That phrase set the bar: not a status page you check, but a
place you work from for an afternoon. Everything below follows from taking it
literally.

---

## 1. The governing idea: a desk, not a dashboard

A dashboard reports. A desk is where work happens, and the distinction drove
every layout decision.

On a desk, the things you are about to do sit in front of you; the thing you
are doing is in the middle; what needs your signature sits to one side. The
money is always in view because it constrains everything. Nothing important
scrolls away while your attention is elsewhere.

So the page is a **fixed, full-height three-column workspace** with the cash in
the masthead — not a scrolling report. Each column scrolls independently,
because the feed grows to dozens of entries while the ticket list stays three
rows, and a single page scroll would drag the tickets off-screen exactly when
you want to click one.

## 2. Layout: left to right is the order of the work

| Column | Holds | Why there |
|---|---|---|
| **The board** (300px) | The three tickets | Where every piece of work starts, so it is where the eye starts — left, where English reading begins. Narrow, because a ticket is a short summary and a button. |
| **The team at work** (flexible) | The live agent feed and the per-agent summary | The widest column, because it is the only one with real prose. Agents write sentences, and sentences need measure. |
| **Waiting on you** (330px) | Approvals needing a decision, then the team roster | The right-hand side is where a human's own tasks belong — out of the reading flow, but never off the page. |

The columns are **not reorderable and not collapsible**. A desk whose drawers
move is not a desk you learn. Fixed positions mean that after an hour you
reach for things without looking.

**The masthead** carries the shop's identity, the shop date, and the balance.
The shop date is there because it is a constant source of confusion — the shop
runs on 2026-08-31, not today — and printing it next to the name settles the
question before it is asked.

## 3. How the agents read differently

This was the hardest problem on the page. Five colleagues write into one feed,
and if every entry looks the same you have to read a name on every line, which
is exactly the work a dashboard should save you.

Each agent has **three** consistent signals, never just one:

| Agent | Monogram | Colour | Why that colour |
|---|---|---|---|
| Boss | `BO` | Yale navy `#00356b` | The Boss is the shop speaking, so it takes the house colour from the masthead. |
| Inventory | `IN` | Green `#0f7b3f` | Stock: the colour of things being in or out. |
| Accounting | `AC` | Amber `#8a5a00` | Money, and the caution that goes with it. |
| Facilities | `FA` | Purple `#6b3fa0` | Far from the others on the wheel; the premises are a world of their own. |
| Customer Service | `CS` | Rose `#a01b46` | The one agent facing outward, in the warmest hue on the page. |

The colour appears as a **4px spine down the left edge of every event card** and
as the tint behind the monogram. Scanning the feed you follow a colour, not a
name — "the green one found the shortfall, then the amber one asked for money"
is readable at arm's length.

**Colour is never the only signal.** The monogram and the full name are always
present, so the feed works in greyscale and for colour-blind readers. The hues
were chosen to stay distinguishable in the common forms of colour blindness
rather than to look pleasant in a swatch.

### Inside one event card

Each card is built so you can stop reading at any point and still have learned
something:

1. **Who, and who asked them.** `Inventory — asked by Boss`. The delegation
   chain is visible without a graph.
2. **What they said**, in prose. Agent output arrives as JSON; showing raw JSON
   on a desk would be a failure of nerve, so the `answer` or `decision` field
   is extracted and the rest discarded. Long outputs are truncated in the audit
   trail and the JSON is then unparseable — a textual extractor handles that
   case and ends the sentence with an ellipsis rather than dumping the object.
3. **Which tools they called**, as small monospace chips. Monospace because
   these are literal function names, and typeface is doing the work of saying
   "this is machinery, not prose".
4. **The figures they cited**, each in a blue pill with the source tool in its
   tooltip. This is the quiet centrepiece: the shop rules say no agent may
   state a number it did not read from a tool, and this row is that rule made
   visible. Hovering `rent due $2,400.00` tells you it came from
   `check_rent_due`.
5. **What blocked them**, in an amber band — the single most useful line when
   a ticket does not finish.
6. **A footer of model, tokens, seconds.** Small and grey. The green `✓` next
   to `gpt-6-luna-2026-09-22` is the model check from the backend surfaced on
   screen: proof, on every single step, that the run used the required model
   and the gateway did not quietly substitute an older one. It turns red with
   a `✗` if it ever does.

New cards **rise in** over 0.28s. Enough to catch the eye and convey that work
is arriving live; short enough that twenty arriving at once do not feel like a
slot machine.

### The per-agent summary

Above the feed, once a ticket has been worked: **one line per colleague** —
monogram, name, how many turns, and which tools they touched. The feed answers
"what happened"; the summary answers "who did what", which is the question you
have after the fact and the one the brief asked for explicitly.

## 4. How resolved tickets show

A resolved ticket **recedes but does not disappear**:

- the left spine turns **green**
- the chip reads `RESOLVED` in green
- the whole card drops to **62% opacity**
- the title gets a **strikethrough** in a pale line

Four signals, deliberately. The work is still part of the day — you may want
to re-read what happened — but it has stopped asking for attention. Removing
it would be worse: a board that empties as you work gives you no sense of what
you have done, and hides the record exactly when someone asks why a ticket was
closed.

The other statuses use the same vocabulary of colour:

| Status | Reads as |
|---|---|
| `open` | neutral grey — nothing has happened yet |
| `working` | amber chip, **pulsing** — the only animated element on the page |
| `awaiting approval` | amber — this one is waiting on *you* |
| `blocked` | red — stopped, and not by you |
| `resolved` | green, faded, struck through |

The pulse is used once and only once. An interface where several things blink
teaches you to ignore blinking.

## 5. How cash shows, and why it is in the masthead

The balance is the **largest number on the page**, top right, always visible.

Cash is the binding constraint in this shop — $3,400 against an $840 invoice
and $2,400 of rent — so it is relevant to every ticket, not to one panel. It
belongs in the chrome rather than in a card you might scroll past. It is set in
**tabular figures** so the digits do not shimmy as they change.

Beneath it, when any money is approved but unpaid, a smaller line reads
`$2,400 promised · $1,000 free`. That distinction is the one real trap in the
shop's finances — plan against the raw balance and two approved payments
overdraw the same account — so the dashboard shows both figures rather than
making anyone remember which is which.

**The till flashes amber for 1.6 seconds when, and only when, the balance
actually changes.** The page polls every two seconds; flashing on every poll
would be noise and you would stop seeing it. Flashing only on real movement
means the one time it catches your eye is the time money moved. Approve a
payment and you watch the number fall — which is the moment the whole
human-in-the-loop design exists for, and it should feel like something.

## 6. The approval card: a decision, not a notification

Approvals are the only place a human changes the world, so they are styled like
something that needs a signature: an amber top border, the **amount set large**,
and the agent's reason in full.

That reason is never summarised or truncated. The shop rules require agents to
write it for a busy owner who will read it and nothing else — what it unblocks,
what it costs, what happens if refused — and the dashboard honours that by
showing all of it. Below it, `Leaves $160 free`, with a red `— tight` when the
spend does not fit within uncommitted cash.

Two buttons: **Approve & pay** in green, **Decline** as a quiet outline. The
green one says `& pay` because that is the truth — the click moves real money,
and a button that said only "Approve" would understate what it does.

When a payment is refused — insufficient cash, an approval already spent — the
backend's own reason is shown **in full in a red toast**, never flattened to
"something went wrong". Those refusals are the system's safety rails doing
their job, and the explanation is the most useful sentence on the screen.

When there is nothing to decide, the empty state does a job too: *"Nothing to
decide. The team asks here before any money moves — it can't approve anything
itself."* It teaches the guarantee at the moment someone is idle enough to read
it.

## 7. Creative choices that make it feel like somewhere

- **Warm paper, not slate.** The background is `#f6f4ef` and cards are
  `#fffdf9` — a faint cream. Every operations dashboard defaults to cool grey;
  this is a small shop on Chapel Street, not a trading floor, and the surface
  should feel like something you would set a coffee down next to. The warmth is
  subtle enough that nobody will name it, which is the point.
- **The `CC` crest.** A small monogrammed tile in the masthead, in the same
  visual language as the agents' monograms. The team and the shop are marked
  the same way, so the five colleagues read as staff rather than as processes.
- **"Put the team on it"** rather than *Run* or *Execute*. The button names the
  thing you are actually doing: handing a job to colleagues. Small wording,
  but it sets the whole relationship — these are people you delegate to, not a
  pipeline you trigger.
- **The roster, always in the sidebar.** Five rows: monogram, name, what they
  own. It teaches the colour code without a legend, gives the empty state
  something to say, and means a newcomer learns the team by sitting at the
  desk rather than reading a manual.
- **"asked by Boss"** on delegated events. Three words that make the hierarchy
  legible without drawing a single line or arrow.
- **Toasts in the bottom-right, six seconds.** Long enough to read a refusal,
  short enough not to pile up.
- **The offline banner names the fix.** If the backend is down it does not say
  "network error" — it prints the exact command to start it. The dashboard is
  the first place anyone will notice the backend is missing, so it is the right
  place to say what to do about it.
- **Typography does the ranking.** Three sizes and two weights, no more. The
  balance is 24px, the approval amount 20px, everything else 13–16px. Column
  headings are 12px uppercase letterspaced grey — present when you look for
  them, invisible when you are not.

## 8. Things deliberately left out

- **No charts.** Nothing here is a trend. The shop has one balance and three
  tickets; a sparkline would be decoration pretending to be information.
- **No dark mode.** One theme done properly beats two done adequately, and the
  warm paper is half the character of the page.
- **No raw JSON, anywhere.** Everything the backend returns is rendered as
  prose, a chip or a pill. If a human has to parse a JSON blob, the interface
  has handed its job back to them.
- **No auto-refresh spinner.** Polling is invisible by design. The only motion
  on the page is a new card rising, the working chip pulsing, and the till
  flashing — each tied to something real.
- **No confirmation dialog on approve.** The amount and the reason are already
  in front of you; a modal asking "are you sure?" adds a click and no
  information. The real safety is elsewhere — the backend refuses anything the
  balance cannot cover, and an approval can only be spent once.

## 9. How it behaves

- **Polls every 2 seconds**, asking for events *since the highest step already
  drawn*. Step numbers never repeat, so the board cannot double-draw an event
  and does not re-fetch the whole trail each tick.
- **Resolution is detected from the ticket, not the run.** When a ticket's
  status moves off `open`, the card updates and a toast announces it. Watching
  the ticket rather than the run keeps the two in step even if a poll is missed.
- **Nothing about the shop is cached.** No prices, no remembered balances, no
  hard-coded ticket list — the frontend knows only what a route just returned.
  The dashboard is a window onto the database, not a second copy of it.
- **The backend is called at `http://localhost:8000` directly**, not through a
  Vite proxy. A proxy would make the request same-origin and hide whether CORS
  is configured correctly; calling it directly means the browser performs a
  genuine cross-origin request every time, so the backend's allowance is
  exercised in development rather than discovered to be wrong later.

## 10. Verified in the browser

The whole loop was driven through the UI, not through curl:

1. Clicked **Put the team on it** on ticket 102 — the chip turned amber and
   pulsed, and agent cards rose into the feed as the team worked.
2. The rent approval appeared under **Waiting on you**, carrying Accounting's
   reasoning and `Leaves $1,000 free`.
3. Clicked **Approve & pay** — the till flashed and fell **$3,400 → $1,000**.
4. Clicked **Put the team on it** again — the team paid out the rest of the
   work and ticket 102 went **green, faded and struck through: RESOLVED**.

**Four defects were found by looking at the page rather than the code**, and
two of them were not cosmetic at all:

1. pydantic-ai's synthetic `final_result` call was being drawn as though it
   were an MCP tool the agent had chosen — a tool on the board that the server
   does not have.
2. Agent output truncated by the audit trail is unparseable JSON and was
   rendering as a raw object. A textual field extractor now recovers the
   sentence and ends it with an ellipsis.
3. **The board was double-drawing events.** One poll makes four requests,
   which easily outlasts the two-second interval, so a second poll began with
   the same `since` as the first and both appended the same events. Fixed with
   an in-flight guard, and by merging on step number rather than trusting
   `since` alone — a stale response can still land after a newer one.
4. **The audit trail was handing out duplicate step numbers.** Chasing (3)
   surfaced a real backend defect: `next_step_number()` was read by the caller
   *before* the write, so two agents finishing at once both claimed the same
   number. The trail then carried two different events both numbered 23. That
   breaks the dashboard's paging and quietly ruins the one property an audit
   trail must have — that a step can be referred to unambiguously. The number
   is now assigned inside `append_step`, under the lock, and a concurrency
   test pins it.

Only the first two were visible as *appearance*. The other two were a correct
backend and a correct frontend disagreeing in a way that no unit test was
asking about, and the page was the only place they showed.

### A note on running the tests

The suite exercises the real MCP server against the real working database,
because a payment rule tested only against a mock is not tested. The cost is
that `pytest` genuinely spends the shop's money, and it used to leave the
working copy mid-payment: cash at $160, two payments written, invoice 501
paid — but all three tickets still `open`. Opening the desk after a test run
then showed a shop that had never existed. The suite now restores the shop on
the way out, so the dashboard and the tests cannot disagree about what day it
is.

### A note on ports

The dashboard runs on **5173**, Vite's default and the port the brief names.

It did not always. Another project in this workspace holds 5173, and the first
run of this dashboard served *that project's storefront* — the browser looked
perfectly fine and was showing an entirely different application. It was moved
to 5180 to get clear of that while building. A clean clone has 5173 free, so
the default is restored, with `strictPort` off so a busy port slides to 5174
and prints where it landed rather than failing outright. The backend accepts
any localhost origin, so the number itself does not matter to CORS.
