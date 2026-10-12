"""The Reflection tab's prose, kept apart from the code that inserts it.

First person, because it is the shop owner's reflection rather than a report
about them. Every figure here is real: the token counts come from
`output/audit_trail.json`, the money from `cash_accounts`, and the
delegations from the trail's `delegated_by` field.
"""

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
    <h3>Ticket 102 &mdash; rent. Best value on the board.</h3>
    <p>
      <strong>4 agent turns, 201,921 tokens</strong> &mdash; by far the cheapest of
      the three, and fully resolved.
    </p>
    <p>
      It earns the mark on one decision. The ticket is only a claim:
      <em>&ldquo;Email: shop rent due in 2 days.&rdquo;</em> Facilities did not take
      it. It called <code>check_rent_due</code> and answered from lease 1 itself
      &mdash; Elm City Properties, <strong>$2,400</strong>, due
      <strong>2026-09-02</strong>, two days out, not overdue. The notice happened to
      be honest; if it had not been, we would have caught it. A shop that pays what
      the invoice says without opening the contract overpays quietly for years.
    </p>
    <p>
      Two colleagues, no wasted calls, and the lease rolled to
      <strong>2026-10-02</strong> so September cannot be billed twice. The Cash tab
      shows the clean <strong>$2,560 &rarr; $160</strong> step.
    </p>

    <h3>Ticket 101 &mdash; tee. Resolved, but it took me to catch a real error.</h3>
    <p><strong>12 agent turns, 685,733 tokens.</strong></p>
    <p>
      The sharpest move of the run happened here. Inventory called
      <code>check_stock_by_size</code> and got <strong>qty 0, shortfall 1</strong>,
      then <code>find_restock_vendors</code> and got
      <strong><code>can_ship: false</code></strong> with <strong>invoice 501</strong>
      named. That turned &ldquo;we are out of stock&rdquo; into &ldquo;there is an
      $840 bill in the way&rdquo; &mdash; a different problem with a different answer.
      Paying it (<strong>$3,400 &rarr; $2,560</strong>) unblocked the vendor, the tee
      went on order, and Tauhid Zaman was drafted a reply carrying the real
      2026-09-05 date.
    </p>
    <p>
      <strong>But Accounting asked me to approve that purchase order at $1.00.</strong>
      <code>pricing.unit_cost</code> for <code>CC-TEE-WHITE</code> is
      <strong>$8.00</strong> and the order is one unit; it had put the quantity in the
      amount field. I rejected it with that reason, the team re-raised at $8.00, and I
      approved that.
    </p>
    <p>
      That is the most instructive thing that happened all run. The shop rules forbid
      stating a figure that did not come from a tool, and the team broke that rule in
      the one place it mattered. Nothing in the system caught it:
      <code>request_approval</code> checks invoice and rent amounts against the
      database, but a purchase-order amount is free text, so the tool had nothing to
      compare it to. <strong>The human gate was not a formality here &mdash; it was
      the only control that worked.</strong>
    </p>

    <h3>Ticket 103 &mdash; hoodies. Right answer, expensive route.</h3>
    <p>
      <strong>20 agent turns, 995,949 tokens</strong> &mdash;
      <strong>53% of the run&rsquo;s entire cost</strong> for a ticket where no money
      moved.
    </p>
    <p>
      The reasoning was good. The Boss called Inventory first on a ticket typed
      <code>price_override</code>, which reframed it correctly: <strong>8 of 20</strong>
      on hand, shortfall <strong>12</strong>, so this was never really a discount
      question. <code>quote_discount</code> gave the shape of the deal &mdash; $22 cost
      against a $58 list, and <strong>$264</strong> to buy the missing twelve.
    </p>
    <p>
      And this time the team <em>asked me</em> rather than deciding for me. It raised
      the $42 price, which I approved, and put the funding gap in figures so the
      restock could be refused explicitly. The ticket ends as a priced partial offer:
      eight hoodies at $42 that genuinely exist, twelve honestly declined, and a draft
      on the board saying exactly that. That is a finished answer, not a shrug.
    </p>
    <p class="note">
      Ranking them: <strong>102 best</strong> on value and judgement; <strong>101
      second</strong>, strong detective work undercut by a pricing error it did not
      catch itself; <strong>103 last</strong> &mdash; the right outcome, reached
      through five times the tokens of the ticket that actually moved money.
    </p>
  </div>

  <h2>2. How the run compared to the plans I approved beforehand</h2>

  <div class="card">
    <p>
      The plans on the three ticket tabs were written <em>before</em> this run and
      restored byte-for-byte from their original commit before the Actual sections
      were filled, so the prediction is provably untouched by the result.
    </p>
    <table>
      <thead><tr><th>Ticket</th><th>Planned</th><th>Happened</th><th>Who was right</th></tr></thead>
      <tbody>
        <tr>
          <td class="step">101</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>3 of 3</strong>, plus a $1-vs-$8 pricing error I rejected.</td>
          <td><strong>The plan.</strong> Insisting on Customer Service is what got Tauhid told.</td>
        </tr>
        <tr>
          <td class="step">102</td>
          <td>Boss &rarr; Facilities, then Facilities &rarr; Accounting</td>
          <td><strong>1 of 2.</strong> Both agents read <code>get_cash_position</code> themselves.</td>
          <td><strong>The team</strong>, for the third run running.</td>
        </tr>
        <tr>
          <td class="step">103</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>3 of 3</strong>, and the &ldquo;optional&rdquo; price override was raised and approved.</td>
          <td><strong>The team.</strong> A priced partial beats the flat refusal I planned for.</td>
        </tr>
      </tbody>
    </table>

    <h3>What the plan got right</h3>
    <p>
      Mostly <strong>who not to call</strong>. Facilities stayed out of 101 and 103;
      Inventory and Customer Service stayed out of 102. Every one of those held, and no
      specialist was sent anywhere it had nothing to add. The plan also called the
      hardest judgement correctly &mdash; Inventory before Accounting on 103, against
      what that ticket&rsquo;s own <code>type</code> column suggests.
    </p>
    <p>
      The most valuable thing the plan did was name Customer Service on 101.
      <em>Earlier runs of this same board dropped that delegation and closed the ticket
      with the customer never written to.</em> Having written down who should be called
      is what made that omission visible as a failure instead of passing for finished
      work.
    </p>

    <h3>What the plan got wrong</h3>
    <p>
      It <strong>assumed delegation where a tool call would do</strong>. The expected
      <code>Facilities &rarr; Accounting</code> hop on 102 would have spent a whole model
      call to fetch a number <code>get_cash_position</code> returns directly. Three runs
      have now skipped it. Writing the plan I was thinking about who owns which topic;
      running it, the team was thinking about what is cheapest to find out. The team was
      right.
    </p>
    <p>
      It also <strong>under-called 103</strong>, treating the price override as optional
      on the grounds that pricing stock you cannot buy is premature. In practice
      approving $42 on the eight hoodies that do exist turned a refusal into an offer,
      which is plainly the better outcome.
    </p>
  </div>

  <h2>3. Would one agent with the same tools have been simpler?</h2>

  <div class="card">
    <p><strong>For this board, yes &mdash; and the numbers on this page say so.</strong></p>

    <h3>The case for one agent</h3>
    <ul class="tight">
      <li>
        <strong>102 is the proof.</strong> The whole job is a three-tool chain:
        <code>check_rent_due</code> &rarr; <code>request_approval</code> &rarr;
        <code>pay_rent</code>. It took 4 turns and 201,921 tokens, and two different
        agents asked <code>get_cash_position</code> the same question.
      </li>
      <li>
        <strong>103 is the stronger proof.</strong> 995,949 tokens to conclude
        &ldquo;we cannot afford the restock&rdquo; &mdash; something
        <code>get_cash_position</code> answers in one call. Most of that cost was the
        same figures re-read through four pairs of eyes.
      </li>
      <li>
        <strong>The expertise is in the prompts, not the models.</strong> All five
        agents load the same <code>shop_rules.md</code>; each role brief is about a
        page. One agent could hold all five pages and all fourteen tools.
      </li>
      <li>
        <strong>The $1 error is a handoff error.</strong> Accounting wrote an amount
        without reading <code>pricing</code> itself, because Inventory had already
        looked at the product and Accounting was working from what it had been told.
        One agent holding the whole ticket has the unit cost in front of it when it
        writes the number.
      </li>
    </ul>

    <h3>Where the team genuinely earned its shape</h3>
    <ul class="tight">
      <li>
        <strong>The audit trail is legible by role.</strong> I can see on the board that
        <em>Facilities</em> verified the lease, without reading a transcript. With one
        agent it is one long monologue.
      </li>
      <li>
        <strong>Ranking across tickets is a distinct job.</strong> Rent before restock is
        the Boss&rsquo;s call, and nobody else sees all three at once.
      </li>
      <li>
        <strong>Separating who computes from who decides</strong> is a real
        organisational idea. Accounting prepares; the Boss and I dispose.
      </li>
    </ul>

    <p>
      <strong>My honest verdict:</strong> for three tickets on one shop date, one agent
      with these fourteen tools and these shop rules would have been simpler, far
      cheaper, and less likely to misprice a purchase order. The team shape starts
      paying for itself at a board of thirty tickets, where specialists run in parallel
      and no single context holds everything &mdash; which is not the shop we have. I
      would keep the five <em>prompts</em> and collapse the five <em>agents</em>.
    </p>
  </div>

  <h2>4. Three problems this team could handle tomorrow, with the tools we already built</h2>

  <div class="card">
    <h3>a. The Crest Mug is at zero, and that vendor is not blocked</h3>
    <p>
      <code>CC-MUG-CREST</code> size OS sits at <strong>qty 0</strong> &mdash; the same
      hole ticket 101 had. The difference is the vendor: Elm City Gifts
      (&ldquo;mugs and small goods&rdquo;, 3-day lead) holds <strong>no unpaid
      invoice</strong>, so <code>find_restock_vendors</code> returns
      <code>can_ship: true</code> and nothing has to be cleared first. The exact path we
      ran on 101 works unchanged, and at $3.50 unit cost it fits inside the $152 still
      uncommitted &mdash; which is precisely why it would succeed where the $264 hoodie
      restock failed.
    </p>

    <h3>b. The rent we just rolled to 2026-10-02</h3>
    <p>
      Paying 102 moved lease 1&rsquo;s <code>next_due</code> to
      <strong>2026-10-02</strong>. When it comes round it is the same ticket again, and
      this is the path we have now run clean three times: Facilities checks the lease
      rather than the notice, raises the request, I approve, and <code>pay_rent</code>
      moves cash, the <code>payments</code> row and the due date together.
    </p>

    <h3>c. The other twelve hoodies, once there is money</h3>
    <p>
      Ticket 103 is resolved but the shortfall is real: 12 units at $22 is
      <strong>$264</strong>, and the $42 price is <em>already approved</em>. The moment
      the shop has the cash that is a <code>request_approval</code> and a
      <code>place_purchase_order</code> away &mdash; no new tool, no new agent, and
      Bulldog Print Co is no longer blocked now invoice 501 is paid. The work we did has
      left that order ready to place rather than needing to start again.
    </p>
  </div>

  <h2>5. Three problems this team cannot touch, and what each would need</h2>

  <div class="card">
    <h3>a. The tee actually arriving</h3>
    <p>
      Ticket 101 is resolved because the <em>desk</em> is finished &mdash; paid, ordered,
      customer told. Tauhid still does not have a tee, and with these tools he never
      will: there is <strong>no tool that receives stock</strong> and <strong>no tool
      that moves <code>desk.date_today</code></strong> off 2026-08-31.
      <code>inventory.qty</code> for <code>CC-TEE-WHITE</code>/S will read 0 forever, and
      the ETA of 2026-09-05 can never arrive.
    </p>
    <p>
      <strong>Needs:</strong> <code>receive_purchase_order(po_id)</code> &mdash;
      increments <code>inventory.qty</code>, writes the vendor&rsquo;s bill into
      <code>invoices</code>, marks the order received; and
      <code>advance_shop_date(to)</code> so overdue tests and ETAs move with the
      calendar. <strong>No new agent</strong> &mdash; Inventory already owns stock.
    </p>

    <h3>b. Money coming <em>in</em></h3>
    <p>
      Rule 8 of this build is that cash only goes out, and the schema has no sales table.
      The Cash tab shows the consequence: three tickets, every arrow pointing down. The
      eight hoodies we hold, at the $42 <em>I approved this run</em>, are
      <strong>$336 of revenue</strong> &mdash; three times the $104 gap that stopped the
      restock. The team cannot see that money, because no tool records a sale or credits
      <code>cash_accounts</code>. A shop that can only get poorer eventually refuses
      everything.
    </p>
    <p>
      <strong>Needs:</strong> a <code>sales</code> table, a
      <code>record_sale(sku, size, qty, unit_price)</code> tool that decrements inventory
      and credits cash in one transaction, and margin reporting over it. Accounting could
      own it; a <strong>Sales agent</strong> earns its place once promotions and returns
      grow past one tool.
    </p>

    <h3>c. Tauhid ever actually hearing from us</h3>
    <p>
      <code>draft_customer_message</code> files a draft and there is deliberately no send
      tool &mdash; the right call for a homework. But there is also <strong>no way for me
      to approve and send a draft the way I approve a payment</strong>, and <strong>no
      inbound channel</strong>, so a reply can never become a ticket. The drafts sit in
      <code>output/board/drafts.json</code> where only I will ever look. Ticket 101 is
      marked resolved on the strength of a message that has not actually been sent.
    </p>
    <p>
      <strong>Needs:</strong> an <code>approve_draft(draft_id)</code> gate mirroring the
      payment gate, so sending is human-authorised and never agent-authorised; a real
      outbound integration behind it; and an inbound path turning a reply into a row in
      <code>tickets</code>. The <strong>Customer Service agent already exists</strong>
      &mdash; what it lacks is a channel, not a brain.
    </p>

    <p class="note">
      The pattern in all three: these are not reasoning gaps. The team can work out that
      stock should arrive, that selling hoodies brings money in, and that Tauhid is
      waiting. It cannot <em>act</em> on any of it, because the shop is reached only
      through the MCP server and those verbs do not exist there. That restriction is the
      safety design working exactly as intended &mdash; and it is also precisely where the
      next problems live.
    </p>
  </div>"""
