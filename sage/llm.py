"""Turn assembly, streaming, and error classification.

There used to be two near-identical stream readers — one that yielded deltas for
the UI and one that collected silently — and the tool loop used the silent one for
its final round. The result was that the *most common* interaction (search → read →
answer) never streamed: users watched a shimmer, then the whole answer appeared at
once. One reader now serves both, so every answer streams.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from . import config
from .providers import Chunk

logger = logging.getLogger(__name__)

_RETRYABLE = {"rate_limit", "network", "unavailable"}

# Read by visitors, so they name what happened and what to do — never a provider,
# a model, a quota or an API key. Which of several backends ran out of credit is
# not something a reader of a blog can act on, and `engine.run_conversation` has
# already tried the others by the time any of this is shown.
#
# That last clause is why the first four say the same thing. By the time any of them
# reaches a reader the whole ladder has refused, so the four causes have collapsed
# into one situation with one useful response, and distinguishing them in the text
# could only be done by naming the thing that is spent. "Busy right now, please wait
# a moment" was worse than dry: on a free tier whose cap is measured in hours it was
# not true, and it read as the panel being broken. The details panel and the log
# still carry the exact cause for whoever is fixing it.
#
# Deliberately lighter than the rest of the site's register, which is the owner's
# call: the reader has been told no through no fault of their own, and a warm sentence
# lands better there than a status code. `context`, `network` and `unknown` stay plain,
# because each names something the reader can actually act on and a joke would be in
# the way of it.
EXHAUSTED = (
    "Even a well-read assistant needs a tea break. \U0001f375 "
    "Please try again a little later."
)

# A model that answered, and answered with nothing. Kept here rather than in the engine
# because it is now the message for a *failure kind* and not for a placeholder the
# engine writes: `engine.run_turn` raises `empty` so the ladder can go on to a model
# that will say something, and this is what the reader gets only once every one of them
# has been asked. `engine.UNFINISHED` is still the name the rest of the code uses.
UNFINISHED = (
    "I wasn't able to finish looking that up. Please try rephrasing your question."
)

_MESSAGES = {
    "auth": EXHAUSTED,
    "rate_limit": EXHAUSTED,
    "quota": EXHAUSTED,
    "unavailable": EXHAUSTED,
    # Not a transport failure, so it never comes out of `classify`. It is raised
    # deliberately by `engine.run_turn` for a 200 that carried no answer, which is a
    # real refusal wearing a success code and used to end the walk as if it had
    # succeeded. See `engine.FAILS_OVER`.
    "empty": UNFINISHED,
    "context": "This conversation got too long. Clear it and ask again.",
    "network": "Could not reach the assistant. Check the connection and retry.",
    "unknown": "Something went wrong. Please try again.",
}


class AssistantError(Exception):
    def __init__(self, kind: str, original: BaseException | None = None) -> None:
        self.kind = kind if kind in _MESSAGES else "unknown"
        self.original = original
        # The model that actually raised, filled in by `engine.run_conversation`,
        # which is the only layer that knows there was more than one candidate. Not
        # for the reader: it goes in the details panel, where the question being
        # answered is "which endpoint said no", and after a failover that is not the
        # model the picker had selected.
        self.model: str = ""
        # Every candidate that refused, in order, as (model key, kind). Filled in by
        # `engine.run_conversation`, and the reason it exists is that reporting only
        # the last link hides which ladder was walked. A 402 from Mistral looks the
        # same whether Zen was tried first and rate-limited, or was never configured
        # and never in the queue: two different problems with two different fixes, and
        # nothing on screen or in the log told them apart.
        self.tried: list[tuple[str, str]] = []
        # Candidates that were never asked because they refused recently enough to still
        # be cooling. Reported next to `tried` and for the same reason: a walk that
        # skipped six of eleven rungs looks, in a count alone, exactly like the pruning
        # bug that skipped nine of them, and those need opposite responses.
        self.skipped: list[str] = []
        super().__init__(_MESSAGES[self.kind])

    @property
    def user_message(self) -> str:
        return _MESSAGES[self.kind]

    @property
    def retryable(self) -> bool:
        return self.kind in _RETRYABLE


def http_detail(exc: BaseException | None) -> str:
    """What the endpoint actually said, which httpx's own message leaves out.

    `HTTPStatusError` stringifies to "Client error '429 Too Many Requests' for url ..."
    and nothing else, so every 429 looked identical and the question "which limit" had
    no answer anywhere: requests a minute, tokens a minute, or a daily cap are three
    different problems with three different responses, and one of them is fixed by
    waiting ninety seconds.

    The body is already there to be read. `OpenAICompatProvider.stream` calls
    `response.read()` before raising, because a status cannot be raised on an unread
    stream, so `.text` is populated and was simply discarded.

    Trimmed, and headers only from a fixed list: the response is the endpoint's own
    error text, but this goes on a public page's details panel and a whitelist is the
    difference between reporting a rate limit and echoing whatever a third party chose
    to put in a header.
    """
    response = getattr(exc, "response", None)
    if response is None:
        return ""
    seen = []
    for header in (
        "retry-after",
        "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
        "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens",
    ):
        try:
            value = response.headers.get(header)
        except Exception:
            value = None
        if value:
            seen.append(f"{header}: {value}")
    try:
        body = (response.text or "").strip()
    except Exception:
        body = ""
    if body:
        seen.append(f"body: {body[:300]}")
    return "\n".join(seen)


def classify(exc: BaseException) -> AssistantError:
    if isinstance(exc, AssistantError):
        return exc

    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status is None:
        # httpx.HTTPStatusError keeps the code on .response
        status = getattr(getattr(exc, "response", None), "status_code", None)
    text = f"{type(exc).__name__} {exc}".lower()

    if status in (401, 403) or "unauthorized" in text or "invalid api key" in text:
        kind = "auth"
    elif status == 402 or any(
        needle in text
        for needle in ("quota", "insufficient", "credit", "billing",
                       "check your subscription", "payment")
    ):
        # Out of credit does not recover by waiting, so it is deliberately not
        # retryable — switching provider is the only useful action.
        kind = "quota"
    elif status == 429 or "rate limit" in text or "too many requests" in text:
        kind = "rate_limit"
    elif (
        ("context" in text and ("length" in text or "token" in text))
        or "too large" in text
        or status == 413
    ):
        kind = "context"
    elif isinstance(status, int) and 500 <= status < 600:
        kind = "unavailable"
    elif any(
        needle in text
        for needle in ("timeout", "timed out", "connection", "network", "dns", "ssl")
    ):
        kind = "network"
    else:
        kind = "unknown"
    return AssistantError(kind, exc)


@dataclass
class Turn:
    """One model turn. Iterate `deltas()` to stream, or `consume()` to block.

    Consumes normalised `Chunk`s, so Mistral and any OpenAI-compatible endpoint
    go through exactly the same assembly and error handling.
    """

    stream: Any
    text: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    finished: bool = False

    def deltas(self) -> Iterator[str]:
        pending: dict[int, dict] = {}
        try:
            for chunk in self.stream:
                if not isinstance(chunk, Chunk):
                    continue
                if chunk.text:
                    self.text += chunk.text
                    yield chunk.text
                for fragment in chunk.tool_calls:
                    slot = pending.setdefault(
                        fragment["index"], {"id": "", "name": "", "args": ""}
                    )
                    if fragment.get("id"):
                        slot["id"] = fragment["id"]
                    if fragment.get("name"):
                        slot["name"] = fragment["name"]
                    if fragment.get("arguments"):
                        slot["args"] += fragment["arguments"]
        except Exception as exc:
            raise classify(exc) from exc

        self.tool_calls = [
            {"id": slot["id"], "name": slot["name"], "input": _parse(slot["args"])}
            for slot in pending.values()
            if slot["name"]
        ]
        self.finished = True

    def consume(self) -> Turn:
        for _ in self.deltas():
            pass
        return self

    def as_message(self) -> dict:
        """The assistant message to append before tool results."""
        return {
            "role": "assistant",
            "content": self.text,
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["input"]),
                    },
                }
                for call in self.tool_calls
            ],
        }


def _parse(arguments: str) -> dict:
    if not arguments:
        return {}
    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError:
        logger.warning("Unparseable tool arguments: %r", arguments[:200])
        return {}
    return parsed if isinstance(parsed, dict) else {}


def start(provider, model: str, messages: list[dict],
          tools: list[dict] | None = None, *, retry: bool = True) -> Turn:
    """Open a streaming turn, retrying transient failures before any output.

    `retry=False` spends one attempt and no backoff. It is for the caller that has
    somewhere better to go: waiting 1s and then 2s on a model that has just reported
    a rate limit is three requests to a service asking for fewer, and it delays the
    failover that was going to answer the question anyway. See
    `engine.run_conversation`, which is the only caller that knows whether an
    alternative exists.
    """
    attempts = (max(config.REQUEST_RETRIES, 0) + 1) if retry else 1
    last: AssistantError | None = None

    for attempt in range(attempts):
        try:
            stream = provider.stream(model, messages, tools)
            # `stream` is a generator, so the request has not been made yet. Pull
            # the first chunk here so connection and auth failures surface where
            # they can still be retried, rather than mid-render.
            first = next(stream, None)
            return Turn(stream=_replay(first, stream))
        except Exception as exc:
            error = classify(exc)
            last = error
            if not error.retryable or attempt == attempts - 1:
                said = http_detail(exc)
                if said:
                    logger.warning("%s from %s said: %s", error.kind, provider.name,
                                   said.replace("\n", " | "))
                raise error from exc
            delay = 2**attempt
            logger.warning(
                "Transient %s from %s, retrying in %ss", error.kind, provider.name, delay
            )
            time.sleep(delay)

    raise last or AssistantError("unknown")


def _replay(first, rest) -> Iterator[Chunk]:
    if first is not None:
        yield first
    yield from rest


def rejects_tools(exc: BaseException) -> bool:
    """Whether a failure looks like the model simply not supporting tool calls."""
    text = f"{type(exc).__name__} {exc}".lower()
    return ("tool" in text or "function" in text) and any(
        mark in text for mark in
        ("not support", "unsupported", "invalid", "unknown parameter", "unrecognized")
    )


def tool_result_message(call: dict, content: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": call["id"],
        "name": call["name"],
        "content": content,
    }
