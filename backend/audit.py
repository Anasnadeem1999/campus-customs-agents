"""The audit trail: append, never wipe.

`output/audit_trail.json` is the shop's history of what its agents did. The
brief is explicit that a run must *append* -- so the file accumulates across
runs and an earlier run can still be read after a later one has happened. A
log that only ever holds the last run is not an audit trail; it is a status
display, and it destroys the evidence exactly when something has gone wrong and
you want it.

Shape on disk:

```json
{"runs": [ {...run header...} ], "steps": [ {...one agent step...} ]}
```

Runs and steps are kept in separate lists, joined by `run_id`, so appending a
step never has to find and rewrite the run it belongs to. Every write is
read-modify-write under a lock and lands through a temporary file, so a crash
mid-write cannot truncate the history.
"""

from __future__ import annotations

import json
import time
import os
import threading
from pathlib import Path
from typing import Any

from .models import AuditStep, HumanDecision, RunRecord

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (REPO_ROOT / os.environ.get("AUDIT_TRAIL_PATH", "output/audit_trail.json")).resolve()

_LOCK = threading.Lock()

_EMPTY: dict[str, list[Any]] = {"runs": [], "steps": []}


def _load() -> dict[str, list[Any]]:
    if not AUDIT_PATH.exists():
        return {"runs": [], "steps": [], "decisions": []}
    raw = AUDIT_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return {"runs": [], "steps": []}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Never destroy history to recover from a bad read. Park the damaged
        # file beside the original so it can be inspected, and carry on.
        damaged = AUDIT_PATH.with_suffix(".corrupt.json")
        AUDIT_PATH.replace(damaged)
        return {"runs": [], "steps": [], "decisions": [],
                "note": f"Previous trail was not valid JSON; kept at {damaged.name}."}
    if isinstance(data, list):
        # Tolerate an older flat-list shape rather than losing it.
        return {"runs": [], "steps": data, "decisions": []}
    data.setdefault("runs", [])
    data.setdefault("steps", [])
    data.setdefault("decisions", [])
    return data


#: How many times to retry the atomic swap, and how long to wait between tries.
#: On Windows the replace fails with PermissionError (WinError 5) whenever
#: another process has the file open for even an instant -- an editor, a
#: virus scanner, or the dashboard backend reading the trail to answer a
#: poll. It is transient and clears in milliseconds, but an unretried failure
#: loses the agent turn that was being recorded, and a trail missing a step is
#: worse than a slow one.
_SAVE_ATTEMPTS = 10
_SAVE_BACKOFF_SECONDS = 0.05


def _save(data: dict[str, Any]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = AUDIT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    for attempt in range(1, _SAVE_ATTEMPTS + 1):
        try:
            tmp.replace(AUDIT_PATH)
            return
        except PermissionError:
            if attempt == _SAVE_ATTEMPTS:
                raise
            time.sleep(_SAVE_BACKOFF_SECONDS * attempt)


def start_run(record: RunRecord) -> None:
    """Write the run header before any agent is invoked.

    Written up front on purpose: if the run then crashes, the trail still shows
    that it was attempted, against which database, on which shop date.
    """
    with _LOCK:
        data = _load()
        data["runs"].append(record.model_dump())
        _save(data)


def append_step(step: AuditStep) -> AuditStep:
    """Append one agent step. Called after every agent turn, success or not.

    **The step number is assigned here, under the lock, and whatever the caller
    put in `step.step` is overwritten.** It used to be read by the caller via
    `next_step_number()` before the write, which left a window: two agents
    finishing at once both read the same count and both wrote that number. The
    trail then carried two different events claiming to be step 23 — which
    breaks the dashboard's paging, and quietly ruins the one property an audit
    trail has to have, that a step can be referred to unambiguously.
    """
    with _LOCK:
        data = _load()
        numbered = step.model_copy(update={"step": len(data["steps"]) + 1})
        data["steps"].append(numbered.model_dump())
        _save(data)
    return numbered


def finish_run(run_id: str, **summary: Any) -> None:
    """Attach the outcome to the run header once the run ends."""
    with _LOCK:
        data = _load()
        for run in data["runs"]:
            if run.get("run_id") == run_id:
                run.update(summary)
                break
        _save(data)


def next_step_number() -> int:
    """A provisional step number, for callers building an `AuditStep`.

    Only ever a placeholder: `append_step` assigns the real number under the
    lock. Do not rely on this value — between reading it and writing, another
    agent may well have taken it.
    """
    return len(_load()["steps"]) + 1


def steps_for_run(run_id: str) -> list[dict[str, Any]]:
    return [s for s in _load()["steps"] if s.get("run_id") == run_id]


def summarise(value: Any, limit: int = 1200) -> str:
    """Trim a tool payload for the trail without hiding what it said.

    A reviewer has to be able to re-check the decision from this string, so the
    cut is generous and it says when it cut. Silently truncating the one figure
    that mattered would make the trail worse than useless.
    """
    # ensure_ascii=False so the agents' own punctuation survives as itself.
    # Escaped, every curly quote reaches the dashboard as a backslash-u
    # sequence that has to be decoded again before anyone can read it.
    text = (
        value if isinstance(value, str)
        else json.dumps(value, default=str, ensure_ascii=False)
    )
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [trimmed {len(text) - limit} chars]"


def append_decision(decision: HumanDecision) -> None:
    """Record a human approval or refusal in the trail.

    Written from `scripts/approve.py` and the backend's approve route -- the
    two places a person can actually decide. Agents never reach this, which is
    the same guarantee the MCP server enforces by simply not having the verb.
    """
    with _LOCK:
        data = _load()
        data["decisions"].append(decision.model_dump())
        _save(data)


def decisions_for_approval(approval_id: int) -> list[dict[str, Any]]:
    return [d for d in _load()["decisions"] if d.get("approval_id") == approval_id]
