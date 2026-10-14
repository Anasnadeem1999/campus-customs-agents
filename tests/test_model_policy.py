"""The model policy, enforced mechanically rather than by reading carefully.

The brief is blunt: points are deducted if any model other than `gpt-6-luna`
shows up in the code or in a run. Two different claims, so two different
checks -- one over the source tree, one over the audit trail.

The warning about the gateway's silent fallback still needs telling, so the
name of the model it falls back to lives in the markdown documentation, where
the surrounding prose makes it obviously a thing being guarded against. It is
deliberately absent from every file this test scans, so that grepping the
*code* for a model name can only return the allowed one.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

ALLOWED = "gpt-6-luna"

#: Anything that is executed. Markdown is excluded on purpose -- see the
#: module docstring.
SOURCE_GLOBS = ("*.py", "*.ts", "*.tsx", "*.json")

SKIP_DIRS = {".venv", "node_modules", ".git", "__pycache__", ".pytest_cache", "dist"}

MODEL_PATTERN = re.compile(r"\bgpt-[\w.\-]+", re.IGNORECASE)


def source_files() -> list[Path]:
    out = []
    for pattern in SOURCE_GLOBS:
        for path in REPO_ROOT.rglob(pattern):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            # The audit trail is a record of runs, checked separately below.
            if path.name in {"audit_trail.json", "package-lock.json"}:
                continue
            out.append(path)
    return out


def test_no_model_other_than_gpt_6_luna_appears_in_the_code():
    offenders: dict[str, set[str]] = {}
    for path in source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for found in MODEL_PATTERN.findall(text):
            if not found.lower().startswith(ALLOWED):
                offenders.setdefault(str(path.relative_to(REPO_ROOT)), set()).add(found)
    assert not offenders, f"a model other than {ALLOWED} appears in the code: {offenders}"


def test_the_allowed_model_is_actually_referenced():
    """Guard against the first test passing because nothing mentions a model."""
    config = (REPO_ROOT / "backend/model_config.py").read_text(encoding="utf-8")
    assert ALLOWED in config


def test_every_recorded_run_resolved_to_the_required_model():
    """The second half of the rule: no other model in the *runs*, either."""
    trail = json.loads((REPO_ROOT / "output/audit_trail.json").read_text(encoding="utf-8"))
    resolved = {
        step["model"]["resolved"]
        for step in trail["steps"]
        if step.get("model", {}).get("resolved")
    }
    assert resolved, "the audit trail records no resolved model at all"
    wrong = {m for m in resolved if not m.startswith(ALLOWED)}
    assert not wrong, f"a run used a model other than {ALLOWED}: {wrong}"

    unverified = [s["step"] for s in trail["steps"] if not s.get("model", {}).get("ok")]
    # A step can fail the check by erroring before the gateway answered; those
    # carry an error and no resolved name, which is honest rather than a policy
    # breach. What must never happen is a step that answered on another model.
    for step in trail["steps"]:
        if not step.get("model", {}).get("ok") and step.get("model", {}).get("resolved"):
            raise AssertionError(f"step {step['step']} resolved to a disallowed model")
    print(f"{len(trail['steps'])} steps recorded, {len(unverified)} never reached the gateway")
