"""The agent loop — search, read, answer — with no view attached.

This used to live inside `app.py`, welded to `st.write_stream`, `st.session_state`
and `st.rerun`, which meant the most interesting 200 lines in the repo could only
run inside a Streamlit script and could only be tested through a stub of one. The
loop is the same loop; what changed is that it now yields `Event`s and lets the
caller decide what a status line or a streamed delta looks like.

The contract is deliberately small:

    for event in run_turn(...):
        match event.kind:
            case "status": ...        # a short line naming what is happening
            case "notice": ...        # a failover is being attempted
            case "answer": ...        # event.data has the final text and its sources

No partial text is handed out, and that is the deliberate part.

There used to be a `stream` event carrying an iterator of deltas, and a `reset`
event telling the caller to throw away what it had just rendered. Every round was
streamed as it arrived, including the rounds that end in a tool call, and models
narrate those ("Let me search the articles for…"). So a sentence appeared in the
answer bubble and was wiped a second later by the status line that replaced it.
Whether a round is the answer or a preamble to a tool call is knowable only once
its stream has ended, so there is no way to show text as it arrives *and* be sure
it will not have to be taken back.

What that costs is the typewriter effect on the answer: it now appears complete
rather than a token at a time. What it buys is that nothing is ever shown to a
reader and then removed, which is worth more: an answer that materialises a
second later reads as considered, and one that erases itself reads as broken.
The status line carries the waiting in the meantime.

Failures are raised, not yielded: `run_turn` lets `llm.AssistantError` out so the
caller can decide between retrying, failing over and giving up. `run_conversation`
is the batteries-included wrapper that makes that decision the way the Streamlit
app always has.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from . import config, feedback, links, llm, profiles
from .corpus import Corpus
from .search import Index
from .tools import READ_DOC, SEARCH_DOCS, ToolRunner, gather_context, tool_schemas

logger = logging.getLogger(__name__)

STATUS = "status"
NOTICE = "notice"
ANSWER = "answer"

# Shown while the first token is still in flight, before the model has said whether
# it wants to search or answer.
THINKING = "Thinking"

# The model asked for tool round after tool round and never settled. Better than an
# empty bubble, and it names the one action that helps.
UNFINISHED = (
    "I wasn't able to finish looking that up. Please try rephrasing your question."
)


@dataclass(frozen=True)
class Event:
    kind: str
    text: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def describe(calls: list[dict], corpus: Corpus) -> str:
    """Name the *kind* of work in flight, and nothing more specific than that.

    Every word this returns is written here. Nothing the model produced and nothing
    from the corpus is interpolated into it: not the search query, not a `path`,
    not a section label.

    That is a privacy rule, not a style one. This status line is rendered in a panel
    on a public website, and the corpus behind it is built from a private checkout:
    the ids are file paths (`post/2026-08-09-dwellsy-rent-index.md#verdict`) and
    `label` falls back to the bare filename whenever a path does not resolve, which
    is exactly when the model has guessed at one. "Reading dwellsy-rent-index.md"
    told a reader the name of a file in a repository that is not published, and the
    echoed query told them how the retrieval prompt is phrased. Neither is anything a
    visitor asked for, and both leak from a surface nobody thinks of as an output.

    So the vocabulary is fixed and small: searching, reading, working.
    """
    noun = (corpus.profile or profiles.active()).searching_noun
    names = {call["name"] for call in calls}
    if SEARCH_DOCS in names:
        return f"Searching {noun}"
    if READ_DOC in names:
        return f"Reading {noun}"
    return "Working"


def _grounded(
    messages: list[dict], index: Index, question: str, runner: ToolRunner, profile
) -> list[dict]:
    """Retrieve up front, for models that cannot call tools."""
    context, chunks = gather_context(index, question)
    for chunk in chunks:
        runner.sources.append(chunk)
    if not context:
        return messages
    return [
        messages[0],
        {
            "role": "system",
            "content": profile.grounding_instruction + "\n\n" + context,
        },
        *messages[1:],
    ]


def _sources(runner: ToolRunner) -> list[dict]:
    return [
        {
            "id": chunk.id,
            "label": chunk.label,
            "url": chunk.url,
            "source": chunk.source,
        }
        for chunk in runner.sources
    ]


def _round_text(turn) -> str:
    """Read a round to the end and return everything it said.

    The whole round is consumed here, with nothing yielded to the caller on the way,
    because until the stream ends there is no way to know whether this text is the
    answer or a preamble the model wrote before calling a tool. See the module
    docstring: showing it and taking it back is the bug this shape exists to remove.
    """
    return "".join(turn.deltas())


def run_turn(
    *,
    index: Index,
    messages: list[dict],
    model,
    provider,
    question: str = "",
    tools: bool = True,
    max_rounds: int | None = None,
    patient: bool = True,
) -> Iterator[Event]:
    """One answer, on one model. Raises `llm.AssistantError` rather than yielding it.

    `messages` is the fully built upstream history (see `history.build`) and is not
    mutated — the tool rounds append to a local copy.

    `patient=False` means the opening request gets one attempt instead of three, with
    no backoff. `run_conversation` passes it for every candidate that has another
    behind it: spending 3s of backoff on a model that has just reported a rate limit
    is two more requests to a service asking for fewer, and it delays the failover
    that was going to answer the question. The mid-conversation calls stay patient
    whatever this says, because by then the tool rounds have been paid for and
    starting over loses them.
    """
    rounds = config.MAX_TOOL_ROUNDS if max_rounds is None else max_rounds
    corpus = index.corpus
    profile = corpus.profile or profiles.active()
    schemas = tool_schemas(profile)
    runner = ToolRunner(index)
    messages = list(messages)
    final_text = ""

    yield Event(STATUS, THINKING)

    use_tools = tools
    if use_tools:
        try:
            turn = llm.start(provider, model.id, messages, schemas,
                             retry=patient)
        except llm.AssistantError as exc:
            if not llm.rejects_tools(exc.original or exc):
                raise
            # The model does not do tool calls; retrieve up front instead.
            logger.info("%s rejected tools; using single-pass retrieval", model.id)
            use_tools = False
    if not use_tools:
        messages = _grounded(messages, index, question, runner, profile)
        turn = llm.start(provider, model.id, messages, None, retry=patient)

    for round_number in range(rounds + 1):
        text = _round_text(turn)
        # The answer is the text of the round that asked for no tools. Nothing
        # else is: a tool round's narration goes no further than this loop, which
        # is what stops a sentence appearing in the bubble and being erased by the
        # status line a second later.
        #
        # It used to be kept as an answer-of-last-resort, and that is how "Let me
        # look that up." came to be stored as an answer when a model spent every
        # round calling tools. The reader is told that plainly below instead.
        if not turn.tool_calls or not use_tools:
            final_text = text
            break
        if round_number == rounds:
            logger.warning("Tool-round limit reached without a final answer")
            break

        yield Event(STATUS, describe(turn.tool_calls, corpus))
        messages.append(turn.as_message())
        for call in turn.tool_calls:
            messages.append(
                llm.tool_result_message(call, runner.run(call["name"], call["input"]))
            )
        turn = llm.start(provider, model.id, messages, schemas)

    # An empty bubble is not an answer, and neither is the last thing a model said
    # on its way to a tool call. Both end here.
    #
    # Logged, and logged apart from the round-limit warning above, because the two
    # look identical from the outside and have nothing to do with each other. A
    # model that returns no text and asks for no tool on its first round has not run
    # out of anything: it answered with nothing at all, which is what a spent key
    # looks like on a provider that reports exhaustion as an empty 200 rather than as
    # an error. Without this line the deployment's logs say nothing and the only
    # symptom is a reader being told to rephrase a perfectly good question.
    if not final_text.strip():
        logger.warning(
            "Empty answer from %s after %d round(s), %d search(es): "
            "the model returned no text and asked for no tool",
            model.key, round_number + 1, len(runner.queries),
        )
        final_text = UNFINISHED

    sources = _sources(runner)
    if runner.queries and not sources:
        feedback.record_miss(runner.queries, question)

    yield Event(
        ANSWER,
        data={
            # Stored stripped, not merely rendered stripped: this text is also what
            # goes back upstream next turn, and a footer in the history is a worked
            # example teaching the model to write another one.
            "text": links.strip_source_footer(final_text),
            "sources": sources,
            "model": model.key,
        },
    )


# Why a model refused, in words a user can act on.
REASONS = {
    "quota": "out of credit",
    "auth": "its key was rejected",
    "rate_limit": "rate limited",
    "unavailable": "temporarily unavailable",
}

# The failures a *different provider* actually fixes, which is the only reason to
# spend a second request on one.
#
# The line is drawn at what the endpoint said about itself. `quota` and `auth` are
# properties of the key, and `rate_limit` and `unavailable` are properties of the
# endpoint: in all four cases the other provider is a different key on a different
# endpoint, so it is either fine or fails for its own reasons.
#
# `rate_limit` and `unavailable` were missing, and a 429 is the most likely failure
# this deployment has: it runs on a free tier by preference. The reader got "the
# assistant is busy right now, please wait a moment" while a second, working provider
# sat configured and untried, which is the one thing having two of them is for.
# Adding them costs nothing in requests, because `llm.open_stream` classifies both as
# retryable and has already spent its attempts and its backoff on them before this
# function ever sees the error. There is nothing left to wait for at this point.
#
# `network`, `context` and `unknown` stay out, and `unknown` is the important one:
# a fault of our own making lands there, and trying it again on someone else's
# endpoint would hide it behind a second bill rather than report it. A timeout stays
# out for a related reason, since the likeliest cause is this end, and the retry buys
# one more connect timeout for the reader to wait through.
FAILS_OVER = frozenset({"quota", "auth", "rate_limit", "unavailable"})

# Of those, the two that are true of the *key* rather than of the request, and so are
# true of every model behind that key. These drop the rest of their provider; the
# other two do not, because a model refused for the endpoint's own reasons says
# nothing about the endpoint's other models.
KEY_LEVEL = frozenset({"quota", "auth"})

# How many models one question may cost, across every provider.
#
# There is no free lunch in the other direction either: the ladder here is three
# Mistral models and a dozen or so free ones, and walking all of it costs a request
# each, plus the retries and the 1s/2s backoff `llm.start` spends on every retryable
# kind on the way past. Unbounded, a question asked while both providers are refusing
# would sit there for the better part of a minute before saying so, which is a worse
# answer than a prompt error.
#
# Four is two providers plus two more attempts, which covers the reported case (a paid
# key out of credit, then a rate-limited free tier that has other models) while
# keeping the failure inside about ten seconds. Anything left untried when this is
# reached is logged, so the ceiling cannot quietly look like an exhausted ladder.
MAX_MODELS_TRIED = 4


def run_conversation(
    *,
    index: Index,
    messages: list[dict],
    models: Sequence,
    provider_for,
    question: str = "",
    max_rounds: int | None = None,
) -> Iterator[Event]:
    """`run_turn` with the failover the Streamlit app has always done by rerunning.

    Tries `models` in order. The kinds in `FAILS_OVER` move to the next provider;
    anything else is raised, because retrying an unattributed fault on another model
    would hide it behind a second bill. See that set for where the line is and why.

    A `notice` event is emitted before the retry, and the successful `answer` event
    carries `switched_from` so a caller can say so in the past tense once there is
    an answer to say it about.
    """
    queue = list(models)
    if not queue:
        raise llm.AssistantError("unknown")

    switched_from: tuple[str, str] | None = None
    attempts = 0

    while queue:
        model = queue.pop(0)
        attempts += 1
        try:
            for event in run_turn(
                index=index,
                messages=messages,
                model=model,
                provider=provider_for(model.provider),
                question=question,
                tools=model.supports_tools,
                max_rounds=max_rounds,
                # Patient only when this is the last thing left to try. Anywhere
                # else the backoff buys nothing that the next candidate does not
                # buy faster, and it buys it by making two more requests to a
                # service that has just asked for fewer.
                patient=not queue or attempts >= MAX_MODELS_TRIED,
            ):
                if event.kind == ANSWER and switched_from:
                    yield Event(
                        ANSWER, data={**event.data, "switched_from": switched_from}
                    )
                else:
                    yield event
            return
        except llm.AssistantError as exc:
            # Which model actually failed, so a caller reporting the failure names
            # that one rather than whichever the picker had selected. After a
            # failover those are two different providers, and a details panel
            # reading `model=mistral:…` under a 429 from Zen's endpoint is a
            # contradiction that sends the reader looking in the wrong place.
            exc.model = model.key
            if exc.kind not in FAILS_OVER:
                raise
            if exc.kind in KEY_LEVEL:
                # A spent or rejected key is spent for every model behind it. Trying
                # each in turn is a round trip per model to learn one fact.
                queue = [item for item in queue if item.provider != model.provider]
            else:
                # The endpoint refused this request, not this key, so the rest of
                # that provider is still worth something. Another provider is the
                # better bet and goes first; a sibling model is tried only once
                # there is no other provider left, which is exactly the case this
                # was reported in. A stable sort on "same provider?" reorders
                # without disturbing the preference order inside either group.
                queue.sort(key=lambda item: item.provider == model.provider)
            if not queue or attempts >= MAX_MODELS_TRIED:
                if queue:
                    logger.warning(
                        "Giving up after %d models; %d left untried (last: %s, %s)",
                        attempts, len(queue), model.key, exc.kind,
                    )
                raise
            alternative = queue[0]
            logger.info(
                "%s unusable (%s); failing over to %s",
                model.key, exc.kind, alternative.key,
            )
            switched_from = (model.label, exc.kind)
            # Present tense: the retry has not happened yet. The past-tense version
            # is written only once an answer actually arrives, off `switched_from`.
            yield Event(
                NOTICE,
                f"{model.label} is unavailable ({REASONS.get(exc.kind, exc.kind)}). "
                f"Retrying with {alternative.label}…",
            )

    raise llm.AssistantError("unknown")
