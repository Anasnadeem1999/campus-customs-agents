"""The audit trail's own guarantees: it appends, and a step number is unique."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import audit  # noqa: E402
from backend.models import AuditStep, ModelCheck, RunRecord, utc_now  # noqa: E402


@pytest.fixture(autouse=True)
def trail(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "AUDIT_PATH", tmp_path / "audit_trail.json")
    yield


def a_step(agent: str = "boss", run_id: str = "run-test") -> AuditStep:
    return AuditStep(
        step=0,  # deliberately wrong -- append_step must assign the real one
        run_id=run_id, agent=agent, task="t", output="o",
        model=ModelCheck(requested="gpt-6-luna", resolved="gpt-6-luna-2026-09-22", ok=True),
        started_at=utc_now(), finished_at=utc_now(), duration_seconds=0.1,
    )


def test_step_numbers_are_unique_under_concurrency():
    """Regression: two agents finishing at once both claimed the same step.

    `next_step_number()` was read by the caller before the write, so parallel
    delegations raced and the trail ended up with two different events both
    numbered 23. The dashboard pages by step number, and an audit trail whose
    identifiers collide cannot be used to refer to anything.
    """
    threads = [threading.Thread(target=lambda: audit.append_step(a_step())) for _ in range(24)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    steps = [s["step"] for s in audit._load()["steps"]]
    assert len(steps) == 24, "every step must survive"
    assert len(set(steps)) == 24, f"step numbers collided: {sorted(steps)}"
    assert sorted(steps) == list(range(1, 25)), "numbers should be a clean sequence"


def test_append_step_returns_the_number_it_assigned():
    first = audit.append_step(a_step())
    second = audit.append_step(a_step())
    assert (first.step, second.step) == (1, 2)


def test_a_second_run_appends_and_does_not_wipe_the_first():
    audit.start_run(RunRecord(
        run_id="run-one", started_at=utc_now(), shop_date_today="2026-08-31",
        model_requested="gpt-6-luna", tickets_in_scope=[101],
        database="data/campus_customs_new.db", reset_before_run=True,
    ))
    audit.append_step(a_step(run_id="run-one"))

    audit.start_run(RunRecord(
        run_id="run-two", started_at=utc_now(), shop_date_today="2026-08-31",
        model_requested="gpt-6-luna", tickets_in_scope=[102],
        database="data/campus_customs_new.db", reset_before_run=False,
    ))
    audit.append_step(a_step(run_id="run-two"))

    data = audit._load()
    assert [r["run_id"] for r in data["runs"]] == ["run-one", "run-two"]
    assert len(data["steps"]) == 2, "the earlier run's steps must survive the later run"
    assert audit.steps_for_run("run-one")[0]["step"] == 1


def test_a_damaged_trail_is_parked_not_destroyed():
    audit.AUDIT_PATH.write_text("{not json", encoding="utf-8")
    audit.append_step(a_step())
    kept = audit.AUDIT_PATH.with_suffix(".corrupt.json")
    assert kept.exists(), "history must never be deleted to recover from a bad read"
    assert kept.read_text(encoding="utf-8") == "{not json"
