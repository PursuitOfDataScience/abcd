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
import time
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
# A fragment of the answer as it arrives. A caller may render these as they come; see
# `_read_round` for the one guarantee attached to them, which is that they are never
# retracted except by the event below.
DELTA = "delta"
# Drop whatever DELTAs have been rendered for this turn. Emitted only when a model
# writes before asking for a tool, which no model on the current lineup does. A caller
# that ignores it is not wrong so much as chatty: it will show a sentence of narration
# above the answer.
RESET = "reset"

# Shown while the first token is still in flight, before the model has said whether
# it wants to search or answer.
THINKING = "Thinking"

# The model asked for tool round after tool round and never settled, or answered with
# nothing at all. Better than an empty bubble, and it names the one action that helps.
#
# It now lives in `llm` because it is the message for the `empty` failure kind rather
# than a placeholder this module writes: a turn that produces no answer raises, so the
# ladder can try a model that will produce one, and a reader sees these words only after
# every candidate has been asked. The name is kept because it reads better here.
UNFINISHED = llm.UNFINISHED


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


def _read_round(turn, *, show: bool) -> Iterator[Event]:
    """Read a round to the end, handing out text only while it cannot be taken back.

    The invariant is unchanged and is the whole point of this function: nothing is ever
    shown to a reader and then removed. What changed is the price paid for it. This used
    to consume the round in silence and hand back a finished string, because a round's
    text is only known to be an answer once the stream has closed without asking for a
    tool, and the alternative was the bug in the module docstring: "Let me search the
    articles for…" appearing in the bubble and being wiped by the status line.

    `turn.wants_tools` is earlier evidence than that. It is set by the first tool-call
    fragment rather than at the end of the round, and measured against every model this
    deployment serves, a tool round carries no content at all: `hy3-free` sent four
    tool-call fragments and zero characters, both nemotrons the same. `deltas()` only
    yields non-empty text, so on those rounds there is nothing to show and the question
    never arises.

    A model that narrates before calling a tool is therefore the only case that can put
    text on screen that is not an answer, and it is handled rather than assumed away: the
    caller is told to drop what it has, once, and the round goes quiet. That is logged,
    because a lineup where it happens often is a lineup this should be turned off for,
    and `SAGE_STREAM=0` does that without a deploy.
    """
    shown = False
    for piece in turn.deltas():
        if turn.wants_tools:
            show = False
            continue
        if show and piece:
            shown = True
            yield Event(DELTA, piece)

    # Checked after the loop and not only inside it. `deltas()` yields text and nothing
    # else, so a round whose tool call arrives after its last word never comes back
    # round the loop to be noticed, and a first draft of this withdrew narration only
    # when the model happened to keep talking afterwards. Which is to say: in the one
    # ordering that does not occur, and not in the one that does.
    if shown and turn.wants_tools:
        logger.warning(
            "%s wrote %d characters and then asked for a tool, so what was shown had "
            "to be withdrawn. Set SAGE_STREAM=0 if this model does it often.",
            getattr(turn, "model_key", "the model"), len(turn.text),
        )
        yield Event(RESET)


# What one model may spend before the ladder stops waiting for it, checked between tool
# rounds.
#
# `nemotron-3-ultra-free` is why this exists. It is a reasoning model that streams its
# thinking in `delta.reasoning` and leaves `delta.content` empty, and it responds to a
# search result by searching again. Every round costs thirty seconds and none of them
# produces a word of answer, so it walked the full six-round cap: a measured 166 seconds
# of a reader's time, ending in "please try rephrasing your question", with three models
# that answer the same question in under thirty sitting untried behind it. The round cap
# is a count, and this failure is a clock.
#
# Forty-five seconds is above every honest turn measured on this lineup and below two of
# that model's rounds, so it lands on the case it is for. Checked between rounds rather
# than mid-stream, deliberately: a check inside the stream would have to decide whether
# a half-written answer is worth keeping, and this way a model that is actually writing
# one is never interrupted. A single round that hangs is bounded by the HTTP read
# timeout in `providers`, not by this.
MODEL_BUDGET = 45.0


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
    budget: float | None = MODEL_BUDGET,
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

    `budget` is how many seconds of tool rounds this model gets before the turn is
    abandoned for the next candidate; `None` removes the limit. See `MODEL_BUDGET`.
    """
    rounds = config.MAX_TOOL_ROUNDS if max_rounds is None else max_rounds
    corpus = index.corpus
    profile = corpus.profile or profiles.active()
    schemas = tool_schemas(profile)
    runner = ToolRunner(index)
    messages = list(messages)
    final_text = ""
    started = time.monotonic()

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

    # Whether this model has already shown, in this turn, that it says nothing while
    # calling a tool. Nothing is streamed until it has.
    #
    # This is what lets the answer be typed out without giving up the guarantee that
    # nothing is shown and then removed. The two cannot both be had in general: a
    # round's text is only known to be an answer once the round has closed without
    # asking for a tool, so any character shown before that is a character that might
    # have to be withdrawn. What can be had is evidence. A model that has completed a
    # tool round in silence has demonstrated the property that makes streaming safe for
    # it, and every model this deployment serves demonstrates it on the first round:
    # `hy3-free` sends four tool-call fragments and no text, both nemotrons the same.
    #
    # A model that narrates instead ("Let me look that up.") never earns it and is never
    # streamed, which is exactly the old behaviour for exactly the models the old
    # behaviour was written for. The cost is that a question answered without any search
    # does not stream, because a first round carrying text is indistinguishable from a
    # narrated preamble until it ends. That is the right way round: the common question
    # here searches first, and the rare one arrives whole a second sooner.
    quiet = model.key in _quiet_while_working

    for round_number in range(rounds + 1):
        turn.model_key = model.key
        yield from _read_round(turn, show=config.STREAM and quiet)
        text = turn.text
        if turn.tool_calls and not text.strip():
            quiet = True
            _quiet_while_working.add(model.key)
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
        # The other way a model can fail to converge, and the one the round cap does
        # not catch: rounds that are cheap in number and expensive in seconds. Checked
        # here, between rounds, so a model part-way through writing an answer is never
        # cut off. See MODEL_BUDGET.
        spent = time.monotonic() - started
        if budget is not None and spent >= budget:
            logger.warning(
                "%s spent %.1fs over %d round(s) without answering; abandoning it for "
                "the next candidate", model.key, spent, round_number + 1,
            )
            break

        yield Event(STATUS, describe(turn.tool_calls, corpus))
        messages.append(turn.as_message())
        for call in turn.tool_calls:
            messages.append(
                llm.tool_result_message(call, runner.run(call["name"], call["input"]))
            )
        turn = llm.start(provider, model.id, messages, schemas)

    sources = _sources(runner)
    if runner.queries and not sources:
        feedback.record_miss(runner.queries, question)

    # An empty bubble is not an answer, and neither is the last thing a model said on
    # its way to a tool call. Both end here, and both now *raise* rather than being
    # dressed up as an answer.
    #
    # This is the bug that survived fixing the ladder, and it was the worse of the two.
    # `nemotron-3-ultra-free` accepts the request, calls `search_docs`, reads the
    # result, and then streams a 200 carrying no content at all. Yielding a placeholder
    # for that told `run_conversation` the turn had succeeded, so the walk stopped
    # there: measured against the live endpoint, a reader waited 166 seconds to be told
    # to rephrase a perfectly good question while three models that answer it in under
    # thirty were sitting untried behind the one that said nothing.
    #
    # A 200 with nothing in it is a refusal wearing a success code, so it is reported as
    # one. The reader still gets these exact words, but only once the whole ladder has
    # been asked, which is the one situation they are true in.
    #
    # The three ways of getting here are worth telling apart in a log, because from the
    # outside they are the same silence and they have nothing to do with each other:
    # a model that ran out of rounds, one that ran out of seconds, and one that simply
    # returned no text on a round where it asked for no tool. Only the third is the
    # spent-key-reported-as-an-empty-200 case, and the warnings above already name the
    # other two, so this says which shape it was rather than asserting the third.
    if not final_text.strip():
        logger.warning(
            "No answer from %s after %d round(s) and %d search(es) (%s). Treating it "
            "as a refusal and moving on to the next candidate.",
            model.key, round_number + 1, len(runner.queries),
            "asked for no tool and returned no text" if not turn.tool_calls
            else "still calling tools when it ran out of rounds or seconds",
        )
        raise llm.AssistantError("empty")

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
    "empty": "returned an empty answer",
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
#
# `empty` joins them for the reason set out where it is raised: a 200 carrying no answer
# is a refusal, and the model that gave it is the last one worth asking again.
FAILS_OVER = frozenset({"quota", "auth", "rate_limit", "unavailable", "empty"})

# Of those, the ones that write off the rest of the provider rather than only this
# model. `quota` and `auth` are properties of the *key*, so they are true of everything
# behind it and asking the siblings is a round trip each to learn one fact.
#
# `rate_limit` is NOT one of them. It was for two commits, on an inference from three
# consecutive 429s that the cap was on the account, and that inference is now measured
# and wrong. Against the live endpoint on one key within one minute:
#
#     deepseek-v4-flash-free   429 FreeUsageLimitError
#     big-pickle               429 FreeUsageLimitError
#     mimo-v2.5-free           429 FreeUsageLimitError
#     hy3-free                 200, answered
#     nemotron-3-ultra-free    200, answered
#     laguna-s-2.1-free        200, answered
#
# Three refused and three answered, so Zen's free limit is per model. The three that
# refuse happen to be the three this deployment tries first, which is why one cap looked
# like a dead account. Pruning on it produced exactly the failure this was reported as:
# `tried 2 of 11 configured`, eight candidates discarded unasked, and a reader told to
# come back later while models that would have answered sat behind the ones that did not.
#
# Nor is it a property of the request. Bare, non-streaming, without `max_tokens`, and
# under the CLI's own user-agent all return the same 429 in 0.2s, so there is nothing to
# fix in what is sent: the key is capped on those models and the answer is to ask a
# different one.
PRUNES_PROVIDER = frozenset({"quota", "auth"})

# The kinds that say something about the *endpoint*, and so are a reason to prefer a
# different one over the sibling that comes next in the ladder's own order.
#
# Only `unavailable`. A 5xx is the endpoint reporting on itself, and while its other
# models are still worth something, a provider that has just failed is the worse bet.
#
# `rate_limit` used to reach this by falling through the `else` it was written under,
# which quietly undid half of taking it out of `PRUNES_PROVIDER`: the sibling stopped
# being written off but still lost its place to whatever provider came next. The
# measurement says the siblings are independent, so a 429 is not evidence about the
# endpoint and there is nothing to reorder for. The ladder's order is the owner's
# preference, and the next model in it is the next one to ask.
#
# `empty` likewise. A model that answers with nothing has told you about that model.
REORDERS_PROVIDER = frozenset({"unavailable"})

# How long a refusal is believed, in seconds, before that model is asked again.
#
# The ladder had no memory at all, so every reader re-derived the same three 429s from
# scratch, and the model that never answers was re-elected on every question. A walk that
# has to rediscover the state of the world each time is not a fallback, it is a queue of
# known-bad calls with a working one somewhere behind it.
#
# The numbers are sized to the failure, not to a policy. A free-tier window is minutes,
# so a 429 is believed for two of them and no longer. A spent balance and a rejected key
# do not recover on their own, so those are held for fifteen minutes, which is short
# enough that topping up an account shows up in the panel without a restart. `empty` is
# held for ten because it is a property of the model rather than of the moment: a model
# that reasons in a field the API does not return as content will do it again in ten
# minutes. `unavailable` gets sixty seconds, because a flapping backend is the one
# failure here that really is about the moment.
#
# Deliberately advisory. `_ready` falls back to the full ladder when everything in it is
# cooling, because a stale note about a model is worth less than one more attempt at an
# answer, and the note is a guess about someone else's rate limiter either way.
COOLOFF = {
    "rate_limit": 120.0,
    "quota": 900.0,
    "auth": 900.0,
    "empty": 600.0,
    "unavailable": 60.0,
}

# model key -> the monotonic time it becomes worth trying again. Process-wide on purpose:
# Streamlit re-executes the script on every interaction but keeps the process, so this is
# what one reader's failed walk can tell the next reader's.
_cooling: dict[str, float] = {}


def _cool(model_key: str, kind: str, now: float) -> None:
    ttl = COOLOFF.get(kind)
    if ttl:
        _cooling[model_key] = now + ttl


def _ready(models: list, now: float) -> list:
    """The candidates not known to be refusing, or all of them if that is none.

    Expired notes are dropped as they are read rather than swept, which keeps the
    dictionary the size of the ladder without a second pass over it.

    Written to survive two readers at once, because that is the normal case: Streamlit
    runs every session in its own thread over this one process-wide dictionary. The
    iteration is over a snapshot so the dictionary can be written while it is walked,
    and the removal is a `pop` rather than a `del` so the loser of a race to expire the
    same note gets `None` instead of a `KeyError` out of a panel that was answering a
    question.
    """
    for key, until in list(_cooling.items()):
        if until <= now:
            _cooling.pop(key, None)
    warm = [model for model in models if model.key not in _cooling]
    return warm or list(models)


def forget_refusals() -> None:
    """Drop every cool-off note. For tests, and for a caller that wants a clean walk."""
    _cooling.clear()
    _quiet_while_working.clear()


# Models seen to complete a tool round without writing a word, which is the evidence
# that streaming their text cannot show a reader something that has to be taken back.
#
# Process-wide, and that is the fix rather than an optimisation. It was learned per
# turn, so a model had to prove itself again on every question, and an answer that
# needed no search never got the chance: "what can you do?" and any follow-up the model
# answers directly have no tool round in them, so nothing streamed and the whole reply
# landed at once. Measured in the harness at one painted frame against six.
#
# A model that narrates before calling a tool never enters this set, so it is never
# streamed, which is the guarantee kept intact. What a model does once it is in the set
# is still watched: `_read_round` withdraws text and logs if one starts narrating.
_quiet_while_working: set[str] = set()

# What bounds the walk, and why it is a clock rather than a count.
#
# The message a reader gets when this function gives up says to come back later, and it
# is meant to mean that everything was tried. A count cannot promise that: this ladder
# is three Mistral models and nine or so free ones, so a limit of four could show the
# last-resort message with eight candidates untouched.
#
# It was four, sized when every candidate cost three requests and 1s+2s of backoff, so
# twelve of them would have been most of a minute. That is no longer what a candidate
# costs: patience now goes only to the last one, so the others are a single request each
# and a refusal comes back in milliseconds. Walking the whole ladder against providers
# that are refusing is a few seconds, and the honest limit is therefore the reader's
# waiting time and not the number of names in a list.
#
# The budget is measured from the first attempt and checked before starting another. In
# every ordinary failure the queue empties first and the reader is told to come back
# later only once that is true. It binds when something is slow rather than absent, which
# is the case where continuing would leave a reader watching a status line with nothing
# behind it.
#
# It was twenty seconds, and twenty seconds was measured against models that refuse in
# milliseconds rather than models that answer. The free lineup does not answer in
# milliseconds: `hy3-free` took 31.7s to say "OK." and `nemotron-3-ultra-free` 30s to
# open a search. A budget below the time a working model takes to reply does not bound
# the reader's wait, it just guarantees that the second slow candidate is never reached,
# which on the measured lineup is the difference between an answer and a tea break.
#
# MAX_MODELS_TRIED stays as a runaway backstop, at a number the present ladder cannot
# reach, because the free lineup is discovered at runtime and nothing here controls how
# long it gets. Either limit stopping early is logged at WARNING with the count left
# untried, so a bounded walk cannot quietly read as an exhausted one.
LADDER_BUDGET = 75.0
MAX_MODELS_TRIED = 24

def _unfinished(model_key: str, switched_from: tuple[str, str] | None) -> Event:
    """What a reader gets when the walk ends on a model that answered with nothing.

    An answer event and not an exception, which is the difference between the reader
    seeing a reply in the transcript and seeing a red card headed "Could not complete
    that request". The endpoint worked, the model responded, and it had nothing to say:
    that is an outcome, and telling the reader to rephrase is a reasonable thing to do
    about it. A rate limit or a spent key is a different matter and still raises.

    So `empty` fails over like a refusal and lands like an answer. The failing over is
    the fix; the landing is what the panel has always done and is deliberately left
    alone.
    """
    return Event(
        ANSWER,
        data={
            "text": UNFINISHED,
            "sources": [],
            "model": model_key,
            **({"switched_from": switched_from} if switched_from else {}),
        },
    )


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

    Candidates that refused recently are skipped rather than re-asked; see `COOLOFF`.
    """
    if not models:
        raise llm.AssistantError("unknown")

    started = time.monotonic()
    # What the last few walks learned, applied before the first request rather than
    # rediscovered by making it. `_ready` returns the whole ladder when every rung is
    # cooling, so this can only reorder the work, never remove the last chance of an
    # answer.
    queue = _ready(list(models), started)
    # What this walk will not ask, taken from the queue rather than from `_cooling`.
    # The two differ in the case that matters: when every rung is cooling `_ready`
    # hands back the whole ladder, and reporting those as skipped would describe a full
    # walk as a truncated one. Recorded before the walk begins, because `_cooling` gains
    # entries as it proceeds and this names what was never asked, not what refused.
    walking = {item.key for item in queue}
    skipped = [item.key for item in models if item.key not in walking]
    if skipped:
        logger.info(
            "Skipping %d model(s) that refused recently: %s",
            len(skipped), ", ".join(skipped),
        )

    switched_from: tuple[str, str] | None = None
    attempts = 0
    # What refused, in order. Attached to whatever is finally raised so the caller can
    # report the ladder rather than its last rung.
    tried: list[tuple[str, str]] = []

    while queue:
        model = queue.pop(0)
        attempts += 1
        # Whether anything would be tried after this one, which is what decides how
        # much patience it gets. Approximated from the time already spent rather than
        # the time this attempt will take, which is not knowable before making it.
        last_chance = (
            not queue
            or attempts >= MAX_MODELS_TRIED
            or time.monotonic() - started >= LADDER_BUDGET
        )
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
                patient=last_chance,
                # The same budget for the last candidate as for the first, which is
                # the opposite of what `patient` does and is deliberate. Patience
                # spends a retry that might work; this spends minutes on a model
                # that has already shown it is not converging, and the measured
                # instance of it produced nothing at the end of 166 seconds. An
                # unbounded last chance is how a reader waits three minutes to be
                # told to rephrase the question.
                budget=MODEL_BUDGET,
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
            tried.append((model.key, exc.kind))
            exc.tried = list(tried)
            exc.skipped = list(skipped)
            if exc.kind not in FAILS_OVER:
                raise
            now = time.monotonic()
            _cool(model.key, exc.kind, now)
            if exc.kind in PRUNES_PROVIDER:
                # One refusal answers for the whole provider: a spent key is spent for
                # every model behind it. Trying each in turn is a round trip per model
                # to learn one fact.
                #
                # Noted against each of them and not only against the one that spoke,
                # so the next question does not pay the same round trip on a sibling.
                # Without that, a three-model provider whose key is dead costs one
                # wasted call per question until each has been asked separately.
                for item in queue:
                    if item.provider == model.provider:
                        _cool(item.key, exc.kind, now)
                queue = [item for item in queue if item.provider != model.provider]
            elif exc.kind in REORDERS_PROVIDER:
                # The provider is up and one of its models is not, so its others are
                # still worth something, but another provider is the better bet and goes
                # first. A stable sort on "same provider?" reorders without disturbing
                # the preference order inside either group.
                queue.sort(key=lambda item: item.provider == model.provider)
            if not queue:
                # The ladder is genuinely exhausted, which is the only case the
                # reader's "try again later" is supposed to describe.
                if exc.kind == "empty":
                    yield _unfinished(model.key, switched_from)
                    return
                raise
            spent = time.monotonic() - started
            if spent >= LADDER_BUDGET or attempts >= MAX_MODELS_TRIED:
                logger.warning(
                    "Giving up after %d models and %.1fs; %d left untried "
                    "(last: %s, %s)",
                    attempts, spent, len(queue), model.key, exc.kind,
                )
                if exc.kind == "empty":
                    yield _unfinished(model.key, switched_from)
                    return
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
