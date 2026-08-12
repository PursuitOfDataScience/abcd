"""The engine behind the Ask panel on this website. Nothing else.

**Read the name with care: `sage` is not a separate project.** It is the assistant that
answers questions about youzhi.netlify.app, and this package is the whole of it apart
from the Streamlit view in `../app.py`. The name is inherited from the deployment this
was forked from, which is also where the maroon in `static/app.css` comes from, and it
has been mistaken for another codebase more than once. If that ever costs more than it
saves, renaming it is contained: about twenty imports, the module digest in
`tools/export_app.py`, and three documents.

There is exactly one thing in the world that runs this code: the panel docked beside the
articles on that site. `sage/profiles/` holds one profile, the second was removed, and
`tools/export_app.py` refuses to publish a tree containing any other. So a change here
reaches that panel and nothing else.

The package is deliberately split so that everything except the Streamlit view is
importable without Streamlit, which is what makes the retrieval layer and the agent
loop unit-testable.

Which corpus it answers from is a `Profile`, not a property of the package. Nothing
outside `sage/profiles/` should name one, because a deployment that can be pointed at a
corpus it does not have is a deployment that answers confidently from an empty index.
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
