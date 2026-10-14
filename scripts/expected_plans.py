"""The Expected Plans for the three tickets, in the owner's words.

Written as the plan of record after the owner reviewed all three tickets. The
page itself says when each plan was written and that the Actual sections are
filled separately, so a reader can see which came first.

Kept here rather than inline in the HTML so that regenerating the page cannot
silently lose them.
"""

PLANS = {
    101: """  <h2>Expected</h2>

  <div class="card">
    <p class="note">
      Owner's plan, reviewed 2026-10-14. The <strong>Actual</strong> section
      below is filled separately, from the agent run.
    </p>

    <div class="first-call">
      <strong>Inventory goes first.</strong>
      <p style="margin:8px 0 0">
        The size Tauhid asked for is out of stock, so the supply position has to
        be established before anything else can be decided. Until we know
        whether we can get a size S tee at all, there is nothing to cost and
        nothing to tell the customer.
      </p>
    </div>

    <h3>Who is needed, and why</h3>
    <table>
      <thead><tr><th>Agent</th><th>Why they are needed</th></tr></thead>
      <tbody>
        <tr>
          <td><strong>Inventory</strong></td>
          <td>Confirm <code>CC-TEE-WHITE</code> size S is at zero, find who can reprint it, and surface anything stopping that vendor from shipping.</td>
        </tr>
        <tr>
          <td><strong>Accounting</strong></td>
          <td>Check the $840 unpaid invoice and the cash we have, then prepare the payment for approval. The invoice is what is blocking the vendor, so it has to be dealt with before we can order.</td>
        </tr>
        <tr>
          <td><strong>Customer Service</strong></td>
          <td>Draft the update to Tauhid once we actually know what we can tell him. Not before.</td>
        </tr>
        <tr>
          <td><strong>Facilities</strong></td>
          <td><em>Not needed.</em> No lease or premises question on this ticket.</td>
        </tr>
      </tbody>
    </table>

    <h3>Tools and actions we expect</h3>
    <p>
      <code>check_stock_by_size</code> &middot; <code>find_restock_vendors</code> &middot;
      <code>list_invoices</code> &middot; <code>get_cash_position</code> &middot;
      <code>request_approval</code> &middot; <code>pay_invoice</code> &middot;
      <code>place_purchase_order</code> &middot; <code>advance_shop_date</code> &middot;
      <code>receive_purchase_order</code> &middot; <code>draft_customer_message</code> &middot;
      <code>update_ticket</code>
    </p>

    <h3>Approvals</h3>
    <p>
      <strong>Two separate human approvals</strong>, not one. First to pay the
      $840 invoice, which clears the vendor to ship. Then a second, separate
      approval for the $8 purchase order for the tee itself. Neither is implied
      by the other.
    </p>

    <h3>Before this can be marked resolved</h3>
    <ul class="tight">
      <li>Invoice 501 is <strong>paid</strong> and the vendor is free to ship.</li>
      <li>The tee has been ordered <em>and</em> <strong>has actually arrived</strong>
          &mdash; stock for size S is above zero.</li>
      <li>Tauhid has been told where his order stands.</li>
    </ul>
    <p>
      <strong>I would not mark this resolved just because the order was
      placed.</strong> If the delivery is still pending, the ticket stays open
      with the expected date recorded on it.
    </p>
  </div>""",

    102: """  <h2>Expected</h2>

  <div class="card">
    <p class="note">
      Owner's plan, reviewed 2026-10-14. The <strong>Actual</strong> section
      below is filled separately, from the agent run.
    </p>

    <div class="first-call">
      <strong>Facilities takes the lead.</strong>
      <p style="margin:8px 0 0">
        This is a rent issue, and the lease is the record. The notice is only a
        claim until someone checks it against lease 1.
      </p>
    </div>

    <h3>Who is needed, and why</h3>
    <table>
      <thead><tr><th>Agent</th><th>Why they are needed</th></tr></thead>
      <tbody>
        <tr>
          <td><strong>Facilities</strong></td>
          <td>Lead the ticket. Read the lease for the real amount, the landlord and the due date, rather than taking the email's word for it.</td>
        </tr>
        <tr>
          <td><strong>Accounting</strong></td>
          <td>Verify the $2,400, check the cash balance, and prepare the payment for human approval.</td>
        </tr>
        <tr>
          <td><strong>Boss</strong></td>
          <td>Close the ticket once the payment has gone through and the records are updated.</td>
        </tr>
        <tr>
          <td><strong>Inventory and Customer Service</strong></td>
          <td><em>Not needed.</em> There is no stock question, and the landlord is not a customer. Nobody else should be involved unless a problem comes up.</td>
        </tr>
      </tbody>
    </table>

    <h3>Tools and actions we expect</h3>
    <p>
      <code>check_rent_due</code> &middot; <code>get_cash_position</code> &middot;
      <code>request_approval</code> &middot; <code>pay_rent</code> &middot;
      <code>update_ticket</code>
    </p>

    <h3>Approvals</h3>
    <p>One human approval: the $2,400 rent payment on lease 1.</p>

    <h3>Before this can be marked resolved</h3>
    <ul class="tight">
      <li>The rent is <strong>paid</strong>, not merely confirmed as owed.</li>
      <li>The records are updated &mdash; the cash balance has moved and the
          lease's next due date has rolled forward.</li>
      <li>The Boss has checked both and closed it.</li>
    </ul>
    <p>
      This is the simplest of the three and should look it. Two agents, one
      approval, done.
    </p>
  </div>""",

    103: """  <h2>Expected</h2>

  <div class="card">
    <p class="note">
      Owner's plan, reviewed 2026-10-14. The <strong>Actual</strong> section
      below is filled separately, from the agent run.
    </p>

    <div class="first-call">
      <strong>Inventory checks the hoodie stock first.</strong>
      <p style="margin:8px 0 0">
        The ticket reads like a pricing question, but the real question is
        whether we can supply the order at all. We have <strong>8</strong> and
        need <strong>12 more</strong> to fill the request for 20. There is no
        point discussing a discount on hoodies we do not have.
      </p>
    </div>

    <h3>Who is needed, and why</h3>
    <table>
      <thead><tr><th>Agent</th><th>Why they are needed</th></tr></thead>
      <tbody>
        <tr>
          <td><strong>Inventory</strong></td>
          <td>Confirm 8 size M on hand against 20 requested, a shortfall of 12, and whether the vendor can actually supply them.</td>
        </tr>
        <tr>
          <td><strong>Accounting</strong></td>
          <td>Work out whether we can afford the additional <strong>$264</strong>, and flag that this vendor carries the same unpaid invoice that has to be cleared first.</td>
        </tr>
        <tr>
          <td><strong>Customer Service</strong></td>
          <td>Draft a reply explaining what we can offer &mdash; without promising all 20.</td>
        </tr>
        <tr>
          <td><strong>Facilities</strong></td>
          <td><em>Not needed.</em> Nothing here touches the lease or the premises.</td>
        </tr>
      </tbody>
    </table>

    <h3>Tools and actions we expect</h3>
    <p>
      <code>check_stock_by_size</code> &middot; <code>find_restock_vendors</code> &middot;
      <code>quote_discount</code> &middot; <code>list_invoices</code> &middot;
      <code>get_cash_position</code> &middot; <code>request_approval</code> &middot;
      <code>draft_customer_message</code> &middot; <code>update_ticket</code>
    </p>

    <h3>Approvals</h3>
    <p>
      Any restock purchase order and any discount on the list price need human
      approval. <strong>I expect the $264 restock to be refused:</strong> after
      paying the $840 invoice and the $2,400 rent we are left with
      <strong>$160</strong>, which does not cover it.
    </p>

    <h3>Before this can be marked resolved</h3>
    <ul class="tight">
      <li>Either the customer's request is <strong>fulfilled</strong>, or there
          is a <strong>clear, documented outcome</strong> &mdash; what we can
          supply, at what price, and what we are declining and why.</li>
      <li>The draft to the Yale AI Club is on the board, offering only what we
          can actually deliver.</li>
    </ul>
    <p>
      A reasoned no, written down and explained, is a finished ticket. A vague
      promise of 20 hoodies is not.
    </p>
  </div>""",
}

OVERALL_NOTE = """  <div class="card">
    <h3 style="margin-top:0">How I want these worked, across all three</h3>
    <ul class="tight">
      <li><strong>Keep the agent involvement focused</strong> on what each
          ticket actually needs. Nobody should be pulled in to confirm something
          a colleague has already established.</li>
      <li><strong>Every payment and purchase order needs human approval</strong>
          &mdash; separately, each time.</li>
      <li><strong>Placing an order does not count as fulfilling it.</strong>
          A ticket is finished when the thing that was asked for has happened,
          or when there is a clear written outcome explaining why it has not.</li>
    </ul>
  </div>"""
