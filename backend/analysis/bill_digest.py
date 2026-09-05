"""Turn a Bill's Explanatory Statement into a lawyer-facing digest:
a plain summary of the Bill's purpose, and the 3 provisions that actually
carry legislative effect for a firm's clients.

Every Singapore Bill ends with an EXPLANATORY STATEMENT: an opening paragraph
stating the Bill's purposes, then clause-by-clause notes. That section is the
authoritative plain-English account of what the Bill does, written by
Parliament itself — so the digest is grounded in it rather than in the model's
own reading of the operative text.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm import chat_json, LLMNotConfigured

CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures", "digests")

SYSTEM = """You are a Singapore legal analyst briefing a law firm partner on a
Bill before Parliament. You are given the Bill's EXPLANATORY STATEMENT — the
opening paragraph stating its purposes, then clause-by-clause notes.

Produce:

1. "purpose" — 2 to 3 sentences, plain English, from the OPENING PARAGRAPH:
   what this Bill seeks to do and why. No legalese, no clause numbers.

2. "main_provisions" — EXACTLY 3, the provisions carrying real legislative
   effect for ordinary clients of a law firm (businesses and individuals).

   INCLUDE provisions that change what someone must do, may do, or is liable
   for: new duties, new thresholds, new rights, new offences or penalties, new
   filing or disclosure requirements, changed time limits.

   EXCLUDE, always: amendments to definitions; changes to terminology or
   headings; editorial, drafting or "for accuracy" amendments; consequential
   amendments to other Acts; saving and transitional provisions; anything
   described as clarifying existing law without changing it.

   Rank by how much the provision would affect a normal client. If the Bill
   genuinely has fewer than 3 substantive provisions, repeat none — return
   what exists and note it in "note".

   For each: "clause" (e.g. "Clause 12"), "heading" (max 8 words),
   "effect" (1-2 sentences: what changes in practice), and
   "who_it_affects" (the kind of client this bites on).

3. "note" — optional, one sentence, only if something needs flagging (e.g.
   fewer than 3 substantive provisions found).

Return ONLY JSON:
{"purpose": "...", "main_provisions": [{"clause": "...", "heading": "...",
 "effect": "...", "who_it_affects": "..."}], "note": "..."}"""


def digest(explanatory_statement: str, bill_name: str,
           cache_key: str | None = None, refresh: bool = False) -> dict:
    """Summarise a Bill's Explanatory Statement. Cached on disk by bill."""
    if not explanatory_statement.strip():
        return {"error": "No Explanatory Statement found in this PDF."}

    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, (cache_key or bill_name).replace("/", "-") + ".json")
    if os.path.exists(path) and not refresh:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # Normalise whitespace; the statement carries all the signal we need and
    # keeps the prompt small.
    text = re.sub(r"\s+", " ", explanatory_statement)[:24000]
    try:
        result = chat_json(SYSTEM, f"BILL: {bill_name}\n\nEXPLANATORY STATEMENT\n{text}")
    except LLMNotConfigured as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Digest failed: {e}"}

    result.setdefault("main_provisions", [])
    result["main_provisions"] = result["main_provisions"][:3]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result
