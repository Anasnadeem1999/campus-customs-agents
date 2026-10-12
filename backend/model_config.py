"""One model, through the course gateway, checked on every call.

The assignment requires every agent to run on `gpt-6-luna`, and the Portkey
gateway has a trap in it: a model name it does not recognise does **not**
error. It quietly answers as `gpt-5.6-luna` instead. A single typo would
therefore cost marks with nothing in the output to show for it -- the run would
look perfect.

So the requested name is never taken as proof. Every agent step reads the
model the gateway says it *actually* used, compares it, and records both in the
audit trail. `assert_model_ok` turns a mismatch into a loud failure.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from .models import ModelCheck

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

#: The only model allowed to answer in this homework.
REQUIRED_MODEL = os.environ.get("MODEL_NAME", "gpt-6-luna")

#: What a correct resolution looks like. The gateway appends a dated suffix
#: (`gpt-6-luna-2026-09-22`), so this is a prefix test, not equality -- but it
#: is a *strict* prefix test: `gpt-6-luna` must not match `gpt-6-luna-mini` by
#: accident, hence the separator check below.
REQUIRED_PREFIX = "gpt-6-luna"

#: Settings every agent shares.
#:
#: `reasoning_effort="none"` is not a preference -- it is required. Asked for
#: function tools with reasoning left on, the gateway refuses the whole call:
#:
#:     azure-openai error: Function tools with reasoning_effort are not
#:     supported for gpt-6-luna-global in /v1/chat/completions. To use function
#:     tools, use /v1/responses or set reasoning_effort to 'none'.
#:
#: Every agent here calls MCP tools, so every agent hits that. Verified against
#: the live gateway on 2026-10-11: with this setting a tool-calling request
#: succeeds and resolves to `gpt-6-luna-2026-09-22`; without it, HTTP 400 and
#: nothing runs at all.
MODEL_SETTINGS = OpenAIChatModelSettings(openai_reasoning_effort="none")


class ModelPolicyError(RuntimeError):
    """Raised when a call did not run on the required model."""


def build_model() -> OpenAIChatModel:
    """The one model object every agent shares.

    Portkey speaks the OpenAI chat API, so the OpenAI provider points at the
    gateway's base URL. The key is read from the environment and never logged.
    """
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        raise ModelPolicyError(
            "PORTKEY_API_KEY is not set. Copy .env.example to .env and fill it in. "
            "Never commit .env."
        )
    base_url = os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
    return OpenAIChatModel(
        REQUIRED_MODEL,
        provider=OpenAIProvider(base_url=base_url, api_key=api_key),
    )


def resolved_model_name(result) -> str | None:
    """Dig the model the gateway actually used out of a pydantic-ai result.

    Different versions hang this in different places, so look in each rather
    than assume. Returning None is honest -- it means we could not prove the
    model, which the caller treats as a failure, not as a pass.
    """
    for message in reversed(getattr(result, "all_messages", lambda: [])()):
        name = getattr(message, "model_name", None)
        if name:
            return name
    return None


def check_model(result) -> ModelCheck:
    """Compare what the gateway used against what the assignment requires."""
    resolved = resolved_model_name(result)
    if resolved is None:
        return ModelCheck(
            requested=REQUIRED_MODEL,
            resolved=None,
            ok=False,
            note="The gateway did not report a model name, so the model could not be "
            "proven. Treat this run as unverified.",
        )

    # Strict prefix: the dated suffix is allowed, a different family is not.
    ok = resolved == REQUIRED_PREFIX or resolved.startswith(REQUIRED_PREFIX + "-")
    note = None
    if not ok:
        note = (
            f"Gateway answered as {resolved!r}, which is not {REQUIRED_PREFIX}. "
            "The gateway silently substitutes an older model for an unrecognised "
            "name, so check MODEL_NAME for a typo. This run is void."
        )
    return ModelCheck(requested=REQUIRED_MODEL, resolved=resolved, ok=ok, note=note)


def assert_model_ok(check: ModelCheck) -> None:
    """Fail loudly rather than let a wrong-model run look like a good one."""
    if not check.ok:
        raise ModelPolicyError(check.note or f"Model check failed: {check!r}")
