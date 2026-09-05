"""Download and parse a Bill PDF from parliament.gov.sg.

The bills listing gives names and dates; the PDF gives the substance — the
long title (what the Act does), the short-title-and-commencement clause (when
it starts, or that it is left to the Minister), and the amended provisions.
"""
import io
import os
import re

import requests
from pypdf import PdfReader

CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures", "bills")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE = "https://www.parliament.gov.sg"


# The heading letter-spaces in the PDF ("EXPLANA TORY ST A TEMENT"), so match
# it whitespace-tolerantly rather than as a literal string.
EXPL_RE = re.compile(
    r"E\s*X\s*P\s*L\s*A\s*N\s*A\s*T\s*O\s*R\s*Y\s+S\s*T\s*A\s*T\s*E\s*M\s*E\s*N\s*T",
    re.I)


def clean_pdf_text(text: str) -> str:
    """PDF extraction leaves non-breaking hyphens, ligatures and smart quotes
    that render as mojibake downstream. Normalise them to plain ASCII."""
    for bad, good in (("‑", "-"), ("‐", "-"), ("–", "-"),
                      ("—", " - "), ("‘", "'"), ("’", "'"),
                      ("“", '"'), ("”", '"'), (" ", " "),
                      ("ﬁ", "fi"), ("ﬂ", "fl")):
        text = text.replace(bad, good)
    return text


def extract_explanatory_statement(text: str) -> str:
    """Return the Explanatory Statement section: the purpose paragraph plus the
    clause-by-clause notes that follow it. This is where Parliament says, in
    plain English, what the Bill actually does."""
    m = EXPL_RE.search(text)
    if not m:
        return ""
    return text[m.end():].strip()


def fetch_pdf_text(url: str, bill_no: str | None = None) -> str:
    """Fetch a bill PDF and extract the full text. The Explanatory Statement
    sits at the END of a Bill, so the whole document is read. Cached to disk so
    repeat runs and the demo do not depend on the network."""
    if url.startswith("/"):
        url = BASE + url
    os.makedirs(CACHE, exist_ok=True)
    key = (bill_no or url.rsplit("/", 1)[-1]).replace("/", "-") + ".txt"
    cached = os.path.join(CACHE, key)
    if os.path.exists(cached):
        with open(cached, encoding="utf-8") as f:
            return f.read()
    try:
        r = requests.get(url, headers=UA, timeout=90)
        r.raise_for_status()
        reader = PdfReader(io.BytesIO(r.content))
        text = clean_pdf_text(
            "\n".join(p.extract_text() or "" for p in reader.pages))
    except Exception:
        return ""
    with open(cached, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def parse_bill(text: str) -> dict:
    """Pull the structured facts a lawyer needs out of the bill text."""
    flat = re.sub(r"\s+", " ", text)

    long_title = None
    m = re.search(r"intituled\s+(An Act .*?)\s*Be it enacted", flat, re.I)
    if m:
        long_title = m.group(1).strip()

    # "Short title and commencement 1. This Act is the ... and comes into
    # operation on ..." — capture the whole clause 1.
    commencement_clause = None
    m = re.search(
        r"Short title and commencement\s*(1\..{0,600}?)(?:\s*2\.|$)", flat, re.I)
    if m:
        commencement_clause = m.group(1).strip()

    # Classify how the Act commences
    signal, note = "not_stated", (
        "The Bill does not state a commencement date and no ministerial "
        "statement was located. Commencement unknown.")
    if commencement_clause:
        c = commencement_clause.lower()
        if re.search(r"appointed by the minister|the minister may.*appoint|"
                     r"on a date that the minister", c):
            signal = "minister_appointed"
            note = ("Commencement is left to a date the Minister appoints by "
                    "notification - no fixed date yet.")
        else:
            d = re.search(r"comes? into operation on (\d{1,2} \w+ \d{4})", c)
            if d:
                signal, note = "fixed", f"Bill fixes commencement at {d.group(1)}."
            elif "date of publication" in c or "upon publication" in c:
                signal = "on_publication"
                note = "Commences on the date of publication in the Gazette."

    amended_acts = sorted(set(re.findall(
        r"\b([A-Z][A-Za-z()' ]{4,60}? Act(?: \d{4})?)\b", long_title or "")))

    return {
        "long_title": long_title,
        "commencement_clause": commencement_clause,
        "commencement_signal": signal,
        "commencement_note": note,
        "amended_acts": amended_acts,
        "chars_extracted": len(text),
    }


def enrich(bill: dict, with_digest: bool = True) -> dict:
    """Given a bill dict from the listing (with pdf_url), attach parsed PDF
    facts and — when enabled — the Explanatory Statement digest."""
    if not bill.get("pdf_url"):
        return bill
    text = fetch_pdf_text(bill["pdf_url"], bill.get("bill_no"))
    if not text:
        return {**bill, "pdf_parsed": False}
    out = {**bill, "pdf_parsed": True, **parse_bill(text)}
    statement = extract_explanatory_statement(text)
    out["has_explanatory_statement"] = bool(statement)
    if with_digest and statement:
        from analysis import bill_digest
        out["digest"] = bill_digest.digest(
            statement, bill["bill_name"], (bill.get("bill_no") or "").replace("/", "-"))
    return out
