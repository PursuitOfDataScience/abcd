"""Sage — a grounded, citation-first documentation assistant.

The package is deliberately split so that everything except the Streamlit view is
importable without Streamlit, which is what makes the retrieval layer and the agent
loop unit-testable.

Which corpus it answers from is a `Profile`, not a property of the package. This
copy carries exactly one — `profiles.site`, the personal-website assistant — and
nothing outside `sage/profiles/` should name it. The upstream project keeps others;
they are deliberately not vendored here, because a deployment that can be pointed
at a corpus it does not have is a deployment that answers confidently from an empty
index.
"""

__all__ = [
    "cite",
    "config",
    "context",
    "corpus",
    "engine",
    "files",
    "history",
    "links",
    "llm",
    "normalize",
    "profile",
    "profiles",
    "search",
    "sitehtml",
]
