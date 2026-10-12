"""Run the agent team over the open tickets.

    python -m backend.run_tickets              # reset first, then work every open ticket
    python -m backend.run_tickets --ticket 101 # one ticket
    python -m backend.run_tickets --no-reset   # continue on the current database
    python -m backend.run_tickets --dry-run    # wiring check, no model calls

Constraint 2 says reset the database before any full ticket-resolution run, so
that is the default rather than a flag someone has to remember. `--no-reset` is
there for picking a run back up after approving something mid-flight, which is
the normal human-in-the-loop rhythm:

    python -m backend.run_tickets --ticket 101   # team asks for approval, stops
    python scripts/approve.py --list             # read what it asked for
    python scripts/approve.py --id 1 --by "Anas Nadeem"
    python -m backend.run_tickets --ticket 101 --no-reset   # team pays and finishes

The ticket list is read from the MCP server, not from this file, so the run
works whatever is on the board.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import audit  # noqa: E402
from backend.agent_team import AgentTeam, RunState, new_run_id  # noqa: E402
from backend.model_config import REQUIRED_MODEL  # noqa: E402
from backend.models import RunRecord, utc_now  # noqa: E402


def reset_database() -> None:
    print("resetting the working database from the pristine seed...")
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "reset_db.py")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"reset_db.py failed:\n{proc.stdout}\n{proc.stderr}")
    print(proc.stdout.strip())


#: Statuses that still count as work. `awaiting_approval` has to be in here:
#: the team parks a ticket there when it raises an approval and stops, so a
#: resume run after the human approves would otherwise find nothing to do and
#: the ticket would sit half-finished forever.
UNFINISHED = ("open", "awaiting_approval", "blocked")


async def read_board(team: AgentTeam, status: str | None = None) -> list[dict]:
    """Read the ticket board through MCP -- the same door the agents use.

    The runner needs the board before any agent exists to ask for it, so it
    speaks to the MCP client underneath the toolset directly. Still the one
    server, still the one database: this is not a second route to shop facts,
    it is the same route without an agent in front of it.
    """
    async with team.mcp_client() as client:
        result = await client.call_tool("list_tickets", {"status": status})

    payload = getattr(result, "structured_content", None) or getattr(result, "data", None)
    if payload is None:
        blocks = getattr(result, "content", result)
        payload = json.loads(blocks[0].text if isinstance(blocks, list) else blocks)
    return payload["tickets"]


async def main_async(args: argparse.Namespace) -> int:
    team = AgentTeam()

    board = await read_board(team)
    if args.ticket:
        tickets = [t for t in board if int(t["id"]) == args.ticket]
        if not tickets:
            raise SystemExit(f"There is no ticket {args.ticket} on the board.")
        if tickets[0]["status"] == "resolved":
            raise SystemExit(f"Ticket {args.ticket} is already resolved; nothing to do.")
    else:
        tickets = [t for t in board if t["status"] in UNFINISHED]

    run_id = new_run_id()
    shop_date = None
    audit.start_run(
        RunRecord(
            run_id=run_id,
            started_at=utc_now(),
            shop_date_today=shop_date or "read from desk.date_today by the tools",
            model_requested=REQUIRED_MODEL,
            tickets_in_scope=[int(t["id"]) for t in tickets],
            database="data/campus_customs_new.db",
            reset_before_run=not args.no_reset,
        )
    )
    print(f"run {run_id}: {len(tickets)} ticket(s) -> {[t['id'] for t in tickets]}")

    if args.dry_run:
        print("--dry-run: wiring is built and the board was read through MCP. "
              "No model was called.")
        audit.finish_run(run_id, finished_at=utc_now(), outcome="dry-run")
        return 0

    resolutions, model_failures = [], []
    for ticket in tickets:
        print(f"\n--- ticket {ticket['id']}: {ticket['subject']} ---")
        resolution = await team.work_ticket(ticket, run_id)
        if resolution is None:
            print("  the team could not produce a resolution; see the audit trail.")
            continue
        resolutions.append(resolution.model_dump())
        print(f"  outcome : {resolution.outcome}")
        print(f"  decision: {resolution.decision}")
        if resolution.blocked_on:
            print(f"  blocked : {resolution.blocked_on}")
        if resolution.approvals_raised:
            print(f"  approvals waiting on a human: {resolution.approvals_raised}")

    steps = audit.steps_for_run(run_id)
    model_failures = [s for s in steps if not s["model"]["ok"]]
    audit.finish_run(
        run_id,
        finished_at=utc_now(),
        outcome="completed",
        steps_recorded=len(steps),
        resolutions=resolutions,
        model_check_failures=len(model_failures),
    )

    print(f"\n{len(steps)} step(s) appended to {audit.AUDIT_PATH.name}")
    if model_failures:
        # Loud, and last, so it cannot be missed in the scroll.
        print("\n*** MODEL POLICY FAILURE ***")
        for step in model_failures:
            print(f"  step {step['step']} ({step['agent']}): {step['model']['note']}")
        print("This run is void for grading. Check MODEL_NAME in .env.")
        return 1

    resolved = sum(1 for r in resolutions if r["outcome"] == "resolved")
    waiting = sum(1 for r in resolutions if r["outcome"] == "awaiting_approval")
    print(f"every step ran on {REQUIRED_MODEL} (verified against the gateway's own answer)")
    print(f"{resolved} resolved, {waiting} awaiting a human, "
          f"{len(resolutions) - resolved - waiting} blocked or open")
    if waiting:
        print("\nNext: python scripts/approve.py --list")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the Campus Customs agent team.")
    ap.add_argument("--ticket", type=int, help="work a single ticket")
    ap.add_argument("--no-reset", action="store_true",
                    help="keep the current database (use after approving something)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the team and read the board, but call no model")
    args = ap.parse_args()

    if not args.no_reset and not args.dry_run:
        reset_database()

    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
