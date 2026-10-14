"""The Reflection tab's prose, kept apart from the code that inserts it.

First person, because it is the shop owner's reflection rather than a report
about them. Every figure here is real: the token counts come from
`output/audit_trail.json`, the money from `cash_accounts`, and the
delegations from the trail's `delegated_by` field.
"""

REFLECTION = """  <div class="card">
    <h2 style="margin-top:0">Reflection</h2>
    <p class="note">
      Written after the run on this page, and after I rewrote the shop rules in
      my own words. Every judgement below points at something on the
      <strong>Ticket</strong> tabs or the <strong>Cash</strong> tab; the token
      costs are the real figures from <code>output/audit_trail.json</code>.
    </p>
  </div>

  <h2>1. How I would rate the team on each ticket</h2>

  <div class="card">
    <h3>Ticket 103 &mdash; hoodies. Best value on the board, by a distance.</h3>
    <p>
      <strong>3 agent turns, 131,349 tokens</strong>, resolved. The same ticket
      cost <strong>995,949 tokens</strong> and twenty turns on an earlier run and
      ended unresolved. Same model, same tools, same data. What changed was my
      rule 7, which told the team what &ldquo;finished&rdquo; means: do the work,
      or refuse it and say why. It stopped circling.
    </p>
    <p>
      The reasoning held up at the lower price. Inventory confirmed 8 of 20 on
      hand and the invoice 501 block; Accounting priced the deal from the table
      &mdash; $22 cost against a $58 list, $264 to buy the missing twelve &mdash;
      and put the funding gap in figures. The Boss declined the bulk order and
      offered the eight hoodies that actually exist, with a draft on the board
      saying exactly that. A clean, reasoned no, delivered cheaply.
    </p>
    <p class="note">
      That single comparison is the most useful thing I learned building this.
      <strong>The expensive failure mode was not a weak model &mdash; it was a
      vague definition of done.</strong>
    </p>

    <h3>Ticket 102 &mdash; rent. Clean, and the control I asked for actually fired.</h3>
    <p><strong>4 agent turns, 184,773 tokens</strong>, resolved.</p>
    <p>
      Facilities did the thing the ticket exists to test: the notice says
      <em>&ldquo;Email: shop rent due in 2 days&rdquo;</em>, and Facilities
      ignored it and read lease 1 instead &mdash; Elm City Properties,
      <strong>$2,400</strong>, due <strong>2026-09-02</strong>, not overdue. The
      notice was honest; if it had not been, we would have caught it.
    </p>
    <p>
      And this time <strong>Accounting was consulted before the money was
      requested</strong>. In three earlier runs that never happened, because the
      old rules told agents not to delegate what a tool could answer. My rule 4
      makes it explicit, and I want it explicit: the agent about to spend the
      shop's money should not also be the one certifying the shop can afford it.
      It costs one call. Separation of duties is worth one call.
    </p>

    <h3>Ticket 101 &mdash; tee. The most work, and the only one that finishes properly.</h3>
    <p><strong>10 agent turns, 615,845 tokens</strong>, resolved.</p>
    <p>
      The sharpest move of the run is still here. Inventory called
      <code>check_stock_by_size</code> and got <strong>qty 0, shortfall 1</strong>,
      then <code>find_restock_vendors</code> and got
      <strong><code>can_ship: false</code></strong> with <strong>invoice 501</strong>
      named. That turns &ldquo;we are out of stock&rdquo; into &ldquo;there is an
      $840 bill in the way&rdquo; &mdash; a different problem with a different
      answer.
    </p>
    <p>
      What is new is what happened after the order went in. Under my rule 7 an
      order placed is not a product delivered, so the team advanced the shop's
      clock to the vendor's <strong>2026-09-05</strong> ETA, received the goods,
      and moved <code>inventory.qty</code> for size S from <strong>0 to 1</strong>.
      Only then did it draft Tauhid to say his tee is ready. <strong>The tee
      physically exists.</strong> On earlier runs this ticket was called
      &ldquo;resolved&rdquo; with the shelf still empty, which is precisely the
      self-deception rule 7 was written to stop.
    </p>
    <p class="note">
      Ranking them: <strong>103 best</strong> on value, <strong>102</strong>
      cleanest on process, <strong>101</strong> most work for the most complete
      result. No ticket was badly handled this time, which was not true before.
    </p>
  </div>

  <h2>2. How the run compared to the plans I approved beforehand</h2>

  <div class="card">
    <p>
      The plans on the three ticket tabs were written <em>before</em> any run and
      restored byte-for-byte from their original commit before the Actual
      sections were filled, so the prediction is provably untouched by the result.
    </p>
    <table>
      <thead><tr><th>Ticket</th><th>Planned</th><th>Happened</th><th>Who was right</th></tr></thead>
      <tbody>
        <tr>
          <td class="step">101</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>3 of 3</strong>, then went further and received the stock.</td>
          <td><strong>Neither &mdash; the rule was.</strong> The plan stopped at &ldquo;ordered&rdquo;.</td>
        </tr>
        <tr>
          <td class="step">102</td>
          <td>Boss &rarr; Facilities, then a second opinion from Accounting</td>
          <td><strong>2 of 2.</strong> Both happened.</td>
          <td><strong>The plan.</strong> It took rule 4 to make it actually happen.</td>
        </tr>
        <tr>
          <td class="step">103</td>
          <td>Boss &rarr; Inventory, Accounting, Customer Service</td>
          <td><strong>2 of 3.</strong> The Boss drafted the customer itself.</td>
          <td><strong>The team, on cost; the plan, on form.</strong></td>
        </tr>
      </tbody>
    </table>

    <h3>What the plan got right</h3>
    <p>
      Mostly <strong>who not to call</strong>. Facilities stayed out of 101 and
      103; Inventory and Customer Service stayed out of 102. Every one of those
      predictions held across every run, and no specialist was ever sent somewhere
      it had nothing to add. The plan also called the hardest judgement correctly
      &mdash; Inventory before Accounting on 103, against what that ticket's own
      <code>type</code> column suggests.
    </p>

    <h3>What the plan got wrong, and what that taught me</h3>
    <p>
      The plan described <strong>who talks to whom</strong>, and that turned out
      to be the least important thing about a run. The delegation pattern barely
      moved between runs; the cost and the quality moved enormously, and both
      tracked the <em>rules</em>, not the org chart. Ticket 103 went from 996k
      tokens and unresolved to 131k and resolved without a single change to who
      called whom.
    </p>
    <p>
      The plan also <strong>stopped too early on 101</strong>. It ended at
      &ldquo;order placed, ETA 2026-09-05&rdquo; and treated that as the finish
      line, because when I wrote it the shop had no way to receive stock at all.
      Writing rule 7 is what exposed that &mdash; the rule demanded a capability
      the system did not have, so we built it.
    </p>
    <p>
      One honest miss: on 103 the <strong>Boss wrote the customer draft itself</strong>
      instead of delegating to Customer Service. The customer was written to, which
      is what matters, but the specialist was bypassed.
    </p>
  </div>

  <h2>3. Would one agent with the same tools have been simpler?</h2>

  <div class="card">
    <p>
      <strong>Yes for this board &mdash; but after this run I think it is the
      second most interesting question.</strong>
    </p>

    <h3>The case for one agent</h3>
    <ul class="tight">
      <li>
        <strong>102 is the proof.</strong> The whole job is a three-tool chain:
        <code>check_rent_due</code> &rarr; <code>request_approval</code> &rarr;
        <code>pay_rent</code>. It took 4 turns and 184,773 tokens.
      </li>
      <li>
        <strong>The expertise is in the prompts, not the models.</strong> All five
        agents load the same <code>shop_rules.md</code>; each role brief is about a
        page. One agent could hold all five pages and all sixteen tools.
      </li>
      <li>
        <strong>Handoffs are where things get dropped.</strong> Across runs the
        recurring failures were a customer never written to and a purchase order
        priced at $1 instead of $8 &mdash; both cases of an agent acting on what it
        had been told rather than what it could read. One agent holding the whole
        ticket has nothing to hand off.
      </li>
    </ul>

    <h3>Where the team earned its shape</h3>
    <ul class="tight">
      <li>
        <strong>Rule 4 is only possible with more than one agent.</strong> Asking a
        different colleague to confirm the shop can afford a payment is separation
        of duties, and a single agent cannot check itself. That is a control, not
        an inefficiency.
      </li>
      <li>
        <strong>The audit trail is legible by role.</strong> I can see that
        <em>Facilities</em> verified the lease without reading a transcript.
      </li>
      <li>
        <strong>Ranking across tickets is a distinct job</strong> that only the Boss
        sees.
      </li>
    </ul>

    <p>
      <strong>My verdict:</strong> for three tickets on one shop date, one agent
      with these sixteen tools would still be simpler and cheaper. But the thing
      that actually moved the numbers was not the architecture &mdash; total cost
      fell from <strong>1,617,595</strong> tokens to <strong>931,967</strong>, a
      42% drop, from rewriting the rules alone. <strong>If I had one change to
      make, I would spend it on clearer rules, not on fewer agents.</strong> I
      would keep rule 4's second pair of eyes on money, and collapse the rest.
    </p>
  </div>

  <h2>4. Three problems this team could handle tomorrow, with the tools we already built</h2>

  <div class="card">
    <h3>a. The $8 we now owe Bulldog Print Co</h3>
    <p>
      Receiving the tee raised <strong>invoice 502 for $8.00</strong> &mdash; a
      real bill, sitting open right now, visible on the Cash tab. The team needs
      nothing new to clear it: <code>list_invoices</code> finds it,
      <code>get_cash_position</code> confirms $160 covers it,
      <code>request_approval</code> puts it to me, <code>pay_invoice</code> settles
      it. Worth doing promptly, because an unpaid invoice blocks that vendor from
      shipping again &mdash; which is the trap ticket 101 started in.
    </p>

    <h3>b. The Crest Mug at zero, from a vendor who is not blocked</h3>
    <p>
      <code>CC-MUG-CREST</code> size OS sits at <strong>qty 0</strong>. Elm City
      Gifts (&ldquo;mugs and small goods&rdquo;, 3-day lead) holds no unpaid
      invoice, so <code>find_restock_vendors</code> returns
      <code>can_ship: true</code>. The full path now exists end to end &mdash;
      order, advance the clock, receive &mdash; and at $3.50 a unit it fits inside
      the $152 uncommitted. It would succeed exactly where the $264 hoodie restock
      failed.
    </p>

    <h3>c. The twelve hoodies, the moment there is money</h3>
    <p>
      Ticket 103 is resolved but the shortfall is real: 12 units at $22 is
      <strong>$264</strong>. Bulldog Print Co is unblocked now invoice 501 is paid,
      the vendor and lead time are known, and the duplicate guard means the order
      can only be placed once. It is a <code>request_approval</code> and a
      <code>place_purchase_order</code> away.
    </p>
  </div>

  <h2>5. Three problems this team cannot touch, and what each would need</h2>

  <div class="card">
    <h3>a. Money coming <em>in</em></h3>
    <p>
      Rule 3 of my own rules says the shop only has cash going out, and the schema
      has no sales table. The Cash tab shows the consequence: every arrow points
      down. We now hold a tee Tauhid wants at a $28 list price and eight hoodies
      at $58, and <strong>none of it can ever become money</strong>. The shop can
      buy stock and owe for it, and that is all. Carry on long enough and it
      refuses everything.
    </p>
    <p>
      <strong>Needs:</strong> a <code>sales</code> table, a
      <code>record_sale(sku, size, qty, unit_price)</code> tool that decrements
      inventory and credits <code>cash_accounts</code> in one transaction, and
      margin reporting over it. Accounting could own it; a <strong>Sales
      agent</strong> earns its place once promotions and refunds arrive.
    </p>

    <h3>b. Tauhid ever actually hearing that his tee is ready</h3>
    <p>
      This one stings more now than it did. The tee is <em>on the shelf</em>, the
      draft is written, and it is sitting in
      <code>output/board/drafts.json</code> where only I will ever see it. There
      is deliberately no send tool &mdash; right for a homework &mdash; but there
      is also <strong>no way for me to approve and send a draft the way I approve
      a payment</strong>, and no inbound channel, so a reply could never become a
      ticket. We did all the work and the customer still does not know.
    </p>
    <p>
      <strong>Needs:</strong> an <code>approve_draft(draft_id)</code> gate
      mirroring the payment gate, so sending is human-authorised and never
      agent-authorised; a real outbound integration behind it; and an inbound path
      turning a reply into a row in <code>tickets</code>. The <strong>Customer
      Service agent already exists</strong> &mdash; it lacks a channel, not a brain.
    </p>

    <h3>c. Deliveries that do not arrive exactly as ordered</h3>
    <p>
      Building <code>receive_purchase_order</code> solved the problem my last
      reflection named, and immediately created a narrower one.
      <strong>It can only receive the whole order, in perfect condition.</strong>
      It books the full quantity, values it at <code>pricing.unit_cost</code>, and
      raises the vendor's bill for all of it. A real shop opens a box and finds
      eight of twelve, or twelve with two damaged, or the wrong size entirely
      &mdash; and ours would have to book that in as a clean full delivery and
      quietly lie to its own inventory.
    </p>
    <p>
      <strong>Needs:</strong> a quantity and condition argument on receiving, so a
      partial receipt leaves the rest outstanding; a <code>returns</code> table
      with a <code>return_to_vendor</code> tool that credits the bill; and a
      short-delivery path that reopens the shortfall rather than closing the
      order. Inventory would own all of it &mdash; no new agent, but the tool it
      has today is the optimistic half of the job.
    </p>

    <p class="note">
      The honest pattern across all three: <strong>every capability we add draws
      a sharper line around what is still missing.</strong> Before this run the
      gap was &ldquo;stock can never arrive&rdquo;. Now stock arrives, and the gap
      is that it always arrives perfectly. That is progress, and it is also a
      warning about reading a working demo as a working business.
    </p>
  </div>"""
