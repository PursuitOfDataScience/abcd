"""Chat providers behind one interface, so the model is a runtime choice.

Three are supported:

* **OpenRouter**, an OpenAI-compatible endpoint at `https://openrouter.ai/api/v1`.
  This deployment offers one entry there and it is a router rather than a model:
  `openrouter/free` picks a free model per request from whatever is currently up. See
  `config.OPENROUTER_BASE_URL` for what that buys and what it costs.
* **OpenCode Zen**, an OpenAI-compatible endpoint at `https://opencode.ai/zen/v1`
  that fronts a set of free models. Useful when a paid key runs out of credit.
* **Mistral**, via the official SDK.

The two OpenAI-compatible ones share `OpenAICompatProvider` and differ only in the
data handed to it, which is the whole reason the class takes its lineup rules as
arguments rather than reading Zen's out of `config` itself.

Both normalise onto `Chunk`, so nothing downstream knows which one is in use.
Model lists are discovered from the provider at runtime rather than hardcoded,
because a free tier's lineup changes without notice; a configured list is the
fallback when discovery fails.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from . import config

logger = logging.getLogger(__name__)

MISTRAL = "mistral"
OPENCODE = "opencode"
OPENROUTER = "openrouter"

#: Every provider this module can build, in the order the app should prefer them. Read
#: by `app.configured_providers`, which filters it to the ones with a key, and by
#: `parse_key`, so a new provider is added here and not in three places.
#:
#: Set by the owner on 2026-08-28, in these words: the OpenRouter free model first, and
#: if it fails then OpenCode, and so on. So the tuple is the instruction, and the reasons
#: below are why it is also the right order rather than what chose it.
#:
#: OpenRouter leads because it is the only one of the three that does not need a name in
#: this file kept true by hand: its entry is a router, so a model that stops answering is
#: the provider's problem to route around rather than a commit here. It is also the only
#: provider whose *first* failure is worth much: a refusal from a router is a refusal
#: from whatever it picked, and the next rung is a different endpoint entirely.
#:
#: Zen second, because its key is free and, on the measurement in `config.ZEN_DENY`, it
#: still has one model that answers. Mistral last, and this is the half that changed:
#: it used to sit second, from before OpenRouter existed. It is paid, out of credit on
#: this deployment, and offers three models, so a walk that reached it spent three round
#: trips learning the same thing three times before it could get to a free model that
#: works. Now it is only reached when nothing free will answer, which is the one
#: situation a spent paid key is worth asking.
NAMES = (OPENROUTER, OPENCODE, MISTRAL)


@dataclass(frozen=True)
class Model:
    provider: str
    id: str

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.id}"

    @property
    def label(self) -> str:
        """The model's own name, and nothing else.

        There was a provider prefix, "Zen · deepseek-v4-flash-free", which spent a
        third of the picker's width restating what the rest of the row already said,
        on every line. The id alone identifies the model, and `mistral-` on the front
        of the Mistral ones does the same job the prefix was doing.

        `config.MODEL_LABELS` gets the first word, for the one case the sentence above
        does not cover: an id that is not a name at all. A router's id describes which
        free tier the request draws on, which is not a thing to put in front of a
        reader, and this deployment does put labels in front of readers: the failover
        notice and the cannot-read-images warning are both prose with a `label` in the
        middle of them.

        Only this property reads that mapping, so the id stays untouched in `key`,
        upstream, in the session state, in the feedback log and in the error card's
        technical details.
        """
        return config.model_label(self.id) or self.id

    @property
    def supports_tools(self) -> bool:
        """Some free models cannot call tools; those fall back to plain retrieval."""
        lowered = self.id.lower()
        return not any(mark and mark in lowered for mark in config.TOOLLESS_MODELS)


@dataclass
class Chunk:
    """One normalised streaming event."""

    text: str = ""
    tool_calls: list[dict] = field(default_factory=list)


class Provider(Protocol):
    name: str

    def models(self) -> list[Model]: ...

    def stream(
        self, model: str, messages: list[dict], tools: list[dict] | None
    ) -> Iterator[Chunk]: ...


def _tool_fragments(raw) -> list[dict]:
    """Normalise a delta's tool_calls, whether objects (SDK) or dicts (JSON)."""
    fragments = []
    for index, call in enumerate(raw or []):
        if isinstance(call, dict):
            function = call.get("function") or {}
            fragments.append(
                {
                    "index": call.get("index", index) or 0,
                    "id": call.get("id") or "",
                    "name": function.get("name") or "",
                    "arguments": function.get("arguments") or "",
                }
            )
            continue
        function = getattr(call, "function", None)
        fragments.append(
            {
                "index": getattr(call, "index", index) or 0,
                "id": getattr(call, "id", "") or "",
                "name": getattr(function, "name", "") or "",
                "arguments": getattr(function, "arguments", "") or "",
            }
        )
    return fragments


def _flatten(content) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part if isinstance(part, str) else (
                part.get("text", "") if isinstance(part, dict)
                else getattr(part, "text", "") or ""
            )
            for part in content
        )
    return str(content)


# --- Mistral ---------------------------------------------------------------


class MistralProvider:
    name = MISTRAL

    def __init__(self, api_key: str) -> None:
        from mistralai import Mistral  # noqa: PLC0415

        self._client = Mistral(api_key=api_key)

    def models(self) -> list[Model]:
        return [Model(MISTRAL, name) for name in config.MISTRAL_MODELS]

    def stream(self, model, messages, tools) -> Iterator[Chunk]:
        stream = self._client.chat.stream(
            model=model,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )
        # SDK 1.x returns a context manager; some builds a bare iterator.
        manager = stream if hasattr(type(stream), "__enter__") else None
        source = manager.__enter__() if manager else stream
        if source is None:
            source = stream
        try:
            for event in source:
                data = getattr(event, "data", None)
                if not data or not getattr(data, "choices", None):
                    continue
                delta = data.choices[0].delta
                yield Chunk(
                    text=_flatten(getattr(delta, "content", None)),
                    tool_calls=_tool_fragments(getattr(delta, "tool_calls", None)),
                )
        finally:
            if manager is not None:
                try:
                    manager.__exit__(None, None, None)
                except Exception:
                    logger.debug("Ignoring error closing the stream", exc_info=True)


# --- OpenAI-compatible (OpenRouter, OpenCode Zen) --------------------------


class OpenAICompatProvider:
    """Any OpenAI-compatible `/chat/completions` endpoint."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        name: str = OPENCODE,
        preferred: tuple[str, ...] | None = None,
        free_marks: tuple[str, ...] | None = None,
        free_only: bool | None = None,
        deny: tuple[str, ...] | None = None,
    ) -> None:
        self.name = name
        self._key = api_key
        self._base = base_url.rstrip("/")
        # Discovery returns the catalogue in arbitrary order. This is the order
        # we would choose, and it decides both the picker's default and what an
        # automatic failover lands on, so it must not be alphabetical.
        self._preferred = (
            config.OPENCODE_MODELS if preferred is None else tuple(preferred)
        )
        # The three rules that turn a served catalogue into a lineup: which ids this
        # key can pay for, whether to apply that at all, and which ids are known not to
        # work whoever is paying. Arguments rather than reads of `config`, because there
        # are two OpenAI-compatible providers now and they answer all three differently.
        # Zen's free rule is a naming convention, so it catches a model this repository
        # has never heard of; OpenRouter's names exactly the one model it offers, so
        # discovery cannot widen it. Same field, opposite intent.
        #
        # `None` means Zen's, so a caller that predates the second provider keeps its
        # behaviour. `build` passes all three explicitly.
        #
        # Kept as `None` rather than resolved here, and read through the properties
        # below. Resolving at construction would move when an override takes effect: a
        # `config` value patched after the provider was built used to count and would
        # silently stop counting, which is a behaviour change hiding inside a
        # refactor. The properties keep the old late binding.
        self._free_marks_setting = None if free_marks is None else tuple(free_marks)
        self._free_only_setting = None if free_only is None else bool(free_only)
        self._deny_setting = None if deny is None else tuple(deny)

    @property
    def _free_marks(self) -> tuple[str, ...]:
        if self._free_marks_setting is None:
            return config.ZEN_FREE_MARKS
        return self._free_marks_setting

    @property
    def _free_only(self) -> bool:
        if self._free_only_setting is None:
            return config.ZEN_FREE_ONLY
        return self._free_only_setting

    @property
    def _deny(self) -> tuple[str, ...]:
        if self._deny_setting is None:
            return config.ZEN_DENY
        return self._deny_setting

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def models(self) -> list[Model]:
        """Ask the endpoint what it serves; fall back to the configured list."""
        try:
            import httpx  # noqa: PLC0415

            response = httpx.get(
                f"{self._base}/models", headers=self._headers(), timeout=10
            )
            response.raise_for_status()
            payload = response.json()
            found = [
                str(entry["id"])
                for entry in payload.get("data", [])
                if isinstance(entry, dict) and entry.get("id")
            ]
            # The endpoint serves this deployment's paid lineup alongside the free
            # one, and offering a model there is no balance for is offering a button
            # that returns a 402. Filtered here rather than in the picker so nothing
            # downstream, failover included, can select one.
            if found and self._free_only:
                free = [name for name in found if self._is_free(name)]
                if free:
                    found = free
                else:
                    logger.warning(
                        "%s served %d models and none matched its free rule (%s); "
                        "offering all of them. Check the marks against the current "
                        "lineup.", self.name, len(found), ", ".join(self._free_marks),
                    )
            # Known not to work, which is a different question from what the key can pay
            # for, and applied after it so a denied id cannot be reinstated by the
            # fall-through above. Never allowed to empty the list: a deny list that
            # takes the last model off the ladder has turned a bad answer into no
            # answer, and every id on it was recorded as broken at one moment rather
            # than for all time.
            refused = [name for name in found if self._denied(name)]
            if refused and len(refused) < len(found):
                logger.info("%s: not offering %s", self.name, ", ".join(refused))
                found = [name for name in found if not self._denied(name)]
            elif refused:
                logger.warning(
                    "%s served only models on its deny list (%s); offering them "
                    "anyway rather than offering nothing.",
                    self.name, ", ".join(refused),
                )
            if found:
                return [Model(self.name, model_id) for model_id in self._order(found)]
            logger.warning("%s returned no models; using the configured list", self.name)
        except Exception as exc:
            logger.warning("Could not list %s models (%s); using configured list",
                           self.name, exc)
        return [Model(self.name, model_id) for model_id in self._preferred]

    def _is_free(self, model_id: str) -> bool:
        lowered = (model_id or "").lower()
        return any(mark and mark.lower() in lowered for mark in self._free_marks)

    def _denied(self, model_id: str) -> bool:
        """Exact ids, not substrings, unlike the free marks above.

        The two rules read alike and must not behave alike. A free mark is a naming
        convention and is meant to match a family: `-free` catches a model nobody has
        heard of yet, which is the point of writing a rule instead of a list. A deny
        entry is the opposite claim, that one particular id was measured and does not
        answer, and there is no family behind it to generalise to. Matching loosely
        would invite a shorthand entry, `nemotron`, that reads as "the ones that
        stopped answering" and means "every model with that word in its name", which on
        2026-08-28 would have included `nemotron-3-super-120b-a12b:free`, the model
        OpenRouter routed a working answer to on the same day.
        """
        return (model_id or "") in self._deny

    def _order(self, found: list[str]) -> list[str]:
        """Preferred models first, in preferred order; then the rest, alphabetically."""
        known = [model_id for model_id in self._preferred if model_id in found]
        return known + sorted(set(found) - set(known))

    def stream(self, model, messages, tools) -> Iterator[Chunk]:
        import httpx  # noqa: PLC0415

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": config.MAX_TOKENS,
            "temperature": config.TEMPERATURE,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        with (
            httpx.Client(timeout=httpx.Timeout(120.0, connect=15.0)) as client,
            client.stream(
                "POST",
                f"{self._base}/chat/completions",
                json=payload,
                headers=self._headers(),
            ) as response,
        ):
            if response.status_code >= 400:
                # Body must be read before the status can be raised on a stream.
                response.read()
                response.raise_for_status()
            yield from parse_sse(response.iter_lines())


#: Where a reasoning model puts its scratchpad. Read only so that it can be recognised
#: if it turns up again in `content`; never shown, and never part of an answer.
_REASONING_KEYS = ("reasoning", "reasoning_content", "thinking")


def parse_sse(lines: Iterator[str]) -> Iterator[Chunk]:
    """Turn an OpenAI-style `data:` event stream into Chunks.

    Content that is the model's own thinking is dropped, because a reader was shown it.

    `nemotron-3.5-lightning-free` streams its reasoning in `delta.reasoning`, which this
    ignores, and that is fine right up until the reasoning runs the round out of tokens
    before an answer exists. At that point the gateway flushes the whole scratchpad into
    a single `content` delta, and it becomes the answer: measured on the question "what
    can you do?", 1,766 reasoning deltas followed by one content delta carrying all 8,006
    characters of them, so a reader got "Here's a thinking process:" and a numbered
    analysis of the system prompt, cut off mid-word at the token cap.

    Identity is the test, not a guess at what thinking looks like. A model that answers
    does not emit an answer byte-identical to everything it just thought; one that does
    has produced no answer, and saying so lets the ladder move to a model that will.
    """
    thought: list[str] = []
    held: list[str] = []
    diverged = False
    for raw in lines:
        line = raw.strip() if isinstance(raw, str) else raw.decode().strip()
        if not line or not line.startswith("data:"):
            continue
        body = line[len("data:") :].strip()
        if body == "[DONE]":
            # `break`, not `return`: content held back below is released after the loop,
            # and returning here threw it away. Every stream ends with this line, so the
            # first version of this dropped a truncated answer every single time.
            break
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("Skipping unparseable stream event: %r", body[:200])
            continue
        choices = event.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        for key in _REASONING_KEYS:
            piece = _flatten(delta.get(key))
            if piece:
                thought.append(piece)
        text = _flatten(delta.get("content"))
        calls = _tool_fragments(delta.get("tool_calls"))
        if text and not diverged:
            # Hold content back only while it is still tracking the reasoning. A real
            # answer stops matching at its first character, so it is released at once
            # and streams as it always did; a scratchpad being replayed keeps matching
            # to the end. Buffering rather than comparing one delta at a time is what
            # makes this independent of how the gateway happens to chunk the dump.
            #
            # `thought` being empty falls through to the release below rather than
            # skipping the block, and that matters: a delta that arrives before any
            # reasoning is real text, and once real text has gone out this stream is not
            # a replay of anything. Leaving `diverged` unset there meant a later delta
            # could still be held and swallowed after the reader had already seen words.
            candidate = "".join(held) + text
            if thought and "".join(thought).startswith(candidate):
                held.append(text)
                if calls:
                    yield Chunk(text="", tool_calls=calls)
                continue
            diverged = True
            text = candidate
            held.clear()
        yield Chunk(text=text, tool_calls=calls)

    # The stream ended with content still tracking the reasoning. Identical means the
    # model replayed its thinking instead of answering; a strict prefix means it was cut
    # off partway, which is a poor answer but is the model's, so it is handed over.
    if held:
        shown = "".join(held)
        if shown == "".join(thought):
            logger.warning(
                "Dropped %d characters of content identical to the model's own "
                "reasoning: it thought until it ran out of room and never answered.",
                len(shown),
            )
        else:
            yield Chunk(text=shown, tool_calls=[])


# --- registry --------------------------------------------------------------


def build(name: str, api_key: str) -> Provider:
    if name == MISTRAL:
        return MistralProvider(api_key)
    if name == OPENCODE:
        return OpenAICompatProvider(
            api_key,
            config.OPENCODE_BASE_URL,
            name=OPENCODE,
            preferred=config.OPENCODE_MODELS,
            free_marks=config.ZEN_FREE_MARKS,
            free_only=config.ZEN_FREE_ONLY,
            deny=config.ZEN_DENY,
        )
    if name == OPENROUTER:
        # No adapter of its own, and that is the argument for choosing this provider
        # rather than an oversight: an OpenAI-compatible endpoint and an entry of data
        # is the whole integration. The line that makes it worth having is
        # `OPENROUTER_MODELS`, which is one router rather than a lineup, so there is no
        # deny list here and nothing to keep true by hand.
        return OpenAICompatProvider(
            api_key,
            config.OPENROUTER_BASE_URL,
            name=OPENROUTER,
            preferred=config.OPENROUTER_MODELS,
            free_marks=config.OPENROUTER_FREE_MARKS,
            free_only=config.OPENROUTER_FREE_ONLY,
            deny=(),
        )
    raise ValueError(f"Unknown provider: {name}")


def parse_key(value: str) -> Model | None:
    """`'opencode:deepseek-v4-flash'` -> Model, or None if malformed.

    Split once from the left, which is what makes `openrouter:openrouter/free` parse:
    the model half may carry a slash, and does for every id OpenRouter serves.
    """
    if not value or ":" not in value:
        return None
    provider, model_id = value.split(":", 1)
    if provider not in NAMES or not model_id:
        return None
    return Model(provider, model_id)
