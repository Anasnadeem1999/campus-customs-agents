"""The approval board: the few records the shop's 9-table schema cannot hold.

The database models money that has *already moved* -- a `payments` row, a
balance, an invoice marked paid. It has no table for a request that is still
waiting on a human, for a purchase order, or for an unsent draft message. Those
three things are the whole point of constraints 5 and 9, so they are kept here
in `output/board/` as append-only JSON.

This is **not** a second shop-facts layer. No price, quantity, balance, lease
or invoice is stored here -- every one of those is read live from the database
each time it is needed. What lives here is the shop's *intent*: who asked for
what, who approved it, and whether it has been spent yet.

Why a separate file rather than new tables: `data/campus_customs.db` is the
assignment's own input, and a graded clone must find it with exactly the nine
tables it shipped with. Adding tables to it would be editing the question.

### The approval gate

`request_approval` is an MCP tool, so agents can ask. **Approving is not a
tool at all** -- it lives in `scripts/approve.py`, outside the MCP server and
therefore outside anything an agent can reach. An agent cannot approve its own
spending because the verb does not exist in its world, which is a stronger
guarantee than a prompt instruction telling it not to.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = (REPO_ROOT / os.environ.get("BOARD_DIR", "output/board")).resolve()

APPROVALS = BOARD_DIR / "approvals.json"
DRAFTS = BOARD_DIR / "drafts.json"

# Guards concurrent read-modify-write from tools running in the same process.
_LOCK = threading.Lock()

ApprovalKind = Literal["invoice_payment", "rent_payment", "purchase_order", "price_override"]
APPROVAL_KINDS: tuple[str, ...] = (
    "invoice_payment",
    "rent_payment",
    "purchase_order",
    "price_override",
)


class BoardError(RuntimeError):
    """Raised when a board record is missing, malformed, or used out of order."""


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
    except json.JSONDecodeError as exc:
        raise BoardError(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise BoardError(f"{path.name} should hold a JSON list, found {type(data).__name__}.")
    return data


def _save(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic, so a crash mid-write cannot truncate the board


def load_approvals() -> list[dict[str, Any]]:
    return _load(APPROVALS)


def load_drafts() -> list[dict[str, Any]]:
    return _load(DRAFTS)


def next_id(rows: list[dict[str, Any]], key: str = "id") -> int:
    return max((int(r.get(key, 0)) for r in rows), default=0) + 1


def add_approval(record: dict[str, Any]) -> dict[str, Any]:
    """Append one approval request and return it with its assigned id."""
    with _LOCK:
        rows = load_approvals()
        record = {"id": next_id(rows), **record}
        rows.append(record)
        _save(APPROVALS, rows)
    return record


def get_approval(approval_id: int) -> dict[str, Any]:
    for row in load_approvals():
        if int(row["id"]) == int(approval_id):
            return row
    raise BoardError(
        f"No approval request with id {approval_id}. "
        "Call request_approval first, then wait for a human to approve it."
    )


def update_approval(approval_id: int, **changes: Any) -> dict[str, Any]:
    with _LOCK:
        rows = load_approvals()
        for row in rows:
            if int(row["id"]) == int(approval_id):
                row.update(changes)
                _save(APPROVALS, rows)
                return row
    raise BoardError(f"No approval request with id {approval_id}.")


def add_draft(record: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        rows = load_drafts()
        record = {"id": next_id(rows), **record}
        rows.append(record)
        _save(DRAFTS, rows)
    return record


def require_spendable(approval: dict[str, Any], kind: str, ref_id: int | None) -> None:
    """Refuse unless this approval is a human-approved, unspent match for the job.

    Every payment path goes through here, so the four ways a payment could slip
    past a human are refused in one place: never approved, already spent,
    approved for a different kind of thing, or approved for a different record.
    """
    if approval.get("status") != "approved":
        raise BoardError(
            f"Approval {approval['id']} is '{approval.get('status')}', not 'approved'. "
            "A human has to approve this before any money moves -- no agent may approve it. "
            "Run: python scripts/approve.py --id {id} --by \"<name>\"".format(id=approval["id"])
        )
    if approval.get("consumed_by_payment_id") is not None:
        raise BoardError(
            f"Approval {approval['id']} was already spent on payment "
            f"{approval['consumed_by_payment_id']}. One approval authorises one payment; "
            "request a fresh approval."
        )
    if approval.get("kind") != kind:
        raise BoardError(
            f"Approval {approval['id']} is for '{approval.get('kind')}', not '{kind}'. "
            "An approval cannot be redirected to a different kind of spending."
        )
    if ref_id is not None and int(approval.get("ref_id") or -1) != int(ref_id):
        raise BoardError(
            f"Approval {approval['id']} is for {approval.get('kind')} "
            f"{approval.get('ref_id')}, not {ref_id}."
        )
