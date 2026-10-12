"""The team's own wiring -- connectivity and delegation, with no model involved.

These never call the gateway. They check the structure: that every agent can
reach every other, and that a reply from any of them renders without blowing
up the agent that asked.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.agent_team import COLLEAGUE_BLURB, ROLE_FILES, build_instructions, render_reply
from backend.models import ColleagueReply, FigureCited, TicketResolution


def test_every_agent_has_a_prompt_file_and_the_rules_come_first():
    for agent in ROLE_FILES:
        text = build_instructions(agent)
        assert "Campus Customs — the shop rules" in text
        assert text.index("the shop rules") < text.index("You are"), (
            "the shared rules must be loaded before the role brief -- the rules "
            "outrank the role and say so"
        )


def test_the_team_is_fully_connected():
    """Every agent must be reachable from every other."""
    assert set(COLLEAGUE_BLURB) == set(ROLE_FILES) == {
        "boss", "inventory", "accounting", "facilities", "customer_service"
    }
    for owner in ROLE_FILES:
        reachable = {c for c in ROLE_FILES if c != owner}
        assert len(reachable) == 4, f"{owner} must be able to ask the other four"


def test_a_boss_reply_renders_for_the_agent_that_asked_it():
    """Regression: asking the Boss crashed the asker.

    The Boss answers with a TicketResolution, every other agent with a
    ColleagueReply. `reply.answer` raised AttributeError on the Boss's shape
    and lost the whole turn -- in a fully connected team, asking the Boss is a
    normal thing to do.
    """
    resolution = TicketResolution(
        ticket_id=103, outcome="blocked",
        decision="Cannot fund the restock.", reasoning="Only $160 uncommitted against $264.",
        figures=[FigureCited(label="uncommitted", value="160.00", from_tool="get_cash_position")],
        blocked_on="funding", approvals_raised=[3],
    )
    text = render_reply(resolution)
    assert "Cannot fund the restock." in text
    assert "blocked" in text
    assert "uncommitted=160.00 (via get_cash_position)" in text
    assert "Approvals raised: [3]" in text


def test_a_colleague_reply_renders_too():
    reply = ColleagueReply(
        answer="Size S is empty; short by 1.",
        figures=[FigureCited(label="qty_on_hand", value="0", from_tool="check_stock_by_size")],
        blocked_on="invoice 501 blocks the vendor",
        needs_human="approval to pay invoice 501",
    )
    text = render_reply(reply)
    assert "Size S is empty" in text
    assert "Needs a human: approval to pay invoice 501" in text
    assert "Blocked on: invoice 501 blocks the vendor" in text
