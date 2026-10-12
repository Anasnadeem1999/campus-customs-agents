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


@pytest.fixture(scope="session", autouse=True)
def leave_the_shop_as_we_found_it():
    """Reset the working database once the whole suite has finished."""
    yield
    reset_working_db()
    # The approval board is part of that state: an approved request pointing at
    # an invoice the reset has just reopened is exactly the half-state this
    # fixture exists to prevent.
    for name in ("approvals.json", "drafts.json"):
        path = REPO_ROOT / "output" / "board" / name
        if path.exists():
            path.unlink()
