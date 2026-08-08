"""What the reader is looking at, told to the model cheaply.

The website hands over the permalink of the page the assistant was opened from.
Without it, "what did he compare it to?" has no antecedent and the assistant is a
blank box that happens to be floating over an article.

The temptation is to paste the article into the prompt. That is the expensive way
to be wrong: the longest article here is about 7,000 tokens, most of it irrelevant
to any one question, and it is paid for on *every* turn of the conversation because
the system prompt is resent each time.

What goes in instead is a brief — the title, the date, the exact `read_doc` path,
and the list of section headings. Two hundred tokens or so, and it buys more than
the full text would: the model can name the section it wants and fetch that one,
which usually removes a whole search round as well. The retrieval tools are still
there for anything the brief does not cover.
"""

from __future__ import annotations

from .corpus import Corpus, Document

# Enough to orient a model in a long article; beyond this the outline is itself
# the expensive thing. The longest article on the site has 21 sections.
MAX_HEADINGS = 40


def _normalise(url: str) -> str:
    return (url or "").strip().rstrip("/").lower()


def resolve(corpus: Corpus, url: str) -> Document | None:
    """The indexed document a permalink refers to, or None.

    Matched on the URL the corpus already stores rather than by rebuilding Hugo's
    slug rule from the path — the sync recorded the real permalink precisely so
    that nothing downstream has to guess at it a second time.
    """
    wanted = _normalise(url)
    if not wanted:
        return None
    for document in corpus.documents.values():
        if _normalise(document.url) == wanted:
            return document
    return None


def brief(document: Document) -> str:
    """A compact note for the system prompt describing the open page."""
    lines = [
        "THE READER IS CURRENTLY ON THIS PAGE",
        f"Title: {document.title}",
    ]
    if document.date:
        lines.append(f"Published: {document.date}")
    lines.append(f"read_doc path: {document.id}")

    outline = [item.strip("- ").strip() for item in document.outline if item.strip()]
    if outline:
        shown = outline[:MAX_HEADINGS]
        lines.append("")
        lines.append("Its sections, for read_doc as `path#anchor`:")
        lines.extend(f"  {name}" for name in shown)
        if len(outline) > len(shown):
            lines.append(f"  … and {len(outline) - len(shown)} more")

    lines.append("")
    lines.append(
        "Prefer this page when the question is ambiguous — 'this', 'it', 'the "
        "model', 'that number' almost certainly refer to it. Read the section you "
        "need with read_doc before answering rather than assuming its contents, "
        "and still search when the question reaches beyond this page."
    )
    return "\n".join(lines)


def apply(system_prompt: str, corpus: Corpus, url: str) -> tuple[str, Document | None]:
    """`(prompt, document)` — the prompt with a brief appended when one applies."""
    document = resolve(corpus, url)
    if document is None:
        return system_prompt, None
    return f"{system_prompt}\n\n{brief(document)}", document
