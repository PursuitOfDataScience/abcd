"""The profile registry.

There is exactly one profile here, and that is the point: this repository is a
website, and an assistant that can be pointed at a corpus the repository does not
contain is one that answers confidently from an empty index. The registry stays
because the abstraction is what keeps deployment-specific copy — prompt, cards,
placeholder, palette — out of the engine, not because a second entry is expected.
"""

from __future__ import annotations

import logging
import os

from ..profile import Profile
from . import site

logger = logging.getLogger(__name__)

PROFILES: dict[str, Profile] = {site.PROFILE.key: site.PROFILE}

# No `SAGE_PROFILE` needed on the host, and nothing it can be set to that changes
# the answer.
DEFAULT = site.PROFILE.key


def get(key: str) -> Profile:
    """Look up a profile, falling back to the default with a warning.

    Loudly rather than silently: a typo in `SAGE_PROFILE` would otherwise deploy
    the wrong assistant against the right corpus and look like a prompt bug.
    """
    if key in PROFILES:
        return PROFILES[key]
    logger.warning(
        "Unknown SAGE_PROFILE %r; using %r. Known profiles: %s",
        key, DEFAULT, ", ".join(sorted(PROFILES)),
    )
    return PROFILES[DEFAULT]


def active() -> Profile:
    return get(os.getenv("SAGE_PROFILE", DEFAULT).strip().lower() or DEFAULT)
