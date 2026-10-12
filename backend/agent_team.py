"""The five agents, fully connected, with every step written to the audit trail.

Five colleagues -- Boss, Inventory, Accounting, Facilities, Customer Service --
each built the same way: the shop rules, then that role's own brief, then the
MCP toolset, then a `ask_<colleague>` tool for every other member of the team.
"Fully connected" is literal: Customer Service can ask Accounting directly
without routing through the Boss, and Inventory can ask the Boss.

**The shop is reached only through MCP.** The toolsets come from the committed
`.mcp.json`, the same file the vibe coder loads, so the agents and the human
are looking at one server. Nothing in this package reads the database. If a
figure is not in a tool result, no agent has any way to know it.

### Why delegation needs a leash

A fully connected team can talk forever -- A asks B, B asks A, and nothing on
either side thinks it is doing anything wrong. Three limits stop that without
getting in the way of real work:

* **Depth.** A delegation chain deeper than `MAX_DEPTH` is refused, and the
  refusal is returned to the asking agent as a normal tool result so it can
  answer with what it already has instead of failing.
* **Steps per ticket.** A whole-ticket budget, so a team that is going in
  circles stops.
* **Usage limits.** Per-agent request and token caps, enforced by pydantic-ai.

Each limit returns a *usable* message rather than an exception wherever it can.
An agent that is told "you are too deep, answer from what you have" produces
something; one that gets an exception produces nothing.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import load_mcp_toolsets
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.usage import UsageLimits

from . import audit
from .model_config import MODEL_SETTINGS, REQUIRED_MODEL, build_model, check_model
from .models import (
    AgentName,
    AuditStep,
    ColleagueReply,
    ModelCheck,
    TicketResolution,
    ToolCallRecord,
    utc_now,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "backend" / "prompts"
MCP_CONFIG = REPO_ROOT / ".mcp.json"

#: How deep a delegation chain may go. 3 lets the Boss ask a colleague who asks
#: a second colleague -- which is the deepest the seeded tickets genuinely
#: need -- and refuses the fourth hop.
MAX_DEPTH = 3

#: Agent turns allowed per ticket, across the whole team.
MAX_STEPS_PER_TICKET = 14

#: Per-agent-turn ceilings. Generous enough that a real chain of tool calls
#: finishes; tight enough that a loop cannot run up a bill unnoticed.
#:
#: The token figure is measured, not guessed. A Boss turn working ticket 101 --
#: the hardest of the three, with two delegations and a payment -- came in at
#: 120,980 tokens and was killed by a 120,000 ceiling after doing nearly all
#: the work. A limit that stops a turn just before it finishes costs the whole
#: turn and buys nothing, so the ceiling is set well clear of the real maximum
#: and left to catch genuine runaways.
AGENT_USAGE_LIMITS = UsageLimits(request_limit=12, total_tokens_limit=250_000)

#: Retries allowed per tool call. The default of 1 is too tight here: this
#: server's tools refuse loudly and on purpose -- wrong amount, vendor blocked,
#: insufficient funds -- and the refusal text is written to be *actionable*, so
#: an agent that reads it can usually fix its arguments and succeed on the next
#: attempt. One retry turns a recoverable correction into a dead run; three
#: lets the agent act on what it was told without licensing an endless loop.
TOOL_RETRIES = 3

#: Wall-clock ceiling on a single agent turn.
#:
#: The usage limits above bound tokens and requests, but neither bounds *time*:
#: a run was observed sitting on one agent turn for ten minutes with no new
#: audit step and no error, which from the outside is indistinguishable from
#: slow progress. A hang is the one failure a budget cannot catch, so it gets
#: its own limit. The turn is abandoned, the timeout is written to the trail as
#: a failed step, and the run carries on with the next ticket rather than
#: taking the whole board down with it.
STEP_TIMEOUT_SECONDS = 240

#: pydantic-ai routes an agent's structured output through a synthetic tool
#: call. It is not an MCP tool and the agent did not choose it, so it is
#: filtered out of the recorded tool list.
OUTPUT_TOOL_NAMES = {"final_result"}

ROLE_FILES: dict[AgentName, str] = {
    "boss": "boss.md",
    "inventory": "inventory.md",
    "accounting": "accounting.md",
    "facilities": "facilities.md",
    "customer_service": "customer_service.md",
}

COLLEAGUE_BLURB: dict[AgentName, str] = {
    "boss": "sets priorities across tickets and makes the final call",
    "inventory": "stock by SKU and size, shortfalls, restock vendors and lead times",
    "accounting": "cash, invoices, margins, affordability, preparing approvals",
    "facilities": "the lease, rent, the landlord, the premises",
    "customer_service": "drafting what a customer will read",
}


def _read(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_instructions(agent: AgentName) -> str:
    """Shop rules first, then the role. Order matters: the rules outrank the role."""
    return (
        f"{_read('shop_rules.md')}\n\n"
        "---\n\n"
        f"{_read(ROLE_FILES[agent])}\n"
    )


@dataclass
class RunState:
    """Everything one ticket-resolution run needs to keep track of itself."""

    run_id: str
    ticket_id: int | None = None
    steps_this_ticket: int = 0
    model_failures: list[ModelCheck] = field(default_factory=list)

    def budget_left(self) -> int:
        return MAX_STEPS_PER_TICKET - self.steps_this_ticket


@dataclass
class Deps:
    """Carried through every agent call so a nested one can find the team."""

    team: "AgentTeam"
    state: RunState
    depth: int = 0
    asked_by: AgentName | None = None


def render_reply(reply: ColleagueReply | TicketResolution) -> str:
    """Turn a colleague's answer into text for the agent that asked.

    Two shapes arrive here, because "fully connected" includes asking the
    Boss, and the Boss answers with a `TicketResolution` rather than a
    `ColleagueReply`. Reading `.answer` off one of those raised an
    AttributeError mid-run and lost the whole turn -- so the two shapes are
    handled explicitly rather than assumed to be interchangeable.
    """
    parts: list[str] = []
    if isinstance(reply, TicketResolution):
        parts.append(reply.decision)
        if reply.reasoning:
            parts.append(f"Reasoning: {reply.reasoning}")
        parts.append(f"Outcome on ticket {reply.ticket_id}: {reply.outcome}")
        if reply.approvals_raised:
            parts.append(f"Approvals raised: {reply.approvals_raised}")
    else:
        parts.append(reply.answer)
        if reply.needs_human:
            parts.append(f"Needs a human: {reply.needs_human}")

    if reply.figures:
        cited = "; ".join(f"{f.label}={f.value} (via {f.from_tool})" for f in reply.figures)
        parts.append(f"Figures: {cited}")
    if reply.blocked_on:
        parts.append(f"Blocked on: {reply.blocked_on}")
    return "\n".join(parts)


def _extract_tool_calls(result: Any) -> list[ToolCallRecord]:
    """Pull the MCP calls an agent made out of its message history.

    This is what makes the trail auditable rather than merely descriptive: the
    arguments and the returned payload are both recorded, so a reviewer can
    replay the exact call and see whether the agent's conclusion followed from
    what it actually got back.
    """
    calls: dict[str, ToolCallRecord] = {}
    order: list[str] = []
    for message in result.all_messages():
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolCallPart):
                if part.tool_name in OUTPUT_TOOL_NAMES:
                    # pydantic-ai's own structured-output call, not something
                    # the agent chose to do. Listing it as a tool the agent
                    # "used" would put a tool on the dashboard that does not
                    # exist on the MCP server, and the agent's conclusion is
                    # already recorded separately as its output.
                    continue
                key = part.tool_call_id or f"{part.tool_name}-{len(order)}"
                args = part.args
                if isinstance(args, str):
                    # The provider sends arguments as a JSON string. Parsing
                    # here means the audit trail and the dashboard both get
                    # real fields instead of one opaque blob, so a reviewer
                    # can see *which invoice* was paid, not just that one was.
                    try:
                        args = json.loads(args)
                    except (json.JSONDecodeError, TypeError):
                        args = {"raw": args}
                if not isinstance(args, dict):
                    args = {"value": args}
                calls[key] = ToolCallRecord(
                    tool=part.tool_name,
                    arguments=args or {},
                    result_summary="(no result recorded)",
                )
                order.append(key)
            elif isinstance(part, ToolReturnPart):
                key = part.tool_call_id
                if key in calls:
                    calls[key].result_summary = audit.summarise(part.content)
                    text = str(part.content).lower()
                    calls[key].is_error = "refused" in text or "error" in text
    return [calls[k] for k in order if k in calls]


class AgentTeam:
    """Builds the five agents and runs them, recording every step."""

    def __init__(self) -> None:
        self.model = build_model()
        # One shared MCP toolset list, loaded from the committed config.
        self.toolsets = load_mcp_toolsets(MCP_CONFIG)
        self.agents: dict[AgentName, Agent] = {}
        for name in ROLE_FILES:
            self.agents[name] = self._build_agent(name)

    def mcp_client(self):
        """The raw MCP client underneath the toolset.

        For callers that need a tool result before any agent exists to ask for
        it -- the runner reading the ticket board. Reaching through the
        prefixed wrapper keeps that read on the same server and the same
        connection settings the agents use, rather than opening a second path
        to the database.
        """
        toolset = self.toolsets[0]
        inner = getattr(toolset, "wrapped", toolset)
        return inner.client

    # --- construction ----------------------------------------------------

    def _build_agent(self, name: AgentName) -> Agent:
        output_type = TicketResolution if name == "boss" else ColleagueReply
        agent = Agent(
            self.model,
            name=name,
            instructions=build_instructions(name),
            deps_type=Deps,
            output_type=output_type,
            model_settings=MODEL_SETTINGS,
            retries=TOOL_RETRIES,
            toolsets=list(self.toolsets),
        )
        self._attach_delegation(agent, name)
        return agent

    def _attach_delegation(self, agent: Agent, owner: AgentName) -> None:
        """Give this agent a way to ask every other agent. Fully connected."""
        for colleague in ROLE_FILES:
            if colleague == owner:
                continue
            self._add_ask_tool(agent, colleague)

    def _add_ask_tool(self, agent: Agent, colleague: AgentName) -> None:
        blurb = COLLEAGUE_BLURB[colleague]

        async def ask(ctx: RunContext[Deps], question: str) -> str:
            """Ask a colleague one specific question and get their answer back."""
            deps = ctx.deps
            if deps.depth + 1 > MAX_DEPTH:
                return (
                    f"[delegation refused] This chain is already {deps.depth} deep, which is "
                    f"the limit. Do not ask anyone else -- answer now from what you have, "
                    f"and say plainly what you could not find out."
                )
            if deps.state.budget_left() <= 0:
                return (
                    "[delegation refused] This ticket has used its whole step budget. "
                    "Answer now with what you have and name what is still unresolved."
                )
            reply = await self.run_agent(
                colleague,
                question,
                state=deps.state,
                depth=deps.depth + 1,
                asked_by=agent.name,  # type: ignore[arg-type]
            )
            if reply is None:
                return f"[{colleague} could not answer] Proceed without it and say so."
            return render_reply(reply)

        ask.__name__ = f"ask_{colleague}"
        ask.__doc__ = (
            f"Ask {colleague.replace('_', ' ').title()} -- {blurb}.\n\n"
            "Ask one specific question and include the figures you already have, "
            "so they can answer rather than re-derive the ticket. Do not use this "
            "for something a tool in front of you already answers."
        )
        agent.tool(ask)

    # --- running ---------------------------------------------------------

    async def run_agent(
        self,
        name: AgentName,
        task: str,
        *,
        state: RunState,
        depth: int = 0,
        asked_by: AgentName | None = None,
    ) -> ColleagueReply | TicketResolution | None:
        """Run one agent for one turn and append exactly one audit step."""
        agent = self.agents[name]
        deps = Deps(team=self, state=state, depth=depth, asked_by=asked_by)
        state.steps_this_ticket += 1

        started = utc_now()
        clock = time.perf_counter()
        error: str | None = None
        result = None
        try:
            result = await asyncio.wait_for(
                agent.run(task, deps=deps, usage_limits=AGENT_USAGE_LIMITS),
                timeout=STEP_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            error = (
                f"TimeoutError: {name} exceeded {STEP_TIMEOUT_SECONDS}s on one turn and "
                "was abandoned. The run continues; this ticket is unfinished."
            )
        except Exception as exc:  # noqa: BLE001 -- the trail must record failures too
            error = f"{type(exc).__name__}: {exc}"

        finished = utc_now()
        duration = round(time.perf_counter() - clock, 3)

        if result is None:
            model_check = ModelCheck(
                requested=REQUIRED_MODEL, resolved=None, ok=False,
                note="The call failed before the gateway reported a model.",
            )
            audit.append_step(
                AuditStep(
                    step=audit.next_step_number(), run_id=state.run_id,
                    ticket_id=state.ticket_id, agent=name, delegated_by=asked_by,
                    task=task, tool_calls=[], output="(failed)", model=model_check,
                    started_at=started, finished_at=finished,
                    duration_seconds=duration, error=error,
                )
            )
            return None

        model_check = check_model(result)
        if not model_check.ok:
            # Recorded, not raised: a void run should still be inspectable, and
            # the runner decides what to do about it once the step is on disk.
            state.model_failures.append(model_check)

        output = result.output
        usage = result.usage
        audit.append_step(
            AuditStep(
                step=audit.next_step_number(),
                run_id=state.run_id,
                ticket_id=state.ticket_id,
                agent=name,
                delegated_by=asked_by,
                task=task,
                tool_calls=_extract_tool_calls(result),
                output=audit.summarise(
                    output.model_dump() if hasattr(output, "model_dump") else output
                ),
                blocked_on=getattr(output, "blocked_on", None),
                needs_human=getattr(output, "needs_human", None),
                model=model_check,
                usage={
                    "requests": getattr(usage, "requests", None),
                    "input_tokens": getattr(usage, "input_tokens", None),
                    "output_tokens": getattr(usage, "output_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                },
                started_at=started,
                finished_at=finished,
                duration_seconds=duration,
                error=None,
            )
        )
        return output

    async def work_ticket(self, ticket: dict[str, Any], run_id: str) -> TicketResolution | None:
        """Hand one ticket to the Boss and let the team work it."""
        state = RunState(run_id=run_id, ticket_id=int(ticket["id"]))
        task = (
            f"Ticket {ticket['id']} ({ticket['type']}) from {ticket['requester']}: "
            f"{ticket['subject']}.\n"
            f"Ticket fields -- sku: {ticket.get('sku')}, size: {ticket.get('size')}, "
            f"qty: {ticket.get('qty')}, lease_id: {ticket.get('lease_id')}, "
            f"invoice_id: {ticket.get('invoice_id')}, status: {ticket.get('status')}.\n"
            f"Customer's note: {ticket.get('notes')}\n\n"
            "Work this ticket to a resolution. Read the shop's own figures with the "
            "tools, delegate to whoever owns each part, and finish by updating the "
            "ticket.\n\n"
            "Start by calling list_approvals. This ticket may have been worked "
            "before and stopped at the approval gate: if there is already an "
            "approved, unspent request for it, a human has said yes and your job "
            "is to act on it now -- pay it and finish the ticket. Only raise a new "
            "approval request if none exists for this job.\n\n"
            "If the shop cannot do what is asked, say so plainly and say what it "
            "would take."
        )
        return await self.run_agent("boss", task, state=state)


def new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:8]}"
