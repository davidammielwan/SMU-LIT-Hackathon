"""Feature 1 — horizon scanning.

parliament.gov.sg 'Bills Introduced' is server-rendered and scrapeable live.
PAIR Search and eGazette are JS applications (verified 5 Sep 2026: app shells
with no content in the HTML; SSO returns 403 to non-browser clients), so those
sources are served from fixtures with the same parser interface. Wiring a
headless browser (Playwright) in their fetch functions is the production path.
"""
import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures")
BILLS_URL = "https://www.parliament.gov.sg/parliamentary-business/bills-introduced"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_bills_live(timeout: int = 15) -> list[dict]:
    """Scrape the Bills Introduced list. Returns [] on any failure so the
    caller can fall back to the cached fixture."""
    try:
        html = requests.get(BILLS_URL, headers=UA, timeout=timeout).text
    except Exception:
        html = ""
    bills = parse_bills(html) if html else []
    if not bills:  # offline / DOM changed: fall back to the cached snapshot
        fixture = os.path.join(FIXTURES, "parliament_bills.html")
        if os.path.exists(fixture):
            with open(fixture, encoding="utf-8") as f:
                bills = parse_bills(f.read())
            for b in bills:
                b["source"] = "parliament.gov.sg (cached snapshot)"
    return bills


def parse_bills(html: str) -> list[dict]:
    """Each bill renders as: <title (PDF...)> | Bill No: | N/YYYY |
    Date Introduced: | dd.mm.yyyy | Date of 2nd Reading: | dd.mm.yyyy |
    Date Passed: | [dd.mm.yyyy]. Parse from the flattened text."""
    soup = BeautifulSoup(html, "html.parser")
    # Map bill title -> PDF href from the anchor tags
    pdf_by_title = {}
    for a in soup.find_all("a", href=True):
        if ".pdf" not in a["href"].lower():
            continue
        label = a.get_text(" ", strip=True)
        m = re.match(r"(.*?Bill)\s*\(PDF", label)
        if m:
            pdf_by_title[m.group(1).strip()] = a["href"]

    text = soup.get_text("|", strip=True)
    pattern = re.compile(
        r"([A-Z][^|]{5,150}?Bill)\s*\(PDF[^|]*\)\|Bill No:\|(\d{1,2}/\d{4})\|"
        r"Date Introduced:\|(\d{2}\.\d{2}\.\d{4})\|Date of 2nd Reading:\|"
        r"(\d{2}\.\d{2}\.\d{4})?\|?Date Passed:\|(\d{2}\.\d{2}\.\d{4})?")
    bills = []
    for m in pattern.finditer(text):
        title, no, introduced, second, passed = m.groups()
        name = title.strip()
        bills.append({
            "bill_name": name,
            "bill_no": no,
            "introduced": _iso(introduced),
            "second_reading": _iso(second) if second else None,
            "passed": _iso(passed) if passed else None,
            "status": "Passed" if passed else (
                "Awaiting 2nd reading" if second else "Introduced"),
            "pdf_url": pdf_by_title.get(name),
            "source": "parliament.gov.sg (live)",
        })
    return bills[:25]


def _iso(d: str) -> str:
    return datetime.strptime(d, "%d.%m.%Y").date().isoformat()


def get_bills_enriched(limit: int = 6) -> list[dict]:
    """Live bills with their PDFs downloaded and parsed (cached after first run)."""
    from . import bill_pdf
    return [bill_pdf.enrich(b) for b in fetch_bills_live()[:limit]]


def get_watchlist() -> dict:
    """Watchlist = live parliament bills merged with the curated Hansard
    analysis (minister commencement signals) from fixtures/seed data."""
    with open(os.path.join(FIXTURES, "..", "amendments", "watchlist.json"),
              encoding="utf-8") as f:
        curated = json.load(f)
    live = get_bills_enriched()
    live_names = {b["bill_name"] for b in live}
    # Mark curated entries that the live scrape corroborates
    for w in curated:
        w["live_corroborated"] = any(
            w.get("bill_name") and w["bill_name"].split(" (")[0] in n
            for n in live_names)
    return {"curated": curated, "live_bills": live,
            "live_ok": bool(live)}
