"""Runtime configuration.

Every value can be overridden by an environment variable so a deployment can be
retuned without touching code. This module must stay importable without Streamlit.
"""

from __future__ import annotations

import json
import os

# --- helpers ---------------------------------------------------------------


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Comma-separated env override. `NAME=` (empty) explicitly clears the list."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


# --- model -----------------------------------------------------------------

# --- providers -------------------------------------------------------------
# Which provider/model a fresh session starts on, as "provider:model-id".
#
# A free model, by the owner's instruction. It was `mistral:mistral-small-latest`,
# which is paid and, on this deployment, out of credit: every turn opened with a
# request that could only fail, waited out its backoff, and then failed over to a free
# model anyway. Starting here removes a wasted round trip from every question and
# spends nothing.
#
# `openrouter:openrouter/free` since 2026-08-28, and the reason it is not a model name
# is that pinning one on a free tier has now failed three times. The defaults before it
# were `deepseek-v4-flash-free`, which answered 429 `FreeUsageLimitError` to every
# request this key made; `nemotron-3.5-lightning-free`, which spent 41 seconds reasoning
# and never reached an answer; and `hy3-free`, which still works and is the only model
# on Zen's free lineup that does. Measured against the live endpoint on 2026-08-28 with
# this deployment's own question and tool schema, in two requests each, one offering the
# tools and one with them withdrawn:
#
#     hy3-free                  6 tool calls, then 267 characters of answer
#     laguna-s-2.1-free         8 tool calls, then 503 Endpoint is unavailable
#     ling-3.0-flash-fin-free   9 tool calls, then nothing at all
#     big-pickle                429 FreeUsageLimitError
#     mimo-v2.5-free            429 FreeUsageLimitError
#     deepseek-v4-flash-free    400 Model is unavailable
#
# One working model behind a default is not a ladder, and the two that answer 429 are
# capped per model rather than per key (see `engine.PRUNES_PROVIDER`), so nothing this
# file can be edited to say would have made that lineup answer.
#
# `openrouter/free` is not a model either. It is OpenRouter's Free Models Router: it
# picks a free model per request from whatever is up, filtered to the ones that support
# the parameters the request actually carries, so a tool-calling turn is never routed to
# a model that cannot call a tool. That moves "notice which free model died today" off
# this file and onto the provider, which is the only place it can be done per request
# instead of per commit.
#
# What it costs, recorded here rather than discovered later: the model changes from turn
# to turn, so speed and answer quality vary in a way a pinned model's do not, and a
# reader cannot tell which model wrote the answer in front of them. Availability over
# consistency, deliberately. A 2.6B model that answers beats a 550B one that returns an
# empty stream, which is what the two Nemotrons were doing when this was changed.
#
# This names the *first* candidate and not the only one. `engine.run_conversation`
# still walks the rest of the ladder behind it, so a details panel reporting a failure
# names whichever model refused last, which is usually not this one.
#
# Best-effort by nature: `app.current_model` only honours it if the provider actually
# serves it, because a free lineup rotates without notice and offering a model that has
# been withdrawn is a button that returns a 404. When it is gone the first model a ready
# provider does serve is used instead.
DEFAULT_MODEL = os.getenv("SAGE_DEFAULT_MODEL", "openrouter:openrouter/free")

# --- OpenRouter ------------------------------------------------------------
#
# An OpenAI-compatible endpoint fronting 388 models, of which 21 are zero-priced
# (measured 2026-08-28 off `GET /models` with this key). This deployment offers exactly
# one, and it is the router rather than any of them.
#
# Measured before it was trusted (2026-08-28, this deployment's own question and tool
# schema, three requests offering the tools and three with them withdrawn): three tool
# calls out of three, routed across `minimax/minimax-m2.7:free`,
# `poolside/laguna-s-2.1:free` and `dots-studio/dots-3-note-preview:free`, median 2.0s;
# and prose on two of the three requests sent without tools, from
# `nvidia/nemotron-3-super-120b-a12b:free` and `minimax/minimax-m3:free`. The third
# returned tool calls and no prose, which is a refusal wearing a success code, and
# `engine.run_turn` raises `empty` for it so the ladder walks past. Note what the router
# did there that a pinned model cannot: the round that searched and the round that
# answered were served by different models, so the turn did not inherit one model's
# inability to write prose.
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# Discovery still runs, because it is how the app learns the router is being served at
# all; this is the fallback when `GET /models` fails, and the preference order applied
# to whatever discovery returns. One entry, and the rule below stops it widening.
OPENROUTER_MODELS = _env_list("SAGE_OPENROUTER_MODELS", ("openrouter/free",))
# The mark is the router's own id, so the rule reads "offer exactly this". That is
# unusual, and it is the point of the entry: 367 of the 388 models cost money this key
# does not have, so a wider rule fills the ladder with rungs that return 402.
#
# `:free` is the wider rule someone will reach for, and it is worth knowing exactly
# what it does. All 18 ids carrying that suffix are zero-priced and every one of them
# would be offered, which hands their upkeep straight back to this file; nine of the
# eighteen were rate-limited or structurally unable to answer on the sweep the router
# sailed through. It also does not mean "the free models": three zero-priced ids do not
# carry it, and one of them is the router itself, so `:free` swaps the one rung that
# needs no checking for eighteen that do.
OPENROUTER_FREE_MARKS = _env_list("SAGE_OPENROUTER_FREE_MARKS", ("openrouter/free",))
# Off for a deployment with a paid OpenRouter balance, which should see what it can use.
OPENROUTER_FREE_ONLY = os.getenv(
    "SAGE_OPENROUTER_FREE_ONLY", "1"
).strip().lower() not in ("0", "false", "no", "")
# There is no `is_free_openrouter_model` to go with the marks above, and no
# `is_free_zen_model` any more either. The rule is one line and it now lives once, on
# `providers.OpenAICompatProvider._is_free`, which reads whichever marks its own
# provider was built with. Two copies of a rule in two functions named after two
# providers is the shape a divergence takes: one gets a fix, the other does not, and
# nothing on screen says which one a given endpoint went through.


# What a reader is shown for a served id, for the case the id is not a name at all.
#
# `openrouter/free` describes which free tier the request draws on and not the thing
# answering: the model behind it is a different one every turn, so no specific model
# name would be right either. `enigma` by the owner's instruction of 2026-08-28, the
# instruction being that the reader should not be shown the billing arrangement.
#
# This deployment has no model picker, so the surfaces that read it are narrower than
# they sound and both are prose: the failover notice, "X is unavailable (out of
# credit), so Y answered instead", and the warning that a model cannot read an image.
# Neither is a place for a slash and the word "free".
#
# The id is untouched everywhere it counts, which is upstream, in `Model.key`, in the
# session state, in the feedback log and in the error card's technical details, so
# nothing that measures a model ends up measuring a nickname. `Model.label` is the only
# reader.
#
# No environment override, unlike every list above it. Those are ids or a flag, which a
# comma-separated variable can carry; a mapping cannot be spelled in one without
# inventing a syntax to get it wrong in.
MODEL_LABELS = {"openrouter/free": "enigma"}


def model_label(model: str) -> str:
    """What to show for this served id, or "" to let the id speak for itself."""
    return MODEL_LABELS.get(model or "", "")


MISTRAL_MODELS = _env_list(
    "SAGE_MISTRAL_MODELS",
    ("mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"),
)

# OpenCode Zen is an OpenAI-compatible endpoint fronting a set of free models —
# a way to keep working once a paid key is out of credit. The live list is
# discovered from GET /models at runtime; this is only the fallback, since a free
# tier's lineup changes without notice.
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
# This is two things at once, and the second is the one that bites: it is the fallback
# list when discovery fails, and it is the *preference order* applied to whatever
# discovery does return (`OpenAICompatProvider._order`). So it decides which model a
# failover lands on, and a name in the wrong place here is a reader's wait.
#
# Checked against the endpoint on 2026-08-12, and re-measured on 2026-08-15 by asking
# every model on the list "what can you do?" with this deployment's own system prompt.
# `north-mini-code-free` and `longcat-2.0-free` are no longer served and are gone.
#
# `hy3-free` leads, which is also `DEFAULT_MODEL`: the two have to agree, or a failover
# walks back to a model the walk had already started on. It is the one that carried this
# deployment while the models above it were rate limited, and on the re-measurement it
# answered in 13s with its reasoning kept properly in `delta.reasoning`, where nothing
# shows it.
#
# `nemotron-3.5-lightning-free` led this list until 2026-08-15 and was the default, and
# it was the wrong choice twice over. Asked anything it can answer without a tool, it
# reasons until the token cap and never reaches an answer: 41 seconds, 1,766 reasoning
# deltas, and then the gateway flushes all 8,006 characters of the scratchpad into one
# `content` delta, which is what a reader saw, cut off mid-word. `parse_sse` now drops
# content identical to the reasoning, so that no longer reaches anyone, but what is left
# is 41 seconds of nothing and a round that then wrote `search_docs("archive")` as prose
# instead of calling the tool. It stays on the list because the lineup rotates, and it is
# below everything that answers.
#
# `nemotron-3-ultra-free` is last on evidence rather than on taste. It is a reasoning
# model that streams its thinking in `delta.reasoning` and never fills `delta.content`
# at all, and it responds to a search result by searching again: six rounds, thirty
# seconds each, no answer at the end of any of them. It stays on the list because the
# lineup rotates and a model that is useless today may be re-pointed at something else
# tomorrow, but nothing should reach it before the models that do answer. Note that it
# is not the same model as `nemotron-3.5-lightning-free` above and does not behave like
# it, which is easy to miss from the names.
OPENCODE_MODELS = _env_list(
    "SAGE_OPENCODE_MODELS",
    (
        "hy3-free",
        "laguna-s-2.1-free",
        "deepseek-v4-flash-free",
        "big-pickle",
        "mimo-v2.5-free",
        "nemotron-3.5-lightning-free",
        "ling-3.0-tiny-free",
        "nemotron-3-ultra-free",
    ),
)

# Zen serves paid models from the same endpoint as the free ones — the discovery call
# came back with the whole Claude and GPT lineup, none of which this deployment has a
# balance for, and every one of which was offered in the picker as if it worked.
#
# Filtered by a RULE rather than a list, because Zen's free lineup changes without
# notice and a hardcoded set goes stale silently: every free model it serves is named
# with a `-free` suffix, the exception being the stealth models it publishes under a
# codename while they are free. Naming the convention keeps working when the list
# changes; naming the list does not.
ZEN_FREE_MARKS = _env_list("SAGE_ZEN_FREE_MARKS", ("-free", "big-pickle"))
# Off for a deployment with a paid Zen balance, which should see everything it can use.
ZEN_FREE_ONLY = os.getenv("SAGE_ZEN_FREE_ONLY", "1").strip().lower() not in (
    "0", "false", "no", ""
)

# Models never offered, however the endpoint lists them. This is "known not to work",
# which is a different question from the free rule above: that one asks what the key can
# pay for.
#
# Both Nemotrons, on the owner's report from the running app and confirmed against the
# live endpoint on 2026-08-28. Asked this deployment's own question and tool schema,
# `nemotron-3.5-lightning-free` held the connection open past a 300-second cap without
# sending one byte, and `nemotron-3-ultra-free` answered 400 wrapping an upstream 404.
# Neither is a model that can be waited for: the first spends more of a reader's time
# than the whole rest of the ladder would, and the second is not being served at all
# while the catalogue still advertises it.
#
# It has to be its own list, because taking a name out of `OPENCODE_MODELS` does not
# remove it. That list is the preference *order* applied to whatever discovery returns,
# and `OpenAICompatProvider._order` puts anything it does not name at the end of the
# ladder rather than off it, so an unlisted model is a demoted model, and a demoted
# model is still one a failover reaches. Emptying this list offers them again, which is
# the right switch to have: a free tier that re-points an id at a working backend is a
# thing that has happened here.
ZEN_DENY = _env_list(
    "SAGE_ZEN_DENY", ("nemotron-3.5-lightning-free", "nemotron-3-ultra-free")
)

# Substrings marking models that cannot call tools. Those answer from a single
# retrieval pass instead of the search/read loop. The app also falls back
# automatically if a provider rejects a request because of tools.
TOOLLESS_MODELS = _env_list("SAGE_TOOLLESS_MODELS", ())

# Substrings marking models that can be handed a picture. Deliberately short and
# conservative: an image sent to a text-only model is a 4xx, not a graceful refusal,
# so anything not listed here gets told the file is attached and left unread rather
# than gambling with the request. Extend it as a deployment learns its own lineup.
VISION_MODELS = _env_list("SAGE_VISION_MODELS", ("pixtral", "claude"))


def sees_images(model: str) -> bool:
    lowered = (model or "").lower()
    return any(mark and mark.lower() in lowered for mark in VISION_MODELS)

# Retained for compatibility; the UI picker overrides it per session.
MODEL = os.getenv("SAGE_MODEL", "mistral-small-latest")
# Generous on purpose. 1600 was the old value and it cut answers off mid-sentence —
# "Per the documentation," and then nothing — worse than a long answer in every
# way: the reader cannot tell a finished thought from a severed one, and asking again
# costs another full request. A walkthrough with two code blocks and a Sources strip
# runs well past 1600, and no answer this app gives is improved by being truncated.
# 8000 upstream, where an answer is a cluster walkthrough with two code blocks.
# A blog answer is a paragraph and a citation, and the cap is a ceiling rather
# than a target — but a generous ceiling on a public endpoint is somebody else's
# bill, so it is sized for the work actually being done here.
# Whether an inline citation is shown as a numbered marker or as the section title the
# model wrote. Off restores the long form exactly, which is what shipped before.
#
# The Sources strip is unaffected either way: it lists what was read whether or not the
# prose points at it, and a citation the reader can follow mid-sentence is a different
# job from a list of what the answer rests on.
INLINE_CITATIONS = os.getenv("SAGE_INLINE_CITATIONS", "1").strip().lower() not in (
    "0", "false", "no", ""
)

# Whether the answer appears a word at a time or all at once when it is finished.
#
# Off for two versions, and for a good reason at the time: every round was streamed
# including the ones that end in a tool call, models narrate those, and the narration
# was wiped from the bubble by the status line replacing it. An answer that erases
# itself reads as broken, so the safe move was to hand out nothing until a round had
# closed without asking for a tool.
#
# On again because the evidence changed rather than the opinion. `engine._read_round`
# now watches `Turn.wants_tools`, which is set by the first tool-call fragment rather
# than at the end of the round, and on the Zen models a tool round carries no content
# whatsoever: the round that searches sends tool-call fragments and not one character.
# There is nothing to wipe because there was never anything to show.
#
# "Every model this deployment serves" is what that sentence used to say, and the
# default is no longer one of them. `openrouter/free` routes to a different model per
# request, and some of them narrate: measured on 2026-08-28, one round opened with three
# characters and then asked for a tool. Nothing reached the reader, because that is the
# guarantee `_quiet_while_working` exists for: a model is streamed only after it has
# completed a tool round in silence, and one that narrates never earns it. The cost is
# real and worth knowing rather than rediscovering, which is why it is written here: the
# router's answers arrive whole rather than a word at a time, on any turn where the
# model it picked said something before searching.
#
# Set `SAGE_STREAM=0` if that becomes the common case rather than the occasional one.
# The engine logs a warning naming the model each time it has to withdraw text, so that
# decision has evidence behind it too.
STREAM = os.getenv("SAGE_STREAM", "1").strip().lower() not in ("0", "false", "no", "")

MAX_TOKENS = _env_int("SAGE_MAX_TOKENS", 1800)
TEMPERATURE = _env_float("SAGE_TEMPERATURE", 0.2)
MAX_TOOL_ROUNDS = _env_int("SAGE_MAX_TOOL_ROUNDS", 6)
REQUEST_RETRIES = _env_int("SAGE_REQUEST_RETRIES", 2)

# --- corpus ----------------------------------------------------------------


# Which assistant this deployment is lives in `sage/profiles/`, selected by
# `SAGE_PROFILE`. It is deliberately *not* mirrored here: the UI resolves it with
# an `st.secrets` fallback the same way it resolves API keys, and a second copy in
# config would be a second answer to the same question.

# The `site` profile: a synced snapshot of the personal website, written by
# tools/build_site_corpus.py.
SITE_PATH = os.getenv("SAGE_SITE_PATH", "./site")
SITE_BASE_URL = os.getenv("SAGE_SITE_BASE_URL", "https://youzhi.netlify.app/")

# Where the website publishes its corpus, and how often to ask whether it changed.
# The deployment has no corpus of its own: it fetches this one, so a new article is
# live once the website is, with no second push to the deployed build. See
# `sage/corpus_source.py` for why there is no fall back to a stale copy.
SITE_CORPUS_URL = os.getenv(
    "SAGE_SITE_CORPUS_URL", SITE_BASE_URL.rstrip("/") + "/assistant"
)
SITE_CORPUS_CACHE = os.getenv("SAGE_SITE_CORPUS_CACHE", "/tmp/sage-corpus")
SITE_CORPUS_TIMEOUT = _env_float("SAGE_SITE_CORPUS_TIMEOUT", 20.0)
# The digest gets its own, much shorter budget, because the two requests are waited on
# by different people. The corpus is a megabyte and is fetched once per revision, on a
# start-up where nobody is mid-sentence. The digest is 65 bytes and is fetched inside a
# rerun, every `SITE_CORPUS_POLL_SECONDS`, while a reader waits for their answer: on the
# 20s corpus budget an unreachable host would freeze the panel for twenty seconds before
# doing what it was always going to do, which is serve the index it already has. It was
# measured at ~85ms against Netlify, so five seconds is roughly sixty times the observed
# cost and still fails fast enough that nobody notices.
SITE_DIGEST_TIMEOUT = _env_float("SAGE_SITE_DIGEST_TIMEOUT", 5.0)
# 600s: a new article appears within ten minutes of the website deploying it, at the
# cost of one 65-byte request per ten minutes per process.
SITE_CORPUS_POLL_SECONDS = _env_int("SAGE_SITE_CORPUS_POLL_SECONDS", 600)

# The source list, extensions, weights and exclusion lists that used to sit here
# belonged to a corpus this repository does not contain. They live on the profile
# now (`sage/profile.py`), and the defaults left behind had no callers.

# --- chunking --------------------------------------------------------------
#
# Whole-file reads used to be truncated at 15k chars, which silently cut 62% of
# docs/slurm/sbatch.md — the single most important page in the corpus. Indexing
# heading-sized chunks removes the need to truncate at all.

MAX_CHUNK_CHARS = _env_int("SAGE_MAX_CHUNK_CHARS", 6000)
MIN_CHUNK_CHARS = _env_int("SAGE_MIN_CHUNK_CHARS", 120)
# Cap for reading a whole page. Pages above it return an outline plus their
# opening, so the model asks for the section it actually needs.
MAX_DOC_CHARS = _env_int("SAGE_MAX_DOC_CHARS", 20000)
WEB_CHUNK_CHARS = _env_int("SAGE_WEB_CHUNK_CHARS", 2400)
WEB_CHUNK_OVERLAP = _env_int("SAGE_WEB_CHUNK_OVERLAP", 240)

# --- search ----------------------------------------------------------------

SEARCH_RESULTS = _env_int("SAGE_SEARCH_RESULTS", 6)
SNIPPET_CHARS = _env_int("SAGE_SNIPPET_CHARS", 240)

BM25_K1 = _env_float("SAGE_BM25_K1", 1.5)
BM25_B = _env_float("SAGE_BM25_B", 0.75)
TITLE_BOOST = _env_float("SAGE_TITLE_BOOST", 2.5)
PATH_BOOST = _env_float("SAGE_PATH_BOOST", 1.2)
# 0.8 measured best on tests/test_retrieval_eval.py (recall@3 94%→97%, p@1 76%→79%)
# without raising scores for off-topic queries. Re-run that eval if you change it.
SYNONYM_WEIGHT = _env_float("SAGE_SYNONYM_WEIGHT", 0.8)

# --- conversation ----------------------------------------------------------

# Rough character budget for the history sent upstream. Trimming happens oldest
# first; the system prompt and the current question are never dropped.
# Halved from upstream. The system prompt now carries a brief about the open
# article on every turn, and the whole point of that brief being an outline
# rather than the article is that the per-turn cost stays small; spending the
# saving on a longer transcript would undo it.
HISTORY_CHAR_BUDGET = _env_int("SAGE_HISTORY_CHAR_BUDGET", 24000)
# Older attachments collapse to a stub so a PDF is not re-uploaded every turn.
ATTACHMENT_FULL_TEXT_TURNS = _env_int("SAGE_ATTACHMENT_FULL_TEXT_TURNS", 1)
MAX_PROMPT_CHARS = _env_int("SAGE_MAX_PROMPT_CHARS", 8000)

# --- uploads ---------------------------------------------------------------

MAX_UPLOAD_BYTES = _env_int("SAGE_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
# Across all files on one turn, which the per-file limit above does not bound: four
# 9 MB screenshots are four legal uploads and one 50 MB request, and the only thing
# that stopped it was the provider's own 413 — surfaced to the reader as "this
# conversation got too long. Clear the chat", about a conversation of one question.
MAX_ATTACHED_BYTES = _env_int("SAGE_MAX_ATTACHED_BYTES", 20 * 1024 * 1024)
MAX_FILE_TEXT_CHARS = _env_int("SAGE_MAX_FILE_TEXT_CHARS", 30000)


# --- links -----------------------------------------------------------------

# The base URL and the "email us" address that the removed second profile owned
# went with it. They had no callers left, and a help desk address for somebody
# else's service is the last thing a blog assistant should be able to put in an
# answer.

# --- ops -------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
# Set to a writable path to collect thumbs-up/down as JSON lines. Unset = no sink.
FEEDBACK_LOG = os.getenv("SAGE_FEEDBACK_LOG", "")
SNAPSHOT_FILE = os.getenv("SAGE_SNAPSHOT_FILE", "./docs_snapshot.json")


API_KEY_VARS = {
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "opencode": "OPENCODE_API_KEY",
}


def api_key(provider: str = "mistral") -> str:
    """Provider key from the environment. The UI adds an `st.secrets` fallback."""
    return os.getenv(API_KEY_VARS.get(provider, "MISTRAL_API_KEY"), "")


def snapshot() -> dict:
    """Docs freshness stamp written by refresh-docs.sh. Never raises."""
    try:
        with open(SNAPSHOT_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}
