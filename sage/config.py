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
# The free model, by the owner's instruction. It was `mistral:mistral-small-latest`,
# which is paid and, on this deployment, out of credit: every turn opened with a
# request that could only fail, waited out its backoff, and then failed over to this
# model anyway. Starting here removes a wasted round trip from every question and
# spends nothing.
#
# This names the *first* candidate and not the only one. `engine.run_conversation`
# still walks the rest of the ladder behind it, so a details panel reporting a failure
# names whichever model refused last, which is usually not this one.
#
# Best-effort by nature: `app.current_model` only honours it if the provider actually
# serves it, because Zen's free lineup rotates without notice and offering a model
# that has been withdrawn is a button that returns a 404. When it is gone the first
# model Zen does serve is used instead.
DEFAULT_MODEL = os.getenv("SAGE_DEFAULT_MODEL", "opencode:deepseek-v4-flash-free")

MISTRAL_MODELS = _env_list(
    "SAGE_MISTRAL_MODELS",
    ("mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"),
)

# OpenCode Zen is an OpenAI-compatible endpoint fronting a set of free models —
# a way to keep working once a paid key is out of credit. The live list is
# discovered from GET /models at runtime; this is only the fallback, since a free
# tier's lineup changes without notice.
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
OPENCODE_MODELS = _env_list(
    "SAGE_OPENCODE_MODELS",
    (
        "deepseek-v4-flash-free",
        "big-pickle",
        "mimo-v2.5-free",
        "nemotron-3-ultra-free",
        "north-mini-code-free",
        "hy3-free",
        "laguna-s-2.1-free",
        "ling-3.0-tiny-free",
        "longcat-2.0-free",
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


def is_free_zen_model(model: str) -> bool:
    lowered = (model or "").lower()
    return any(mark and mark.lower() in lowered for mark in ZEN_FREE_MARKS)

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


API_KEY_VARS = {"mistral": "MISTRAL_API_KEY", "opencode": "OPENCODE_API_KEY"}


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
