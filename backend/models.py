"""The shapes the agent team passes around.

Two kinds of thing live here and they are deliberately separate:

* **Agent output types** -- what an agent is required to hand back. Giving the
  model a schema is how "say what is blocked and on what" stops being a polite
  request in a prompt and becomes a field it cannot leave out.
* **Audit records** -- what we write down about a run so a human can check it
  afterwards.

Note what is *not* here: no price, stock, balance or invoice model. Those are
shop facts, they come from the MCP server on every call, and giving them a
local class would invite someone to cache one. The only shop figures that
appear below are inside `FigureCited`, where an agent is quoting a number it
read and saying which tool it read it from.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]

TicketOutcome = Literal["resolved", "awaiting_approval", "blocked", "open"]


class FigureCited(BaseModel):
    """A number an agent used, and where it got it.

    The shop rules say every figure must come from a tool. This type is how
    that gets checked rather than hoped for: an agent that quotes $2,400 has to
    name the tool call it came from, and a reviewer can replay that call.
    """

    label: str = Field(description="What the number is, e.g. 'rent due' or 'cash on hand'.")
    value: str = Field(description="The figure as used, e.g. '2400.00' or '2026-09-02'.")
    from_tool: str = Field(description="The MCP tool that returned it.")


class ColleagueReply(BaseModel):
    """What one agent hands back when another delegates to it."""

    answer: str = Field(
        description="The answer to the question asked, in a few sentences. "
        "No preamble, no restating the ticket."
    )
    figures: list[FigureCited] = Field(
        default_factory=list,
        description="Every shop figure quoted in the answer, with its source tool.",
    )
    blocked_on: str | None = Field(
        default=None,
        description="What stands in the way, if anything. Name it specifically "
        "-- 'invoice 501 is unpaid, so vendor 1 will not ship'.",
    )
    needs_human: str | None = Field(
        default=None,
        description="What a human has to decide, if anything, and the approval id if raised.",
    )


class TicketResolution(BaseModel):
    """The Boss's final word on one ticket."""

    ticket_id: int
    outcome: TicketOutcome = Field(
        description="resolved | awaiting_approval | blocked | open. "
        "'open' means the run failed to move it, which is itself a finding."
    )
    decision: str = Field(
        description="What was decided, lead sentence first. If the shop is "
        "refusing something, the refusal goes here, not buried."
    )
    reasoning: str = Field(
        description="Why, in terms of the shop's figures and priorities."
    )
    figures: list[FigureCited] = Field(default_factory=list)
    blocked_on: str | None = None
    approvals_raised: list[int] = Field(
        default_factory=list, description="Approval ids this ticket is waiting on."
    )
    money_moved: float = Field(
        default=0.0, description="Cash that actually left the shop on this ticket."
    )
    delegated_to: list[str] = Field(
        default_factory=list, description="Colleagues the Boss consulted."
    )
    customer_draft_id: int | None = Field(
        default=None, description="Draft filed for a human to send, if any."
    )


# --- audit ---------------------------------------------------------------


class ModelCheck(BaseModel):
    """Proof that a call ran on the model the assignment requires.

    The gateway answers a misspelled model name with an older model instead of
    erroring, so `requested` matching `gpt-6-luna` proves nothing on its own.
    `resolved` is what the gateway said it actually used, and `ok` is the
    comparison. A run with `ok: false` anywhere in it is void.
    """

    requested: str
    resolved: str | None = None
    ok: bool = False
    note: str | None = None


class ToolCallRecord(BaseModel):
    """One MCP tool call: what was asked, what came back."""

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_summary: str = Field(
        description="The returned payload, trimmed. Enough to re-check the decision."
    )
    is_error: bool = False


class AuditStep(BaseModel):
    """One step of one agent's loop -- the unit a reviewer reads.

    Enough has to live in here that someone can audit the run later without the
    transcript: who acted, on what ticket, who asked them, which tools they
    called with which arguments, what came back, what they concluded, what the
    model actually was, and what it cost.
    """

    step: int
    run_id: str
    ticket_id: int | None = None
    agent: AgentName
    delegated_by: AgentName | None = Field(
        default=None, description="None when the run itself invoked this agent."
    )
    task: str = Field(description="The question this agent was asked.")
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    output: str = Field(description="What the agent concluded.")
    blocked_on: str | None = None
    needs_human: str | None = None
    model: ModelCheck
    usage: dict[str, Any] = Field(
        default_factory=dict, description="Token counts for this step."
    )
    started_at: str
    finished_at: str
    duration_seconds: float
    error: str | None = None


class RunRecord(BaseModel):
    """The header written once per run, before any agent is invoked."""

    run_id: str
    started_at: str
    shop_date_today: str
    model_requested: str
    tickets_in_scope: list[int]
    database: str
    reset_before_run: bool
    note: str = (
        "Appended to output/audit_trail.json. Earlier runs are never "
        "overwritten -- the file is the shop's history, not the last run's."
    )


def utc_now() -> str:
    """Wall-clock timestamp, for audit ordering only.

    Deliberately distinct from the shop's clock: `desk.date_today` is what the
    *business* reasons about, while an audit trail needs to know when the run
    really happened. The two must never be confused, which is why they are
    different functions with different names.
    """
    return dt.datetime.now(dt.timezone.utc).isoformat()
