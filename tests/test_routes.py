"""The HTTP routes, exercised against a real MCP server but no model.

Everything here is real except the agents: the routes talk to the actual
`campus-customs` server over stdio and the actual working database, so a
refusal in a tool is a refusal in the response. Only `POST /run` is skipped,
because that one needs the gateway and costs money -- it is covered by the
live runs recorded in the audit trail instead.

The database is reset through the API itself at the start, which also tests
the reset route.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from mcp_server import board  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.post("/api/reset")
        yield c


# --- the board -----------------------------------------------------------

def test_tickets_route_returns_three_tickets_with_open_or_resolved(client):
    r = client.get("/api/tickets")
    assert r.status_code == 200
    body = r.json()
    assert body["ticket_count"] == 3
    assert {t["id"] for t in body["tickets"]} == {101, 102, 103}
    for t in body["tickets"]:
        # The question the dashboard actually asks of each row.
        assert t["is_resolved"] == (t["status"] == "resolved")
        assert t["is_open"] != t["is_resolved"]


def test_cash_route_returns_the_checking_balance(client):
    body = client.get("/api/cash").json()
    assert body["checking_balance"] == 3400.0
    assert body["shop_date_today"] == "2026-08-31"
    # Both figures, because the raw balance alone misleads once money is
    # approved but not yet paid.
    assert "approved_not_yet_paid" in body and "uncommitted" in body


def test_reset_restores_the_shop_and_keeps_the_audit_trail(client):
    body = client.post("/api/reset").json()
    assert body["reset"] is True
    assert body["checking_balance"] == 3400.0
    # The trail is history, not state -- a reset must not erase it by default.
    assert body["audit_trail_kept"] is True


def test_events_route_pages_by_step_number(client):
    all_events = client.get("/api/events?limit=500").json()
    if all_events["returned"] == 0:
        pytest.skip("no runs recorded yet")
    latest = all_events["latest_step"]
    # Polling with the newest step already drawn must return nothing new,
    # which is what stops the board double-drawing an event.
    assert client.get(f"/api/events?since={latest}").json()["returned"] == 0


def test_events_never_report_the_synthetic_output_tool(client):
    body = client.get("/api/events?limit=500").json()
    if body["returned"] == 0:
        pytest.skip("no runs recorded yet")
    for event in body["events"]:
        for tool in event["tools_used"]:
            assert tool["tool"] != "final_result", (
                "final_result is pydantic-ai's structured-output call, not a tool "
                "the agent chose -- showing it would put a non-existent tool on the board"
            )
            # Arguments must be real fields, not one opaque JSON blob.
            assert isinstance(tool["arguments"], dict)


# --- the approval gate over HTTP -----------------------------------------

def test_running_a_ticket_that_does_not_exist_is_404(client):
    assert client.post("/api/tickets/999/run").status_code == 404


def test_approving_something_that_does_not_exist_is_404(client):
    r = client.post("/api/approvals/9999/approve", json={"approved_by": "Someone"})
    assert r.status_code == 404


def test_an_approval_must_name_a_person(client):
    r = client.post("/api/approvals/1/approve", json={"approved_by": "   "})
    assert r.status_code == 422
    assert "name a person" in r.json()["detail"]


def test_the_approve_route_pays_and_the_cash_actually_moves(client):
    """The one route that spends money, end to end.

    The agents only ever prepare; this is the human's click. So the request is
    created the way an agent would, then approved through the API, and the
    balance has to move as a result.
    """
    client.post("/api/reset")
    before = client.get("/api/cash").json()["checking_balance"]
    assert before == 3400.0

    # Stand in for the agent raising the request.
    from mcp_server import server as shop_server
    req = shop_server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent due 2026-09-02.", requested_by="facilities",
    )
    approval_id = req["approval_id"]

    listed = client.get("/api/approvals?status=pending").json()
    assert any(a["id"] == approval_id for a in listed["approvals"])

    r = client.post(
        f"/api/approvals/{approval_id}/approve", json={"approved_by": "Anas Nadeem"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["cash_moved"] is True
    assert body["checking_balance"] == 1000.0
    assert body["result"]["approved_by"] == "Anas Nadeem"
    assert body["result"]["settles"]["next_due"] == "2026-10-02"

    assert client.get("/api/cash").json()["checking_balance"] == 1000.0

    # And it cannot be paid twice.
    again = client.post(
        f"/api/approvals/{approval_id}/approve", json={"approved_by": "Anas Nadeem"}
    )
    assert again.status_code == 409
    assert "already paid" in again.json()["detail"]
    assert client.get("/api/cash").json()["checking_balance"] == 1000.0


def test_a_rejected_request_cannot_then_be_approved(client):
    client.post("/api/reset")
    from mcp_server import server as shop_server
    req = shop_server.request_approval(
        kind="invoice_payment", amount=840.0, ref_id=501,
        reason="Unblock the vendor.", requested_by="accounting",
    )
    approval_id = req["approval_id"]

    assert client.post(
        f"/api/approvals/{approval_id}/reject", json={"approved_by": "Anas Nadeem"}
    ).status_code == 200

    r = client.post(
        f"/api/approvals/{approval_id}/approve", json={"approved_by": "Anas Nadeem"}
    )
    assert r.status_code == 409
    assert client.get("/api/cash").json()["checking_balance"] == 3400.0, "a no costs nothing"


def test_a_payment_the_balance_cannot_cover_is_refused_over_http(client):
    """A refusal in the tool has to surface as an HTTP error, not a quiet success."""
    client.post("/api/reset")
    from mcp_server import server as shop_server
    from mcp_server.db import connect

    conn = connect(read_only=False)
    conn.execute("UPDATE cash_accounts SET balance = 100.0 WHERE name='checking'")
    conn.commit()
    conn.close()

    req = shop_server.request_approval(
        kind="rent_payment", amount=2400.0, ref_id=1,
        reason="Rent.", requested_by="facilities",
    )
    r = client.post(
        f"/api/approvals/{req['approval_id']}/approve", json={"approved_by": "Anas Nadeem"}
    )
    assert r.status_code == 409
    assert "refused" in r.json()["detail"].lower()
    assert client.get("/api/cash").json()["checking_balance"] == 100.0, "nothing was written"
    client.post("/api/reset")


def test_no_route_lets_an_agent_approve(client):
    """The gate is structural: approving is HTTP, and agents only speak MCP.

    An agent reaches the shop through the MCP server, which has no approving
    tool. The approve route lives here instead, where nothing the agent can
    call will reach it.
    """
    import asyncio
    from mcp_server import server as shop_server

    names = {t.name for t in asyncio.run(shop_server.mcp.list_tools())}
    assert not {n for n in names if "approve" in n and n != "list_approvals"}

    approve_routes = [r for r in app.routes if "approve" in getattr(r, "path", "")]
    assert approve_routes, "the human needs a way to approve"
    for route in approve_routes:
        assert set(route.methods) == {"POST"}
