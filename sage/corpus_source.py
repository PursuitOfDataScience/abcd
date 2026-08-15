"""Where the corpus comes from: a local tree, or one published beside the website.

The deployment used to carry the corpus inside its own build. That made the corpus a
*code* artefact: every new article on the website needed a second commit to a second
repository before the panel could cite it, and forgetting the second one produced a
panel that resolved the newest article's permalink against an index built before that
article existed. The failure was silent, and it happened.

This module removes the coupling. `tools/build_site_corpus.py` publishes the whole
corpus as one JSON file under the website's `static/`, so Netlify serves it next to
the articles it was built from, and the deployment fetches it at start-up.
Adding an article is one push again, and the deployed build never has to change.

The added dependency is smaller than it looks: the panel is embedded in the website,
so a host that cannot serve `corpus.json` cannot serve the page the panel is on
either. Two failure modes, stated exactly, because "it falls back" and "it fails" are
both wrong on their own:

* Nothing on disk and the corpus unreachable: the panel says so and stops. It does not
  come up with an empty index, because an empty index answers every question with "the
  site does not cover that" and looks like a working assistant.
* The corpus already downloaded in this container and only the digest unreachable: it
  goes on serving what it has. That is a deliberate preference for a slightly old
  answer over no answer, it is bounded by the life of the process, and it resolves
  itself as soon as the digest is readable again.

Locally nothing changes. If the corpus tree is on disk it is used untouched, so the
tests, `render_check.py` and a development run all read the files they always did.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

import httpx

from . import config
from .profile import Profile

logger = logging.getLogger(__name__)

# A corpus path is `<source>/<relative path>.md` and nothing else. Checked rather
# than trusted because these keys are written to disk: `..` or a leading slash in a
# downloaded key would put a file outside the directory meant to hold it.
_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ /-]*$")

#: A published revision is a sha256 and nothing else. Checked rather than trusted,
#: because this string is what `resolve` verifies the corpus against: a digest that is
#: not a digest turns that check off, and it did. Measured: an empty file, an HTML page
#: served with a 200 and a truncated hash all produced a "revision" that was carried
#: through, skipped verification and served the corpus with nothing logged. A guard that
#: unusable input can switch off silently is not a guard.
_DIGEST = re.compile(r"^[0-9a-f]{64}$")

LOCAL = "local"
PUBLISHED = "published"

#: Bundle formats this deployment can read. The builder stamps one into every bundle
#: and, until now, nothing read it back.
#:
#: It matters because of what moving the corpus out actually changed. The corpus and
#: the code used to travel together in one commit to the published repository, so they
#: could not disagree about anything; now the website publishes the bundle and the
#: deployment is rebuilt separately, which is the whole point and is also the exact
#: condition under which the two can be of different vintages. This field is the
#: contract across that gap, and a contract nobody checks is a comment. Refusing a
#: format this code does not know beats guessing at it: a bundle whose shape moved
#: would otherwise be read by whatever `_unpack` happens to do with it.
SUPPORTED_BUNDLE_VERSIONS = frozenset({1})


#: The last digest each corpus URL answered with, for as long as this process lives.
#: Without it a momentary failure to read the digest returns a *different* revision
#: string, and since the index is cached under that string the app misses its own cache,
#: re-resolves, fails on the same unreachable host and shows the reader an error while a
#: perfectly good index sits in memory. Measured, not reasoned about: stopping the corpus
#: server took `published:<sha>` to `published:unknown` and `resolve` straight to
#: CorpusUnavailable. Keyed by URL so that repointing the corpus cannot inherit a digest
#: belonging to the old one.
_LAST_GOOD: dict[str, str] = {}


class CorpusUnavailable(RuntimeError):
    """The corpus is neither on disk nor fetchable, so there is nothing to index."""


def _local_paths(profile: Profile) -> dict[str, str] | None:
    """The profile's own paths, if every one of them is a directory that exists."""
    paths = profile.paths
    if paths and all(os.path.isdir(base) for base in paths.values()):
        return dict(paths)
    return None


def _url(name: str) -> str:
    base = config.SITE_CORPUS_URL.rstrip("/")
    return f"{base}/{name}"


def revision(profile: Profile) -> str:
    """A short token that changes when the corpus changes, and not otherwise.

    Used as the cache key for the index, so a new article reaches readers without a
    redeploy and without rebuilding the index on a timer. Cheap by design: the
    published digest is 65 bytes, where the corpus is most of a megabyte.

    A local corpus is keyed by its own contents for the same reason, so editing a
    file during development rebuilds the index rather than serving the old one.
    """
    local = _local_paths(profile)
    if local is not None:
        digest = hashlib.sha256()
        for _source, base in sorted(local.items()):
            for root, _dirs, names in os.walk(base):
                for name in sorted(names):
                    full = Path(root) / name
                    digest.update(str(full.relative_to(base)).encode())
                    try:
                        digest.update(full.read_bytes())
                    except OSError:
                        continue
        return f"{LOCAL}:{digest.hexdigest()[:16]}"

    if not config.SITE_CORPUS_URL:
        return f"{PUBLISHED}:unconfigured"
    try:
        # `no-cache` asks for revalidation rather than forbidding storage. Measured
        # rather than assumed: Netlify already answers static files with
        # `public,max-age=0,must-revalidate` and an ETag, so today this changes nothing
        # and costs a 304. It stays because the failure it prevents is the quiet one,
        # and because it should not depend on a host's default never changing: a cache
        # serving yesterday's 65 bytes would leave the panel citing yesterday's corpus
        # with nothing looking wrong. `resolve` no longer takes the corpus on trust
        # either; it checks the bytes against this digest.
        response = httpx.get(
            _url("corpus.sha256"), timeout=config.SITE_DIGEST_TIMEOUT,
            headers={"Cache-Control": "no-cache"}, follow_redirects=True,
        )
        response.raise_for_status()
        # The first whitespace-delimited token, so `sha256sum`'s own `<hash>  <file>`
        # output is accepted deliberately rather than by the accident of a hash being
        # exactly the 64 characters a `[:64]` slice used to take.
        body = response.text.strip()
        digest = body.split()[0] if body else ""
        if not _DIGEST.match(digest):
            raise ValueError(f"not a sha256: {body[:48]!r}")
        _LAST_GOOD[config.SITE_CORPUS_URL] = digest
        return f"{PUBLISHED}:{digest}"
    except Exception as exc:  # noqa: BLE001 - any failure means "unknown revision"
        # Not fatal. The revision this returns is the index's cache key, so returning
        # the last one that worked is what lets the app go on answering from the index
        # it already built: a slightly old answer in preference to no answer, bounded by
        # the life of the process, and resolved the moment the digest is readable again.
        # Only when there has never been a good one is the revision genuinely unknown,
        # and then `resolve` is where the absence has to be raised.
        previous = _LAST_GOOD.get(config.SITE_CORPUS_URL)
        if previous:
            logger.warning(
                "Could not read the published corpus digest (%s); keeping revision %s",
                exc, previous[:12],
            )
            return f"{PUBLISHED}:{previous}"
        logger.warning("Could not read the published corpus digest: %s", exc)
        return f"{PUBLISHED}:unknown"


def _cache_root() -> Path:
    """Where downloaded corpora live, or a temporary directory if that is not writable.

    The configured default is under `/tmp`, which every host this runs on allows. The
    fallback is here because "the corpus is unavailable" is a bad thing to tell a
    reader on account of a read-only directory, and because a host that forbids the
    configured path is exactly the kind of difference that does not show up until it is
    in production.
    """
    configured = Path(config.SITE_CORPUS_CACHE)
    try:
        configured.mkdir(parents=True, exist_ok=True)
        probe = configured / ".writable"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return configured
    except OSError as exc:
        fallback = Path(tempfile.mkdtemp(prefix="sage-corpus-"))
        logger.warning(
            "Corpus cache %s is not writable (%s); using %s for this process",
            configured, exc, fallback,
        )
        return fallback


def _forget_other_revisions(cache: Path, keep: str) -> None:
    """Delete corpora for revisions no longer in use.

    Each revision unpacks a couple of megabytes into its own directory and nothing
    removed the last one, so a container that runs for weeks accumulated one per
    article. Only the revision being served can ever be wanted: the index is keyed on
    the digest, and a digest never comes back.
    """
    for entry in cache.iterdir():
        if entry.name == keep or not entry.is_dir():
            continue
        shutil.rmtree(entry, ignore_errors=True)


def _unpack(blob: bytes, into: Path) -> int:
    payload = json.loads(blob)
    # Absent means the first format, which is what every bundle written so far holds
    # even though they all state it. Present and unknown is a deployment too old for
    # the corpus it just fetched, and the remedy is on the deployment's side.
    version = payload.get("version", 1)
    if version not in SUPPORTED_BUNDLE_VERSIONS:
        raise CorpusUnavailable(
            f"the published corpus is format {version!r} and this deployment reads "
            f"{sorted(SUPPORTED_BUNDLE_VERSIONS)}; re-export and push the deployed "
            f"build so it can read what the website is publishing"
        )
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise CorpusUnavailable("the published corpus contains no files")

    written = 0
    for key, text in sorted(files.items()):
        if not _SAFE_KEY.match(key) or ".." in key.split("/"):
            raise CorpusUnavailable(f"refusing a corpus path that is not relative: {key!r}")
        target = into / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written += 1
    return written


def _expected_digest(rev: str) -> str:
    """The sha256 a fetched corpus must have, or "" when there is nothing to check."""
    candidate = rev.split(":", 1)[1].strip() if ":" in rev else ""
    return candidate if _DIGEST.match(candidate) else ""


#: Fetches of a corpus whose bytes do not match the digest that asked for them. Three,
#: because the usual cause is a caching layer a moment behind and the second request
#: carries `no-cache`; more than that is waiting out a failure rather than a delay.
ATTEMPTS = 3


def _fetch_verified(url: str, expected: str) -> bytes:
    """The published corpus, checked against the digest that asked for it.

    The index is keyed on the digest, so a fetch that returns the wrong bytes is not a
    transient wrong answer: those bytes are filed under that digest and served until
    the corpus changes again. A cache anywhere in the path makes that possible, because
    a cache is keyed on the URL and this URL is the same for every revision. Comparing
    what arrived against what was asked for costs one hash of a file already in memory
    and removes the whole class.

    A mismatch is usually a caching layer a moment behind, so it is retried before it
    is called a failure. Persisting past that, it is raised rather than served: an
    error a reader can see beats an assistant confidently citing an older site.
    """
    last = ""
    for attempt in range(ATTEMPTS):
        try:
            response = httpx.get(url, timeout=config.SITE_CORPUS_TIMEOUT,
                                 follow_redirects=True,
                                 headers={"Cache-Control": "no-cache"} if attempt else {})
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - reported to the reader verbatim
            raise CorpusUnavailable(f"could not fetch {url}: {exc}") from exc
        if not expected:
            return response.content
        got = hashlib.sha256(response.content).hexdigest()
        if got == expected:
            return response.content
        last = got
        remaining = ATTEMPTS - attempt - 1
        logger.warning("Published corpus is %s but the digest asked for %s; %s",
                       got[:12], expected[:12],
                       f"{remaining} attempt(s) left" if remaining else "giving up")
        # Only between attempts. Sleeping after the last one delayed an error the
        # reader was going to see anyway by the longest backoff of the three.
        if remaining:
            time.sleep(0.4 * (attempt + 1))
    raise CorpusUnavailable(
        f"{url} does not match the published digest (wanted {expected[:12]}, "
        f"got {last[:12]}); refusing to serve it as that revision"
    )


def resolve(profile: Profile, rev: str = "") -> tuple[dict[str, str], str]:
    """Return the source-name to directory map to index, and where it came from.

    Prefers a local tree. Otherwise downloads the published bundle into a directory
    named for its revision, so a restart with an unchanged corpus reuses it and a
    changed one cannot be served from the old directory.
    """
    local = _local_paths(profile)
    if local is not None:
        return local, LOCAL

    if not config.SITE_CORPUS_URL:
        raise CorpusUnavailable(
            "no corpus on disk and SAGE_SITE_CORPUS_URL is not set, so there is "
            "nothing to index"
        )

    token = re.sub(r"[^A-Za-z0-9]", "", rev)[-32:] or "current"
    cache = _cache_root()
    root = cache / token
    if not root.is_dir():
        url = _url("corpus.json")
        blob = _fetch_verified(url, _expected_digest(rev))

        # Unpacked beside the destination and moved into place in one step, so the
        # directory a reader consults either does not exist or holds every article.
        # Writing the files where they will be read and marking them complete
        # afterwards leaves a window in which another process indexes a truncated
        # article, and a truncated article answers questions rather than raising.
        # `rename` also settles the race between two processes fetching one revision:
        # the first wins and the second throws its copy away, same bytes either way.
        staging = cache / f".staging-{token}-{os.getpid()}"
        shutil.rmtree(staging, ignore_errors=True)
        try:
            written = _unpack(blob, staging)
        except CorpusUnavailable:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        except Exception as exc:  # noqa: BLE001
            shutil.rmtree(staging, ignore_errors=True)
            raise CorpusUnavailable(f"could not read {url}: {exc}") from exc
        try:
            os.rename(staging, root)
            logger.warning("Fetched the published corpus: %d files from %s",
                           written, url)
        except OSError:
            # Another process published this revision while this one unpacked.
            shutil.rmtree(staging, ignore_errors=True)
        _forget_other_revisions(cache, keep=root.name)

    # The bundle's keys are `<source>/…`, and its sources are the profile's, so each
    # source is simply the directory of that name. Missing ones are left out rather
    # than invented, which lets `corpus.build` log the gap it already logs.
    paths = {
        name: str(root / name) for name in profile.paths if (root / name).is_dir()
    }
    if not paths:
        raise CorpusUnavailable(
            f"the published corpus has none of the expected sources "
            f"({', '.join(sorted(profile.paths))})"
        )
    return paths, PUBLISHED
