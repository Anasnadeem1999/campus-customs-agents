"""Reset the working database from the pristine seed file.

The agents only ever read and write data/campus_customs_new.db. The seed file
data/campus_customs.db is the assignment's original data and must stay byte
for byte untouched, so that a full ticket-resolution run can be repeated from
a clean slate at any time.

Usage:
    python scripts/reset_db.py            # overwrite the working copy
    python scripts/reset_db.py --verify   # report state, change nothing
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SEED_DB = REPO_ROOT / os.environ.get("SEED_DB_PATH", "data/campus_customs.db")
WORKING_DB = REPO_ROOT / os.environ.get("WORKING_DB_PATH", "data/campus_customs_new.db")

# Tables whose row counts are printed as a quick sanity check after a reset.
SUMMARY_TABLES = (
    "desk",
    "tickets",
    "inventory",
    "pricing",
    "vendors",
    "leases",
    "invoices",
    "payments",
    "cash_accounts",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarise(path: Path) -> str:
    """One-line-per-table row counts, plus the shop's cash and 'today'."""
    lines = []
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        for table in SUMMARY_TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            lines.append(f"  {table:<14} {count:>4} rows")
        today = conn.execute("SELECT date_today FROM desk").fetchone()[0]
        cash = conn.execute("SELECT name, balance FROM cash_accounts").fetchall()
    lines.append(f"  shop date_today: {today}")
    for name, balance in cash:
        lines.append(f"  cash[{name}]: {balance:,.2f}")
    return "\n".join(lines)


def reset() -> None:
    if not SEED_DB.exists():
        sys.exit(f"Seed database missing: {SEED_DB}")

    seed_hash_before = sha256(SEED_DB)

    # Drop stale WAL/SHM sidecars so the copy cannot inherit old transactions.
    for suffix in ("-wal", "-shm"):
        sidecar = WORKING_DB.with_name(WORKING_DB.name + suffix)
        sidecar.unlink(missing_ok=True)

    WORKING_DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SEED_DB, WORKING_DB)

    if sha256(SEED_DB) != seed_hash_before:
        sys.exit("Seed database changed during reset -- aborting.")

    print(f"Reset  {WORKING_DB.relative_to(REPO_ROOT)}  from  {SEED_DB.relative_to(REPO_ROOT)}")
    print(f"Seed sha256 (unchanged): {seed_hash_before}")
    print(summarise(WORKING_DB))


def verify() -> None:
    print(f"Seed    {SEED_DB}  exists={SEED_DB.exists()}")
    if SEED_DB.exists():
        print(f"  sha256 {sha256(SEED_DB)}")
    print(f"Working {WORKING_DB}  exists={WORKING_DB.exists()}")
    if WORKING_DB.exists():
        print(summarise(WORKING_DB))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="report state without copying")
    args = parser.parse_args()
    verify() if args.verify else reset()
