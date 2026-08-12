#!/usr/bin/env python3
"""Sage — the assistant UI (Streamlit).

Retrieval, chunking, ranking, link resolution and file handling live in the `sage`
package so they can be unit-tested without Streamlit. This module is only the view:
session state, layout, and the tool loop that drives them.
"""

from __future__ import annotations

import hashlib
import html
import logging
import os
import subprocess

import streamlit as st
import streamlit.components.v1 as components

from sage import (
    cite,
    config,
    context,
    engine,
    feedback,
    files,
    history,
    links,
    llm,
    profiles,
    providers,
)
from sage import corpus as corpus_mod
from sage.search import Index

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.WARNING),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sage.app")

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

def setting(name: str, default: str = "") -> str:
    """A deployment setting from the environment, falling back to `st.secrets`.

    Community Cloud does surface root-level secrets as environment variables, but
    this does not rely on that having happened by the time this module is imported.
    Community Cloud does surface root-level secrets as environment variables, but
    reading both is one line and removes the question of whether it had happened
    by the time this module was imported.

    Safe before `set_page_config` — `st.secrets` enqueues nothing, and the
    page title and icon below are the profile's.
    """
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:  # no secrets.toml present
        return default


# Which assistant this is: corpus, prompt, tool copy, starter cards and brand.
# There is one profile in this repository, and `SAGE_PROFILE` cannot select another.
PROFILE = profiles.get(setting("SAGE_PROFILE", profiles.DEFAULT).lower())
SYSTEM_PROMPT = PROFILE.system_prompt


def _flag(name: str, default: bool) -> bool:
    raw = setting(name, "1" if default else "").lower()
    return raw not in ("", "0", "false", "no")


# --- what a public endpoint may do ------------------------------------------
# Both of these default to the *closed* position, so a deployment that sets nothing
# is the safe one. The app was written as a personal tool, where an open file
# ingest and an uncapped question count cost nothing; embedded in a public page they
# are somebody else's upload and somebody else's bill.

# The composer's attachment picker. Useful when the app is your own tab, an open
# file-ingest endpoint when it is an iframe on a public site.
UPLOADS_ON = _flag("SAGE_UPLOADS", False)

# Questions one browser session may ask. Not a security boundary — a new session is
# a reload away — but it turns "hold the key down and drain the balance" into
# something deliberate, which is the difference that matters for a metered key.
# 0 disables the cap.
SESSION_LIMIT = max(0, int(setting("SAGE_SESSION_LIMIT", "40") or 0))

WELCOME_TITLE = PROFILE.welcome_title
WELCOME_SUBTITLE = PROFILE.welcome_subtitle

# The commit this build came from, rendered where a reader never sees it and anyone
# debugging can. "Is the fix actually live?" has now been asked three times and
# guessed at three times, most recently while a broken stylesheet was on screen and
# the stamp meant to settle it was the thing that was broken.
#
# Two deployment shapes, so two sources. `tools/export_app.py` writes BUILD into the
# slim tree it publishes. Community Cloud deploying straight from a branch — which is
# what DEPLOYING.md §3 describes and what this app does — clones the repository
# instead, so there is no BUILD and the SHA has to come from the clone. Returning
# "source" for that case, as this first did, made the stamp useless on the only
# deployment that exists: it said the same word before and after every push.
#
# Both are best-effort and neither can take the app down with it: a missing file, no
# git, no `.git`, or a hung subprocess all fall through to "unknown".
def _build() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(here, "BUILD"), encoding="utf-8") as fh:
            stamped = fh.read().strip()
        if stamped:
            return stamped
    except OSError:
        pass
    try:
        sha = subprocess.run(
            ["git", "-C", here, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    return sha or "unknown"


st.set_page_config(
    page_title=PROFILE.page_title,
    page_icon=PROFILE.page_icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- assets ----------------------------------------------------------------


def _stamp(name: str) -> float:
    """A file's mtime, or 0 if it is not there.

    Part of the cache key below rather than a nicety. Community Cloud answers a push
    by pulling the files and rerunning the script in the process it already has, so a
    cache keyed on the name alone serves the stylesheet the process read at boot for
    as long as that process lives: the new CSS is on disk, is never read, and the fix
    looks like it did not work. See DEPLOYING.md.
    """
    try:
        return os.stat(os.path.join(STATIC, name)).st_mtime
    except OSError:
        return 0.0


@st.cache_resource(show_spinner=False)
def _read_asset(name: str, _mtime: float) -> str:
    try:
        with open(os.path.join(STATIC, name), encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        logger.error("Missing static asset %s: %s", name, exc)
        return ""


def load_asset(name: str) -> str:
    return _read_asset(name, _stamp(name))


# --- which way the panel is set ---------------------------------------------
#
# The website has its own light/dark switch and passes the result in
# `embed_options`, which is Streamlit's own parameter for it. The app used to leave
# the question entirely to Streamlit and to `@media (prefers-color-scheme: dark)`,
# and that produced a panel that disagreed with the page it was docked in: inside a
# site set to dark, Safari rendered this app light and Chrome rendered it dark. Same
# reader, same machine, a white rectangle in one browser.
#
# So the palette is applied from what the site said, and the canvas is painted here
# rather than left to Streamlit's theme, which is the part Safari was not applying.
# `auto` is what a direct visit to the app's own URL gets, and only there does the
# operating system get a vote.

# The website's own colours: `--bg-color`, `--body-color` and `--secondary-bg-color`
# in assets/css/custom.css. Matched exactly, because the panel's frame and title bar
# are painted in them by chat.css, and any other values put a seam down the inside
# of the panel.
#
# The third is the composer's surface, and it is here for the same reason the first
# two are. app.css styles that box, its border, its radius and its focus ring, but
# never its background: it left that to Streamlit's theme, and Streamlit's theme is
# exactly the thing that was not being applied. Measured on the deployed app with
# the palette in force: a 240,242,246 strip across an otherwise dark panel, which is
# Streamlit's light secondary background showing through everything.
CANVAS = {
    "dark": ("#0d1117", "#c3ccd6", "#161b22"),
    "light": ("#ffffff", "#334155", "#f3f4f6"),
}


def scheme() -> str:
    """"dark", "light", or "" when the reader did not arrive from the website.

    `theme`, and not the `embed_options=dark_theme` beside it in the same URL.
    Streamlit reserves `embed` and `embed_options`, consumes them in the frontend
    and does not put them in `st.query_params`, so an app reading them sees nothing
    however carefully the site sets them. Measured, after an afternoon of assuming
    otherwise: `?embed=true&embed_options=dark_theme&theme=dark&ctx_url=x` arrives
    here as `{'theme': ['dark'], 'ctx_url': ['x']}`.

    Defined above `query_param` and not using it, because the stylesheet this feeds
    has to be on the page before anything is drawn on it.
    """
    asked = ""
    try:
        asked = str(st.query_params.get("theme", "") or "").strip().lower()
    except Exception:
        try:
            values = st.experimental_get_query_params().get("theme", [])
            asked = str(values[0] if values else "").strip().lower()
        except Exception:
            asked = ""
    return asked if asked in CANVAS else ""


def scheme_css(mode: str) -> str:
    """The palette for `mode`, plus the canvas Streamlit may not have painted."""
    palette = load_asset("app-dark.css")
    if mode == "dark":
        block = palette
    elif mode == "light":
        block = ""      # app.css is light where it stands
    else:
        block = f"@media (prefers-color-scheme: dark) {{\n{palette}\n}}"
    if mode not in CANVAS:
        return block
    background, text, surface = CANVAS[mode]
    return (
        f"{block}\n"
        # The composer's box. Streamlit paints this one on a generated class name
        # that changes between versions, so it is reached through the test id above
        # it, which does not.
        f'[data-testid="stChatInput"] > div {{ background: {surface} !important; }}\n'
        # `color-scheme` as well as the colours: it is what makes the browser draw
        # the scrollbar, the caret and any native control on the right side of the
        # divide. Without it a dark panel gets a light scrollbar down its edge.
        #
        # `:root` and not `html`, which is the same element and loses. app.css says
        # `:root { color-scheme: light dark }`, meaning "this app can do either",
        # and a type selector cannot outrank a pseudo-class however late it comes.
        # Measured: the canvas went dark and the colour scheme stayed `light dark`.
        #
        # `[data-testid="stBottom"] > div` is the strip the composer sits on, and it
        # is a separate element from the one above it. Streamlit's bottom dock is two
        # nested divs: a sticky outer one carrying the test id, which paints nothing,
        # and an inner one that fills itself with the background of *Streamlit's own*
        # theme and carries no test id at all, only a generated class that changes
        # between releases. So painting the test id alone left the inner one white,
        # which is what a reader of a dark page saw: a hundred pixels of white across
        # the foot of the panel, with a correctly dark question box floating on it.
        #
        # Measured against the deployed app in a headless browser, with the site set
        # to dark and the browser to light, which is the arrangement the screenshots
        # came from: the outer div answered rgb(13, 17, 23) and the inner one
        # rgb(255, 255, 255). Reached as a child rather than by its class, because
        # the class is `e1td4qo63` today and something else next release.
        f":root, body, .stApp, [data-testid=\"stAppViewContainer\"], "
        f"[data-testid=\"stMain\"], [data-testid=\"stBottom\"], "
        f"[data-testid=\"stBottom\"] > div {{\n"
        f"    background: {background} !important;\n"
        f"    color: {text};\n"
        f"    color-scheme: {mode};\n"
        f"}}\n"
    )


# The profile's brand comes after the stylesheet so its custom properties win.
#
# `<style>` must be the very first thing in this string, and the build stamp is a CSS
# comment inside it rather than an HTML comment before it. st.markdown parses its
# argument as Markdown before any of it is HTML, and in CommonMark a raw-HTML block
# opened by `<!--` ends on the line containing `-->` — not at the `</style>` a
# thousand lines later. A `<!-- build … --><style>…` prefix therefore closed the
# block at the end of its own line and handed the entire remaining stylesheet to the
# Markdown parser, which rendered it as visible prose: two hundred bullets of CSS
# above the conversation, `[class*="st-key-…"]` with the asterisks eaten as emphasis,
# and not one rule applied, because there was no longer a style element to apply.
# Opened by `<style>` the block is CommonMark type 1 instead, which ends only at the
# closing tag, so the stylesheet cannot be reinterpreted however many blank lines and
# asterisks it contains. tests/test_app_smoke.py::TestStylesheet holds the invariant.
SCHEME = scheme()
st.markdown(
    f"<style>/* build {_build()} */\n"
    f"{load_asset('app.css')}\n{scheme_css(SCHEME)}\n"
    f"{PROFILE.brand_css_for(SCHEME)}</style>",
    unsafe_allow_html=True,
)
components.html(f"<script>{load_asset('app.js')}</script>", height=0)


# --- resources -------------------------------------------------------------


@st.cache_resource(show_spinner=PROFILE.index_spinner)
def get_index() -> Index:
    built = corpus_mod.build(profile=PROFILE)
    index = Index(built)
    # The profile is named here, at WARNING, because it is the one fact you need
    # from a deployment's logs to know it came up as the assistant you meant. At
    # INFO it would be invisible under the default LOG_LEVEL.
    logger.warning(
        "Sage ready: profile=%s, %s", PROFILE.key, corpus_mod.summarize(built)
    )
    if not built.chunks:
        st.error(
            f"**The `{PROFILE.key}` corpus is empty.** Nothing was found under "
            f"{', '.join(sorted(PROFILE.paths.values()))}. The assistant would "
            "answer every question with 'not covered'."
        )
        st.stop()
    return index


def resolve_api_key(provider: str) -> str:
    key = config.api_key(provider)
    if key:
        return key
    try:
        return str(st.secrets.get(config.API_KEY_VARS[provider], ""))
    except Exception:  # no secrets.toml present
        return ""


def configured_providers() -> list[str]:
    """Providers that actually have a key, in preference order."""
    return [name for name in (providers.MISTRAL, providers.OPENCODE)
            if resolve_api_key(name)]


@st.cache_resource(show_spinner=False)
def get_provider(name: str):
    """Cached per provider; the key is read inside so it never becomes a cache key."""
    return providers.build(name, resolve_api_key(name))


@st.cache_resource(show_spinner=False)
def available_models(name: str) -> list[providers.Model]:
    try:
        return get_provider(name).models()
    except Exception as exc:
        logger.warning("Could not list models for %s: %s", name, exc)
        return []


READY = configured_providers()
if not READY:
    st.error(
        "**No API key is set.** Provide `MISTRAL_API_KEY` and/or `OPENCODE_API_KEY` "
        "in the environment or `.streamlit/secrets.toml`, then reload. "
        "OpenCode Zen keys are free and start with `sk-zen-`."
    )
    st.stop()

INDEX = get_index()
CORPUS = INDEX.corpus


def query_param(name: str) -> str:
    """One query-string value, whichever Streamlit version is installed.

    `st.query_params` arrived in 1.30 and `experimental_get_query_params` is on the
    way out; reading both means the embed keeps working across an upgrade instead
    of silently losing the reader's page context, which nothing would report.
    """
    try:
        value = st.query_params.get(name, "")
    except Exception:
        try:
            values = st.experimental_get_query_params().get(name, [])
        except Exception:
            return ""
        value = values[0] if values else ""
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


# The page the reader opened the assistant from. The website puts it here; the
# brief it produces is what makes "how does it compare?" answerable.
CONTEXT_URL = query_param("ctx_url")
SYSTEM_PROMPT, CONTEXT_DOC = context.apply(SYSTEM_PROMPT, CORPUS, CONTEXT_URL)
# No welcome heading when the reader arrived from an article either. The panel's
# own title bar on the website already reads "Asking about this article", so it was
# the same statement twice, eighty pixels apart.
if CONTEXT_URL and CONTEXT_DOC is None:
    # Worth a line in the log: it means the site and this corpus disagree about a
    # URL, which is what happens when a post is published and the corpus has not
    # been re-synced.
    logger.warning("Unknown ctx_url %r — not in the index", CONTEXT_URL)

for key, default in (
    ("messages", []),
    ("processing", False),
    # A list, not one file. Holding one meant the guard below dropped anything
    # offered while a file was already attached, and a second attachment looked from
    # the outside like a control that does nothing.
    ("attachments", []),
    # How many times the user has dismissed each uploaded file with a chip's ✕. The
    # uploader widget still reports them on every rerun — nothing here can reach into
    # it and remove one — so without this they come straight back on the next run. A
    # count rather than a flag, so a file that is deliberately re-picked can return
    # while one merely still being reported cannot.
    ("dropped_uploads", {}),
    # Why a file was refused, keyed the same way, so the reason survives a rerun.
    ("upload_refusals", {}),
    ("uploader_key", 0),
    # Whether the `?q=` the page was opened with has been sent. See ask_from_url.
    ("asked_from_url", False),
    # Questions asked this session, against SESSION_LIMIT.
    ("asked_count", 0),
    ("error", None),
    ("error_detail", ""),
    ("model", ""),
    ("notice", ""),
):
    st.session_state.setdefault(key, default)


def model_options() -> list[providers.Model]:
    options: list[providers.Model] = []
    for name in READY:
        options.extend(available_models(name))
    return options


MODELS = model_options()


def current_model() -> providers.Model:
    """The selected model, falling back to the configured default then anything."""
    for candidate in (st.session_state.model, config.DEFAULT_MODEL):
        chosen = providers.parse_key(candidate)
        if chosen and any(option.key == chosen.key for option in MODELS):
            return chosen
    if MODELS:
        return MODELS[0]
    # Nothing listed a single model, which means every provider's discovery call
    # failed. The last resort has to name a provider *and* a model that belong
    # together, and pairing `READY[0]` with `config.MODEL` did not: that constant is a
    # Mistral id, so with only a Zen key configured this asked Zen for
    # `mistral-small-latest` and got a 404 for a model nobody had chosen. The default
    # is used when its own provider is one of the ready ones, and only then.
    fallback = providers.parse_key(config.DEFAULT_MODEL)
    if fallback and fallback.provider in READY:
        return fallback
    return providers.Model(READY[0], config.MODEL)


MODEL = current_model()
st.session_state.model = MODEL.key


# Streamlit signals "stop this script and start again" by raising. Matched by class
# name rather than imported, because the module those classes live in has moved
# between versions (`scriptrunner.script_runner` → `scriptrunner_utils.exceptions`)
# and because the test stub raises its own equivalents — a name test covers all
# three, an import covers whichever one happened to be installed when it was written.
CONTROL_FLOW_NAMES = frozenset(
    {"RerunException", "StopException", "Rerun", "Stop", "RerunError"}
)


def is_control_flow(exc: BaseException) -> bool:
    return type(exc).__name__ in CONTROL_FLOW_NAMES


# --- rendering helpers -----------------------------------------------------


def escape(text: str) -> str:
    return html.escape(text, quote=False).replace("\n", "<br>")


def render_user(message: dict) -> None:
    badge = "".join(
        f'<div class="attachment-badge">{item.icon} '
        f"{html.escape(item.filename)}</div>"
        for item in (message.get("attachments") or [])
    )
    st.markdown(
        f'<div class="user-message"><div class="user-bubble">{badge}'
        f'{escape(message.get("text", ""))}</div></div>',
        unsafe_allow_html=True,
    )


def related_sections(sources: list[dict], limit: int = 3) -> list[dict]:
    """Sibling sections of the pages actually cited — discovery for free.

    No extra model call: the chunks are already indexed, so neighbouring sections
    of a cited page are known and are always real documentation.
    """
    cited = {source["id"] for source in sources}
    pages = {source["id"].split("#", 1)[0] for source in sources}
    out: list[dict] = []
    for chunk in CORPUS.chunks:
        if len(out) >= limit:
            break
        page = f"{chunk.source}/{chunk.path}"
        if page in pages and chunk.id not in cited and chunk.heading:
            out.append({"label": chunk.heading, "url": cite.url_for(chunk)})
    return out


def _page_of(url: str) -> str:
    """A URL reduced to the page it names, so two links to it compare equal."""
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def cited_href(source: dict) -> str:
    """A source's link, carrying enough for the page to show where the citation is.

    Built at render time from the chunk rather than stored on the message: the
    quote is derived from a corpus this app already holds, and a URL saved into
    session state months of conversation ago would be one the highlighter had
    since learned to read differently.
    """
    chunk = CORPUS.chunk(source.get("id", ""))
    return cite.with_citation(source["url"], cite.quote_of(chunk) if chunk else "")


def _chip(url: str, label: str, kind: str = "") -> str:
    """One source chip.

    A citation to the article the reader already has open behind the panel is not
    a link to somewhere else. Opening a second tab on the page you are looking at
    is a worse answer to "where is this?" than scrolling to it. Those chips are
    marked, and `static/app.js` turns a click on one into a `sage:cite` message to
    the website, which scrolls the article behind the panel to the section and
    tints it. Everything else stays an ordinary link, opening in a new tab so the
    conversation is not navigated away from.
    """
    here = bool(CONTEXT_URL) and _page_of(url) == _page_of(CONTEXT_URL)
    classes = "source-chip source-chip--here" if here else "source-chip"
    tail = f'<span class="source-kind">{html.escape(kind)}</span>' if kind else ""
    return (
        f'<a class="{classes}" href="{html.escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{html.escape(label)}{tail}</a>'
    )


def render_sources(sources: list[dict], related: list[dict]) -> None:
    if not sources:
        return
    chips = "".join(
        _chip(cited_href(source), source["label"], source["source"])
        for source in sources
    )
    strip = f'<div class="sources"><span class="sources-label">Sources</span>{chips}</div>'

    if related:
        more = "".join(_chip(item["url"], item["label"]) for item in related)
        strip += (
            f'<div class="sources"><span class="sources-label">Related</span>{more}</div>'
        )
    st.markdown(strip, unsafe_allow_html=True)


def render_rating(position: int, message: dict) -> None:
    if not feedback.enabled():
        return
    if message.get("rating"):
        st.markdown(
            '<div class="rating-thanks">Thanks — noted.</div>', unsafe_allow_html=True
        )
        return

    with st.container(key=f"rate-{position}"):
        columns = st.columns([1, 1, 12], gap="small")
        for column, verdict, glyph, hint in (
            (columns[0], "up", "👍", "This answered my question"),
            (columns[1], "down", "👎", "This was wrong or unhelpful"),
        ):
            with column:
                if st.button(glyph, key=f"rate-{position}-{verdict}", help=hint):
                    question = next(
                        (
                            item.get("text", "")
                            for item in reversed(
                                st.session_state.messages[:position]
                            )
                            if item.get("role") == "user"
                        ),
                        "",
                    )
                    feedback.record_rating(
                        verdict,
                        question,
                        message.get("text", ""),
                        message.get("sources", []),
                    )
                    message["rating"] = verdict
                    st.rerun()


def render_assistant(position: int, message: dict) -> None:
    with st.container(key=f"answer-{position}"):
        with st.chat_message("assistant"):
            st.markdown(links.fix_links(message.get("text", ""), CORPUS))
        sources = message.get("sources", [])
        render_sources(sources, related_sections(sources))
        render_rating(position, message)


def _detail(exc: BaseException | None, model_key: str = "") -> str:
    """A one-line, non-secret description of a failure for the details panel.

    `model_key` is the model that actually raised, which after a failover is not
    `MODEL`: that one is only what the picker settled on before the turn began.
    Reporting the selection produced a panel that named a Mistral model above a 429
    from Zen's endpoint, which reads as a bug in the app rather than as what it was,
    the second provider refusing after the first had already been abandoned.
    """
    if exc is None:
        return ""
    text = f"{type(exc).__name__}: {exc}"
    status = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    if status:
        text = f"{text}  (HTTP {status})"
    # What the endpoint said about itself. Without this every 429 read the same and
    # "which limit" had no answer: requests a minute, tokens a minute and a daily cap
    # are three problems, and only one of them is fixed by waiting.
    said = llm.http_detail(exc)
    if said:
        text = f"{text}\n{said}"
    return f"{text}\nmodel={model_key or MODEL.key}"[:800]


def status_html(text: str) -> str:
    return (
        '<div class="status-row" role="status" aria-live="polite">'
        '<span class="status-dot" aria-hidden="true"></span>'
        f'<span class="status-text">{html.escape(text)}</span>'
        '<span class="status-dots" aria-hidden="true"><span></span><span></span>'
        "<span></span></span></div>"
    )


def show_status(slot, text: str) -> None:
    slot.empty()
    with slot.container(), st.chat_message("assistant"):
        st.markdown(status_html(text), unsafe_allow_html=True)


def ask_from_url() -> None:
    """Send the question the website arrived with, once.

    The homepage box, the example chips and the "Ask about this" bubble all open
    the app with `?q=…`. Asking it here rather than making the reader press send
    again is the difference between the chip being a shortcut and being a detour.

    Guarded by session state, not by the parameter: Streamlit reruns this script on
    every interaction and the query string does not change, so without the guard
    the same question would be re-asked forever.
    """
    if st.session_state.asked_from_url or st.session_state.messages:
        return
    st.session_state.asked_from_url = True
    question = query_param("q").strip()
    if question:
        start_new_turn(question)


def start_new_turn(question: str, attachments=None) -> None:
    st.session_state.messages.append(
        {"role": "user", "text": question, "attachments": list(attachments or [])}
    )
    # Enforced here rather than at each submit site: the composer, a starter card and
    # the `?q=` the page can be opened with all arrive through this one function, and
    # a cap that only covers the composer is not a cap.
    st.session_state.asked_count += 1
    if SESSION_LIMIT and st.session_state.asked_count > SESSION_LIMIT:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "text": (
                    "That is as far as one session goes. Reload the page to carry on "
                    "— the conversation starts fresh, but everything published here "
                    "is still searchable."
                ),
                "sources": [],
                "rating": None,
                "model": "",
            }
        )
        st.session_state.attachments = []
        st.session_state.uploader_key += 1
        st.rerun()
    st.session_state.processing = True
    st.session_state.error = None
    st.session_state.attachments = []
    # Both, together: the widget is reset so its files stop being reported, and the
    # dismissal list is emptied because the keys in it refer to a widget that no
    # longer exists. Leaving stale keys behind would silently refuse a file with the
    # same name later in the conversation.
    st.session_state.dropped_uploads = {}
    st.session_state.upload_refusals = {}
    st.session_state.uploader_key += 1
    st.rerun()


ask_from_url()


# --- composer strip --------------------------------------------------------

# There is deliberately no caveat line under the input. It went from a popover, to
# three paragraphs under the starter cards, to one 11px line beside the model name,
# and each version was still a permanent fixture at the bottom of every screen for
# something read once and then ignored. Neither half of it is lost: every answer
# carries a Sources strip to the documentation it came from, so "this can be wrong,
# here is what it read" is attached to the thing that might be wrong; and the system
# prompt hands out the Help Desk address (`sage/prompts.py`, `sage/tools.py`) in the
# answer to a question the documentation cannot settle, which is when it is wanted.

has_messages = bool(st.session_state.messages)


# There is no model picker. Which model answers is an operational detail of this
# deployment, not a choice a reader of a blog should be asked to make — and naming
# it invites "why is it using that one?" about a decision that changes hourly as
# quotas move. `engine.run_conversation` walks the configured models itself.


# `render_controls()` and the `composer-strip` container it drew stood here. The
# strip's last inhabitant was a 🗑️ that cleared the conversation, and the strip is
# the reason the composer floated: the bar reserves `--strip-h` of room beneath the
# input for it, so an empty strip is a band of nothing holding the box off the
# bottom of the panel. Both are gone, and `--strip-h` is 0.


# --- body ------------------------------------------------------------------

if not has_messages:
    # Only if there is something to say. An empty heading still renders an <h1> with
    # its own margins, so a blank profile would leave a band of nothing above the
    # composer rather than an empty panel.
    if WELCOME_TITLE or WELCOME_SUBTITLE:
        title = (
            f'<h1 class="welcome-title">{escape(WELCOME_TITLE)}</h1>'
            if WELCOME_TITLE else ""
        )
        subtitle = (
            f'<p class="welcome-subtitle">{escape(WELCOME_SUBTITLE)}</p>'
            if WELCOME_SUBTITLE else ""
        )
        st.markdown(
            f'<div class="welcome">{title}{subtitle}</div>', unsafe_allow_html=True
        )

else:
    # Marker only: app.js keys page-scroll behaviour off its presence — without it
    # the screen is the landing screen, which always starts at the top.
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)

    rendered = st.session_state.messages
    if st.session_state.processing and rendered and rendered[-1]["role"] == "user":
        rendered = rendered[:-1]

    for position, message in enumerate(rendered):
        if message["role"] == "user":
            render_user(message)
        elif message.get("text"):
            render_assistant(position, message)

    if st.session_state.notice:
        st.markdown(
            f'<div class="notice">{html.escape(st.session_state.notice)}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.error and not st.session_state.processing:
        st.markdown(
            '<div class="error-card" role="alert">'
            '<div class="error-title">Could not complete that request</div>'
            f'<div class="error-body">{html.escape(st.session_state.error)}</div></div>',
            unsafe_allow_html=True,
        )
        if st.session_state.error_detail:
            # Streamlit Cloud logs are awkward to reach; surfacing the real
            # exception here is what turns "something went wrong" into a fixable
            # report. Collapsed so it stays out of the way for normal users.
            with st.expander("Technical details"):
                st.code(st.session_state.error_detail, language="text")
        # Retry, and nothing else. By the time this card is on screen the engine
        # has already tried every configured model, so a "use a different one"
        # button would offer a choice that does not exist — and would be the one
        # place a reader learns there are several.
        with st.container(key="error-actions"):
            slots = st.columns([1, 2, 1])
            with slots[1]:
                retry = st.button("↻ Try again", key="retry", use_container_width=True)
        if retry:
            st.session_state.error = None
            st.session_state.error_detail = ""
            if st.session_state.messages[-1]["role"] == "user":
                st.session_state.processing = True
            st.rerun()


# --- input -----------------------------------------------------------------

# `accept_multiple_files`, and no `type=`.
#
# The type filter was a list of extensions the picker would offer, and it is gone for
# the same reason the extension gate in `files.process` went: it refused a pasted
# screenshot outright (the name app.js gives one is not on any list) and it refused
# every cluster file whose extension nobody thought of. `files.process` reads the
# bytes and says yes or no with a reason, which is the check that was doing the work
# anyway.
if UPLOADS_ON:
    upload = st.file_uploader(
        "Attach a file",
        accept_multiple_files=True,
        key=f"uploader-{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )
else:
    # Not rendered at all rather than rendered disabled. A disabled widget is still
    # a widget: Streamlit keeps the upload endpoint behind it live, so hiding it in
    # CSS would leave the door open and only move the handle.
    upload = []


def upload_key(item) -> tuple:
    """Identity of an uploaded file across reruns.

    Name, size and a digest of the first 4 KB — not Streamlit's `file_id`, which
    changes on every rerun for the same file in some versions and would re-process and
    re-append one attachment per interaction with the page.

    The digest is there because name and size alone collided: two different
    `config.yaml` files of the same length were one attachment, and the second was
    dropped without a word. 4 KB rather than the whole file so a 10 MB upload is not
    rehashed on every rerun.
    """
    head = item.getvalue()[:4096]
    return (item.name, item.size, hashlib.blake2b(head, digest_size=8).hexdigest())


keyed = [(upload_key(item), item) for item in upload or []]
offered = {key for key, _item in keyed}

# Dismissals are COUNTED, not just remembered, and the count is how many copies of a
# file to skip on this run.
#
# A plain set of keys blacklisted the file outright, so after dismissing a chip the
# user could pick the *same file* again and nothing whatsoever happened — no chip, no
# warning. Worse on the landing screen, where the Clear button that resets this does
# not render, so there was no route back at all short of reloading the page.
#
# Counting keeps the distinction that matters. `accept_multiple_files` accumulates, so
# a re-picked file is reported twice: one dismissal skips the first copy and the second
# is a fresh offer and attaches. A file dismissed and not re-picked is still reported
# once, still skipped, and still does not come back on its own.
dismissed = dict(st.session_state.dropped_uploads)
# Keys the widget has stopped reporting cannot come back, so their counts are dead.
dismissed = {key: count for key, count in dismissed.items() if key in offered}

# Reasons files were refused, so the explanation outlives the run that produced it. A
# bare `st.warning` is discarded whenever the run ends in a rerun — which it does
# whenever a file is dropped while an answer is generating — and the refusal was
# permanent, so the user was left with a file in the uploader, no chip, and no reason.
refusals = {
    key: why
    for key, why in dict(st.session_state.get("upload_refusals", {})).items()
    if key in offered
}

held = {item.key for item in st.session_state.attachments if item.key}
for key, item in keyed:
    if key in held:
        continue
    if dismissed.get(key, 0) > 0:
        dismissed[key] -= 1
        continue
    attachment, error = files.process(item.name, item.getvalue())
    if not error:
        # The per-file limit does not bound the total, and a handful of legal
        # screenshots made one illegal request. Refused here rather than by the
        # provider, which reports it as "this conversation got too long".
        attached = sum(held_item.size for held_item in st.session_state.attachments)
        if attached + item.size > config.MAX_ATTACHED_BYTES:
            limit = config.MAX_ATTACHED_BYTES // (1024 * 1024)
            error = (
                f"{item.name} would put this turn over the {limit} MB total for "
                "attachments. Send what is attached first, or drop something."
            )
    if error:
        # Remembered rather than clearing the whole widget: a bad file among three
        # good ones used to reset the uploader and take the other two with it.
        st.session_state.dropped_uploads[key] = (
            st.session_state.dropped_uploads.get(key, 0) + 1
        )
        refusals[key] = error
        continue
    attachment.size = item.size
    attachment.key = key
    st.session_state.attachments.append(attachment)
    held.add(key)

st.session_state.upload_refusals = refusals
for why in refusals.values():
    st.warning(f"⚠️ {why}")


def render_attachments() -> None:
    """The chips for what is attached, pinned directly above the input box.

    They used to render wherever the script happened to reach them — in the middle of
    the page, under the starter cards, a long way from the box they belong to. They
    are part of the composer, so they are pinned to it: app.js measures this row and
    the page reserves room for it, exactly as it does for the controls underneath.
    """
    if not st.session_state.attachments:
        return
    with st.container(key="attachments"):
        for index, item in enumerate(st.session_state.attachments):
            if st.button(
                # Filename and the ✕, and a truncation warning if there is one. The
                # character and page counts that used to sit here were four chips of
                # arithmetic on a four-file turn, none of it telling the reader
                # anything they did not already know about a file they chose.
                f"{item.icon} {item.filename}"
                + (f" · {item.summary}" if item.summary else "")
                + "  ✕",
                key=f"drop-attachment-{index}",
                help="Remove this attachment",
            ):
                dropped = st.session_state.attachments.pop(index)
                if dropped.key:
                    st.session_state.dropped_uploads[dropped.key] = (
                        st.session_state.dropped_uploads.get(dropped.key, 0) + 1
                    )
                st.rerun()
        if any(item.kind == "image" for item in st.session_state.attachments) and not (
            config.sees_images(MODEL.id)
        ):
            # Said next to the picture, once, rather than discovered when the answer
            # ignores it. The picker is right there.
            st.caption(
                f"{MODEL.label} cannot read images — pick a Pixtral or Claude model "
                "to have this one looked at."
            )

# No `max_chars`. That argument is the only thing that puts Streamlit's "15/8000"
# counter inside the box, and a running character count is noise in a box you type a
# question into — it reads as a form field with a quota. The limit itself is still
# enforced, below, where it costs nothing to look at.
#
# Enforced here rather than hidden with CSS on purpose: the counter's own test id is
# Streamlit's, unversioned, and not visible from this repo, so a rule naming it would
# be a guess that fails silently the day it changes. Not asking for the counter
# cannot fail that way.
prompt = st.chat_input(PROFILE.input_placeholder)

# Rendered here, before the turn below: that block ends in `st.rerun()`, so
# anything after it is never reached while an answer is generating — which is
# exactly when a user whose model just ran out of credit reaches for the picker.
# The chips go with it: they are pinned to the composer too, and rendering them up
# where the script first hears about the upload is what put them mid-page.
render_attachments()

if prompt and prompt.strip():
    asked = prompt.strip()
    if len(asked) > config.MAX_PROMPT_CHARS:
        # The cap the counter used to advertise. Said once, at the moment it matters,
        # instead of counted out on screen for every question that was never near it.
        over = len(asked) - config.MAX_PROMPT_CHARS
        st.warning(
            f"⚠️ That question is {over:,} characters over the "
            f"{config.MAX_PROMPT_CHARS:,}-character limit. Shorten it, or attach the "
            "long part as a file."
        )
        # And handed back, because `st.chat_input` empties its box on submit: without
        # this, "shorten it" asks the reader to shorten something the app has just
        # destroyed. The counter that used to enforce this made overrunning impossible
        # in the first place, so losing the text is a regression this pays off.
        with st.expander("Your question, to copy back out", expanded=True):
            st.code(asked, language=None)
    else:
        start_new_turn(asked, st.session_state.attachments)


# --- the turn --------------------------------------------------------------

if st.session_state.processing:
    # Marker element app.js polls to know a generation is in flight.
    st.markdown('<div id="processing-signal" hidden></div>', unsafe_allow_html=True)

    render_user(st.session_state.messages[-1])
    status = st.empty()
    show_status(status, "Thinking")

    answer = st.empty()
    question = st.session_state.messages[-1].get("text", "")
    # Set only when Streamlit aborts this run from underneath us. The `finally` below
    # must then leave `processing` alone and not issue a rerun of its own: the abort
    # already is one, and clearing the flag on a turn that never finished left the
    # question on screen with no answer, no error and nothing to click.
    interrupted = False

    def fail(message: str, detail: str) -> None:
        """Surface a failure — and drop any notice, which can only contradict it.

        A leftover "retrying with X…" sitting above "could not complete that
        request" is how the UI ended up arguing with itself.
        """
        st.session_state.error = message
        st.session_state.error_detail = detail
        st.session_state.notice = ""

    try:
        messages = history.build(
            st.session_state.messages,
            SYSTEM_PROMPT,
            vision=config.sees_images(MODEL.id),
        )

        # `run_conversation`, not `run_turn`: it walks every configured model
        # itself, so a spent quota moves to the next one inside a single turn with
        # nothing said about it. The old path failed over by rerunning and printing
        # "X is unavailable, retrying with Y" — accurate, and an answer to a
        # question no visitor asked.
        answered: dict | None = None
        for event in engine.run_conversation(
            index=INDEX,
            messages=messages,
            models=[MODEL, *(option for option in MODELS if option.key != MODEL.key)],
            provider_for=get_provider,
            question=question,
        ):
            if event.kind == engine.STATUS:
                show_status(status, event.text)
            elif event.kind == engine.ANSWER:
                answered = event.data

        status.empty()
        # Drawn once, finished, with its links already resolved, and drawn here
        # rather than left to the rerun below so the panel is not empty for the
        # width of a script run.
        #
        # Nothing is painted before this point. The engine no longer hands out
        # partial text (see its module docstring), which is what stops the model's
        # "Let me search the articles…" appearing in this bubble and being wiped by
        # the next status line. The rerun that follows redraws exactly what is drawn
        # here, from the same text through the same `fix_links`, so the handover
        # between the two is invisible.
        if answered and answered["text"]:
            with answer.container(), st.chat_message("assistant"):
                st.markdown(links.fix_links(answered["text"], CORPUS))
        else:
            answer.empty()
        st.session_state.messages.append(
            {
                "role": "assistant",
                "text": answered["text"] if answered else "",
                "sources": answered["sources"] if answered else [],
                "rating": None,
                "model": MODEL.key,
            }
        )
        # A failover happened or it did not; either way the reader gets an answer
        # and no commentary. The switch is logged, not printed.
        if answered and answered.get("switched_from"):
            logger.info(
                "Answered on a fallback model after %s was %s",
                answered["switched_from"][0], answered["switched_from"][1],
            )
    except llm.AssistantError as exc:
        status.empty()
        answer.empty()
        # Every configured model has now been tried. There is nothing left to fail
        # over to and nothing useful to say about which one gave up first.
        logger.error(
            "Turn failed (%s): %r",
            exc.kind,
            exc.original,
            exc_info=exc.original if exc.kind == "unknown" else None,
        )
        fail(exc.user_message, _detail(exc.original or exc, getattr(exc, "model", "")))
    except Exception as exc:  # last-resort guard so the UI never dies
        if is_control_flow(exc):
            # Streamlit's own control flow, not a failure. Re-raised so the rerun or
            # stop it represents actually happens.
            interrupted = True
            raise
        status.empty()
        answer.empty()
        logger.exception("Unexpected failure")
        fail(llm.classify(exc).user_message, _detail(exc))
    finally:
        if not interrupted:
            st.session_state.processing = False
        # Not while interrupted: the abort in flight IS a rerun, and calling another
        # one here replaced it — which left the question on screen with no answer, no
        # error card and nothing to click, because `processing` had been cleared by a
        # turn that never finished.
        if not interrupted:
            st.rerun()
