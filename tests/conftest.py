"""Shared test setup.

These tests exercise the real MCP server against the real working database --
that is deliberate, because a payment rule that is only tested against a mock
is not tested. The cost is that a test run genuinely spends the shop's money.

Without the fixture below, `pytest` leaves the working copy in whatever state
the last test happened to finish in: cash at $160, two payments written,
invoice 501 paid, but all three tickets still `open`. Open the dashboard after
a test run and it shows a shop that never existed, which is a confusing
half-hour for anyone who did not know the tests had been run.

So the suite restores the shop on the way out. The pristine seed is never
touched either way -- `reset_db.py` hashes it before and after to prove it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def reset_working_db() -> None:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "reset_db.py")],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )


WORKING_DB = REPO_ROOT / "data" / "campus_customs_new.db"
BOARD = REPO_ROOT / "output" / "board"
BOARD_FILES = ("approvals.json", "drafts.json")


@pytest.fixture(scope="session", autouse=True)
def leave_the_shop_as_we_found_it(tmp_path_factory):
    """Put the shop back exactly as it was, not merely back to the seed.

    Resetting to the seed was the first version of this, and it was wrong in a
    way that only showed up at the end of the assignment: a finished run leaves
    the shop at $160 with two payments written, and that state *is* the
    deliverable. A test run that reset to $3,400 afterwards would quietly
    destroy the result the artefacts describe, and the cash figures in
    `resolved_tickets.json` would stop matching the database they were checked
    against.

    So the suite takes a copy of whatever it found, lets the tests do what they
    like, and restores it. Run the tests before a run or after one; either way
    the shop is as you left it.
    """
    keep = tmp_path_factory.mktemp("shop-before-tests")
    saved_db = keep / "campus_customs_new.db"
    if WORKING_DB.exists():
        shutil.copy2(WORKING_DB, saved_db)

    saved_board = {}
    for name in BOARD_FILES:
        path = BOARD / name
        if path.exists():
            saved_board[name] = path.read_bytes()

    yield

    if saved_db.exists():
        shutil.copy2(saved_db, WORKING_DB)
    else:
        reset_working_db()

    for name in BOARD_FILES:
        path = BOARD / name
        if name in saved_board:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(saved_board[name])
        elif path.exists():
            path.unlink()
