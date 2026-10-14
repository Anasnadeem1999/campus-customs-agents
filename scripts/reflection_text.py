"""The Reflection tab's prose — the owner's own answers.

Written by the shop owner after reviewing all three tickets, and reproduced
here as given. Four details were re-anchored against the audit trail before
publishing: the $1 purchase-order error belongs to an earlier run, the
Customer Service delegation on 103 happened once that ticket was re-run, and
the token figures and efficiency ranking follow from that re-run. The
arguments are the owner's throughout.

Figures come from `output/audit_trail.json` and `cash_accounts`.
"""

REFLECTION = """  <div class="card">
    <h2 style="margin-top:0">Reflection</h2>
    <p class="note">
      My own answers, written after reviewing all three tickets. The figures are
      taken from <code>output/audit_trail.json</code> and the
      <strong>Cash</strong> tab of this page.
    </p>
  </div>

  <h2>1. How I would evaluate the agents on each ticket</h2>

  <div class="card">
    <p>
      I think the team handled all three tickets well in the final run, although
      each ticket tested something different.
    </p>

    <h3>Ticket 101 &mdash; the most work</h3>
    <p>
      The agents did the most work here. Inventory found that the requested
      size-S tee was out of stock and that the vendor could not ship because of
      the unpaid <strong>$840</strong> invoice. Accounting handled the payment
      approval, and the team ordered the tee, received it into inventory, and
      drafted a message for the customer. <strong>11 agent turns, 619,229
      tokens</strong> &mdash; the most expensive ticket, and the only one that
      had to move stock as well as money.
    </p>
    <p>
      On an <em>earlier</em> run of this same ticket, Accounting requested
      approval for <strong>$1</strong> instead of the correct <strong>$8</strong>
      purchase order. I rejected it and the team corrected the amount. It did not
      recur in the final run, but it is the clearest thing I saw all project about
      why human approval matters &mdash; the tooling could not catch that error,
      because a purchase-order amount has no record in the database to be checked
      against. Only a person reading it could.
    </p>

    <h3>Ticket 102 &mdash; the cleanest process, and the cheapest</h3>
    <p>
      The team followed the process most cleanly here. Facilities checked the
      landlord's notice against the actual lease rather than taking the email at
      face value, and Accounting confirmed the amount and available cash before
      the payment was approved. The <strong>$2,400</strong> rent was paid and the
      lease record was updated. It did this in <strong>6 agent turns and 258,145
      tokens</strong>, the least of any ticket.
    </p>

    <h3>Ticket 103 &mdash; the sharpest judgement</h3>
    <p>
      Inventory confirmed that only <strong>8 of the 20</strong> requested hoodies
      were available, while Accounting worked out that restocking the remaining
      12 would cost <strong>$264</strong>. Since only <strong>$160</strong>
      remained after the invoice and rent payments, the team correctly refused the
      restock and Customer Service drafted an offer for the 8 hoodies in stock.
      <strong>7 agent turns, 371,465 tokens.</strong>
    </p>

    <h3>Ranking them</h3>
    <p>
      <strong>Ticket 102</strong> comes first: it followed the process most
      closely and cost the least. <strong>Ticket 103</strong> second, for the
      sharpest judgement call &mdash; refusing a spend the shop could not fund,
      and saying so in figures rather than half-promising. <strong>Ticket
      101</strong> third, for completing the most complicated task, though it took
      the most work to get there.
    </p>
    <p class="note">
      The main lesson for me is that the agents performed better when the rules
      clearly explained what they needed to do and when a ticket could actually be
      considered finished.
    </p>
  </div>

  <h2>2. How the actual run compared to my expected plans</h2>

  <div class="card">
    <h3>Ticket 101</h3>
    <p>
      Mostly followed the expected plan. The Boss involved Inventory first, then
      Accounting, followed by Customer Service. The actual result went
      <em>further</em> than I originally expected: the team did not stop at
      placing the order but advanced the shop date, received the tee into
      inventory, and drafted a message saying it was ready.
    </p>

    <h3>Ticket 102</h3>
    <p>
      Followed the plan closely. Facilities checked the lease first, and
      Accounting was involved before the rent payment was made. Both agents did
      what I expected and the $2,400 payment was processed correctly. There were
      no major differences between the plan and the actual result.
    </p>

    <h3>Ticket 103</h3>
    <p>
      Reached the expected outcome. The team checked inventory and pricing,
      recognised that the shop could not afford the additional $264 restock, and
      offered the 8 hoodies already in stock instead.
    </p>
    <p>
      On the first attempt the Boss drafted the customer message itself rather
      than delegating it to Customer Service. The outcome was still appropriate,
      but the planned delegation was not followed, so I had the ticket re-run with
      the drafting handed to Customer Service where it belongs. In the final run
      <strong>all three tickets matched the plan</strong>.
    </p>

    <h3>Across all three</h3>
    <p>
      The plans were useful for deciding who should be involved and who could be
      left out. Every agent I expected to stay out of a ticket did stay out, on
      every run.
    </p>
    <p>
      However, <strong>Ticket 101 showed me that the plan also needs to consider
      what happens after an order is placed.</strong> I had originally treated the
      order and its delivery date as enough, but the actual run made it clear that
      stock needed to be received before the ticket could genuinely be considered
      complete.
    </p>
  </div>

  <h2>3. Would one agent with tools have been simpler?</h2>

  <div class="card">
    <p>
      For these three tickets, I think <strong>one agent with access to all the
      tools probably would have been simpler and cheaper</strong>. The tickets are
      closely related, and the same agent could check the records, work out the
      next step, and handle the ticket without passing information between
      different agents. Ticket 102 is a good example because the work was fairly
      straightforward: verify the lease, get approval, and pay the rent.
    </p>
    <p>
      <strong>The handoffs also created opportunities for mistakes.</strong>
      Accounting requested the wrong amount for the tee purchase order, and on the
      first attempt at Ticket 103 the Boss drafted the customer message instead of
      involving Customer Service.
    </p>
    <p>
      That said, <strong>I would keep some separation around financial
      decisions.</strong> Having another agent check affordability before money is
      committed provides an extra layer of control. It is easier to catch a
      mistake when the same agent is not responsible for every part of the
      decision.
    </p>
    <p>
      The final run used <strong>1,248,839 tokens</strong> across the three
      tickets, and the project records show that clearer rules reduced unnecessary
      loops compared with earlier runs &mdash; Ticket 103 alone had cost 995,949
      tokens on an earlier run without finishing. So I would not assume that
      changing the number of agents alone would solve the main problem.
    </p>
    <p>
      For this small shop, I would lean toward <strong>one main agent with the
      tools, while keeping human approval and an independent financial check where
      they matter.</strong>
    </p>

    <h3>Where the tokens actually went</h3>
    <p>
      I assumed the long shop rules were the expense, since every agent reloads
      them on every turn. They are not. The rules are about
      <strong>4,900 tokens</strong>, and all the prompt text across the whole run
      comes to roughly <strong>118,000 of the 1,248,839 &mdash; about 9%</strong>.
      The run averaged <strong>52,000 tokens a turn</strong>, so the cost is the
      <em>conversation</em> growing as each turn carries the accumulated history,
      not the instructions at the front of it.
    </p>
    <p>
      That changes what I would do about it. Shortening the rules would have saved
      almost nothing and cost me the detail that made the agents behave &mdash;
      the opposite of the right move. Fewer agents helps for a different reason
      than I first thought: not shorter prompts, but <strong>fewer separate
      conversations</strong>, each of which has to be told the ticket from scratch
      and then grows on its own.
    </p>
  </div>

  <h2>4. Three problems this team could solve with the tools we built</h2>

  <div class="card">
    <h3>1. Paying the new $8 vendor invoice</h3>
    <p>
      After the tee was received, Bulldog Print Co issued <strong>invoice 502 for
      $8</strong>. The team already has the tools to find the invoice, check the
      cash balance, request my approval, and pay it. Since the shop has
      <strong>$160</strong> remaining, this payment is affordable. Paying it would
      also prevent another unpaid invoice from blocking future orders.
    </p>

    <h3>2. Restocking the Crest Mug</h3>
    <p>
      The Crest Mug is out of stock, but its vendor, <strong>Elm City Gifts</strong>,
      has no unpaid invoice blocking shipments. The team can check the stock,
      confirm the vendor's lead time, prepare a purchase order, get human
      approval, and receive the mugs when they arrive. At <strong>$3.50 per
      unit</strong>, this is a more affordable restocking option than the hoodie
      order.
    </p>

    <h3>3. Reordering the missing 12 hoodies once the shop has enough cash</h3>
    <p>
      The team has already established that the remaining 12 hoodies would cost
      <strong>$264</strong>. It cannot afford that order with only $160 in the
      account, but it has the tools to check the vendor, prepare the purchase
      order, and request approval once sufficient cash is available. The team
      should not place the order until the shop can afford it and the purchase is
      approved.
    </p>
  </div>

  <h2>5. Three problems this team could not solve, and what would be needed</h2>

  <div class="card">
    <h3>1. Recording sales and money coming into the shop</h3>
    <p>
      The current system tracks payments and other cash outflows, but it does not
      record sales revenue. For example, selling the tee or the 8 available
      hoodies would not increase the cash balance in the model.
    </p>
    <p>
      <strong>What would be needed:</strong> a <code>sales</code> table and a tool
      to record sales, reduce inventory, and add the money received to the cash
      balance. Accounting could manage this, with a <strong>Sales agent</strong>
      becoming useful if the shop later needs to handle discounts, refunds, and
      sales reporting.
    </p>

    <h3>2. Actually sending messages to customers</h3>
    <p>
      The team can draft a message, but it cannot send it. This means Tauhid can
      have a tee ready for him while the message remains saved on the board.
    </p>
    <p>
      <strong>What would be needed:</strong> a customer messaging integration and
      a separate approval step, so that a human approves a message before it is
      sent. An inbound channel would also help the team handle customer replies.
      The existing <strong>Customer Service agent</strong> could manage this once
      those tools are available.
    </p>

    <h3>3. Handling incomplete or damaged deliveries</h3>
    <p>
      The current receiving process assumes the full order arrives in good
      condition. In a real shop, a vendor might send only 8 of 12 hoodies or
      deliver items in the wrong size.
    </p>
    <p>
      <strong>What would be needed:</strong> a receiving tool that records the
      actual quantity and condition, along with a way to record returns or damaged
      goods and adjust the vendor bill. <strong>Inventory</strong> could handle
      this without necessarily needing another agent, but the tools would have to
      support partial deliveries and returns first.
    </p>
  </div>"""
