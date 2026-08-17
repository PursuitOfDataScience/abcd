"""Make sure the app is awake, and wake it if it is not.

Run on a schedule, this is what stops readers meeting a sleeping app. It is deliberately
layered, cheapest first, and only the last layer is authoritative:

1. `GET /~/+/_stcore/health` returns plain `ok` from the app's own container, with no
   redirects and no cookies. That is the honest liveness test and it is the reason this
   file exists at all. The URL the first version of this keepalive used, the app root,
   is served by the *proxy*: it answers 200 with ~9.3 kB of React shell whether or not
   the app is running, so it can never report sleep. (`/~/+/` is where Community Cloud
   mounts the app. `/_stcore/health` at the root is the proxy again.)

2. `GET /api/v2/app/status` is readable anonymously and reports the platform's own view.
   Its `status` field is logged verbatim rather than interpreted, because the only value
   measured so far is 5, from a running app. Once a run catches a sleeping one the log
   will say what sleep looks like, which is better than guessing at an enum today.

3. `POST /api/v2/app/resume` is what the shell's own "Yes, get this app back up!" button
   calls: `resumeAppFromSubdomain()` in its bundle, a POST with no body and no auth. It
   answered 403 when tried against a *running* app, which is consistent either with
   "already running" or with "viewers may not", and those cannot be told apart until the
   app is asleep. So this is attempted and its result logged, and nothing depends on it.
   If it turns out to work, the whole schedule can move off GitHub Actions and onto a
   Netlify scheduled function, which would remove the sixty-day auto-disable that is
   currently this arrangement's expiry date.

4. A real browser, which is the guarantee. It clicks the wake control and waits out the
   cold start, and it is the only layer that cannot be wrong about what a reader sees.

Then it asserts: the app view rendered, the composer exists, no corpus error. A run is
red when the app is not serving. The version this replaces could not fail: its curl died
at 50 redirects with exit 47, `|| echo "000"` swallowed that, and every run from the
first to the last was green while readers met a sleeping app every morning.

No question is asked, so no model quota is spent. The public URL shares your provider
credit with every visitor and a scheduled ping must not touch it.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "https://yu-site-assistant.streamlit.app/").rstrip("/")

#: How long to wait for a cold start. Measured 2026-08-17: a wake from sleep took
#: fourteen minutes, of which the app's own startup is about 1.2 seconds. The rest is
#: Community Cloud discarding the container and rebuilding the environment, and a cold
#: `pip install` of this app's three requirements is 78 seconds on hardware considerably
#: faster than a Cloud instance. Generous on purpose: a budget shorter than a real wake
#: turns a slow success into a red run, and this file exists because a check that
#: misreports is worse than no check.
WAKE_BUDGET = int(os.environ.get("WAKE_BUDGET", "900"))

HEALTH = f"{APP_URL}/~/+/_stcore/health"
STATUS = f"{APP_URL}/api/v2/app/status"
RESUME = f"{APP_URL}/api/v2/app/resume"

SLEEP_PAGE = re.compile(r"gone to sleep|Zzzz|get this app back up", re.I)
WAKE_SELECTORS = (
    '[data-testid="wakeup-button-viewer"]',
    '[data-testid="wakeup-button-owner"]',
    'text="Yes, get this app back up!"',
)
APP_VIEW = '[data-testid="stAppViewContainer"]'


def _get(url: str, timeout: int = 30) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "keepalive-probe"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(4096).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(1024).decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - unreachable is a result, not a crash
        return 0, f"{type(exc).__name__}: {exc}"


def _post(url: str, timeout: int = 45) -> tuple[int, str]:
    request = urllib.request.Request(
        url, data=b"", method="POST",
        headers={"User-Agent": "keepalive-probe", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(1024).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(1024).decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def is_serving() -> bool:
    code, body = _get(HEALTH)
    return code == 200 and body.strip() == "ok"


def platform_status() -> str:
    """The platform's own status field, verbatim. For the log, not for a decision."""
    code, body = _get(STATUS)
    if code != 200:
        return f"http {code}"
    try:
        return json.dumps({k: json.loads(body).get(k) for k in
                           ("status", "platformStatus", "isCpuThrottled",
                            "streamlitVersion")})
    except Exception:  # noqa: BLE001
        return body[:200]


def app_frame(page):
    """The frame the app is actually in.

    Community Cloud nests the app under `/~/+/` inside the shell, so the app view is
    never in the top-level document. Looking for it there finds nothing and reads
    exactly like an app that failed to start.
    """
    for frame in page.frames:
        try:
            if frame.query_selector(APP_VIEW):
                return frame
        except Exception:  # noqa: BLE001 - a frame can navigate mid-query
            continue
    return None


def main() -> int:
    started = time.monotonic()

    def at() -> str:
        return f"[{time.monotonic() - started:6.1f}s]"

    serving = is_serving()
    print(f"{at()} health   {HEALTH} -> {'ok' if serving else 'NOT ok'}")
    print(f"{at()} status   {platform_status()}")

    if not serving:
        code, body = _post(RESUME)
        print(f"{at()} resume   POST -> http {code} {body[:160]!r}")
        print(f"{at()}          (logged only; the browser below is the guarantee)")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1000, "height": 800})
        print(f"{at()} GET      {APP_URL}/")
        page.goto(f"{APP_URL}/", wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(6_000)

        if SLEEP_PAGE.search(page.inner_text("body")[:2_000]):
            for selector in WAKE_SELECTORS:
                button = page.query_selector(selector)
                if button:
                    print(f"{at()} asleep;  clicking {selector}")
                    button.click()
                    break
            else:
                print(f"{at()} asleep but no wake control is offered")
        else:
            print(f"{at()} no sleep page")

        deadline = started + WAKE_BUDGET
        frame = None
        while time.monotonic() < deadline:
            frame = app_frame(page)
            if frame is not None:
                break
            page.wait_for_timeout(5_000)

        if frame is None:
            print(f"{at()} FAILED: no app view within {WAKE_BUDGET}s")
            print("  top-level text:", repr(page.inner_text("body")[:300]))
            browser.close()
            return 1

        print(f"{at()} app view rendered in {frame.url[:100]}")

        # The composer, because an app view that renders empty is what a boot that died
        # halfway looks like, and that would otherwise pass as awake.
        composer = None
        while time.monotonic() < deadline:
            composer = frame.query_selector("textarea[placeholder]")
            if composer:
                break
            page.wait_for_timeout(2_000)

        if composer is None:
            print(f"{at()} FAILED: app view has no composer")
            print("  app frame text:", repr(frame.inner_text("body")[:300]))
            browser.close()
            return 1

        print(f"{at()} composer {composer.get_attribute('placeholder')!r}")

        if "could not be loaded" in frame.inner_text("body"):
            print(f"{at()} FAILED: the app is up but its corpus is unreachable")
            browser.close()
            return 1

        print(f"{at()} awake and serving")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
