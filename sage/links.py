"""The citations a model emits: point them at real URLs, drop the duplicate list.

The previous version sent *every* `web/` citation to the user-guide root on the
stated grounds that "website pages have no stable per-page docs URL". They do —
each scraped file records it on line 1 — and they span five different hosts, so a
Skyway or Beagle3 answer was being cited to the Midway user guide.
"""

from __future__ import annotations

import re

from . import cite, profiles
from .corpus import Corpus
from .profile import MARKDOWN

_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
_ATTR_LIST = re.compile(r"\{:[^}]*\}")
_EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#")


def resolve(target: str, corpus: Corpus) -> str | None:
    """Best URL for an internal doc reference, or None if it cannot be resolved."""
    target = target.strip()
    if not target:
        return None

    chunk = corpus.chunk(target)
    if chunk is not None:
        # The inline citations are the ones read in the flow of an answer, so they
        # get the same treatment as the Sources strip: the link points at the
        # section *and* says which passage in it was used. See `sage/cite.py`.
        return cite.url_for(chunk)

    base, _, anchor = target.partition("#")
    base = base.strip().lstrip("./")

    document = corpus.document(base)
    if document is None:
        for source in ("docs", "web"):
            document = corpus.document(f"{source}/{base}")
            if document is not None:
                break

    if document is None:
        # A bare or relative filename: match on path suffix.
        candidates = [
            item
            for item in corpus.documents.values()
            if item.path == base or item.path.endswith(f"/{base}")
        ]
        document = candidates[0] if len(candidates) == 1 else None

    if document is None:
        return None
    profile = corpus.profile or profiles.active()
    # A page that carries its own URL (a scraped page, a synced blog post) keeps
    # it; anything else is mapped from its path by the profile.
    if document.url and profile.kind(document.source) != MARKDOWN:
        return f"{document.url}#{anchor}" if anchor else document.url
    return profile.url_for(document.source, document.path, anchor)


def compact_citations(text: str, corpus: Corpus) -> tuple[str, dict[str, int]]:
    """Shrink the inline citations to numbered markers, and say which is which.

    A model cites by writing the section's title into the link, so a sentence arrives
    as "...for each card a job holds [Graphics cards, where there are graphics
    cards](post/…/slurmwatch.md#graphics-cards-where-there-are-graphics-cards)." The
    citation is then longer than the clause it supports and the eye has to step over it
    to finish the sentence. Numbered markers say the same thing in one character.

    Numbered by **first appearance in the answer**, not by the order of the Sources
    strip. That is what makes the same numbering hold while the answer is still
    streaming: a marker is assigned when its citation first arrives and nothing later in
    the text can renumber what is already on screen. The strip is numbered from the
    mapping returned here, so the two agree without either having to be built first.

    A link is shrunk when the URL it resolves to points at a passage, which is the
    same question `cite.points_at_a_passage` answers for the stylesheet. Both have to
    ask it the same way, and for one commit they did not: this shrank anything that
    resolved to a chunk while the stylesheet matched on `sage-cite` alone, so a section
    with no anchor of its own became a bare "1" in ordinary link blue with no pill and
    nothing to say it was a citation. Asking the finished URL rather than the chunk is
    what keeps the two from drifting apart again.

    A link to a whole page, carrying neither an anchor nor a quote, keeps the words the
    model wrote: a bare number pointing at nothing in particular is a footnote to
    nothing.

    Returns the rewritten text with the original targets still in place, so
    `fix_links` runs afterwards exactly as it did before and resolves them as usual.
    """
    numbering: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        target = match.group(2)
        if target.startswith(_EXTERNAL):
            return match.group(0)
        chunk = corpus.chunk(target.strip())
        if chunk is None or not cite.points_at_a_passage(cite.url_for(chunk)):
            return match.group(0)
        number = numbering.setdefault(chunk.id, len(numbering) + 1)
        return f"[{number}]({target})"

    return _MARKDOWN_LINK.sub(replace, text), numbering


def fix_links(text: str, corpus: Corpus) -> str:
    """Point internal links at published URLs; unlink what cannot be resolved."""
    text = _ATTR_LIST.sub("", text)

    def replace(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if target.startswith(_EXTERNAL):
            # A bare in-page anchor has nowhere to go in a chat transcript.
            return label if target.startswith("#") else match.group(0)
        url = resolve(target, corpus)
        if url:
            return f"[{label}]({url})"
        home = (corpus.profile or profiles.active()).home_url
        return f"[{label}]({home})" if home else label

    return _MARKDOWN_LINK.sub(replace, text)


# `Sources:`, `**References:**`, `**Citations**:`, `## Sources` — every decoration a
# model puts round the word, matched by treating `*_#` and space as noise either side
# of it. Both spellings of the bold form turn up, which is why the colon is allowed to
# fall on either side of the markup rather than in one fixed place.
_LABEL = r"(?:sources?|references?|citations?)"
_MARKUP = r"[*_#\s]*"
_LABEL_LINE = re.compile(
    rf"^\s{{0,3}}{_MARKUP}{_LABEL}{_MARKUP}(?P<colon>:?){_MARKUP}(?P<rest>.*)$",
    re.IGNORECASE,
)
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_BARE_LINK = re.compile(r"^\s*\[[^\]]+\]\([^)]*\)[\s,;.]*$")
_FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
_RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")


def _footer_label(line: str) -> str | None:
    """The text after a `Sources:`-style label, `None` if this is not such a line.

    A payload without a colon is prose — "Sources of variation include …" opens with
    the word and is a sentence, not a footer — so the colon is what licenses cutting
    anything that sits on the same line.
    """
    match = _LABEL_LINE.match(line)
    if not match:
        return None
    rest = match.group("rest").strip()
    if rest and not match.group("colon"):
        return None
    return rest


def _is_citation_line(line: str) -> bool:
    """A line that could only be part of a citation list, never of an answer.

    Deliberately narrow. `- Run \\`sbatch job.sh\\`` is a step, not a citation, so a
    code span disqualifies a line; so does the length of a real paragraph. What is
    left is bullets of titles and bare links, which is what the footer is made of.
    """
    if _FENCE.match(line) or "`" in line:
        return False
    stripped = line.strip()
    if stripped.startswith("#"):
        return False
    if _BARE_LINK.match(line) or _LIST_ITEM.match(line):
        return True
    return len(stripped) <= 120


def strip_source_footer(text: str) -> str:
    """Remove a trailing "Sources:" list the model wrote for itself.

    Every answer already gets a Sources strip built from the chunks that were
    actually retrieved, so a model that also signs off with `Sources: A, B` prints
    the same citations twice, three lines apart. The system prompt asks for inline
    links and no footer; across nine models that holds on most turns and not all of
    them, so the footer comes off here too. Prompt and strip together are what makes
    the duplicate stop.

    Only a *trailing* block goes, and only one labelled Sources / References /
    Citations. The inline `[Section title](path)` links inside the prose are the
    citation format this app wants and are untouched.
    """
    if not text or not text.strip():
        return text

    lines = text.splitlines()
    last = len(lines) - 1
    while last >= 0 and not lines[last].strip():
        last -= 1

    cut = None
    if _footer_label(lines[last]):
        # The whole list sits on the label's own line: that one line is the footer.
        cut = last
    else:
        # Otherwise the list is underneath a label of its own. Only the last such
        # label is considered — scanning further back to find a block that happens
        # to look like citations is how a strip like this eats half an answer.
        for idx in range(last, -1, -1):
            if _footer_label(lines[idx]) is None:
                continue
            if all(_is_citation_line(line) for line in lines[idx + 1 : last + 1]):
                cut = idx
            break

    if cut is None:
        return text

    kept = lines[:cut] + lines[last + 1 :]
    # Models fence the footer off with a rule; without the footer it leads nowhere.
    while kept and (not kept[-1].strip() or _RULE.match(kept[-1])):
        kept.pop()
    # An answer that was *only* a footer is a failure of the model, not something to
    # blank out: a duplicate Sources strip beats an empty bubble.
    if not any(line.strip() for line in kept):
        return text
    return "\n".join(kept)
