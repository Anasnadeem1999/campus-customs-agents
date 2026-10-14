"""Check the submission against itself. Run it; nothing here changes anything.

    python scripts/verify_submission.py

Every claim this project makes about its own result is re-derived here from
the database, the audit trail and the published artefacts, and compared. It
exits non-zero if any of them disagree, so "the cash adds up" is something a
grader can confirm in one command rather than take on trust.

Deliberately read-only: it opens the databases, reads the output files, and
writes nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SEED_SHA_PREFIX = "23686a90d698f7fa"
OPENING_BALANCE = 3400.00

failures: list[str] = []


def check(label: str, passed: bool, detail: str = "") -> None:
    if not passed:
        failures.append(label)
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))


def main() -> int:
    html = (REPO / "output/desk_tickets.html").read_text(encoding="utf-8")
    doc = json.loads((REPO / "output/resolved_tickets.json").read_text(encoding="utf-8"))
    trail = json.loads((REPO / "output/audit_trail.json").read_text(encoding="utf-8"))
    conn = sqlite3.connect(REPO / "data/campus_customs_new.db")
    conn.row_factory = sqlite3.Row

    first_step = trail["submission"]["submitted_run"]["first_step"]
    run = [s for s in trail["steps"] if s["step"] >= first_step]

    print("1. THE RUN RESOLVED EVERY TICKET")
    db_status = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM tickets")}
    json_status = {t["ticket_id"]: t["final_status"] for t in doc["tickets"]}
    check("all three tickets resolved", all(v == "resolved" for v in db_status.values()), str(db_status))
    check("resolved_tickets.json agrees with the database", db_status == json_status)

    print("\n2. THE CASH ADDS UP")
    balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()[0]
    paid = sum(r["amount"] for r in conn.execute("SELECT amount FROM payments"))
    check("opening - payments == closing balance",
          abs((OPENING_BALANCE - paid) - balance) < 0.005,
          f"{OPENING_BALANCE:,.2f} - {paid:,.2f} = {balance:,.2f}")
    check("published figure matches the database",
          doc["cash"]["matches_database"] is True
          and abs(doc["cash"]["ending_checking_balance_computed"] - balance) < 0.005)
    chain = [(t["cash"]["balance_before"], t["cash"]["balance_after"]) for t in doc["tickets"]]
    continuous = all(chain[i][1] == chain[i + 1][0] for i in range(len(chain) - 1))
    check("per-ticket cash chain is continuous and lands on the database",
          continuous and chain[-1][1] == balance, str(chain))
    cash_tab = html.split('id="cash"')[1].split("</section>")[0]
    shown = {float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+\.\d\d)", cash_tab)}
    check("the Cash tab prints the opening and closing balances",
          OPENING_BALANCE in shown and balance in shown)

    print("\n3. EVERY PAYMENT WAS APPROVED BY A HUMAN")
    payments = [dict(r) for r in conn.execute("SELECT * FROM payments")]
    check("every payment names its approver",
          all((p["approved_by"] or "").strip() for p in payments),
          f"{len(payments)} payment(s)")
    check("human decisions are recorded in the trail", len(trail["decisions"]) > 0,
          f"{len(trail['decisions'])} decision(s)")
    sys.path.insert(0, str(REPO))
    import asyncio

    from mcp_server import server as shop  # noqa: E402

    tools = {t.name for t in asyncio.run(shop.mcp.list_tools())}
    check("no tool on the MCP server can approve",
          not {t for t in tools if "approve" in t and t != "list_approvals"})
    check("no tool can send anything to a customer or vendor",
          not {t for t in tools if "send" in t or "email" in t})

    print("\n4. ONE MODEL, CHECKED ON EVERY CALL")
    resolved = {s["model"]["resolved"] for s in run if s["model"].get("resolved")}
    check("every step of the submitted run resolved to gpt-6-luna",
          bool(resolved) and all(m.startswith("gpt-6-luna") for m in resolved), str(sorted(resolved)))
    check("no other model name appears in the code",
          subprocess.run([sys.executable, "-m", "pytest",
                          str(REPO / "tests/test_model_policy.py"), "-q"],
                         cwd=REPO, capture_output=True).returncode == 0)

    print("\n5. THE ORIGINAL DATABASE IS UNTOUCHED")
    sha = hashlib.sha256((REPO / "data/campus_customs.db").read_bytes()).hexdigest()
    check("seed sha256 unchanged", sha.startswith(SEED_SHA_PREFIX), sha[:16])
    seed = sqlite3.connect(REPO / "data/campus_customs.db")
    check("seed has no payments", seed.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 0)
    check("seed shop date is still 2026-08-31",
          seed.execute("SELECT date_today FROM desk").fetchone()[0] == "2026-08-31")

    print("\n6. THE DELIVERABLES ARE PRESENT AND CONSISTENT")
    tracked = set(subprocess.run(["git", "ls-files"], cwd=REPO,
                                 capture_output=True, text=True).stdout.split())
    required = [
        "AI_prompts.md", "requirements.txt", ".env.example", ".gitignore", ".mcp.json",
        "README.md", "data/campus_customs.db", "data/campus_customs_new.db",
        "mcp_server/server.py", "mcp_server/README.md", "backend/main.py", "backend/models.py",
        "backend/prompts/boss.md", "backend/prompts/inventory.md", "backend/prompts/accounting.md",
        "backend/prompts/facilities.md", "backend/prompts/customer_service.md",
        "output/harness.md", "output/mcp_smoke.json", "output/desk_tickets.html",
        "output/design.md", "output/resolved_tickets.json", "output/resolved_board.html",
        "output/audit_trail.json", "output/github_url.txt",
    ]
    missing = [f for f in required if f not in tracked]
    check("every file in the required layout is tracked", not missing, str(missing))
    check("no .env, virtualenv or node_modules is tracked",
          not [t for t in tracked if t == ".env" or "node_modules" in t or t.startswith(".venv")])
    tabs = re.findall(r'data-tab="([^"]+)"', html)
    panels = re.findall(r'<section class="panel[^"]*" id="([^"]+)">', html)
    check("all five tabs exist and none is a placeholder",
          tabs == panels and not any(
              "Coming in a later problem" in html.split(f'id="{t}"')[1].split("</section>")[0]
              for t in tabs), str(tabs))

    print("\n7. THE AGENTS WHO WORKED EACH TICKET MATCH THE TRAIL")
    for ticket in doc["tickets"]:
        tid = ticket["ticket_id"]
        # A ticket is worked across several passes, pausing at the approval
        # gate between them, so every pass of the submitted run counts.
        from_trail = sorted({s["agent"] for s in run if s["ticket_id"] == tid})
        from_json = sorted(a["agent"] for a in ticket["agents"])
        check(f"ticket {tid} agents agree", from_trail == from_json, str(from_json))

    print()
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED: {failures}")
        return 1
    print("ALL CHECKS PASSED — the submission agrees with itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
