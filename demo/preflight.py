"""Pre-flight check for the Amenda demo. Run this, then present.

    python demo/preflight.py

Checks the four things that can break a live demo, fixes the one that is
safe to fix automatically (the redline state), and tells you plainly
what to do about anything else. Does NOT spend money: it makes no LLM
calls, so it is safe to run repeatedly right before you go on.
"""
import json
import os
import subprocess
import sys

import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
PROPOSALS = os.path.join(BACKEND, "data", "proposals.json")
BASE = "http://127.0.0.1:8000"

OK, WARN, BAD = "  OK  ", " WARN ", " STOP "
results = []


def record(level, title, detail):
    results.append((level, title, detail))
    print(f"[{level}] {title}")
    if detail:
        print(f"         {detail}")


def get(path, timeout=8):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


def check_deps():
    """Missing packages are the first thing a fresh clone hits."""
    missing = []
    for mod, pkg in (("fastapi", "fastapi"), ("uvicorn", "uvicorn"),
                     ("multipart", "python-multipart"),
                     ("dotenv", "python-dotenv"), ("httpx", "httpx"),
                     ("requests", "requests"), ("bs4", "beautifulsoup4"),
                     ("pypdf", "pypdf"), ("docx", "python-docx")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        record(BAD, f"{len(missing)} Python package(s) missing",
               "Run:  pip install -r backend/requirements.txt\n"
               f"         (missing: {', '.join(missing)})")
        return
    record(OK, "all Python dependencies installed", "")


def check_env():
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        record(BAD, ".env is missing",
               "The sweep cannot run. Copy .env.example to .env and add your "
               "key:  OPENROUTER_API_KEY=sk-or-...  (.env is gitignored, so a "
               "fresh clone never has it - ask a teammate for the key).")
        return
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if "OPENROUTER_API_KEY" not in body or "sk-or-" not in body:
        record(BAD, ".env has no usable API key",
               "Expected a line OPENROUTER_API_KEY=sk-or-...")
        return
    record(OK, ".env present with an API key", "")


def check_server():
    try:
        health = get("/api/health", timeout=5)
    except (urllib.error.URLError, OSError):
        record(BAD, "server is not running",
               "Start it:  cd backend && python -m uvicorn main:app --port 8000")
        return False

    # Port 8000 might be someone else's Amenda (a teammate's laptop on the
    # same machine, an old process from another checkout). Confirm the
    # server is serving THIS working copy before trusting any other check.
    try:
        served = urllib.request.urlopen(BASE + "/", timeout=5).read()
        local = open(os.path.join(ROOT, "frontend", "index.html"), "rb").read()
        if served.strip() != local.strip():
            record(BAD, "port 8000 is serving a DIFFERENT copy of Amenda",
                   "Another uvicorn is already running - probably from an "
                   "older checkout. Stop it and restart from this folder, "
                   "or every check below describes the wrong app.")
            return False
    except Exception:
        pass  # not fatal; the health check already succeeded

    if not health.get("llm_configured"):
        record(BAD, "server is up but has no LLM key",
               "It was started before .env existed - restart it so it "
               "picks the key up.")
        return False
    record(OK, f"server up, model {health.get('model')}", "")
    return True


def check_data():
    try:
        amendments = get("/api/amendments")
        clients = get("/api/clients")
    except Exception as e:
        record(BAD, "cannot read amendments/clients", str(e))
        return
    ids = {a["id"] for a in amendments}
    cids = {c["id"] for c in clients}
    docs = sum(c.get("docCount", 0) for c in clients)
    if "a7" not in ids or "c7" not in cids:
        record(BAD, "demo scenario missing",
               "Expected amendment a7 (Workplace Fairness) and client c7 "
               "(PivotStack). Run: git checkout -- backend/data/")
        return
    record(OK, f"{len(clients)} clients, {docs} documents, "
               f"{len(amendments)} amendments (a7 + c7 present)", "")


def check_watchlist():
    try:
        w = get("/api/watchlist", timeout=45)
    except Exception as e:
        record(WARN, "watchlist did not load", f"{e} - the panel may be slow to open.")
        return
    if w.get("live_ok"):
        n = len(w.get("live_bills", []))
        record(OK, f"live scrape working ({n} bills from parliament.gov.sg)",
               "The gold 'live' tag will show.")
    else:
        record(WARN, "live scrape unavailable - using cached snapshot",
               "The demo still works. Say 'cached snapshot' if asked, "
               "do not claim it is live.")


def check_redline():
    if not os.path.exists(PROPOSALS):
        record(WARN, "no seeded redline proposal",
               "'Propose the edit' will call the LLM live (slower, and the "
               "wording will not match the deck).")
        return
    with open(PROPOSALS, encoding="utf-8") as f:
        store = json.load(f)
    p = store.get("proposals", {}).get("a7:c7d1")
    if not p:
        record(WARN, "demo redline a7:c7d1 not seeded", "")
        return
    if p.get("status") != "pending" or store.get("audit"):
        # safe to fix automatically: this is committed demo state
        subprocess.run(["git", "checkout", "--", "backend/data/proposals.json"],
                       cwd=ROOT, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(PROPOSALS, encoding="utf-8") as f:
            store = json.load(f)
        now = store.get("proposals", {}).get("a7:c7d1", {}).get("status")
        if now == "pending" and not store.get("audit"):
            record(OK, "redline reset to pending (was already approved)",
                   "The Approve moment is back.")
        else:
            record(BAD, "could not reset the redline",
                   "Run: git checkout -- backend/data/proposals.json")
        return
    record(OK, "redline pending, audit trail empty", "")


def main():
    print("\nAmenda pre-flight\n" + "-" * 52)
    check_deps()
    check_env()
    up = check_server()
    if up:
        check_data()
        check_redline()
        check_watchlist()
    else:
        check_redline()

    print("-" * 52)
    stops = [r for r in results if r[0] == BAD]
    warns = [r for r in results if r[0] == WARN]
    if stops:
        print(f"\n{len(stops)} thing(s) will break the demo. Fix before presenting:")
        for _, title, detail in stops:
            print(f"  - {title}: {detail}")
        return 1
    if warns:
        print(f"\nReady, with {len(warns)} thing(s) to be aware of:")
        for _, title, detail in warns:
            print(f"  - {title}")
        return 0
    print("\nReady to present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
