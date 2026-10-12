"""Database access for the Campus Customs MCP server.

Everything the shop's agents see comes through here, and it points at exactly
one file: the working copy, `data/campus_customs_new.db`. The pristine seed
`data/campus_customs.db` is never opened by the server -- `_assert_not_seed`
turns that rule into a runtime error rather than a convention.
"""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SEED_DB = (REPO_ROOT / os.environ.get("SEED_DB_PATH", "data/campus_customs.db")).resolve()
WORKING_DB = (REPO_ROOT / os.environ.get("WORKING_DB_PATH", "data/campus_customs_new.db")).resolve()


class ShopDataError(RuntimeError):
    """Raised when the database cannot answer a question it should be able to."""


def _assert_not_seed(path: Path) -> None:
    if path == SEED_DB:
        raise ShopDataError(
            f"Refusing to open the pristine seed database at {path}. "
            "The MCP server works only on the copy at "
            f"{WORKING_DB.relative_to(REPO_ROOT)}; run scripts/reset_db.py to recreate it."
        )


def connect(*, read_only: bool = True) -> sqlite3.Connection:
    """Open the working copy.

    Read-only by default: the three tools in this problem only answer
    questions. Tools that spend money or change a ticket come later and will
    ask for a writable handle explicitly, so that a read path can never
    mutate the shop by accident.
    """
    _assert_not_seed(WORKING_DB)
    if not WORKING_DB.exists():
        raise ShopDataError(
            f"Working database missing at {WORKING_DB}. Run: python scripts/reset_db.py"
        )

    uri = f"file:{WORKING_DB.as_posix()}" + ("?mode=ro" if read_only else "")
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def shop_today(conn: sqlite3.Connection) -> dt.date:
    """The shop's 'today', read from `desk.date_today`.

    Deliberately not `date.today()`. The seeded shop runs on 2026-08-31, and
    every overdue test and delivery estimate in this homework is measured
    against that field -- using the wall clock would mis-rank the whole board.
    """
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    if row is None:
        raise ShopDataError("The desk table is empty, so the shop has no 'today'.")
    return dt.date.fromisoformat(row["date_today"])


def days_between(start: dt.date, end: dt.date) -> int:
    """Whole days from `start` to `end`; negative when `end` is in the past."""
    return (end - start).days
