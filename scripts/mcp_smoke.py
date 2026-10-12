"""Smoke-test the Campus Customs MCP server and record the evidence.

Launches the server exactly as `.mcp.json` declares it -- same interpreter,
same args, same env -- then speaks real MCP over stdio: initialize, list the
tools, call each one. Nothing is imported from `mcp_server` here, so a config
that would fail inside the vibe coder fails here too.

Every tool result is then cross-checked against `data/campus_customs_new.db`
with raw SQL written independently of the tool's own query. A tool agreeing
with itself proves nothing; a tool agreeing with a separate SELECT is
evidence.

Writes `output/mcp_smoke.json` and exits non-zero if any check fails.

Usage:
    python scripts/mcp_smoke.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_CONFIG = REPO_ROOT / ".mcp.json"
WORKING_DB = REPO_ROOT / "data" / "campus_customs_new.db"
EVIDENCE = REPO_ROOT / "output" / "mcp_smoke.json"
SERVER_NAME = "campus-customs"

# The prompt that set this whole problem in motion, quoted verbatim.
DRIVING_PROMPT = (
    "Problem 4: Add the MCP server to vibe coder and test each tool -- "
    "Alright so now please add the MCP server to this assignment so that the "
    "tools can be called upon. Please save the connecting JSON text in the "
    ".mcp.json at the project root or however the local mcp server lists are "
    "saved. Once the vibe coder is connected please test each one of the three "
    "mcp tools while saving the evidence into output/mcp_smoke.json. For every "
    "tool it shall include the prompt given by me to the vibe coder, the tools "
    "name, the tools output which must match the values in "
    "data/campus_customs_new.db"
)

# One case per tool. Each `prompt` is a test prompt written for this smoke
# test at the user's instruction ("please also write the test prompt for each
# of the tool"), phrased the way a person working the shop would actually type
# it, and worded so that it can only be answered by the tool it targets.
CASES: list[dict[str, Any]] = [
    {
        "ticket": 101,
        "prompt": (
            "Ticket 101 just came in: Tauhid Zaman wants one Bulldog tee, SKU "
            "CC-TEE-WHITE, in size S. Check the shelf for that exact size -- how "
            "many do we have, and if we cannot fill it, how many are we short?"
        ),
        "tool": "check_stock_by_size",
        "arguments": {"sku": "CC-TEE-WHITE", "size": "S", "requested_qty": 1},
        "expects": "Size S is empty, so the order cannot be filled and we are short 1.",
    },
    {
        "ticket": 103,
        "prompt": (
            "Ticket 103: the Yale AI Club wants 20 navy hoodies in size M and we "
            "only hold 8. Find me a vendor who could reprint the missing 12 -- "
            "give me their lead time, whether anything is stopping them from "
            "shipping, and the date an order placed today would land."
        ),
        "tool": "find_restock_vendors",
        "arguments": {"specialty_contains": "apparel"},
        "expects": (
            "Exactly one apparel vendor, Bulldog Print Co, blocked from shipping "
            "by an unpaid invoice, with a 5-day lead time."
        ),
    },
    {
        "ticket": 102,
        "prompt": (
            "Ticket 102: Elm City Properties emailed claiming the shop rent is due "
            "in two days. Do not take the email's word for it -- pull the lease "
            "itself and tell me the landlord, the amount owed, the due date, and "
            "how many days away that is."
        ),
        "tool": "check_rent_due",
        "arguments": {"lease_id": 1},
        "expects": "Lease 1, Elm City Properties, $2,400 due 2026-09-02, two days out.",
    },
]


def load_server_params() -> StdioServerParameters:
    """Build the launch parameters straight out of .mcp.json."""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    entry = config["mcpServers"][SERVER_NAME]
    # Merge over the real environment, which is what a host does: the config's
    # env adds to the inherited one rather than replacing PATH and friends.
    env = {**os.environ, **entry.get("env", {})}
    return StdioServerParameters(command=entry["command"], args=entry.get("args", []), env=env)


def db_crosscheck(case: dict[str, Any]) -> dict[str, Any]:
    """Re-derive the expected answer with SQL written independently of the tool."""
    conn = sqlite3.connect(f"file:{WORKING_DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        today = dt.date.fromisoformat(conn.execute("SELECT date_today FROM desk").fetchone()[0])

        if case["tool"] == "check_stock_by_size":
            args = case["arguments"]
            row = conn.execute(
                "SELECT qty, location, name FROM inventory WHERE sku = ? AND size = ?",
                (args["sku"], args["size"]),
            ).fetchone()
            return {
                "source": "SELECT qty, location, name FROM inventory WHERE sku=? AND size=?",
                "qty_on_hand": row["qty"],
                "location": row["location"],
                "product_name": row["name"],
                "shortfall": max(0, args["requested_qty"] - row["qty"]),
            }

        if case["tool"] == "find_restock_vendors":
            vendor = conn.execute(
                "SELECT id, name, specialty, lead_days FROM vendors "
                "WHERE LOWER(specialty) LIKE '%apparel%'"
            ).fetchone()
            unpaid = conn.execute(
                "SELECT id, amount, due_date FROM invoices "
                "WHERE vendor_id = ? AND status != 'paid'",
                (vendor["id"],),
            ).fetchall()
            return {
                "source": "SELECT vendors JOIN unpaid invoices, lead time from vendors.lead_days",
                "vendor_count": 1,
                "vendor_id": vendor["id"],
                "name": vendor["name"],
                "specialty": vendor["specialty"],
                "lead_days": vendor["lead_days"],
                "eta_if_ordered_today": (
                    today + dt.timedelta(days=vendor["lead_days"])
                ).isoformat(),
                "can_ship": len(unpaid) == 0,
                "blocked_amount": round(sum(r["amount"] for r in unpaid), 2),
                "blocking_invoice_ids": [r["id"] for r in unpaid],
                "days_overdue": max(
                    (today - dt.date.fromisoformat(r["due_date"])).days for r in unpaid
                )
                if unpaid
                else 0,
            }

        if case["tool"] == "check_rent_due":
            lease = conn.execute(
                "SELECT id, space_name, landlord, monthly_rent, next_due FROM leases WHERE id = ?",
                (case["arguments"]["lease_id"],),
            ).fetchone()
            due = dt.date.fromisoformat(lease["next_due"])
            return {
                "source": "SELECT monthly_rent, next_due FROM leases WHERE id=?",
                "lease_id": lease["id"],
                "space_name": lease["space_name"],
                "landlord": lease["landlord"],
                "amount_due": lease["monthly_rent"],
                "next_due": lease["next_due"],
                "days_until_due": (due - today).days,
                "is_overdue": (due - today).days < 0,
            }

        raise ValueError(f"No cross-check defined for {case['tool']}")
    finally:
        conn.close()


def compare(tool_output: dict[str, Any], expected: dict[str, Any], tool: str) -> dict[str, Any]:
    """Field-by-field comparison of the tool's answer against the SQL answer."""
    if tool == "find_restock_vendors":
        # Reach into the single vendor the filter returns.
        actual = dict(tool_output["vendors"][0])
        actual["vendor_count"] = tool_output["vendor_count"]
        actual["blocking_invoice_ids"] = [i["invoice_id"] for i in actual["blocking_invoices"]]
        actual["days_overdue"] = max(
            (i["days_overdue"] for i in actual["blocking_invoices"]), default=0
        )
    elif tool == "check_rent_due":
        actual = dict(tool_output["leases"][0])
    else:
        actual = dict(tool_output)

    checks = {}
    for field, want in expected.items():
        if field == "source":
            continue
        got = actual.get(field)
        checks[field] = {"expected_from_sql": want, "returned_by_tool": got, "match": got == want}

    return {
        "all_match": all(c["match"] for c in checks.values()),
        "fields_checked": len(checks),
        "fields": checks,
    }


def unwrap(result: Any) -> dict[str, Any]:
    """Pull the JSON payload out of an MCP tool result."""
    if getattr(result, "structured_content", None):
        payload = result.structured_content
        # FastMCP wraps a bare dict return under "result".
        return payload.get("result", payload)
    return json.loads(result.content[0].text)


async def main() -> int:
    params = load_server_params()
    started = dt.datetime.now().astimezone().isoformat(timespec="seconds")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            listed = await session.list_tools()
            registered = [t.name for t in listed.tools]

            results = []
            for case in CASES:
                called = await session.call_tool(case["tool"], case["arguments"])
                output = unwrap(called)
                expected = db_crosscheck(case)
                verdict = compare(output, expected, case["tool"])
                results.append(
                    {
                        "ticket": case["ticket"],
                        "prompt": case["prompt"],
                        "expected_in_plain_english": case["expects"],
                        "tool": case["tool"],
                        "arguments": case["arguments"],
                        "tool_output": output,
                        "database_crosscheck": expected,
                        "verification": verdict,
                        "is_error": bool(getattr(called, "is_error", False)),
                    }
                )

    passed = all(r["verification"]["all_match"] and not r["is_error"] for r in results)

    evidence = {
        "problem": "4 - Add the MCP server to the vibe coder and test each tool",
        "run_at": started,
        "transport": "stdio",
        "launched_from": ".mcp.json",
        "server_name": SERVER_NAME,
        "server_info": {
            "name": init.server_info.name,
            "version": init.server_info.version,
            "protocol_version": init.protocol_version,
        },
        "database_under_test": str(WORKING_DB.relative_to(REPO_ROOT)).replace("\\", "/"),
        "model_calls_made": 0,
        "driving_prompt_from_user": DRIVING_PROMPT,
        "prompt_provenance": (
            "driving_prompt_from_user and prompt_authorship_instruction are quoted "
            "verbatim from the user. Each case's 'prompt' was written by the "
            "assistant at the user's explicit request -- they are test prompts "
            "authored for this smoke test, not transcriptions of separately typed "
            "user messages."
        ),
        "prompt_authorship_instruction": (
            "Please choose how to connect the server in our tool, and also write "
            "the test prompt for each of the tool. please also check each of the "
            "output against campus_customs_new.db."
        ),
        "connection_method": {
            "chosen": "project-scoped .mcp.json, committed, pre-approved in .claude/settings.json",
            "why": (
                "The config travels with the repository, so a graded clone gets the "
                "server without any manual setup, and nothing is written to global "
                "machine state. .claude/settings.json lists campus-customs under "
                "enabledMcpjsonServers so the host does not have to prompt for "
                "approval -- scoped to this one server rather than enabling all "
                "project servers blanket."
            ),
            "portability": (
                "The command is an absolute path to this project's venv, which does "
                "not survive a clone onto another machine. scripts/setup_mcp_config.py "
                "regenerates .mcp.json for whatever machine it runs on; --check "
                "reports drift without writing."
            ),
        },
        "vibe_coder_connection": {
            "config_file": ".mcp.json",
            "server_key": SERVER_NAME,
            "status": "configured; requires a vibe-coder restart to appear as tools",
            "detail": (
                "Claude Code reads .mcp.json when a session starts, so the session "
                "that wrote this config does not itself expose the tools as "
                "mcp__campus-customs__*. Restart the session (and approve the "
                "project server when prompted) to call them from the chat. This "
                "evidence was produced by launching the server with the exact "
                "command, args and env from .mcp.json over the same stdio "
                "transport the vibe coder uses, so the config is proven to work "
                "even though the chat connection is pending a restart."
            ),
        },
        "tools_registered": registered,
        "tools_tested": [c["tool"] for c in CASES],
        "all_tools_tested": sorted(registered) == sorted(c["tool"] for c in CASES),
        "overall_result": "PASS" if passed else "FAIL",
        "cases": results,
    }

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    print(f"server   : {init.server_info.name} v{init.server_info.version}")
    print(f"registered: {registered}")
    for r in results:
        mark = "PASS" if r["verification"]["all_match"] else "FAIL"
        n = r["verification"]["fields_checked"]
        print(f"  [{mark}] ticket {r['ticket']:<4} {r['tool']:<22} {n} fields vs SQL")
    print(f"overall  : {evidence['overall_result']}  -> {EVIDENCE.relative_to(REPO_ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
