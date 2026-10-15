"""Photograph the dashboard, one shot per ticket, into output/screens/.

    python scripts/take_screenshots.py

The three JPEGs embedded in `output/resolved_board.html` come from here. They
used to be taken by hand, which meant that re-running the board left the board
page illustrated with the previous run: the same three tickets and the same
ending balance, but step numbers and turn counts belonging to a run that no
longer existed. Anything the submission shows should be regenerable from the
submission, screenshots included.

Needs the backend on :8000 and the dev server on :5173, and `playwright`
(which is a tool for building this page, not a dependency of the shop -- it is
deliberately absent from requirements.txt).

**It clicks the ticket's heading, never the card.** The card's centre sits on
the "Put the team on it" button, so a click aimed at the middle of `.ticket`
starts a fresh agent run. That is not hypothetical: it destroyed a finished
run once already, and the only evidence was the audit trail growing while the
screenshots were being taken.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCREENS = REPO / "output/screens"
DASHBOARD = "http://localhost:5173/"
TICKETS = (101, 102, 103)

VIEWPORT = {"width": 1600, "height": 1000}


def shop_fingerprint() -> tuple[str, str]:
    """Everything a stray click would change, in one comparable pair."""
    conn = sqlite3.connect(REPO / "data/campus_customs_new.db")
    rows = conn.execute(
        "SELECT id, status FROM tickets ORDER BY id"
    ).fetchall()
    balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()[0]
    conn.close()
    db = f"{rows}|{balance}"
    trail = json.loads((REPO / "output/audit_trail.json").read_text(encoding="utf-8"))
    return db, hashlib.sha256(str(len(trail["steps"])).encode()).hexdigest()[:12]


def main() -> int:
    from playwright.sync_api import sync_playwright

    SCREENS.mkdir(parents=True, exist_ok=True)
    before = shop_fingerprint()

    with sync_playwright() as p:
        # Use a Chromium already on the machine when the bundled build is a
        # different revision, so this does not require a fresh browser
        # download just to re-photograph a page.
        launch: dict = {}
        for candidate in sorted(
            (Path.home() / "AppData/Local/ms-playwright").glob("chromium-*/chrome-win64/chrome.exe"),
            reverse=True,
        ):
            launch["executable_path"] = str(candidate)
            break
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1.6)
        page.goto(DASHBOARD, wait_until="networkidle")

        for ticket_id in TICKETS:
            # The heading, not the card. See the module docstring.
            page.click(f"article:has-text('#{ticket_id}') h3")
            page.wait_for_timeout(900)
            out = SCREENS / f"ticket-{ticket_id}.jpg"
            page.screenshot(path=str(out), quality=72, type="jpeg")
            print(f"  wrote {out.relative_to(REPO)}")

        browser.close()

    after = shop_fingerprint()
    if before != after:
        print(
            "\nSTOP: the shop changed while screenshots were being taken.\n"
            f"  before: {before}\n  after : {after}\n"
            "Something clicked a control that does real work. Restore the run "
            "before publishing anything.",
            file=sys.stderr,
        )
        return 1

    print("\nthe database and the audit trail are untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
