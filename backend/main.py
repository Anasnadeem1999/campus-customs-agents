"""FastAPI backend for the Campus Customs dashboard.

Run it from this folder, exactly as the assignment asks:

    cd backend
    uvicorn main:app --reload --port 8000

That command imports this file as the top-level module `main`, not as
`backend.main`, so the repository root is put on `sys.path` below before
anything else is imported. Without it, `from backend.models import ...` fails
the moment the working directory is `backend/` -- and the same insert is what
lets `python -m backend.main` and the test suite import it the other way
round. Both entry points work; neither is a special case.

### What the dashboard can do through here

| Route | Does |
|---|---|
| `GET /api/tickets` | the three tickets and whether each is open or resolved |
| `POST /api/tickets/{ticket_id}/run` | run the agent team on one ticket |
| `GET /api/events` | recent agent steps -- who spoke, what tools they used |
| `GET /api/approvals` | what the agents have asked a human to approve |
| `POST /api/approvals/{approval_id}/approve` | **the human's click. This is what moves cash.** |
| `GET /api/cash` | the current checking balance |
| `POST /api/reset` | reset the database for a fresh run |

### The one route that spends money

Everywhere else in this project, agents prepare and humans decide. The
approve route is where the deciding actually happens, so it is the only place
in the whole backend that causes cash to leave the shop.

It is deliberately not an MCP tool and never will be. The agents reach the
shop only through MCP, and MCP has no approving verb -- so an agent cannot
call this even if a prompt told it to. The route reaches the approval board
directly, exactly as `scripts/approve.py` does, because that is the human's
side of the gate rather than the team's.

Every route reads shop facts through the MCP server. Nothing here opens
SQLite, with one deliberate exception: `POST /api/reset` runs the reset
script, which is a file-copy operation on the database rather than a question
about the shop.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    # Must happen before the backend/ imports below -- see the module docstring.
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from backend import audit, shop  # noqa: E402
from backend.agent_team import OUTPUT_TOOL_NAMES, AgentTeam, new_run_id  # noqa: E402
from backend.model_config import REQUIRED_MODEL  # noqa: E402
from backend.models import RunRecord, utc_now  # noqa: E402
from mcp_server import board  # noqa: E402

app = FastAPI(
    title="Campus Customs — operations backend",
    description="The API behind the agent dashboard.",
    version="1.0.0",
)

# The dashboard is served by Vite on another port in development, so the
# browser treats it as a different origin. Localhost only -- this backend
# moves real money in the shop's books and has no business answering the
# public internet.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

#: Agent runs in flight, keyed by run id. A run takes minutes, which is far
#: too long to hold an HTTP request open, so the route starts the work and
#: returns immediately; the board follows along through `GET /api/events`.
_RUNS: dict[str, dict[str, Any]] = {}

_TEAM: AgentTeam | None = None


def _as_fields(arguments: Any) -> dict[str, Any]:
    """Give the dashboard real argument fields rather than one opaque blob.

    Older steps in the trail stored the provider's raw JSON string under a
    `raw` key, before it was parsed at write time. Unpacking it here means the
    board shows *which* invoice was paid for those steps too, instead of a
    wall of escaped JSON.
    """
    if not isinstance(arguments, dict):
        return {"value": arguments}
    if set(arguments) == {"raw"} and isinstance(arguments["raw"], str):
        try:
            parsed = json.loads(arguments["raw"])
        except (json.JSONDecodeError, TypeError):
            return arguments
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    return arguments


def team() -> AgentTeam:
    """Build the agent team once and reuse it.

    Construction loads five prompt files and opens an MCP toolset, so doing it
    per request would make every run slower and spawn a server process each
    time.
    """
    global _TEAM
    if _TEAM is None:
        _TEAM = AgentTeam()
    return _TEAM


# --- tickets -------------------------------------------------------------


@app.get("/api/tickets", summary="The three tickets and whether each is open or resolved")
async def get_tickets() -> dict[str, Any]:
    """Return every ticket on the board with its current status."""
    try:
        payload = await shop.call_tool("list_tickets", {"status": None})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"Could not read the ticket board: {exc}") from exc

    tickets = []
    for t in payload["tickets"]:
        tickets.append(
            {
                **t,
                # The dashboard colours rows on this, so it is computed here
                # once rather than in three places in the frontend.
                "is_resolved": t["status"] == "resolved",
                "is_open": t["status"] not in ("resolved",),
            }
        )
    return {
        "shop_date_today": payload["shop_date_today"],
        "ticket_count": len(tickets),
        "open_count": sum(1 for t in tickets if t["is_open"]),
        "resolved_count": sum(1 for t in tickets if t["is_resolved"]),
        "tickets": tickets,
    }


async def _run_team(ticket: dict[str, Any], run_id: str) -> None:
    """Work one ticket in the background and record how it went."""
    _RUNS[run_id] = {
        "run_id": run_id,
        "ticket_id": int(ticket["id"]),
        "status": "running",
        "started_at": utc_now(),
        "first_step": audit.next_step_number(),
    }
    audit.start_run(
        RunRecord(
            run_id=run_id,
            started_at=utc_now(),
            shop_date_today="read from desk.date_today by the tools",
            model_requested=REQUIRED_MODEL,
            tickets_in_scope=[int(ticket["id"])],
            database="data/campus_customs_new.db",
            reset_before_run=False,
        )
    )
    try:
        resolution = await team().work_ticket(ticket, run_id)
        _RUNS[run_id].update(
            status="finished",
            finished_at=utc_now(),
            resolution=resolution.model_dump() if resolution else None,
        )
        audit.finish_run(run_id, finished_at=utc_now(), outcome="completed")
    except Exception as exc:  # noqa: BLE001 -- a failed run must still be reportable
        _RUNS[run_id].update(status="failed", finished_at=utc_now(), error=str(exc))
        audit.finish_run(run_id, finished_at=utc_now(), outcome="failed", error=str(exc))


@app.post("/api/tickets/{ticket_id}/run", summary="Run the agent team on one ticket")
async def run_ticket(ticket_id: int, wait: bool = Query(False)) -> dict[str, Any]:
    """Hand one ticket to the Boss and let the team work it.

    Returns as soon as the run starts. A run takes minutes, so holding the
    request open would time out the browser long before the team finished;
    the dashboard polls `GET /api/events` to watch it instead.

    Args:
        wait: block until the run finishes. For scripts and tests, not the UI.
    """
    payload = await shop.call_tool("list_tickets", {"status": None})
    matches = [t for t in payload["tickets"] if int(t["id"]) == ticket_id]
    if not matches:
        raise HTTPException(404, f"There is no ticket {ticket_id} on the board.")
    ticket = matches[0]

    # Refuse to start a second run on a ticket already being worked: two teams
    # on one ticket would race for the same cash and raise duplicate approvals.
    for run in _RUNS.values():
        if run["ticket_id"] == ticket_id and run["status"] == "running":
            raise HTTPException(
                409,
                f"Ticket {ticket_id} is already being worked by run {run['run_id']}.",
            )

    run_id = new_run_id()
    task = asyncio.create_task(_run_team(ticket, run_id))
    if wait:
        await task
        return _RUNS[run_id]

    # Hold a reference so the task is not garbage-collected mid-run.
    _RUNS.setdefault(run_id, {})["_task"] = task
    await asyncio.sleep(0)  # let the task register its start state
    return {
        "run_id": run_id,
        "ticket_id": ticket_id,
        "status": _RUNS[run_id].get("status", "starting"),
        "poll": "/api/events",
    }


@app.get("/api/runs/{run_id}", summary="How one agent run is going")
async def get_run(run_id: str) -> dict[str, Any]:
    run = _RUNS.get(run_id)
    if run is None:
        raise HTTPException(404, f"No run {run_id} in this server's memory.")
    return {k: v for k, v in run.items() if not k.startswith("_")}


# --- events --------------------------------------------------------------


@app.get("/api/events", summary="Recent agent steps — what each agent said and which tools it used")
async def get_events(
    since: int = Query(0, description="Return steps numbered above this. 0 for all."),
    limit: int = Query(50, le=500),
    ticket_id: int | None = Query(None),
) -> dict[str, Any]:
    """The feed the board refreshes from.

    Step numbers never repeat, across runs or restarts, so the dashboard polls
    with the highest `step` it has already drawn and gets only what is new.
    That is cheaper than re-sending the whole trail and it cannot double-draw
    an event.
    """
    steps = audit._load()["steps"]  # noqa: SLF001 -- same package, one reader
    if ticket_id is not None:
        steps = [s for s in steps if s.get("ticket_id") == ticket_id]
    fresh = [s for s in steps if int(s.get("step", 0)) > since][:limit]

    events = []
    for s in fresh:
        events.append(
            {
                "step": s["step"],
                "run_id": s["run_id"],
                "ticket_id": s.get("ticket_id"),
                "agent": s["agent"],
                "delegated_by": s.get("delegated_by"),
                "task": s.get("task"),
                "says": s.get("output"),
                "tools_used": [
                    {
                        "tool": c["tool"],
                        "arguments": _as_fields(c.get("arguments")),
                        "is_error": c.get("is_error", False),
                    }
                    for c in s.get("tool_calls", [])
                    # Filtered on read as well as on write: steps recorded
                    # before that filter existed are still in the trail, and
                    # the board should never show a tool the MCP server does
                    # not have, whenever the step happened to be written.
                    if c["tool"] not in OUTPUT_TOOL_NAMES
                ],
                "blocked_on": s.get("blocked_on"),
                "needs_human": s.get("needs_human"),
                "model": s.get("model", {}).get("resolved"),
                "model_ok": s.get("model", {}).get("ok"),
                "tokens": (s.get("usage") or {}).get("total_tokens"),
                "duration_seconds": s.get("duration_seconds"),
                "started_at": s.get("started_at"),
                "error": s.get("error"),
            }
        )

    return {
        "since": since,
        "returned": len(events),
        "latest_step": max((e["step"] for e in events), default=since),
        "events": events,
    }


# --- approvals: the human's side of the gate ------------------------------


class ApproveBody(BaseModel):
    """Who is approving, and anything a purchase order needs to be placed."""

    approved_by: str = Field(
        description="The person approving. Written into payments.approved_by."
    )
    sku: str | None = Field(default=None, description="Purchase orders only.")
    size: str | None = Field(default=None, description="Purchase orders only.")
    qty: int | None = Field(default=None, description="Purchase orders only.")
    needed_for_ticket: int | None = None


@app.get("/api/approvals", summary="What the agents have asked a human to approve")
async def get_approvals(status: str | None = Query(None)) -> dict[str, Any]:
    payload = await shop.call_tool("list_approvals", {"status": status})
    return payload


@app.post(
    "/api/approvals/{approval_id}/approve",
    summary="Approve a payment or purchase — this is the call that moves cash",
)
async def approve(approval_id: int, body: ApproveBody) -> dict[str, Any]:
    """The human clicks approve, and the money actually moves.

    Everywhere else agents only *prepare*. This route is where the decision is
    made and carried out, and it is the only thing in the backend that causes
    cash to leave the shop.

    Two steps, in this order:

    1. **Approve** — recorded on the board. Deliberately not an MCP tool, so
       no agent can reach it. This is the same action `scripts/approve.py`
       performs, exposed for the dashboard's button.
    2. **Execute** — through the MCP tools, so every rule still applies. The
       payment refuses if cash will not cover it, if the approval is already
       spent, or if the amount no longer matches the bill, and it writes
       nothing at all when it refuses.

    A **purchase order** is approved but not placed here, because placing one
    moves no cash and needs the SKU, size and quantity the agent decided on.
    Pass them to place it in the same call; otherwise the team places it on
    its next run. A **price override** is approved and nothing is executed —
    there is no cash in it.
    """
    if not body.approved_by.strip():
        raise HTTPException(422, "approved_by is required: an approval has to name a person.")

    try:
        record = board.get_approval(approval_id)
    except board.BoardError as exc:
        raise HTTPException(404, str(exc)) from exc

    if record.get("status") == "approved" and record.get("consumed_by_payment_id"):
        raise HTTPException(
            409,
            f"Approval {approval_id} was already paid on payment "
            f"{record['consumed_by_payment_id']}.",
        )
    if record.get("status") == "rejected":
        raise HTTPException(409, f"Approval {approval_id} was rejected; it cannot be approved now.")

    shop_date = (await shop.call_tool("get_cash_position"))["shop_date_today"]
    if record.get("status") != "approved":
        board.update_approval(
            approval_id,
            status="approved",
            approved_by=body.approved_by.strip(),
            approved_at=shop_date,
        )

    kind, ref_id = record["kind"], record.get("ref_id")
    executed: dict[str, Any] | None = None
    try:
        if kind == "invoice_payment":
            executed = await shop.call_tool(
                "pay_invoice", {"invoice_id": ref_id, "approval_id": approval_id}
            )
        elif kind == "rent_payment":
            executed = await shop.call_tool(
                "pay_rent", {"lease_id": ref_id, "approval_id": approval_id}
            )
        elif kind == "purchase_order" and body.sku and body.size and body.qty:
            executed = await shop.call_tool(
                "place_purchase_order",
                {
                    "vendor_id": ref_id,
                    "sku": body.sku,
                    "size": body.size,
                    "qty": body.qty,
                    "approval_id": approval_id,
                    "needed_for_ticket": body.needed_for_ticket,
                },
            )
    except Exception as exc:  # noqa: BLE001
        # The approval stands -- a human did say yes -- but the execution was
        # refused. Say which, plainly, rather than reporting a silent success.
        raise HTTPException(
            409,
            f"Approval {approval_id} is approved, but carrying it out was refused: {exc}",
        ) from exc

    cash = await shop.call_tool("get_cash_position")
    return {
        "approval_id": approval_id,
        "kind": kind,
        "approved_by": body.approved_by.strip(),
        "executed": executed is not None,
        "result": executed,
        "cash_moved": bool(executed and executed.get("paid")),
        "checking_balance": cash["total_balance"],
        "note": (
            "Approved and paid." if executed and executed.get("paid")
            else "Approved. Nothing was paid -- this kind moves no cash."
        ),
    }


@app.post("/api/approvals/{approval_id}/reject", summary="Reject a request instead of approving it")
async def reject(approval_id: int, body: ApproveBody) -> dict[str, Any]:
    """Say no. Recorded with the name, so a refusal is as accountable as a yes."""
    try:
        record = board.get_approval(approval_id)
    except board.BoardError as exc:
        raise HTTPException(404, str(exc)) from exc
    if record.get("status") != "pending":
        raise HTTPException(409, f"Approval {approval_id} is already '{record['status']}'.")

    shop_date = (await shop.call_tool("get_cash_position"))["shop_date_today"]
    board.update_approval(
        approval_id, status="rejected", rejected_by=body.approved_by.strip(),
        rejected_at=shop_date,
    )
    return {"approval_id": approval_id, "status": "rejected", "by": body.approved_by.strip()}


# --- cash ----------------------------------------------------------------


@app.get("/api/cash", summary="The current checking balance")
async def get_cash() -> dict[str, Any]:
    """The balance, plus what is already promised to approvals not yet paid.

    Both figures, because the raw balance alone is misleading: money a human
    has approved is spoken for even while it is still sitting in the account.
    """
    payload = await shop.call_tool("get_cash_position")
    checking = next(
        (a for a in payload["accounts"] if a["name"] == "checking"),
        payload["accounts"][0] if payload["accounts"] else None,
    )
    return {
        "shop_date_today": payload["shop_date_today"],
        "checking_balance": checking["balance"] if checking else 0.0,
        "accounts": payload["accounts"],
        "approved_not_yet_paid": payload["approved_not_yet_paid"],
        "uncommitted": payload["uncommitted"],
    }


# --- reset ---------------------------------------------------------------


@app.post("/api/reset", summary="Reset the database to its original values for a fresh run")
async def reset(clear_board: bool = Query(True), clear_audit: bool = Query(False)) -> dict[str, Any]:
    """Restore the working database from the pristine seed.

    The seed itself is never touched -- `reset_db.py` hashes it before and
    after to prove it.

    Args:
        clear_board: also clear approval requests and drafts. On by default,
            because leaving an approval behind that points at an invoice the
            reset has just reopened is a confusing half-state.
        clear_audit: also wipe `output/audit_trail.json`. **Off by default and
            deliberately so** -- the trail is meant to accumulate across runs,
            and a reset is about the shop's data, not its history.
    """
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "reset_db.py")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise HTTPException(500, f"reset_db.py failed: {proc.stderr or proc.stdout}")

    cleared = []
    if clear_board:
        for path in (board.APPROVALS, board.DRAFTS):
            if path.exists():
                path.unlink()
                cleared.append(path.name)
    if clear_audit and audit.AUDIT_PATH.exists():
        audit.AUDIT_PATH.unlink()
        cleared.append(audit.AUDIT_PATH.name)

    _RUNS.clear()
    cash = await shop.call_tool("get_cash_position")
    return {
        "reset": True,
        "cleared": cleared,
        "audit_trail_kept": not clear_audit,
        "checking_balance": cash["total_balance"],
        "detail": proc.stdout.strip().splitlines()[:3],
    }


@app.get("/api/health", summary="Is the backend up and can it reach the shop?")
async def health() -> dict[str, Any]:
    try:
        cash = await shop.call_tool("get_cash_position")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"MCP server unreachable: {exc}") from exc
    return {
        "ok": True,
        "model": REQUIRED_MODEL,
        "shop_date_today": cash["shop_date_today"],
        "checking_balance": cash["total_balance"],
    }

