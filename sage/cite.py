"""Citations that show the reader *where* in the article the answer came from.

A citation used to be a link to a page, and at best to an anchor on it. Following
one landed the reader somewhere near the right place on a nine-thousand-word
article and left them to work out which two sentences the assistant had actually
read. The Sources strip listed five of those, so five near-misses.

What travels here is enough for the page to show it: the section's anchor, and the
opening of the section's own text. `assets/js/chat.js` on the website reads the two
off the URL (or off a `sage:cite` message, when the article is already open behind
the panel), tints the section the citation refers to and marks the sentence the
quote matches.

Both are carried as query parameters rather than as a `#:~:text=` fragment. The
text-fragment syntax is a browser feature, so it highlights nothing in Firefox, it
cannot tint a whole section, and it is stripped by the same history rewrite the
site uses to keep a copied URL clean. A parameter the site reads itself works
everywhere and can be removed from the address bar once it has been used.

The quote is deliberately short and deliberately plain. The corpus is written from
the *rendered* article (`tools/build_site_corpus.py` converts the published HTML),
so its prose is the prose on the page character for character. But it is markdown
prose, and `**both**` on this side is `both` on that one. Everything that is markup
rather than words comes off here, so the site is matching text against text.
"""

from __future__ import annotations

import re
from urllib.parse import quote as urlquote

from .normalize import plain_heading

# Read by `assets/js/chat.js`. Renaming one means renaming it there too.
ANCHOR_PARAM = "sage-cite"
QUOTE_PARAM = "sage-quote"

# Long enough to be unambiguous in an article that repeats a phrase, short enough
# that a rendering difference in the tail cannot stop it matching, since the site falls
# back to progressively shorter prefixes, and this is the longest one it tries.
QUOTE_CHARS = 180
# Below this a "quote" is a heading fragment or a stray caption line, which matches
# in twenty places or in none.
MIN_QUOTE_CHARS = 40

_FENCE = re.compile(r"^[ \t]*(?:`{3,}|~{3,})")
_TABLE_ROW = re.compile(r"^\s*\|")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# `[figure: …]` is how `sage/sitehtml.py` records a figure whose caption it kept.
_FIGURE = re.compile(r"^\s*\[figure:.*?\]\s*", re.IGNORECASE)
_HEADING = re.compile(r"^\s*#{1,6}\s+")
_BLOCKQUOTE = re.compile(r"^\s*>\s?")
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")


def _prose(text: str) -> list[str]:
    """The lines of a chunk that are sentences, as a reader sees them."""
    out: list[str] = []
    fenced = False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or _TABLE_ROW.match(line) or _RULE.match(line):
            continue
        stripped = _FIGURE.sub("", line)
        stripped = _IMAGE.sub("", stripped)
        stripped = _HEADING.sub("", stripped)
        stripped = _BLOCKQUOTE.sub("", stripped)
        stripped = _BULLET.sub("", stripped)
        # `plain_heading` is the inline-markup stripper: links unwrapped, emphasis
        # and code ticks dropped, whitespace collapsed. Its name is about where it
        # was first needed, not about what it does.
        cleaned = plain_heading(stripped)
        if cleaned:
            out.append(cleaned)
    return out


def _clip(text: str, limit: int) -> str:
    """Cut on a word, so the tail the site matches on is a whole word."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit * 0.6 else cut).rstrip(" ,;:")


def quote_of(chunk) -> str:
    """The opening of the cited section, in plain words, or "" if it has none.

    A figure-only or table-only chunk has nothing quotable in it, and returning
    its caption would mark a caption as the source of a claim about the prose.
    """
    for line in _prose(getattr(chunk, "text", "") or ""):
        # One line, never two joined: the corpus keeps a paragraph on a line of its
        # own, so joining across the break would build a string that appears
        # nowhere in the rendered page.
        if len(line) >= MIN_QUOTE_CHARS:
            return _clip(line, QUOTE_CHARS)
    return ""


def anchor_of(url: str) -> str:
    _, _, anchor = url.partition("#")
    return anchor


def with_citation(url: str, quote: str = "") -> str:
    """`url` with whatever the page needs to point at the passage inside it.

    The anchor is read back off the URL rather than passed in, so a caller cannot
    hand over a link and a marker that disagree.
    """
    base, _, anchor = url.partition("#")
    params = []
    if anchor:
        params.append(f"{ANCHOR_PARAM}={urlquote(anchor, safe='')}")
    if quote:
        params.append(f"{QUOTE_PARAM}={urlquote(quote, safe='')}")
    if not params:
        return url
    joined = "&".join(params)
    base = f"{base}&{joined}" if "?" in base else f"{base}?{joined}"
    return f"{base}#{anchor}" if anchor else base


def url_for(chunk) -> str:
    """The published URL of a chunk, carrying its own highlight."""
    return with_citation(chunk.url, quote_of(chunk))


# The parameters that mark a link as pointing *into* a page rather than at it. Either
# one is enough: a section citation carries the anchor, and a page whose sections have
# no published anchors of their own still carries the quote, which is what the site
# matches on to find the passage.
CITATION_PARAMS = (ANCHOR_PARAM, QUOTE_PARAM)


def points_at_a_passage(url: str) -> bool:
    """Whether `url` is a citation, asked of the finished URL rather than the chunk.

    Read by two places that must agree and did not: `links.compact_citations`, which
    decides whether to shrink a citation to a numbered marker, and the stylesheet,
    which decides whether to draw one as a marker. The first used to ask "did this
    resolve to a chunk?" and the second "does the href carry `sage-cite`?", and those
    are different questions for any chunk without an anchor: the about note's sections
    have none, so a real answer showed two bare "1"s set in ordinary link blue with
    nothing to say they were citations.

    `assistant/static/app.css` selects on the same two parameters. Adding a third here
    means adding it there.
    """
    return any(f"{param}=" in url for param in CITATION_PARAMS)
