"""Fill the Reflection tab of `output/desk_tickets.html`.

Written in the first person because it is the owner's reflection, not the
assistant's. Every claim is tied to something on the Tickets or Cash tabs of
this same page, or to a figure in `output/resolved_tickets.json` /
`output/audit_trail.json` -- the costs below are real token counts from the
run, not estimates.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "output/desk_tickets.html"

REFLECTION = """  <div class="card">
    <h2 style="margin-top:0">Reflection</h2>
    <p class="note">
      Written after the run on this page. Every judgement below points at
      something on the <strong>Ticket</strong> tabs or the <strong>Cash</strong>
      tab; the token costs are the real figures from
      <code>output/audit_trail.json</code>.
    </p>
  </div>

  <h2>1. How I would rate the team on each ticket</h2>

  <div class="card">
    <h3>Ticket 102 &mdash; rent. The best work on the board.</h3>
    <p>
      <strong>4 agent turns, 20 tool calls, 171,259 tokens</strong> &mdash; the
      cheapest ticket of the three and the only one that reached
      <code>resolved</code>.
    </p>
    <p>
      What earns the mark is one decision. The ticket note is just a claim:
      <em>&ldquo;Email: shop rent due in 2 days.&rdquo;</em> Facilities did not
      take it. It called <code>check_rent_due</code> and answered from lease 1
      itself &mdash; Elm City Properties, <strong>$2,400</strong>, due
      <strong>2026-09-02</strong>, two days out, not overdue. The notice happened
      to be honest, but if the landlord had overstated the figure we would have
      caught it, and a shop that pays what the invoice says without opening the
      contract overpays quietly for years.
    </p>
    <p>
      It then did the whole job: raised the request, waited for me, paid on my
      approval, and rolled the lease to <strong>2026-10-02</strong> so the same
      month cannot be paid twice. The Cash tab shows the clean
      <strong>$2,560 &rarr; $160</strong> step.
    </p>
    <p class="note">
      The one criticism: <code>get_cash_position</code> was called by both
      Facilities and the Boss. Harmless here, but it is the same question asked
      twice.
    </p>

    <h3>Ticket 101 &mdash; tee. Good mechanics, failed the customer.</h3>
    <p><strong>12 agent turns, 82 tool calls, 528,061 tokens.</strong></p>
    <p>
      The best single move of the entire run happened here. Inventory called
      <code>check_stock_by_size</code> and got <strong>qty 0, shortfall 1</strong>,
      then <code>find_restock_vendors</code> and got
      <strong><code>can_ship: false</code></strong> with
      <strong>invoice 501</strong> named as the reason. That turned
      &ldquo;we&rsquo;re out of stock&rdquo; into &ldquo;there is an $840 bill
      standing in the way&rdquo; &mdash; a different problem with a different
      answer. Paying it (Cash tab: <strong>$3,400 &rarr; $2,560</strong>) unblocked
      the vendor, and the $8 order went out with an ETA of 2026-09-05.
    </p>
    <p>
      And then it failed the only person actually waiting.
      <strong>Customer Service was never called.</strong> Tauhid Zaman has a tee
      on order and has been told nothing. The shop spent <strong>$848</strong> on
      his behalf and sent him no word. In a real shop that is the failure the
      customer notices &mdash; not the stock level, the silence. It happened in
      this run and in the previous one, so it is a pattern in how the Boss works
      this ticket rather than bad luck.
    </p>

    <h3>Ticket 103 &mdash; hoodies. Sharpest thinking, worst value, and it took a decision off me.</h3>
    <p>
      <strong>19 agent turns, 141 tool calls, 918,275 tokens</strong> &mdash;
      <strong>57% of the entire run&rsquo;s cost</strong> for a ticket where no
      money moved and nothing resolved.
    </p>
    <p>
      The reasoning was genuinely good. The Boss called Inventory first on a
      ticket typed <code>price_override</code>, which reframed it correctly:
      <strong>8 of 20</strong> on hand, shortfall <strong>12</strong>, so this was
      never really a discount question. <code>quote_discount</code> put the shape
      of the deal on the table &mdash; $22 unit cost against a $58 list, and
      <strong>$264</strong> to buy the missing 12. Accounting then escalated back
      up to the Boss rather than deciding beyond its remit.
    </p>
    <p>
      What I hold against it: <strong>Accounting decided not to ask me about the
      $264 at all</strong>, on the grounds that $160 would not cover it. It
      protected me from a decision that was mine to make. I would rather have
      seen &ldquo;$264 needed, $160 available, a $104 gap &mdash; do you want to
      find it, or shall we decline?&rdquo; and said no myself. Being shielded from
      a trade-off is not the same as the trade-off not existing, and the Cash tab
      shows the consequence: ticket 103 contributes a dash, not a decision.
    </p>
    <p class="note">
      Ranking them: <strong>102 clearly best</strong>, 101 second on mechanics but
      with the worst single omission, 103 last &mdash; it thought the hardest and
      delivered the least, at more than five times the cost of the ticket that
      actually finished.
    </p>
  </div>

  <h2>2. How the run compared to the plans I approved beforehand</h2>

  <div class="card">
    <p>
      The plans on the three ticket tabs were written <em>before</em> this run and
      were restored byte-for-byte from the Problem 6 commit before the Actual
      sections were filled, so the prediction is provably untouched by the result.
    </p>
    <table>
      <thead><tr><th>Ticket</th><th>Planned delegations</th><th>What happened</th><th>Who was right</th></tr></thead>
      <tbody>
        <tr>
          <td class="step">101</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>2 of 3.</strong> Customer Service never called.</td>
          <td><strong>The plan.</strong> The customer should have been written to.</td>
        </tr>
        <tr>
          <td class="step">102</td>
          <td>Boss &rarr; Facilities, then Facilities &rarr; Accounting</td>
          <td><strong>1 of 2.</strong> Both agents called <code>get_cash_position</code> themselves.</td>
          <td><strong>The team.</strong> Shop rule 7 says not to delegate what a tool already answers.</td>
        </tr>
        <tr>
          <td class="step">103</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>3 of 3</strong>, plus an unplanned <code>accounting &rarr; boss</code> escalation.</td>
          <td><strong>The team.</strong> The plan did not imagine a specialist handing a call upward.</td>
        </tr>
      </tbody>
    </table>

    <h3>What the plan got right</h3>
    <p>
      Mostly <strong>who not to call</strong>. Facilities stayed out of 101 and 103;
      Inventory and Customer Service stayed out of 102. Every one of those
      predictions held, and not a single specialist was sent somewhere it had
      nothing to add. The plan also called the hardest judgement correctly &mdash;
      Inventory before Accounting on 103, on a ticket whose own <code>type</code>
      column argues for the opposite.
    </p>

    <h3>What the plan got wrong</h3>
    <p>
      It <strong>assumed delegation where a tool call would do</strong>. The
      expected <code>Facilities &rarr; Accounting</code> hop on 102 would have spent
      an entire model call to return a number <code>get_cash_position</code> hands
      over in one. Writing the plan, I was thinking about who owns which topic;
      running it, the team was thinking about what is cheapest to find out. The
      team was right.
    </p>
    <p>
      It also under-predicted the <em>shape</em> of connectivity. I planned one
      peer-to-peer hop and got a different one in a different place &mdash;
      Accounting escalating to the Boss on 103. That is the sort of thing a plan
      cannot really anticipate, and it is the clearest evidence on this page that
      the team is genuinely fully connected rather than a hub with spokes.
    </p>
  </div>

  <h2>3. Would one agent with the same tools have been simpler?</h2>

  <div class="card">
    <p><strong>For this board, yes &mdash; and the numbers on this page say so.</strong></p>

    <h3>The case for one agent</h3>
    <ul class="tight">
      <li>
        <strong>Ticket 102 is the proof.</strong> The entire job is a three-tool
        chain: <code>check_rent_due</code> &rarr; <code>request_approval</code>
        &rarr; <code>pay_rent</code>. It took 4 agent turns and 171,259 tokens, and
        two different agents asked <code>get_cash_position</code> the same
        question. One agent holding the same tools does that in one or two turns.
      </li>
      <li>
        <strong>Ticket 103 is the stronger proof.</strong> 918,275 tokens and 141
        tool calls to conclude &ldquo;we cannot afford the restock&rdquo; &mdash; a
        conclusion <code>get_cash_position</code> returns in a single call. The
        deliberation was real, but most of the cost was the team re-reading the
        same figures through four pairs of eyes.
      </li>
      <li>
        <strong>The expertise is in the prompts, not in the models.</strong> All
        five agents load the same <code>shop_rules.md</code>; each role brief is
        about a page. One agent could hold all five pages and all fourteen tools.
        Nothing about Inventory&rsquo;s knowledge requires a separate model call
        from Accounting&rsquo;s.
      </li>
      <li>
        <strong>101&rsquo;s failure is a handoff failure.</strong> The customer was
        dropped <em>between</em> delegations &mdash; the Boss farmed out stock and
        cash, got both answers, and closed without the third. A single agent
        holding the whole ticket has nothing to hand off and nothing to forget.
      </li>
    </ul>

    <h3>Where the team genuinely earned its shape</h3>
    <ul class="tight">
      <li>
        <strong>The <code>accounting &rarr; boss</code> escalation on 103.</strong>
        Separating who computes from who decides is a real organisational idea, not
        a technical one. A single agent would have just decided.
      </li>
      <li>
        <strong>The audit trail is legible by role.</strong> I can see on the
        dashboard that <em>Facilities</em> verified the lease, without reading a
        transcript. With one agent the trail is one long monologue.
      </li>
      <li>
        <strong>Ranking across tickets is a distinct job.</strong> Rent before
        restock, on this board, is the Boss&rsquo;s call and nobody else sees all
        three tickets at once.
      </li>
    </ul>

    <p>
      <strong>My honest verdict:</strong> for three tickets on one shop date, one
      agent with these fourteen tools and these shop rules would have been simpler,
      far cheaper, and probably better on 101. The team shape starts to pay for
      itself at a board of thirty tickets where specialists can run in parallel and
      no single context can hold everything &mdash; which is not the shop we have.
      I would keep the five <em>prompts</em> and collapse the five <em>agents</em>.
    </p>
  </div>

  <h2>4. Three problems this team could handle tomorrow, with the tools we already built</h2>

  <div class="card">
    <h3>a. The Crest Mug is at zero, and that vendor is not blocked</h3>
    <p>
      <code>CC-MUG-CREST</code> size OS sits at <strong>qty 0</strong> &mdash; the
      same hole ticket 101 had. The difference is the vendor: Elm City Gifts
      (&ldquo;mugs and small goods&rdquo;, 3-day lead) holds <strong>no unpaid
      invoice</strong>, so <code>find_restock_vendors</code> returns
      <code>can_ship: true</code> and nothing has to be cleared first. The exact
      path we ran on 101 works unchanged: <code>check_stock_by_size</code> &rarr;
      <code>find_restock_vendors</code> &rarr; <code>get_cash_position</code> &rarr;
      <code>request_approval</code> &rarr; <code>place_purchase_order</code>. At
      $3.50 unit cost it fits in the $160 we have left, which is precisely why it
      would succeed where the $264 hoodie restock failed.
    </p>

    <h3>b. The rent we just rolled to 2026-10-02</h3>
    <p>
      Paying ticket 102 moved lease 1&rsquo;s <code>next_due</code> from 2026-09-02
      to <strong>2026-10-02</strong>. When that comes round it is the same ticket
      again, and this is the one path we have proven end to end: Facilities checks
      the lease rather than the notice, raises the request, I approve, and
      <code>pay_rent</code> moves cash, the <code>payments</code> row and the due
      date together. No new tool, no new agent &mdash; and the rolled date means
      the shop cannot be billed twice for September.
    </p>

    <h3>c. A part-fillable order on a size that is low rather than empty</h3>
    <p>
      Say someone wants 6 navy hoodies in <strong>S</strong>, where we hold
      <strong>4</strong>. <code>check_stock_by_size</code> reports shortfall 2 and
      hands back the sibling sizes (S&nbsp;4, M&nbsp;8, L&nbsp;14, XL&nbsp;6), so
      Customer Service can offer 4 now with 2 to follow, or a different size that
      genuinely exists. <code>quote_discount</code> prices it,
      <code>draft_customer_message</code> writes it. Ticket 103 already exercised
      this exact shape &mdash; it only failed because the shortfall there was 12
      units and $264 we did not have.
    </p>
  </div>

  <h2>5. Three problems this team cannot touch, and what each would need</h2>

  <div class="card">
    <h3>a. The tee actually arriving &mdash; this is blocking ticket 101 right now</h3>
    <p>
      Not hypothetical. We placed a purchase order with an ETA of
      <strong>2026-09-05</strong>, but there is <strong>no tool that receives
      stock</strong> and <strong>no tool that moves <code>desk.date_today</code></strong>
      off 2026-08-31. <code>inventory.qty</code> for <code>CC-TEE-WHITE</code>/S will
      read 0 forever, so ticket 101 can never leave <code>blocked</code>. We proved
      that by running it twice and getting the same answer.
    </p>
    <p>
      <strong>Needs:</strong> <code>receive_purchase_order(po_id)</code> &mdash;
      increments <code>inventory.qty</code>, writes the vendor&rsquo;s bill into
      <code>invoices</code>, marks the order received; and
      <code>advance_shop_date(to)</code>, so overdue tests and ETAs move with the
      calendar. <strong>No new agent</strong> &mdash; Inventory already owns stock
      and would own receiving it.
    </p>

    <h3>b. Money coming <em>in</em></h3>
    <p>
      Hard rule 8 of this build is that cash only goes out, and the schema has no
      sales table. The consequence is visible on the Cash tab: three tickets, and
      every arrow points down. The 8 hoodies we do hold, at the $50 the team itself
      quoted, are <strong>$400 of revenue</strong> &mdash; nearly four times the
      $104 gap that stopped ticket 103. The team cannot see that money, because no
      tool records a sale or credits <code>cash_accounts</code>. A shop that can
      only ever get poorer will eventually refuse everything.
    </p>
    <p>
      <strong>Needs:</strong> a <code>sales</code> table, a
      <code>record_sale(sku, size, qty, unit_price)</code> tool that decrements
      inventory and credits cash in one transaction, and margin reporting on top of
      it. Accounting could own this, or it justifies a <strong>Sales agent</strong>
      once pricing, promotions and returns grow past one tool.
    </p>

    <h3>c. Tauhid ever hearing back</h3>
    <p>
      <code>draft_customer_message</code> files a draft and there is deliberately no
      send tool &mdash; that was the right call for a homework. But there is also
      <strong>no way for me to approve and send a draft the way I approve a
      payment</strong>, and <strong>no inbound channel</strong>, so a customer&rsquo;s
      reply can never become a ticket. The drafts sit in
      <code>output/board/drafts.json</code> where only I will ever look. That is why
      101 ended with the shop $848 lighter and the customer silent &mdash; even if
      Customer Service <em>had</em> been called, the message would still not have
      reached him.
    </p>
    <p>
      <strong>Needs:</strong> an <code>approve_draft(draft_id)</code> gate mirroring
      the payment gate, so sending is human-authorised and never agent-authorised; a
      real outbound integration behind that gate; and an inbound path that turns a
      reply into a row in <code>tickets</code>. The <strong>Customer Service agent
      already exists</strong> &mdash; what it lacks is a channel, not a brain.
    </p>

    <p class="note">
      The pattern in all three: the gaps are not reasoning gaps. The team is
      perfectly capable of working out that stock should arrive, that selling
      hoodies brings money in, and that Tauhid is waiting. It cannot <em>act</em> on
      any of it, because the shop is reached only through the MCP server and those
      verbs do not exist there. That restriction is the safety design working as
      intended &mdash; and it is also exactly where the next problems live.
    </p>
  </div>"""


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")

    start = html.index('<section class="panel" id="reflection">')
    end = html.index("</section>", start)
    html = (
        html[:start]
        + '<section class="panel" id="reflection">\n'
        + REFLECTION
        + "\n"
        + html[end:]
    )

    html = html.replace(
        '<button role="tab" aria-selected="false" data-tab="reflection">Reflection<span class="sub">later</span></button>',
        '<button role="tab" aria-selected="false" data-tab="reflection">Reflection<span class="sub">what I learned</span></button>',
    )

    PAGE.write_text(html, encoding="utf-8")
    print(f"filled the Reflection tab in {PAGE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
